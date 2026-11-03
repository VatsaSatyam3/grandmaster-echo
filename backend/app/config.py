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

    # ── Langfuse observability (optional) ─────────────────────────────────
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str | None = None

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
