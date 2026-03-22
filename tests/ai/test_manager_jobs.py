from __future__ import annotations

import json
from pathlib import Path

from tqqq_strategy.ai.manager_jobs import build_manager_summary_records, refresh_manager_summaries
from tqqq_strategy.wealth.manual_inputs import load_manual_truth
from tqqq_strategy.wealth.summary_store import load_summary_store


SIGNALS = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,0.1,1,0.1
2026-03-06,0,0.0,2,1.0,2,1.0
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
        {"entry_id": "cash-main", "kind": "cash", "label": "투자예수금", "balance_krw": 1500000},
        {"entry_id": "loan-main", "kind": "debt", "label": "신용대출", "balance_krw": 500000},
    ],
    "stock_watchlist": [
        {"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI"},
        {"idea_id": "stock-2", "symbol": "META", "status": "후보", "memo": "광고 회복"},
        {"idea_id": "stock-3", "symbol": "AAPL", "status": "매수후보", "memo": "legacy candidate"},
    ],
    "property_watchlist": [
        {"property_id": "apt-1", "name": "마포래미안푸르지오", "region": "서울", "status": "관심"},
        {"property_id": "apt-2", "name": "래미안원베일리", "region": "서울", "status": "검토"},
    ],
    "transactions": [],
}

SNAPSHOT = {
    "action_hero": {
        "action": "매수",
        "target_weight_pct": 100.0,
        "reason_summary": "코어전략 목표 비중 100.00% 기준 요약",
        "updated_at": "2026-03-06T22:35:00+00:00",
    },
    "core_strategy_actuals": {
        "actual_weight_pct": 86.63,
        "target_weight_pct": 100.0,
        "gap_weight_pct": 13.37,
        "rebalance_gap_krw": 1500000,
    },
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

    records = build_manager_summary_records(
        SNAPSHOT,
        manual_inputs,
        source_version="wealth_manual.json:v1",
        generated_at="2026-03-06T22:35:00+00:00",
    )

    assert set(records) == {"core_strategy", "stock_research", "real_estate", "cash_debt"}
    assert records["core_strategy"]["summary_text"].startswith("실보유")
    assert records["core_strategy"]["recommended_actions"] == ["장마감 기준 추가 매수 검토"]
    assert records["stock_research"]["key_points"] == ["관심종목 3개", "후보 2개", "관찰 1개"]
    assert records["real_estate"]["key_points"] == ["관심 단지 2개", "검토 1개", "관심 1개"]
    assert records["cash_debt"]["warnings"] == ["부채 500,000원이 있어 상환 우선순위를 함께 점검해야 합니다."]
    assert all(record["source_version"] == "wealth_manual.json:v1" for record in records.values())
    assert all(record["generated_at"] == "2026-03-06T22:35:00+00:00" for record in records.values())


def test_refresh_manager_summaries_persists_records_to_summary_store(tmp_path: Path) -> None:
    manual_path = _write_manual(tmp_path / "wealth_manual.json")
    summary_store_path = tmp_path / "manager_summaries.json"

    records = refresh_manager_summaries(
        signal_csv_path=_write(tmp_path / "signals.csv", SIGNALS),
        data_csv_path=tmp_path / "unused-data.csv",
        metrics_csv_path=tmp_path / "unused-metrics.csv",
        state_path=tmp_path / "unused-state.json",
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
