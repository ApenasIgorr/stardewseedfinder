from core.config import parse_requirements


def test_schema_valid_example():
    cfg = parse_requirements(
        {
            "hard_constraints": [{"type": "weather", "season": "spring", "year": 1, "min_rain_days": 3}],
            "soft_preferences": [],
            "search": {"mode": "range", "seed_min": 1, "seed_max": 10},
            "context": {"game_version": "1.6.x", "mode": "single"},
            "output": {"top_n": 5, "export_formats": ["json"]},
        }
    )
    assert cfg.search.seed_max == 10
