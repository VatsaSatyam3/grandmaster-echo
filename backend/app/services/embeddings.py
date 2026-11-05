"""Embedding provider: Gemini embeddings with a deterministic fallback.

The fallback (hashed bag-of-words) keeps RAG functional offline / in CI where
no API key is available, so retrieval never hard-fails the analysis pipeline.
"""

from __future__ import annotations

import hashlib
import logging
import math

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _hash_embedding(text: str, dim: int) -> list[float]:
    vec = [0.0] * dim
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        vec[int(digest, 16) % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, preferring Gemini and falling back to hashing."""
    if not texts:
        return []

    if settings.GEMINI_API_KEY:
        try:
            return await _gemini_embed(texts)
        except Exception as exc:  # noqa: BLE001 - graceful degradation
            logger.warning("Gemini embeddings failed (%s); using hash fallback", exc)

    return [_hash_embedding(text, settings.EMBEDDING_DIM) for text in texts]


async def _gemini_embed(texts: list[str]) -> list[list[float]]:
    url = f"{_GEMINI_BASE}/{settings.GEMINI_EMBEDDING_MODEL}:batchEmbedContents"
    requests = [
        {
            "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": settings.EMBEDDING_DIM,
        }
        for text in texts
    ]
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            url,
            params={"key": settings.GEMINI_API_KEY},
            json={"requests": requests},
        )
        resp.raise_for_status()
        data = resp.json()

    return [item["values"] for item in data["embeddings"]]
