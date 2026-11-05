"""Application configuration loaded from environment variables."""

import os
import shutil
from pydantic_settings import BaseSettings


def _default_stockfish_path() -> str:
    which_path = shutil.which("stockfish")
    if which_path:
        return which_path
    for p in ["/opt/homebrew/bin/stockfish", "/usr/local/bin/stockfish", "/usr/bin/stockfish"]:
        if os.path.exists(p):
            return p
    return "/usr/bin/stockfish"


class Settings(BaseSettings):
    """Central configuration for the Grandmaster Echo backend."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/grandmaster_echo"
    )

    # ── Stockfish engine ──────────────────────────────────────────────────
    STOCKFISH_PATH: str = _default_stockfish_path()
    STOCKFISH_DEPTH: int = 18
    STOCKFISH_THREADS: int = 2
    STOCKFISH_HASH: int = 256

    # ── OpenAI / LLM ─────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── Groq (OpenAI-compatible fallback for fast structured output) ─────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # ── Langfuse observability (optional) ─────────────────────────────────
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str | None = None

    # ── Gemini (primary LLM + embeddings) ─────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # ── Qdrant vector store (RAG over player move histories) ──────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "grandmaster_echo_moves"
    ENABLE_RAG: bool = True
    RAG_TOP_K: int = 5
    EMBEDDING_DIM: int = 768

    # ── External chess APIs ───────────────────────────────────────────────
    CHESS_COM_API_BASE: str = "https://api.chess.com/pub/player"
    LICHESS_API_BASE: str = "https://lichess.org/api"

    # ── Analysis tunables ─────────────────────────────────────────────────
    MAX_GAMES: int = 200
    BLUNDER_THRESHOLD: float = 2.0  # centipawn drop that counts as a blunder

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()
