"""Versioned momentum labels for signals that already passed the entry rules.

These labels are not calibrated win probabilities and never gate publication.
"""
from __future__ import annotations

GRADING_VERSION = "williams_momentum_v1"
GRADING_FIELDS = ("setup_grade", "grade_score", "grade_checks", "grade_reason", "grading_version")


def grade_momentum(direction: str, wr: float, k: float, d: float, cfg: dict) -> dict:
    """Score raw indicator values, after the existing entry filters pass."""
    if direction not in {"BUY", "SELL"}:
        raise ValueError("Grading requires BUY or SELL")
    buy = direction == "BUY"
    # Halfway from each style's existing cutoff to the indicator's extreme.
    wr_cutoff = cfg["wr_long"] / 2 if buy else (cfg["wr_short"] - 100) / 2
    k_cutoff = (cfg["stoch_long"] + 100) / 2 if buy else cfg["stoch_short"] / 2
    gap = k - d if buy else d - k
    checks = {
        "williams_strength": {"passed": wr > wr_cutoff if buy else wr < wr_cutoff,
                              "value": wr, "threshold": wr_cutoff,
                              "operator": ">" if buy else "<"},
        "stochastic_strength": {"passed": k > k_cutoff if buy else k < k_cutoff,
                                "value": k, "threshold": k_cutoff,
                                "operator": ">" if buy else "<"},
        "stochastic_separation": {"passed": gap >= 5.0, "value": gap,
                                  "threshold": 5.0, "operator": ">="},
    }
    score = sum(int(check["passed"]) for check in checks.values())
    grade = "S" if score == 3 else "A+" if score == 2 else "A"
    return {"setup_grade": grade, "grade_score": score, "grade_checks": checks,
            "grade_reason": f"{score}/3 extra momentum checks passed; not a win probability.",
            "grading_version": GRADING_VERSION}
