"""Vector store abstraction: Qdrant (REST) with an in-memory fallback.
The in-memory store
keeps local development and CI completely dependency-free when Qdrant is not
running.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VectorHit:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class BaseVectorStore:
    async def ensure_collection(self, dim: int) -> None:  # pragma: no cover
        raise NotImplementedError

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:  # pragma: no cover
        raise NotImplementedError

    async def search(
        self,
        vector: list[float],
        top_k: int,
        username: str | None = None,
    ) -> list[VectorHit]:  # pragma: no cover
        raise NotImplementedError


class InMemoryVectorStore(BaseVectorStore):
    """Cosine-similarity store used when Qdrant is unreachable."""

    def __init__(self) -> None:
        self.points: list[tuple[str, list[float], dict[str, Any]]] = []
        self.dim = 0

    async def ensure_collection(self, dim: int) -> None:
        self.dim = dim

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        existing = {point_id for point_id, _, _ in self.points}
        for point_id, vector, payload in zip(ids, vectors, payloads):
            if point_id in existing:
                # Replace the previous document to keep re-analysis idempotent.
                self.points = [
                    point for point in self.points if point[0] != point_id
                ]
            self.points.append((point_id, vector, payload))
            existing.add(point_id)
        if vectors and not self.dim:
            self.dim = len(vectors[0])

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    async def search(
        self,
        vector: list[float],
        top_k: int,
        username: str | None = None,
    ) -> list[VectorHit]:
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for point_id, stored, payload in self.points:
            if username and payload.get("username") != username:
                continue
            scored.append((self._cosine(vector, stored), point_id, payload))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            VectorHit(
                id=point_id,
                text=payload.get("text", ""),
                metadata=payload,
                score=round(score, 4),
            )
            for score, point_id, payload in scored[:top_k]
        ]


class QdrantVectorStore(BaseVectorStore):
    """Thin REST client for Qdrant (no SDK dependency)."""

    def __init__(self) -> None:
        self.base = settings.QDRANT_URL.rstrip("/")
        self.collection = settings.QDRANT_COLLECTION
        self.headers: dict[str, str] = {}
        if settings.QDRANT_API_KEY:
            self.headers["api-key"] = settings.QDRANT_API_KEY
        self._ready = False

    async def ensure_collection(self, dim: int) -> None:
        if self._ready:
            return

        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as client:
            resp = await client.get(f"{self.base}/collections/{self.collection}")
            if resp.status_code == 404:
                resp = await client.put(
                    f"{self.base}/collections/{self.collection}",
                    json={"vectors": {"size": dim, "distance": "Cosine"}},
                )
                resp.raise_for_status()
            elif resp.status_code >= 400:
                resp.raise_for_status()

            # Qdrant Cloud enforces payload filtering: without a keyword index
            # on `username`, filtered searches fail with HTTP 400.
            index_resp = await client.put(
                f"{self.base}/collections/{self.collection}/index",
                params={"wait": "true"},
                json={"field_name": "username", "field_schema": "keyword"},
            )
            if index_resp.status_code >= 400:
                index_resp.raise_for_status()

        self._ready = True

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        points = [
            {
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, point_id)),
                "vector": vector,
                "payload": payload,
            }
            for point_id, vector, payload in zip(ids, vectors, payloads)
        ]
        async with httpx.AsyncClient(timeout=30.0, headers=self.headers) as client:
            resp = await client.put(
                f"{self.base}/collections/{self.collection}/points?wait=true",
                json={"points": points},
            )
            resp.raise_for_status()

    async def search(
        self,
        vector: list[float],
        top_k: int,
        username: str | None = None,
    ) -> list[VectorHit]:
        body: dict[str, Any] = {
            "vector": vector,
            "limit": top_k,
            "with_payload": True,
        }
        if username:
            body["filter"] = {
                "must": [{"key": "username", "match": {"value": username}}]
            }

        async with httpx.AsyncClient(timeout=15.0, headers=self.headers) as client:
            resp = await client.post(
                f"{self.base}/collections/{self.collection}/points/search",
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            VectorHit(
                id=str(hit.get("id", "")),
                text=(hit.get("payload") or {}).get("text", ""),
                metadata=hit.get("payload") or {},
                score=float(hit.get("score", 0.0)),
            )
            for hit in data.get("result", [])
        ]


async def _qdrant_available() -> bool:
    headers: dict[str, str] = {}
    if settings.QDRANT_API_KEY:
        headers["api-key"] = settings.QDRANT_API_KEY
    try:
        async with httpx.AsyncClient(timeout=2.0, headers=headers) as client:
            resp = await client.get(f"{settings.QDRANT_URL.rstrip('/')}/collections")
            return resp.status_code < 500
    except Exception:  # noqa: BLE001 - availability probe
        return False


def _select_store() -> BaseVectorStore:
    # Prefer Qdrant; the caller will fall back to memory if the first call fails.
    try:
        return QdrantVectorStore()
    except Exception as exc:  # noqa: BLE001 - defensive
        logger.info("Qdrant client unavailable (%s); using in-memory store", exc)
        return InMemoryVectorStore()


_STORE: BaseVectorStore | None = None


def get_vector_store() -> BaseVectorStore:
    global _STORE
    if _STORE is None:
        _STORE = _select_store()
    return _STORE


async def get_available_store() -> BaseVectorStore:
    """Return a store that is guaranteed to respond."""
    global _STORE
    store = get_vector_store()
    if isinstance(store, QdrantVectorStore) and not await _qdrant_available():
        logger.info("Qdrant unreachable; switching to in-memory vector store")
        _STORE = InMemoryVectorStore()
    return _STORE  # type: ignore[return-value]
