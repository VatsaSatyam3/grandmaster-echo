"""Automated evaluation metrics for LLM-generated analysis.

Metrics
-------
``schema_validity``    Required fields are populated and internally coherent.
``elo_alignment``      Closeness of the LLM estimate to the engine estimate.
``opening_grounding``  Narrative references the player's real repertoire.
``citation_coverage``  Fraction of retrieved RAG hits surfaced as citations.
``guardrail_pass``     1.0 when the guardrail layer reports no errors.
``overall``            Weighted composite in [0, 1].
"""

from __future__ import annotations

import logging
from typing import Any

from app.schemas import EvalMetrics

logger = logging.getLogger(__name__)

# Composite weights (sum to 1.0)
_WEIGHTS = {
    "schema_validity": 0.25,
    "elo_alignment": 0.25,
    "opening_grounding": 0.20,
    "citation_coverage": 0.15,
    "guardrail_pass": 0.15,
}


def _elo_alignment(estimated_elo: int, stockfish_elo: int) -> float:
    """1.0 at zero deviation, decaying linearly to 0 at 800 Elo."""
    deviation = abs(int(estimated_elo) - int(stockfish_elo))
    return round(max(0.0, 1.0 - deviation / 800.0), 4)


def _opening_grounding(summary: str, opening_names: list[str]) -> float:
    if not opening_names:
        return 1.0
    narrative = (summary or "").lower()
    matched = sum(1 for name in opening_names if name.lower() in narrative)
    # Full credit once at least two real openings are referenced.
    return round(min(1.0, matched / 2.0), 4)


def run_evals(
    *,
    estimated_elo: int,
    stockfish_elo: int,
    executive_summary: str,
    opening_names: list[str],
    citation_count: int,
    top_k: int,
    guardrail_passed: bool,
    strengths: list[str] | None = None,
    weaknesses: list[str] | None = None,
    priorities: list[str] | None = None,
    latency_ms: float = 0.0,
) -> EvalMetrics:
    """Compute the evaluation bundle for one analysis run."""
    schema_validity = 1.0
    if not executive_summary or len(executive_summary.strip()) < 40:
        schema_validity = 0.0
    if not strengths or not weaknesses or not priorities:
        schema_validity = min(schema_validity, 0.5)

    citation_coverage = round(min(1.0, citation_count / max(1, top_k)), 4)
    elo_alignment = _elo_alignment(estimated_elo, stockfish_elo)
    grounding = _opening_grounding(executive_summary, opening_names)
    guardrail_score = 1.0 if guardrail_passed else 0.0

    overall = round(
        _WEIGHTS["schema_validity"] * schema_validity
        + _WEIGHTS["elo_alignment"] * elo_alignment
        + _WEIGHTS["opening_grounding"] * grounding
        + _WEIGHTS["citation_coverage"] * citation_coverage
        + _WEIGHTS["guardrail_pass"] * guardrail_score,
        4,
    )

    metrics = EvalMetrics(
        overall=overall,
        schema_validity=schema_validity,
        elo_alignment=elo_alignment,
        opening_grounding=grounding,
        citation_coverage=citation_coverage,
        guardrail_pass=guardrail_score,
        latency_ms=round(latency_ms, 2),
    )
    logger.info("Evals: %s", metrics.model_dump())
    return metrics


def aggregate(metrics: list[EvalMetrics]) -> dict[str, Any]:
    """Average a batch of eval results (used by offline eval harnesses)."""
    if not metrics:
        return {}
    keys = [
        "schema_validity",
        "elo_alignment",
        "opening_grounding",
        "citation_coverage",
        "guardrail_pass",
        "overall",
    ]
    return {
        key: round(sum(getattr(m, key) for m in metrics) / len(metrics), 4)
        for key in keys
    }
