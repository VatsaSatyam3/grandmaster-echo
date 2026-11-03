"""SQLAlchemy ORM models for the Grandmaster Echo database."""

from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JSON_TYPE = JSON().with_variant(JSONB, "postgresql")


class Player(Base):
    """A chess player tracked by username and platform."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    current_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    games: Mapped[list["Game"]] = relationship(
        "Game", back_populates="player", cascade="all, delete-orphan"
    )
    profiles: Mapped[list["PlayerProfile"]] = relationship(
        "PlayerProfile", back_populates="player", cascade="all, delete-orphan"
    )


class Game(Base):
    """A single chess game with metadata and PGN."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    game_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    pgn: Mapped[str] = mapped_column(Text, nullable=False)
    opening_eco: Mapped[str | None] = mapped_column(String(10), nullable=True)
    opening_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    result: Mapped[str | None] = mapped_column(String(10), nullable=True)
    time_control: Mapped[str | None] = mapped_column(String(50), nullable=True)
    played_as: Mapped[str | None] = mapped_column(String(5), nullable=True)  # 'white' or 'black'
    num_moves: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="games")
    evals: Mapped[list["GameEval"]] = relationship(
        "GameEval", back_populates="game", cascade="all, delete-orphan"
    )


class GameEval(Base):
    """Per-move engine evaluation for a game."""

    __tablename__ = "game_evals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    move_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fen: Mapped[str | None] = mapped_column(Text, nullable=True)
    eval_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    eval_diff: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_blunder: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    best_move: Mapped[str | None] = mapped_column(String(10), nullable=True)
    played_move: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phase: Mapped[str | None] = mapped_column(String(20), nullable=True)  # opening / middlegame / endgame

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="evals")


class PlayerProfile(Base):
    """AI-generated profile summarising a player's style and patterns."""

    __tablename__ = "player_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    strengths: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    weaknesses: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    opening_repertoire: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    tactical_patterns: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    endgame_profile: Mapped[dict | None] = mapped_column(JSON_TYPE, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_elo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blunder_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_centipawn_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    player: Mapped["Player"] = relationship("Player", back_populates="profiles")
