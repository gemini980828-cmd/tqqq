from pathlib import Path

from app.api.main import build_dashboard_snapshot


MANUAL_TRUTH = """
{
  "positions": [
    {
      "account_id": "samsung-core",
      "asset_id": "tqqq-core",
      "manager_id": "core_strategy",
      "symbol": "TQQQ",
      "name": "ProShares UltraPro QQQ",
      "quantity": 100,
      "avg_cost_krw": 5200000,
      "market_price_krw": 65000,
      "market_value_krw": 6500000
    }
  ],
  "cash_debt": [
    {"entry_id": "cash", "kind": "cash", "label": "예수금", "balance_krw": 10000000},
    {"entry_id": "debt", "kind": "debt", "label": "대출", "balance_krw": 3000000}
  ],
  "stock_watchlist": [{"idea_id": "nvda", "symbol": "NVDA", "status": "관찰", "memo": "AI"}],
  "property_watchlist": [{"property_id": "apt", "name": "테스트아파트", "region": "서울", "status": "검토"}]
}
"""


def test_step1_snapshot_contains_wealth_overview_and_core_strategy_actuals(tmp_path: Path) -> None:
    manual_truth = tmp_path / "wealth_manual.json"
    manual_truth.write_text(MANUAL_TRUTH, encoding="utf-8")

    snap = build_dashboard_snapshot(manual_truth_path=manual_truth)

    assert snap["wealth_overview"]["net_worth_krw"] == 13500000
    assert snap["core_strategy_actuals"]["target_weight_pct"] == snap["action_hero"]["target_weight_pct"]
    assert len(snap["manager_cards"]) == 4
    assert snap["meta"]["manual_source_version"] == "wealth_manual.json"
