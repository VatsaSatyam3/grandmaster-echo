"""
LangGraph profiler workflow for Grandmaster Echo.

Graph topology (parallel fan-out / fan-in)::

    START ──┬── opening_analyst  ──┬── synthesis_writer ── END
            └── tactical_auditor ──┘

The *opening_analyst* and *tactical_auditor* run **in parallel** because
they consume independent slices of the input data.  The *synthesis_writer*
waits for both to complete before generating the final coaching report.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph

try:
    from langfuse import observe
except ImportError:
    try:
        from langfuse.decorators import observe
    except ImportError:
        def observe(*args, **kwargs):
            def decorator(fn):
                return fn
            return decorator
from pydantic import BaseModel, Field

from app.agents.nodes import (
    opening_analyst_node,
    synthesis_writer_node,
    tactical_auditor_node,
)
from app.agents.schemas import (
    OpeningAnalysis,
    PlayerSynthesis,
    TacticalAudit,
)

logger = logging.getLogger(__name__)


# ── Graph-compatible state ───────────────────────────────────────────────────
# LangGraph requires the state to support *reducer* semantics so that
# parallel branches can merge cleanly.  For list fields that accumulate
# (like ``errors``) we use an annotation with an ``operator.add`` reducer.
# For all other fields the default "last writer wins" behaviour is fine.

def _merge_lists(left: list[str], right: list[str]) -> list[str]:
    """Reducer that concatenates two error lists during fan-in."""
    return left + right


class GraphState(BaseModel):
    """Internal state schema wired into the StateGraph.

    Mirrors :class:`~app.agents.schemas.ProfilerState` but uses LangGraph-
    compatible reducer annotations so parallel branches can merge without
    conflict.
    """

    # ── Inputs (immutable across nodes) ──────────────────────────────────
    username: str = ""
    platform: str = ""
    opening_stats: list[dict] = Field(default_factory=list)
    color_stats: dict = Field(default_factory=dict)
    engine_stats: dict = Field(default_factory=dict)
    game_analyses: list[dict] = Field(default_factory=list)
    total_games: int = 0

    # ── Node outputs ─────────────────────────────────────────────────────
    opening_analysis: OpeningAnalysis | None = None
    tactical_audit: TacticalAudit | None = None
    player_synthesis: PlayerSynthesis | None = None

    # ── Metadata (uses add-reducer so parallel errors merge) ─────────────
    errors: Annotated[list[str], _merge_lists] = Field(default_factory=list)


# ── Graph builder ────────────────────────────────────────────────────────────


def build_profiler_graph() -> Any:
    """Construct and compile the profiler ``StateGraph``.

    Returns
    -------
    CompiledGraph
        A compiled LangGraph graph ready to be invoked with a ``GraphState``
        (or an equivalent dict).
    """
    graph = StateGraph(GraphState)

    # Register nodes
    graph.add_node("opening_analyst", opening_analyst_node)
    graph.add_node("tactical_auditor", tactical_auditor_node)
    graph.add_node("synthesis_writer", synthesis_writer_node)

    # Fan-out: START → both analysts run in parallel
    graph.add_edge(START, "opening_analyst")
    graph.add_edge(START, "tactical_auditor")

    # Fan-in: both analysts → synthesis writer
    graph.add_edge("opening_analyst", "synthesis_writer")
    graph.add_edge("tactical_auditor", "synthesis_writer")

    # Terminal
    graph.add_edge("synthesis_writer", END)

    compiled = graph.compile()
    logger.info("Profiler graph compiled successfully")
    return compiled


# Keep a module-level singleton so the graph is compiled once at import time
# and reused across requests.
_compiled_graph = None


def _get_graph() -> Any:
    """Lazy singleton accessor for the compiled graph."""
    global _compiled_graph  # noqa: PLW0603
    if _compiled_graph is None:
        _compiled_graph = build_profiler_graph()
    return _compiled_graph


# ── Public entry point ───────────────────────────────────────────────────────


@observe(name="profiler_graph")
async def run_profiler_graph(
    username: str,
    platform: str,
    opening_stats: list[dict],
    color_stats: dict,
    engine_stats: dict,
    game_analyses: list[dict],
    total_games: int,
) -> GraphState:
    """Build the initial state and execute the full profiler graph.

    This is the primary public interface.  It constructs the input state,
    invokes the compiled LangGraph graph, and returns the fully-populated
    ``GraphState`` containing all node outputs.

    Parameters
    ----------
    username:
        The player's username on the chess platform.
    platform:
        Chess platform identifier (e.g. ``"lichess"``, ``"chess.com"``).
    opening_stats:
        List of opening-frequency dicts from the data pipeline.
    color_stats:
        Aggregate win/draw/loss stats per colour.
    engine_stats:
        Aggregate Stockfish analysis statistics (ACPL, blunders, etc.).
    game_analyses:
        Per-game engine analysis summaries.
    total_games:
        Total number of games in the dataset.

    Returns
    -------
    GraphState
        The final state with ``opening_analysis``, ``tactical_audit``,
        ``player_synthesis`` populated (and any ``errors`` accumulated).
    """
    logger.info(
        "Running profiler graph for %s@%s (%d games)",
        username,
        platform,
        total_games,
    )

    initial_state: dict[str, Any] = {
        "username": username,
        "platform": platform,
        "opening_stats": opening_stats,
        "color_stats": color_stats,
        "engine_stats": engine_stats,
        "game_analyses": game_analyses,
        "total_games": total_games,
        "errors": [],
    }

    compiled = _get_graph()
    final_state = await compiled.ainvoke(initial_state)

    # ``final_state`` is a dict; coerce to GraphState for a typed return.
    result = GraphState(**final_state)

    if result.errors:
        logger.warning(
            "Profiler graph completed with %d error(s): %s",
            len(result.errors),
            result.errors,
        )
    else:
        logger.info("Profiler graph completed successfully")

    return result
