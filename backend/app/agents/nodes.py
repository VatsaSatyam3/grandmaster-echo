"""
LangGraph agent nodes for the Grandmaster Echo profiler.

Each node:
1. Takes the ``ProfilerState`` as input (via a dict representation).
2. Calls an LLM with a specialised chess-expert system prompt plus the
   relevant slice of statistical data.
3. Parses the LLM output into a strict Pydantic schema using
   ``model.with_structured_output()``.
4. Returns a dict of state updates.
5. Is decorated with Langfuse ``@observe()`` for full trace visibility.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

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

from app.agents.schemas import (
    OpeningAnalysis,
    PlayerSynthesis,
    ProfilerState,
    TacticalAudit,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_MODEL_FAST = "gpt-4o-mini"
_MODEL_QUALITY = "gpt-4o"
_TEMPERATURE = 0.3  # low temperature for analytical consistency


# ── Helpers ──────────────────────────────────────────────────────────────────


def _dump(obj: Any) -> str:
    """Compact JSON serialisation for feeding data to the LLM."""
    return json.dumps(obj, indent=2, default=str)


# ── Node 1: Opening Analyst ─────────────────────────────────────────────────

_OPENING_SYSTEM_PROMPT = """\
You are the Opening Analyst module of Grandmaster Echo, an elite chess coaching
system. You possess grandmaster-level knowledge of opening theory, ECO codes,
and the strategic ideas behind every major opening system.

Your task is to analyse raw statistical data about a player's opening choices
and produce a structured assessment. You will receive:

• **opening_stats** – a list of openings played, each with ECO code, name,
  number of games, and win/draw/loss counts.
• **color_stats** – aggregate win/draw/loss percentages for White and Black.
• **total_games** – total number of games in the dataset.

Follow these analytical steps:

1. **Top Openings**: Identify the five most-played openings for each colour.
   For each, report ECO code, full opening name, frequency (game count), and
   win rate (wins ÷ games played with that opening, as a decimal 0.0–1.0).

2. **Repertoire Breadth**: Count unique openings played. If fewer than 5
   distinct openings make up > 80 % of games → "narrow". 5-12 openings →
   "moderate". More than 12 → "wide".

3. **Style Classification**: Based on the *types* of openings favoured,
   classify the player. Consider whether they prefer 1.e4, 1.d4, or
   hypermodern setups; whether they choose sharp Sicilians or solid Slavs;
   whether they play gambits or quiet systems. Produce a short natural-
   language label such as "aggressive e4 player who favours the Sicilian
   Najdorf" or "solid d4 positional player leaning on the Queen's Gambit
   Declined".

4. **Preparation Depth**: Infer how deeply the player follows known theory.
   If their openings tend to be well-known mainlines played to move 15+, that
   is "deep". If they deviate by move 5-6, that is "shallow". Otherwise
   "moderate".

5. **Narrative**: Write 2-3 flowing sentences summarising the player's
   opening identity, suitable for an executive coaching report.

Return your analysis strictly in the requested JSON schema. Do not include
any commentary outside the schema fields.
"""


@observe(name="opening_analyst")
async def opening_analyst_node(state: dict) -> dict:
    """Analyse the player's opening repertoire and classify their style.

    Parameters
    ----------
    state:
        The current ``ProfilerState`` represented as a dict (LangGraph
        convention).

    Returns
    -------
    dict
        State update containing ``opening_analysis``.
    """
    logger.info("Opening Analyst node started for user=%s", state.get("username"))

    try:
        llm = ChatOpenAI(model=_MODEL_FAST, temperature=_TEMPERATURE)
        structured_llm = llm.with_structured_output(OpeningAnalysis)

        human_content = (
            f"Player: {state.get('username', 'unknown')} on {state.get('platform', 'unknown')}\n"
            f"Total games analysed: {state.get('total_games', 0)}\n\n"
            f"## Opening Statistics\n```json\n{_dump(state.get('opening_stats', []))}\n```\n\n"
            f"## Colour Statistics\n```json\n{_dump(state.get('color_stats', {}))}\n```"
        )

        result: OpeningAnalysis = await structured_llm.ainvoke(
            [
                SystemMessage(content=_OPENING_SYSTEM_PROMPT),
                HumanMessage(content=human_content),
            ]
        )

        logger.info("Opening Analyst node completed successfully")
        return {"opening_analysis": result}

    except Exception as exc:
        error_msg = f"Opening Analyst failed: {exc!s}"
        logger.exception(error_msg)
        return {"errors": state.get("errors", []) + [error_msg]}


# ── Node 2: Tactical Auditor ────────────────────────────────────────────────

_TACTICAL_SYSTEM_PROMPT = """\
You are the Tactical Auditor module of Grandmaster Echo, an elite chess
coaching system. You have deep expertise in engine-assisted game analysis,
centipawn-loss interpretation, and pattern recognition in tactical play.

