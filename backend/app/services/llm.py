"""Unified LLM provider for Grandmaster Echo.

Primary provider: Google Gemini (REST, no SDK required).
Fallback providers: Groq (OpenAI-compatible REST) and OpenAI via LangChain.

Every call returns a Pydantic-validated structured object, which keeps the
downstream LangGraph nodes type-safe and makes guardrail checks deterministic.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TypeVar

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _strip_code_fence(text: str) -> str:
    """Remove ```json ... ``` wrappers some providers add around JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    return cleaned.strip()


class LLMUnavailableError(RuntimeError):
    """Raised when no provider is configured or every provider fails."""


class LLMProvider:
    """Provider-agnostic structured-output client."""

    def __init__(self) -> None:
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_model = settings.GEMINI_MODEL
        self.groq_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.groq_base = settings.GROQ_BASE_URL.rstrip("/")
        self.openai_key = settings.OPENAI_API_KEY
        # Free-tier Groq keys have small per-minute token budgets. Serialise
        # graph fan-out calls and retry on 429/413 instead of failing the node.
        self._groq_lock = asyncio.Lock()

    @property
    def available(self) -> bool:
        return bool(self.gemini_key or self.groq_key or self.openai_key)

    @property
    def active_provider(self) -> str:
        """Name of the first configured provider, for status reporting."""
        if self.gemini_key:
            return "gemini"
        if self.groq_key:
            return "groq"
        if self.openai_key:
            return "openai"
        return "heuristic"

    async def structured(
        self,
        *,
        system: str,
        human: str,
        schema: type[T],
        temperature: float = 0.3,
        openai_model: str = "gpt-4o-mini",
    ) -> T:
        """Return a validated instance of ``schema``."""
        errors: list[str] = []

        if self.gemini_key:
            try:
                return await self._gemini(system, human, schema, temperature)
            except Exception as exc:  # noqa: BLE001 - provider fallback
                logger.warning("Gemini structured call failed: %s", exc)
                errors.append(f"gemini: {exc}")

        if self.groq_key:
            try:
                return await self._groq(system, human, schema, temperature)
            except Exception as exc:  # noqa: BLE001 - provider fallback
                logger.warning("Groq structured call failed: %s", exc)
                errors.append(f"groq: {exc}")

        if self.openai_key:
            try:
                return await self._openai(
                    system, human, schema, temperature, openai_model
                )
            except Exception as exc:  # noqa: BLE001 - provider fallback
                logger.warning("OpenAI structured call failed: %s", exc)
                errors.append(f"openai: {exc}")

        raise LLMUnavailableError(
            "; ".join(errors) if errors else "No LLM provider configured"
        )

    async def _gemini(
        self,
        system: str,
        human: str,
        schema: type[T],
        temperature: float,
    ) -> T:
        prompt = (
            f"{human}\n\n"
            "Return ONLY valid JSON conforming to this JSON schema:\n"
            f"{json.dumps(schema.model_json_schema(), indent=2)}"
        )
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }
        url = f"{_GEMINI_BASE}/{self.gemini_model}:generateContent"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                url, params={"key": self.gemini_key}, json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return schema.model_validate(json.loads(text))

    async def _groq(
        self,
        system: str,
        human: str,
        schema: type[T],
        temperature: float,
    ) -> T:
        """Groq's OpenAI-compatible chat completions endpoint."""
        prompt = (
            f"{human}\n\n"
            "Return ONLY valid JSON conforming to this JSON schema:\n"
            f"{json.dumps(schema.model_json_schema(), separators=(',', ':'))}"
        )
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 1400,
            "response_format": {"type": "json_object"},
        }

        async with self._groq_lock:
            for attempt in range(3):
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{self.groq_base}/chat/completions",
                        headers={"Authorization": f"Bearer {self.groq_key}"},
                        json=payload,
                    )
                if resp.status_code in {413, 429} and attempt < 2:
                    # Prefer the provider's own reset hint, capped so a
                    # request never stalls the pipeline for too long.
                    reset = resp.headers.get("x-ratelimit-reset-tokens", "")
                    delay = min(8.0, 2.0 * (attempt + 1))
                    if reset.endswith("s"):
                        try:
                            delay = min(8.0, max(1.0, float(reset[:-1])))
                        except ValueError:
                            pass
                    logger.info(
                        "Groq throttled (%s); retrying in %.1fs",
                        resp.status_code,
                        delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    logger.warning(
                        "Groq request rejected (%s): %s",
                        resp.status_code,
                        resp.text[:600],
                    )
                resp.raise_for_status()
                data = resp.json()
                break

        text = data["choices"][0]["message"]["content"]
        return schema.model_validate(json.loads(_strip_code_fence(text)))

    async def _openai(
        self,
        system: str,
        human: str,
        schema: type[T],
        temperature: float,
        model: str,
    ) -> T:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model=model, temperature=temperature)
        structured = llm.with_structured_output(schema)
        result = await structured.ainvoke(
            [SystemMessage(content=system), HumanMessage(content=human)]
        )
        return result  # type: ignore[return-value]


provider = LLMProvider()
