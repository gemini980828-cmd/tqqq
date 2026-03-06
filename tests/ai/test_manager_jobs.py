from __future__ import annotations

import json
from pathlib import Path

from tqqq_strategy.ai.manager_jobs import build_manager_summary_records, refresh_manager_summaries
from tqqq_strategy.ops.dashboard_snapshot import generate_dashboard_snapshot
from tqqq_strategy.wealth.manual_inputs import load_manual_truth
from tqqq_strategy.wealth.summary_store import load_summary_store


SIGNALS = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,0.1,1,0.1
2026-03-06,0,0.0,2,1.0,2,1.0
"""

DATA = """time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,TQQQ200일 이격도
2026-02-12,105,45,506,101,99,39,490,115.38
2026-02-13,106,46,507,101,99,39,490,117.95
2026-02-14,107,47,508,101,99,39,490,120.51
2026-02-17,108,48,509,101,99,39,490,123.08
2026-02-18,109,49,510,101,99,39,490,125.64
2026-02-19,110,50,511,101,99,39,490,128.21
2026-02-20,111,51,512,101,99,39,490,130.77
2026-02-21,112,52,513,101,99,39,490,133.33
2026-02-24,113,53,514,101,99,39,490,135.90
2026-02-25,114,54,515,101,99,39,490,138.46
2026-02-26,115,55,516,101,99,39,490,141.03
2026-02-27,116,56,517,101,99,39,490,143.59
2026-02-28,117,57,518,101,99,39,490,146.15
2026-03-03,118,58,519,101,99,39,490,148.72
2026-03-04,119,59,520,120,100,39,490,151.28
2026-03-05,120,60,521,121,100,39,490,153.85
2026-03-06,121,61,522,122,100,39,490,156.41
"""

METRICS = """CAGR,MDD,AnnualVol,Sharpe,Sortino,Calmar,WinRateDaily,ProfitFactor,UlcerIndex,BetaVsQQQ,MaxDDDurationDays,AfterTaxCAGR
0.3506,-0.3421,0.36,1.0,1.09,1.02,0.39,1.23,14.58,1.01,381,0.3216
"""

STATE = '{"last_alert_key":"2026-03-06:1->2","last_sent_at":"2026-03-06T22:30:00+00:00"}'

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
        {"entry_id": "cash-main", "kind": "cash", "label": "투자예수금", "balance_krw": 1500000},
        {"entry_id": "loan-main", "kind": "debt", "label": "신용대출", "balance_krw": 500000},
    ],
    "stock_watchlist": [
        {"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI"},
        {"idea_id": "stock-2", "symbol": "META", "status": "후보", "memo": "광고 회복"},
    ],
    "property_watchlist": [
        {"property_id": "apt-1", "name": "마포래미안푸르지오", "region": "서울", "status": "관심"},
        {"property_id": "apt-2", "name": "래미안원베일리", "region": "서울", "status": "검토"},
    ],
}


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _write_manual(path: Path) -> Path:
    path.write_text(json.dumps(MANUAL, ensure_ascii=False), encoding="utf-8")
    return path


def test_build_manager_summary_records_covers_all_four_managers(tmp_path: Path) -> None:
    manual_path = _write_manual(tmp_path / "wealth_manual.json")
    manual_inputs = load_manual_truth(manual_path)
    snapshot = generate_dashboard_snapshot(
        signal_csv_path=_write(tmp_path / "signals.csv", SIGNALS),
        data_csv_path=_write(tmp_path / "data.csv", DATA),
        metrics_csv_path=_write(tmp_path / "metrics.csv", METRICS),
        state_path=_write(tmp_path / "state.json", STATE),
        manual_truth_path=manual_path,
    )

    records = build_manager_summary_records(
        snapshot,
        manual_inputs,
        source_version="wealth_manual.json:v1",
        generated_at="2026-03-06T22:35:00+00:00",
    )

    assert set(records) == {"core_strategy", "stock_research", "real_estate", "cash_debt"}
    assert records["core_strategy"]["summary_text"].startswith("실보유")
    assert records["core_strategy"]["recommended_actions"]
    assert records["stock_research"]["key_points"] == ["관심종목 2개", "후보 1개", "관찰 1개"]
    assert records["real_estate"]["key_points"] == ["관심 단지 2개", "검토 1개", "관심 1개"]
    assert records["cash_debt"]["warnings"] == ["부채 500,000원이 있어 상환 우선순위를 함께 점검해야 합니다."]
    assert all(record["source_version"] == "wealth_manual.json:v1" for record in records.values())
    assert all(record["generated_at"] == "2026-03-06T22:35:00+00:00" for record in records.values())


def test_refresh_manager_summaries_persists_records_to_summary_store(tmp_path: Path) -> None:
    manual_path = _write_manual(tmp_path / "wealth_manual.json")
    summary_store_path = tmp_path / "manager_summaries.json"

    records = refresh_manager_summaries(
        signal_csv_path=_write(tmp_path / "signals.csv", SIGNALS),
        data_csv_path=_write(tmp_path / "data.csv", DATA),
        metrics_csv_path=_write(tmp_path / "metrics.csv", METRICS),
        state_path=_write(tmp_path / "state.json", STATE),
        manual_truth_path=manual_path,
        summary_store_path=summary_store_path,
        generated_at="2026-03-06T22:35:00+00:00",
    )
    store = load_summary_store(summary_store_path)

    assert set(records) == {"core_strategy", "stock_research", "real_estate", "cash_debt"}
    assert set(store) == set(records)
    assert store["core_strategy"]["summary_text"] == records["core_strategy"]["summary_text"]
    assert store["stock_research"]["stale"] is False
    assert store["cash_debt"]["source_version"].startswith("wealth_manual.json:")
