"""Async SQLAlchemy engine, session factory, and helpers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

engine_kwargs: dict = {"echo": False}
if "sqlite" in settings.DATABASE_URL:
    # Wait for concurrent writers instead of failing immediately.
    engine_kwargs["connect_args"] = {"timeout": 30}
else:
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    })

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables (dev convenience; production should use Alembic)."""
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
