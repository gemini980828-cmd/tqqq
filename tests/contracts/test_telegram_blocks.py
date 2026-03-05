from app.api.main import build_dashboard_snapshot


def test_dashboard_contains_required_telegram_blocks() -> None:
    snap = build_dashboard_snapshot({})
    required = {"header", "position_change", "reason", "market_summary", "ops_log"}
    assert required.issubset(set(snap.keys()))
