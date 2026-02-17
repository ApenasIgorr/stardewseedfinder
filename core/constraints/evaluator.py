from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.predictor_adapter.base import PredictionBundle

SEASON_ORDER = {"spring": 1, "summer": 2, "fall": 3, "winter": 4}


@dataclass
class EvalResult:
    matched: bool
    score: float
    detail: str
    unsupported: bool = False


def _date_leq(y: int, s: str, d: int, y2: int, s2: str, d2: int) -> bool:
    return (y, SEASON_ORDER[s], d) <= (y2, SEASON_ORDER[s2], d2)


def evaluate_constraint(pred: PredictionBundle, c: dict[str, Any], weight: float = 0.0, tolerance: float = 0.0) -> EvalResult:
    ctype = c.get("type")
    if not c.get("enabled", True):
        return EvalResult(True, 0.0, "constraint disabled")

    if ctype == "weather":
        season, year = c["season"], c["year"]
        if c.get("day") and c.get("expected"):
            key = f"Y{year}-{season}-{c['day']}"
            ok = pred.weather.get(key) == c["expected"]
            return EvalResult(ok, weight if ok else -tolerance, f"weather on {key}={pred.weather.get(key)}")
        if c.get("min_rain_days") is not None:
            count = sum(
                1
                for k, v in pred.weather.items()
                if k.startswith(f"Y{year}-{season}-") and v in ("rain", "green_rain")
            )
            ok = count >= c["min_rain_days"]
            return EvalResult(ok, weight if ok else -(c["min_rain_days"] - count) * tolerance, f"rain days={count}")
        if c.get("avoid_day") is not None:
            key = f"Y{year}-{season}-{c['avoid_day']}"
            ok = pred.weather.get(key) != "rain"
            return EvalResult(ok, weight if ok else -tolerance, f"avoid rain on {key}")

    elif ctype == "traveling_cart":
        found = None
        for e in pred.traveling_cart:
            if e["item"].lower() == c["item"].lower() and _date_leq(
                e["year"], e["season"], e["day"], c["latest_year"], c["latest_season"], c["latest_day"]
            ):
                if c.get("max_price") is None or e["price"] <= c["max_price"]:
                    found = e
                    break
        ok = found is not None
        return EvalResult(ok, weight if ok else -tolerance, f"cart match={found}")

    elif ctype == "night_event":
        found = any(
            e["event"] == c["event"]
            and _date_leq(e["year"], e["season"], e["day"], c["latest_year"], c["latest_season"], c["latest_day"])
            for e in pred.night_events
        )
        ok = not found if c.get("avoid", False) else found
        return EvalResult(ok, weight if ok else -tolerance, f"night event found={found}")

    elif ctype == "train":
        count = sum(1 for t in pred.trains if t["year"] == c["year"] and t["season"] == c["season"])
        ok = count >= c["min_count"]
        return EvalResult(ok, weight if ok else -(c["min_count"] - count) * tolerance, f"trains={count}")

    elif ctype == "sequence":
        seq = pred.sequences.get(c["source"], [])[: c["within_attempts"]]
        ok = c["desired_item"] in seq
        return EvalResult(ok, weight if ok else -tolerance, f"sequence first {c['within_attempts']} contains item={ok}")

    elif ctype == "multi":
        inner = [evaluate_constraint(pred, cc, weight=weight, tolerance=tolerance) for cc in c.get("constraints", [])]
        if c["op"] == "and":
            ok = all(x.matched for x in inner)
        else:
            ok = any(x.matched for x in inner)
        score = sum(x.score for x in inner)
        return EvalResult(ok, score, f"multi({c['op']}) => {[x.matched for x in inner]}")

    else:
        return EvalResult(False, 0.0, f"unsupported constraint type: {ctype}", unsupported=True)

    return EvalResult(False, 0.0, "invalid constraint payload")
