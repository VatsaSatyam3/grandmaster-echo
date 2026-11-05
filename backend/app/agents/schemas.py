"""
Pydantic v2 output schemas for the Grandmaster Echo profiler agent graph.

Each schema maps to a single LangGraph node's structured output.
ProfilerState is the shared state object that flows through the entire graph.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Node output schemas ─────────────────────────────────────────────────────


class OpeningAnalysis(BaseModel):
    """Output schema for the Opening Analyst node."""

    primary_openings_white: list[dict] = Field(
        description=(
            "Top 5 openings as White with ECO code, name, frequency (number of "
            "games), and win_rate (0.0–1.0)"
        ),
    )
    primary_openings_black: list[dict] = Field(
        description=(
            "Top 5 openings as Black with ECO code, name, frequency (number of "
            "games), and win_rate (0.0–1.0)"
        ),
    )
    repertoire_breadth: str = Field(
        description="'narrow', 'moderate', or 'wide' based on number of unique openings played",
    )
    style_classification: str = Field(
        description=(
            "Natural-language style tag, e.g. 'aggressive e4 player', "
            "'solid d4 positional player', 'hypermodern'"
        ),
    )
    opening_preparation_depth: str = Field(
        description=(
            "'shallow' (deviates early), 'moderate', or 'deep' (follows "
            "theory deep into known lines)"
        ),
    )
    narrative: str = Field(
        description="2-3 sentence natural language summary of the player's opening tendencies",
    )


class TacticalAudit(BaseModel):
    """Output schema for the Tactical Auditor node."""

    overall_accuracy: str = Field(
        description="'low', 'moderate', 'high', or 'very high' based on average centipawn loss",
    )
    blunder_rate_per_game: float = Field(
        description="Average number of blunders per game across all analysed games",
    )
    weakest_phase: str = Field(
        description="'opening', 'middlegame', or 'endgame' — the phase with the most errors",
    )
    common_blunder_patterns: list[str] = Field(
        description="List of identified tactical weakness patterns (e.g. 'missed back-rank mates')",
    )
    strength_patterns: list[str] = Field(
        description="List of identified tactical strengths (e.g. 'strong exchange sacrifices')",
    )
    pressure_response: str = Field(
        description="How the player handles complex/sharp positions under pressure",
    )
    endgame_competence: str = Field(
        description="Assessment of endgame play quality ('weak', 'adequate', 'strong', 'expert')",
    )
    narrative: str = Field(
        description="3-4 sentence tactical assessment summarising accuracy and patterns",
    )


class PlayerSynthesis(BaseModel):
    """Output schema for the Synthesis Writer node."""

    executive_summary: str = Field(
        description="One paragraph executive coaching summary of the player's profile",
    )
    strengths: list[str] = Field(
        description="Top 3-5 identified strengths",
    )
    weaknesses: list[str] = Field(
        description="Top 3-5 identified weaknesses",
    )
    improvement_priorities: list[str] = Field(
        description="Ordered list of what to work on first, second, third, etc.",
    )
    playstyle_archetype: str = Field(
        description=(
            "A pithy archetype label, e.g. 'The Aggressive Tactician', "
            "'The Solid Positional Grinder'"
        ),
    )
    comparable_gm: str = Field(
        description=(
            "Which famous GM this player's style most resembles, with a "
            "sentence of reasoning"
        ),
    )
    estimated_true_strength: int = Field(
        description="Estimated Elo rating based on observed play quality",
    )
    coaching_plan: str = Field(
        description="Specific 3-step improvement plan with actionable exercises",
    )


# ── LangGraph shared state ──────────────────────────────────────────────────


class ProfilerState(BaseModel):
    """LangGraph state that flows through the profiler agent graph.

    The *input* fields are populated before the graph is invoked.
    The *node output* fields are populated as the respective nodes complete.
    ``errors`` accumulates any non-fatal issues encountered during execution.
    """

    # ── Inputs ───────────────────────────────────────────────────────────
    username: str = ""
    platform: str = ""
    opening_stats: list[dict] = Field(default_factory=list)
    color_stats: dict = Field(default_factory=dict)
    engine_stats: dict = Field(default_factory=dict)
    game_analyses: list[dict] = Field(default_factory=list)
    total_games: int = 0
    # Retrieved similar games from the Qdrant RAG loop.
    rag_context: list[dict] = Field(default_factory=list)

    # ── Node outputs (populated as the graph executes) ───────────────────
    opening_analysis: OpeningAnalysis | None = None
    tactical_audit: TacticalAudit | None = None
    player_synthesis: PlayerSynthesis | None = None

    # ── Metadata ─────────────────────────────────────────────────────────
    errors: list[str] = Field(default_factory=list)
