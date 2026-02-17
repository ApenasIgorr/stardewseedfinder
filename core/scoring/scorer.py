from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.constraints.evaluator import EvalResult, evaluate_constraint
from core.predictor_adapter.base import PredictionBundle


@dataclass
class SeedEvaluation:
    seed: int
    hard_passed: bool
    score: float
    details: list[dict[str, Any]]
    unsupported: list[str]


def evaluate_seed(seed: int, pred: PredictionBundle, hard: list[dict[str, Any]], soft: list[dict[str, Any]]) -> SeedEvaluation:
    details: list[dict[str, Any]] = []
    unsupported: list[str] = []

    for c in hard:
        res: EvalResult = evaluate_constraint(pred, c)
        details.append({"kind": "hard", "constraint": c, "matched": res.matched, "detail": res.detail})
        if res.unsupported:
            unsupported.append(c.get("type", "unknown"))
        if not res.matched:
            return SeedEvaluation(seed=seed, hard_passed=False, score=-1e9, details=details, unsupported=unsupported)

    score = 0.0
    for pref in soft:
        res = evaluate_constraint(pred, pref["constraint"], weight=pref.get("weight", 1.0), tolerance=pref.get("tolerance", 0.0))
        score += res.score
        details.append(
            {
                "kind": "soft",
                "constraint": pref["constraint"],
                "matched": res.matched,
                "delta": res.score,
                "detail": res.detail,
            }
        )
        if res.unsupported:
            unsupported.append(pref["constraint"].get("type", "unknown"))

    return SeedEvaluation(seed=seed, hard_passed=True, score=score, details=details, unsupported=unsupported)
