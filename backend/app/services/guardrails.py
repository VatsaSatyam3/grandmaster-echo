"""Runtime guardrails for LLM-generated chess analysis.

The guardrails are deliberately deterministic and cheap.  They run *after*
the LangGraph agents and validate the generated profile against the
Stockfish-derived ground truth before the response is returned or persisted.

Rules
-----
1. **Schema completeness** — required narrative fields must be present.
2. **Elo plausibility** — LLM-estimated strength must be within a tolerance
   of the Stockfish/ACPL-derived estimate.
3. **Opening grounding** — the narrative must reference an opening the player
   actually played, not an invented repertoire.
4. **Unsupported certainty** — reject absolute claims ("guaranteed win",
   "100% accuracy", "never loses") that an analysis engine cannot support.
5. **Blunder-rate sanity** — a claimed blunder rate may not contradict the
   engine aggregate by more than the configured tolerance.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.schemas import GuardrailIssue, GuardrailResult

logger = logging.getLogger(__name__)

ELO_TOLERANCE = 400
BLUNDER_TOLERANCE = 0.15
MIN_BLUNDER_RATE = 0.0
MAX_BLUNDER_RATE = 1.0

_UNSUPPORTED_CERTAINTY = [
    r"\bguaranteed\s+win\b",
    r"\b100%\s+accuracy\b",
    r"\bnever\s+loses?\b",
    r"\bperfect\s+play\b",
    r"\bunbeatable\b",
]


def _issue(
    rule: str,
    message: str,
    severity: str = "warning",
    corrected: bool = False,
) -> GuardrailIssue:
    return GuardrailIssue(
        rule=rule, message=message, severity=severity, corrected=corrected
    )


def apply_guardrails(
    *,
    estimated_elo: int,
    stockfish_elo: int,
    executive_summary: str,
    opening_names: list[str],
    blunder_rate: float,
    engine_blunder_rate: float,
) -> tuple[GuardrailResult, int]:
    """Validate the synthesis and return ``(result, safe_elo)``.

    ``safe_elo`` is the value the API should use.  When the LLM estimate is
    implausible it is clamped to a Stockfish-derived band and the correction
    is recorded in the result.
    """
    issues: list[GuardrailIssue] = []
    checks = 0

    # 1. Schema completeness
    checks += 1
    if not executive_summary or len(executive_summary.strip()) < 40:
        issues.append(
            _issue(
                "schema_completeness",
                "Executive summary is missing or too short to be useful.",
                severity="error",
            )
        )

    # 2. Elo plausibility
    checks += 1
    safe_elo = int(estimated_elo)
    deviation = abs(int(estimated_elo) - int(stockfish_elo))
    if deviation > ELO_TOLERANCE:
        lower = max(600, stockfish_elo - 200)
        upper = min(3000, stockfish_elo + 200)
        safe_elo = max(lower, min(upper, int(estimated_elo)))
        issues.append(
            _issue(
                "elo_plausibility",
                (
                    f"LLM estimate {estimated_elo} deviates from Stockfish-derived "
                    f"estimate {stockfish_elo} by {deviation} Elo; clamped to {safe_elo}."
                ),
                severity="warning",
                corrected=True,
            )
        )
        logger.info("Guardrail clamped Elo %s -> %s", estimated_elo, safe_elo)

    # 3. Opening grounding
    checks += 1
    narrative = (executive_summary or "").lower()
    if opening_names and not any(name.lower() in narrative for name in opening_names):
        issues.append(
            _issue(
                "opening_grounding",
                (
                    "Executive summary does not reference any opening present in "
                    "the parsed repertoire."
                ),
                severity="warning",
            )
        )

    # 4. Unsupported certainty
    checks += 1
    for pattern in _UNSUPPORTED_CERTAINTY:
        if re.search(pattern, narrative):
            issues.append(
                _issue(
                    "unsupported_certainty",
                    f"Removed an unsupported absolute claim matching /{pattern}/.",
                    severity="warning",
                    corrected=True,
                )
            )

    # 5. Blunder-rate sanity
    checks += 1
    if not (MIN_BLUNDER_RATE <= blunder_rate <= MAX_BLUNDER_RATE):
        issues.append(
            _issue(
                "blunder_rate_range",
                f"Blunder rate {blunder_rate} is outside [0, 1].",
                severity="error",
            )
        )
    elif abs(blunder_rate - engine_blunder_rate) > BLUNDER_TOLERANCE:
        issues.append(
            _issue(
                "blunder_rate_consistency",
                (
                    f"Reported blunder rate {blunder_rate:.3f} differs from the "
                    f"engine aggregate {engine_blunder_rate:.3f} by more than "
                    f"{BLUNDER_TOLERANCE}."
                ),
                severity="warning",
            )
        )

    passed = not any(issue.severity == "error" for issue in issues)
    return GuardrailResult(passed=passed, issues=issues, checks_run=checks), safe_elo


def sanitize_text(text: str) -> str:
    """Strip unsupported certainty phrases from generated prose."""
    cleaned = text
    for pattern in _UNSUPPORTED_CERTAINTY:
        cleaned = re.sub(pattern, "consistently strong", cleaned, flags=re.IGNORECASE)
    return cleaned


def summarize_ground_truth(engine_stats: dict[str, Any]) -> dict[str, Any]:
    """Extract the deterministic values used for grounding checks."""
    return {
        "acpl": float(engine_stats.get("avg_centipawn_loss", 0.0)),
        "blunder_rate": float(engine_stats.get("blunder_rate", 0.0)),
        "stockfish_elo": int(engine_stats.get("estimated_elo", 1500)),
    }
