from core.constraints.evaluator import evaluate_constraint
from core.predictor_adapter.v16_simulator import V16Simulator


def test_weather_constraint_runs():
    pred = V16Simulator().predict(12345, {"game_version": "1.6.x"})
    c = {"type": "weather", "season": "spring", "year": 1, "day": 3, "expected": pred.weather["Y1-spring-3"]}
    res = evaluate_constraint(pred, c)
    assert res.matched is True
