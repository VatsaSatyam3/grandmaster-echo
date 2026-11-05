"""Retrieval-Augmented Generation over a player's move history.

Every parsed game is embedded and upserted into the configured vector store
(Qdrant in production, in-memory for local/CI).  Before the LangGraph agents
run, the analysis pipeline retrieves the games most semantically similar to
the player's current repertoire and feeds them to the LLM as grounded context.

"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.services.embeddings import embed_texts
from app.services.parser import ParsedGame
from app.services.vector_store import VectorHit, get_available_store

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievedGame:
    """A single RAG hit, normalised for prompt injection and citations."""

    game_id: str
    opening: str
    eco: str
    result: str
    played_as: str
    score: float
    excerpt: str
    document: str

    def as_context(self) -> dict[str, Any]:
        return {
            "game_id": self.game_id,
            "opening": self.opening,
            "eco": self.eco,
            "result": self.result,
            "played_as": self.played_as,
            "similarity": self.score,
            "excerpt": self.document[:400],
        }


def _document_text(game: ParsedGame) -> str:
    """Build the embedded document for one game.

    The text deliberately duplicates the structured metadata in natural
    language so that both lexical (hash fallback) and semantic (Gemini)
    embeddings can match on opening names, results, and move patterns.
    """
    moves = " ".join(game.moves[:60])
    return (
        f"Opening: {game.opening_name} ({game.opening_eco}). "
        f"Played as {game.played_as}. Result: {game.result}. "
        f"Length: {game.num_moves} moves. Time control: {game.time_control}. "
        f"Moves: {moves}"
    )


def _excerpt(text: str, limit: int = 220) -> str:
    """Human-readable citation excerpt (drop the raw move list)."""
    summary = text.split(" Moves:")[0]
    return summary if len(summary) <= limit else summary[: limit - 1].rstrip() + "…"


class MoveHistoryRAG:
    """Index and retrieve a player's games using vector similarity."""

    def __init__(self, top_k: int | None = None) -> None:
        self.top_k = top_k or settings.RAG_TOP_K
        self.store = None
        self._dim = settings.EMBEDDING_DIM

    async def index_games(
        self,
        games: Iterable[ParsedGame],
        *,
        username: str,
        platform: str,
    ) -> int:
        """Embed and upsert games. Returns the number of indexed documents."""
        game_list = list(games)
        if not game_list:
            return 0

        docs = [_document_text(g) for g in game_list]
        vectors = await embed_texts(docs)
        if not vectors:
            return 0

        self._dim = len(vectors[0])
        self.store = await get_available_store()
        await self.store.ensure_collection(self._dim)

        ids = [f"{username}:{platform}:{g.game_id}" for g in game_list]
        payloads = [
            {
                "text": doc,
                "game_id": g.game_id,
                "username": username,
                "platform": platform,
                "opening": g.opening_name,
                "eco": g.opening_eco,
                "result": g.result,
                "played_as": g.played_as,
                "num_moves": g.num_moves,
            }
            for doc, g in zip(docs, game_list)
        ]
        await self.store.upsert(ids, vectors, payloads)
        logger.info("Indexed %d games for %s@%s", len(ids), username, platform)
        return len(ids)

    async def retrieve(
        self,
        query: str,
        *,
        username: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedGame]:
        """Return the games most similar to ``query``."""
        if not query.strip():
            return []

        self.store = self.store or await get_available_store()
        await self.store.ensure_collection(self._dim)

        vectors = await embed_texts([query])
        if not vectors:
            return []

        hits: list[VectorHit] = await self.store.search(
            vectors[0], top_k or self.top_k, username=username
        )
        return [
            RetrievedGame(
                game_id=str(hit.metadata.get("game_id", hit.id)),
                opening=str(hit.metadata.get("opening", "Unknown")),
                eco=str(hit.metadata.get("eco", "A00")),
                result=str(hit.metadata.get("result", "unknown")),
                played_as=str(hit.metadata.get("played_as", "white")),
                score=hit.score,
                excerpt=_excerpt(hit.text),
                document=hit.text,
            )
            for hit in hits
        ]


def build_retrieval_query(
    *,
    username: str,
    opening_stats: list[dict[str, Any]],
    weaknesses: list[str] | None = None,
) -> str:
    """Compose a semantic query from the player's dominant openings."""
    openings = [
        f"{item.get('name', 'Unknown')} ({item.get('eco', 'A00')})"
        for item in opening_stats[:4]
    ]
    parts = [
        f"Tactical patterns and recurring mistakes for {username}.",
        f"Main openings: {', '.join(openings)}." if openings else "",
        f"Focus areas: {', '.join(weaknesses)}." if weaknesses else "",
    ]
    return " ".join(part for part in parts if part)


def to_citations(games: list[RetrievedGame]) -> list[dict[str, Any]]:
    """Convert retrieved games into API citation payloads."""
    return [
        {
            "game_id": g.game_id,
            "opening": g.opening,
            "eco": g.eco,
            "result": g.result,
            "played_as": g.played_as,
            "score": round(g.score, 4),
            "excerpt": g.excerpt,
        }
        for g in games
    ]
