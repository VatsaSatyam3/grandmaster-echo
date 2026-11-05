"""Pydantic v2 request / response schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Player ────────────────────────────────────────────────────────────────────


class PlayerCreate(BaseModel):
    """Payload to register or look up a player."""

    username: str
    platform: str


class PlayerResponse(BaseModel):
    """Public representation of a player row."""

    id: int
    username: str
    platform: str
    current_rating: int | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Game ──────────────────────────────────────────────────────────────────────


class GameResponse(BaseModel):
    """Summary of one analysed game (no PGN blob)."""

    id: int
    game_id: str | None = None
    opening_eco: str | None = None
    opening_name: str | None = None
    result: str | None = None
    played_as: str | None = None
    num_moves: int | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Game evaluation ───────────────────────────────────────────────────────────


class GameEvalResponse(BaseModel):
    """Single-move engine evaluation."""

    move_number: int | None = None
    fen: str | None = None
    eval_score: float | None = None
    eval_diff: float | None = None
    is_blunder: bool | None = None
    best_move: str | None = None
    played_move: str | None = None
    phase: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Opening statistics ────────────────────────────────────────────────────────


class OpeningStats(BaseModel):
    """Aggregated stats for a single opening."""

    eco: str
    name: str
    games: int = 0
    count: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    win_rate: float = 0.0
    draw_rate: float = 0.0
    loss_rate: float = 0.0

    model_config = ConfigDict(populate_by_name=True)


# ── Coaching Step ─────────────────────────────────────────────────────────────


class CoachingStep(BaseModel):
    step: int
    title: str
    description: str


# ── Player profile ────────────────────────────────────────────────────────────


class PlayerProfile(BaseModel):
    """AI-generated chess profile."""

    username: str | None = None
    platform: str | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opening_repertoire: Any | None = None
    opening_repertoire_white: list[OpeningStats] = Field(default_factory=list)
    opening_repertoire_black: list[OpeningStats] = Field(default_factory=list)
    tactical_patterns: Any | None = None
    endgame_profile: Any | None = None
    summary_text: str | None = None
    executive_summary: str | None = None
    playstyle_archetype: str | None = "Dynamic Tactician"
    comparable_gm: str | None = "Garry Kasparov"
    improvement_priorities: list[str] = Field(default_factory=list)
    estimated_elo: int = 1500
    blunder_rate: float = 0.05
    avg_centipawn_loss: float = 45.0
    games_analyzed: int = 0

    model_config = ConfigDict(from_attributes=True)


# ── RAG / guardrails / evals ──────────────────────────────────────────────────


class RAGCitation(BaseModel):
    """A retrieved game that grounded the generated analysis."""

    game_id: str
    opening: str = "Unknown"
    eco: str = "A00"
    result: str = "unknown"
    played_as: str = "white"
    score: float = 0.0
    excerpt: str = ""


class GuardrailIssue(BaseModel):
    """A single guardrail finding."""

    rule: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    corrected: bool = False


class GuardrailResult(BaseModel):
    """Outcome of the LLM output guardrail layer."""

    passed: bool = True
    checks_run: int = 0
    issues: list[GuardrailIssue] = Field(default_factory=list)


class EvalMetrics(BaseModel):
    """Automated evaluation scores for one analysis run."""

    overall: float = 0.0
    schema_validity: float = 0.0
    elo_alignment: float = 0.0
    opening_grounding: float = 0.0
    citation_coverage: float = 0.0
    guardrail_pass: float = 0.0
    latency_ms: float = 0.0


# ── Analyze request / response ────────────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Kick off a full analysis pipeline for a player."""

    username: str
    platform: str = "chesscom"


class AnalyzeResponse(BaseModel):
    """Result of a completed analysis run."""

    player: PlayerResponse
    profile: PlayerProfile
    games_analyzed: int
    openings: list[OpeningStats] = Field(default_factory=list)
    coaching_plan: list[CoachingStep] = Field(default_factory=list)
    citations: list[RAGCitation] = Field(default_factory=list)
    rag_enabled: bool = False
    guardrails: GuardrailResult = Field(default_factory=GuardrailResult)
    evals: EvalMetrics = Field(default_factory=EvalMetrics)
    pipeline_ms: dict[str, float] = Field(default_factory=dict)


# ── Bot ───────────────────────────────────────────────────────────────────────


class BotMoveRequest(BaseModel):
    """Ask the impersonation bot for a move."""

    fen: str
    player_username: str
    platform: str | None = None


class BotMoveResponse(BaseModel):
    """The bot's chosen move and its reasoning."""

    move: str
    explanation: str
    source: str = "stockfish_clone"
    fen_after: str | None = None
    evaluation: float = 0.0
