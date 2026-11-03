"""FastAPI application entry-point for Grandmaster Echo."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import analyze, bot


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle hook."""
    await init_db()
    yield


app = FastAPI(
    title="Grandmaster Echo API",
    description=(
        "Analyse chess games, build player profiles, and play against "
        "an AI bot that mimics a real player's style."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow-all for local dev) ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze.router, prefix="/api")
app.include_router(bot.router, prefix="/api")


# ── Root & health ─────────────────────────────────────────────────────────────


@app.get("/")
async def root() -> dict[str, str]:
    """Welcome message at the API root."""
    return {
        "message": "Welcome to Grandmaster Echo – the chess style analyzer & bot API.",
    }


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}