Your task is to synthesise raw Stockfish analysis data into a structured
tactical assessment. You will receive:

• **engine_stats** – aggregate statistics from Stockfish analysis including
  average centipawn loss (ACPL) overall and per phase (opening, middlegame,
  endgame), total blunders, mistakes, inaccuracies, and game count.
• **game_analyses** – per-game analysis summaries, each containing the game's
  ACPL, blunder/mistake/inaccuracy counts, the phase in which the worst
  errors occurred, and any notable patterns flagged by the engine.

Follow these analytical steps:

1. **Overall Accuracy**: Map ACPL to a qualitative label.
   - ACPL ≤ 15 → "very high"
   - 15 < ACPL ≤ 30 → "high"
   - 30 < ACPL ≤ 55 → "moderate"
   - ACPL > 55 → "low"

2. **Blunder Rate**: Compute total blunders ÷ total games as a float rounded
   to two decimal places.

3. **Weakest Phase**: Determine which game phase (opening, middlegame,
   endgame) has the highest average centipawn loss. That is the weakest phase.

4. **Common Blunder Patterns**: Look across the game analyses for recurring
   tactical themes in errors. Examples: "missed back-rank mates", "hangs
   pieces in time pressure", "poor piece coordination in closed positions",
   "overlooks knight forks", "weak calculation in complex middlegames",
   "fails to convert winning endgames". List 3-6 concrete patterns.

5. **Strength Patterns**: Similarly identify 3-5 tactical strengths. Examples:
   "accurate exchange sacrifices", "strong intuitive piece sacrifices",
   "excellent rook endgame technique", "solid defensive resources under
   pressure".

6. **Pressure Response**: Assess how the player performs when the position is
   sharp or complex. Do they maintain accuracy or does their ACPL spike?
   Summarise in 1-2 sentences.

7. **Endgame Competence**: Based on endgame-phase ACPL and specific endgame
   patterns, rate competence as "weak", "adequate", "strong", or "expert".

8. **Narrative**: Write 3-4 flowing sentences summarising the player's
   tactical profile, balancing strengths and weaknesses in a way suitable
   for an executive coaching report.

Return your analysis strictly in the requested JSON schema.
"""


@observe(name="tactical_auditor")
async def tactical_auditor_node(state: dict) -> dict:
    """Synthesise Stockfish analysis data into a tactical assessment.

    Parameters
    ----------
    state:
        The current ``ProfilerState`` represented as a dict.

    Returns
    -------
    dict
        State update containing ``tactical_audit``.
    """
    logger.info("Tactical Auditor node started for user=%s", state.get("username"))

    try:
        llm = ChatOpenAI(model=_MODEL_FAST, temperature=_TEMPERATURE)
        structured_llm = llm.with_structured_output(TacticalAudit)

        human_content = (
            f"Player: {state.get('username', 'unknown')} on {state.get('platform', 'unknown')}\n"
            f"Total games analysed: {state.get('total_games', 0)}\n\n"
            f"## Engine Statistics (Aggregate)\n```json\n{_dump(state.get('engine_stats', {}))}\n```\n\n"
            f"## Per-Game Analyses\n```json\n{_dump(state.get('game_analyses', []))}\n```"
        )

        result: TacticalAudit = await structured_llm.ainvoke(
            [
                SystemMessage(content=_TACTICAL_SYSTEM_PROMPT),
                HumanMessage(content=human_content),
            ]
        )

        logger.info("Tactical Auditor node completed successfully")
        return {"tactical_audit": result}

    except Exception as exc:
        error_msg = f"Tactical Auditor failed: {exc!s}"
        logger.exception(error_msg)
        return {"errors": state.get("errors", []) + [error_msg]}


# ── Node 3: Synthesis Writer ────────────────────────────────────────────────

_SYNTHESIS_SYSTEM_PROMPT = """\
You are the Synthesis Writer module of Grandmaster Echo, an elite chess
coaching system. You combine the outputs of the Opening Analyst and the
Tactical Auditor into a single, cohesive player profile and coaching report.

You have the chess knowledge of a veteran grandmaster coach who has trained
players from club level to international master. You write with clarity,
insight, and motivational tone — direct but encouraging.

You will receive:

