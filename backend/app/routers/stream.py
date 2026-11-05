"""Server-Sent Events (SSE) streaming for the analysis pipeline.

Event format (SSE)::

    event: progress
    data: {"event": "progress", "stage": "agents", "rag_documents": 5}

    event: result
    data: {"event": "result", "data": { ...AnalyzeResponse... }}
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.database import async_session
from app.routers.analyze import _run_pipeline
from app.schemas import AnalyzeRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["stream"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _format_event(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"


@router.get("/analyze/{username}")
async def stream_analysis(
    username: str,
    platform: str = Query("chesscom"),
) -> StreamingResponse:
    """Stream analysis progress and the final profile over SSE."""

    async def event_generator() -> AsyncIterator[str]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        async def emit(stage: str, payload: dict[str, Any]) -> None:
            await queue.put({"event": "progress", "stage": stage, **payload})

        async def run_pipeline() -> None:
            async with async_session() as session:
                try:
                    response = await _run_pipeline(
                        AnalyzeRequest(username=username, platform=platform),
                        session,
                        emit=emit,
                    )
                    await queue.put(
                        {
                            "event": "result",
                            "data": response.model_dump(mode="json"),
                        }
                    )
                except Exception as exc:  # noqa: BLE001 - surfaced to client
                    logger.exception("Streaming pipeline failed")
                    await queue.put(
                        {"event": "error", "message": str(exc)}
                    )

        task = asyncio.create_task(run_pipeline())
        yield _format_event(
            "progress",
            {"event": "progress", "stage": "queued", "username": username},
        )

        try:
            while True:
                item = await queue.get()
                event = item.get("event", "message")
                yield _format_event(event, item)
                if event in {"result", "error"}:
                    break
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    return StreamingResponse(
        event_generator(), media_type="text/event-stream", headers=_SSE_HEADERS
    )
