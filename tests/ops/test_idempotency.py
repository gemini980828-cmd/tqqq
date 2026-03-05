from tqqq_strategy.ops.idempotency import build_alert_key


def test_alert_key_is_stable_per_day_signal():
    k1 = build_alert_key("2026-03-05", 1, 2)
    k2 = build_alert_key("2026-03-05", 1, 2)
    assert k1 == k2
