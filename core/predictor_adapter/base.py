from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PredictionBundle:
    supported_features: dict[str, bool]
    weather: dict[str, str]
    traveling_cart: list[dict[str, Any]]
    night_events: list[dict[str, Any]]
    trains: list[dict[str, Any]]
    garbage_cans: list[dict[str, Any]]
    sequences: dict[str, list[str]]


class PredictorAdapter:
    def predict(self, seed: int, context: dict[str, Any]) -> PredictionBundle:
        raise NotImplementedError
