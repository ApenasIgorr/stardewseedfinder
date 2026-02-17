from core.predictor_adapter.v16_simulator import V16Simulator


def test_predictor_deterministic():
    p = V16Simulator()
    a = p.predict(42, {"game_version": "1.6.x"})
    b = p.predict(42, {"game_version": "1.6.x"})
    assert a.weather == b.weather
    assert a.traveling_cart == b.traveling_cart
