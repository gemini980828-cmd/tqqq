import json
from pathlib import Path

from app.api.main import build_dashboard_snapshot


SIGNALS = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,0.1,1,0.1
2026-03-06,0,0.0,2,1.0,2,1.0
"""

DATA = """time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,TQQQ200일 이격도
2026-03-05,120,60,521,121,100,39,490,153.85
2026-03-06,121,61,522,122,100,39,490,156.41
"""

METRICS = """CAGR,MDD,AnnualVol,Sharpe,Sortino,Calmar,WinRateDaily,ProfitFactor,UlcerIndex,BetaVsQQQ,MaxDDDurationDays,AfterTaxCAGR
0.3506,-0.3421,0.36,1.0,1.09,1.02,0.39,1.23,14.58,1.01,381,0.3216
"""

MANUAL = {
    "positions": [
        {
            "account_id": "samsung-core",
            "asset_id": "tqqq-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "name": "ProShares UltraPro QQQ",
            "quantity": 120,
            "avg_cost_krw": 76000,
            "market_price_krw": 81000,
            "market_value_krw": 9720000,
        }
    ],
    "cash_debt": [
        {
            "entry_id": "cash-main",
            "kind": "cash",
            "label": "투자예수금",
            "balance_krw": 1500000,
        }
    ],
    "stock_watchlist": [
        {
            "idea_id": "stock-1",
            "symbol": "NVDA",
            "status": "관찰",
            "memo": "AI 수혜 지속 모니터링",
        }
    ],
    "property_watchlist": [
        {
            "property_id": "apt-1",
            "name": "마포래미안푸르지오",
            "status": "검토",
            "region": "서울 마포구",
        }
    ],
    "transactions": [
        {
            "transaction_id": "tx-1",
            "account_id": "samsung-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "side": "buy",
            "quantity": 5,
            "price_krw": 80000,
            "total_value_krw": 400000,
            "traded_at": "2026-03-05T14:10:00+00:00",
        }
    ],
}


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_build_dashboard_snapshot_includes_wealth_home_and_core_strategy_position(tmp_path: Path) -> None:
    manual_path = tmp_path / "manual.json"
    manual_path.write_text(json.dumps(MANUAL, ensure_ascii=False), encoding="utf-8")

    snap = build_dashboard_snapshot(
        None,
        signal_csv_path=_write(tmp_path / "signals.csv", SIGNALS),
        data_csv_path=_write(tmp_path / "data.csv", DATA),
        metrics_csv_path=_write(tmp_path / "metrics.csv", METRICS),
        manual_inputs_path=manual_path,
    )

    wealth = snap["wealth_home"]
    core = snap["core_strategy_position"]

    assert wealth["overview"] == {
        "invested_krw": 9720000,
        "investable_assets_krw": 9720000,
        "cash_krw": 1500000,
        "debt_krw": 0,
        "net_worth_krw": 11220000,
    }
    assert len(wealth["manager_cards"]) == 4
    assert wealth["manager_cards"][0]["manager_id"] == "core_strategy"

    assert core["symbol"] == "TQQQ"
    assert core["quantity"] == 120
    assert core["target_weight_pct"] == 100.0
    assert core["actual_weight_pct"] == round(9720000 / 11220000 * 100.0, 2)
    assert core["gap_weight_pct"] == round(100.0 - core["actual_weight_pct"], 2)
    assert core["rebalance_gap_krw"] == 1500000
    assert core["transaction_count"] == 1
    assert core["last_traded_at"] == "2026-03-05T14:10:00+00:00"
    assert snap["meta"]["signal_updated_at"] == "2026-03-06T00:00:00"
    assert snap["meta"]["market_updated_at"] == "2026-03-06T00:00:00"
