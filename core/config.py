from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchConfig:
    mode: str = "range"
    seed_min: int | None = None
    seed_max: int | None = None
    random_count: int = 1000
    random_seed: int = 42
    workers: int = 4
    timeout_seconds: int | None = None


@dataclass
class ContextConfig:
    game_version: str = "1.6.x"
    mode: str = "single"
    days_played: int = 0
    daily_luck: float = 0.0
    luck_level: int = 0
    geode_counter: int = 0
    mystery_box_counter: int = 0
    prize_ticket_counter: int = 0
    progression_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class OutputConfig:
    top_n: int = 20
    export_formats: list[str] = field(default_factory=lambda: ["json"])
    include_unsupported: bool = True


@dataclass
class RequirementsConfig:
    hard_constraints: list[dict[str, Any]] = field(default_factory=list)
    soft_preferences: list[dict[str, Any]] = field(default_factory=list)
    search: SearchConfig = field(default_factory=SearchConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    def model_dump(self) -> dict[str, Any]:
        return {
            "hard_constraints": self.hard_constraints,
            "soft_preferences": self.soft_preferences,
            "search": self.search.__dict__,
            "context": self.context.__dict__,
            "output": self.output.__dict__,
        }


def parse_requirements(raw: dict[str, Any]) -> RequirementsConfig:
    search = SearchConfig(**raw.get("search", {}))
    if search.mode not in {"range", "random", "mixed"}:
        raise ValueError("search.mode must be range/random/mixed")
    if search.mode in {"range", "mixed"} and (search.seed_min is None or search.seed_max is None):
        raise ValueError("seed_min and seed_max are required for range/mixed")
    if search.seed_min is not None and search.seed_max is not None and search.seed_max < search.seed_min:
        raise ValueError("seed_max must be >= seed_min")

    context = ContextConfig(**raw.get("context", {}))
    output = OutputConfig(**raw.get("output", {}))
    return RequirementsConfig(
        hard_constraints=raw.get("hard_constraints", []),
        soft_preferences=raw.get("soft_preferences", []),
        search=search,
        context=context,
        output=output,
    )


def requirements_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["hard_constraints", "soft_preferences", "search", "context", "output"],
        "properties": {
            "hard_constraints": {"type": "array"},
            "soft_preferences": {"type": "array"},
            "search": {"type": "object"},
            "context": {"type": "object"},
            "output": {"type": "object"},
        },
        "examples": [],
    }


def parse_json_or_yaml(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text)
        except Exception as exc:
            raise ValueError("Invalid JSON. YAML requires PyYAML installed.") from exc


def try_parse(raw: dict[str, Any]) -> tuple[RequirementsConfig | None, str | None]:
    try:
        return parse_requirements(raw), None
    except Exception as exc:
        return None, str(exc)