• **opening_analysis** – the structured output of the Opening Analyst,
  containing top openings, repertoire breadth, style classification,
  preparation depth, and a narrative.
• **tactical_audit** – the structured output of the Tactical Auditor,
  containing accuracy ratings, blunder patterns, strengths, endgame
  competence, and a narrative.
• **engine_stats** – raw aggregate engine statistics for additional context.
• **total_games** – the number of games in the dataset.

Follow these steps:

1. **Executive Summary**: Write one compelling paragraph (4-6 sentences) that
   captures who this player is on the chessboard. Blend opening identity with
   tactical tendencies. Write as if addressing the player directly ("You are
   …" or "Your play shows …").

2. **Strengths**: Distill the top 3-5 strengths from both analyses. Be
   specific — not "good tactics" but "accurate piece sacrifices in open
   positions" or "deep Sicilian Najdorf preparation".

3. **Weaknesses**: Distill the top 3-5 weaknesses. Again, be specific.

4. **Improvement Priorities**: Create an ordered list (most impactful first)
   of what the player should work on. Each item should be a concrete study
   area, not vague advice.

5. **Playstyle Archetype**: Assign a pithy label that captures the player's
   essence. Examples: "The Aggressive Tactician", "The Solid Positional
   Grinder", "The Hypermodern Strategist", "The Universal Player",
   "The Counter-Puncher".

6. **Comparable GM**: Which famous grandmaster does this player most resemble
   in style? Choose from the full history of chess (Morphy, Capablanca,
   Alekhine, Tal, Petrosian, Fischer, Karpov, Kasparov, Anand, Carlsen,
   Caruana, Nakamura, etc.). Provide the GM name and 1-2 sentences of
   reasoning.

7. **Estimated True Strength**: Based on ACPL, blunder rate, opening
   preparation, and endgame competence, estimate a realistic Elo. Use these
   rough guidelines:
   - ACPL > 60, frequent blunders → 800-1200
   - ACPL 40-60, some blunders → 1200-1500
   - ACPL 25-40, occasional mistakes → 1500-1800
   - ACPL 15-25, rare blunders → 1800-2100
   - ACPL < 15, very few errors → 2100-2400+

8. **Coaching Plan**: Write a specific 3-step improvement plan. Each step
   should name a concrete exercise or study method (e.g., "Solve 20 tactical
   puzzles daily focusing on back-rank motifs on chesstempo.com",
   "Study Capablanca's endgames from 'My Chess Career', focusing on rook
   endgame technique").

Return your analysis strictly in the requested JSON schema.
"""


@observe(name="synthesis_writer")
async def synthesis_writer_node(state: dict) -> dict:
    """Generate the final executive coaching report from prior node outputs.

    Parameters
    ----------
    state:
        The current ``ProfilerState`` represented as a dict.  By this point
        both ``opening_analysis`` and ``tactical_audit`` should be populated.

    Returns
    -------
    dict
        State update containing ``player_synthesis``.
    """
    logger.info("Synthesis Writer node started for user=%s", state.get("username"))

    try:
        llm = ChatOpenAI(model=_MODEL_QUALITY, temperature=_TEMPERATURE)
        structured_llm = llm.with_structured_output(PlayerSynthesis)

        # Serialise upstream node outputs — they may be Pydantic models or
        # already dicts depending on LangGraph's internal handling.
        opening_raw = state.get("opening_analysis")
        tactical_raw = state.get("tactical_audit")

        def _to_dict(obj: Any) -> dict:
            if obj is None:
                return {}
            if isinstance(obj, dict):
                return obj
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return dict(obj)

        human_content = (
            f"Player: {state.get('username', 'unknown')} on {state.get('platform', 'unknown')}\n"
            f"Total games: {state.get('total_games', 0)}\n\n"
            f"## Opening Analysis\n```json\n{_dump(_to_dict(opening_raw))}\n```\n\n"
            f"## Tactical Audit\n```json\n{_dump(_to_dict(tactical_raw))}\n```\n\n"
            f"## Engine Statistics\n```json\n{_dump(state.get('engine_stats', {}))}\n```"
        )

        result: PlayerSynthesis = await structured_llm.ainvoke(
            [
                SystemMessage(content=_SYNTHESIS_SYSTEM_PROMPT),
                HumanMessage(content=human_content),
            ]
        )

        logger.info("Synthesis Writer node completed successfully")
        return {"player_synthesis": result}

    except Exception as exc:
        error_msg = f"Synthesis Writer failed: {exc!s}"
        logger.exception(error_msg)
        return {"errors": state.get("errors", []) + [error_msg]}
