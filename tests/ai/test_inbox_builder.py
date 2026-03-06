from tqqq_strategy.ai.inbox_builder import build_home_inbox


MANUAL_PAYLOAD = {
    "positions": [],
    "cash_debt": [
        {"entry_id": "cash-main", "kind": "cash", "label": "투자대기현금", "balance_krw": 1500000},
        {"entry_id": "loan-margin", "kind": "debt", "label": "마이너스통장", "balance_krw": 2000000},
    ],
    "stock_watchlist": [
        {"idea_id": "stock-1", "symbol": "NVDA", "status": "후보", "memo": "AI 인프라 핵심 수혜"},
    ],
    "property_watchlist": [
        {"property_id": "apt-1", "name": "마포래미안푸르지오", "region": "서울 마포구", "status": "검토"},
    ],
    "transactions": [],
}

SNAPSHOT = {
    "action_hero": {
        "action": "매수",
        "target_weight_pct": 100.0,
        "reason_summary": "추세 강화로 비중 확대",
        "updated_at": "2026-03-06T22:30:00+00:00",
    },
    "core_strategy_actuals": {
        "actual_weight_pct": 31.59,
        "target_weight_pct": 100.0,
        "rebalance_gap_krw": 19511500,
    },
    "wealth_overview": {"cash_krw": 1500000, "debt_krw": 2000000},
}

SUMMARIES = {
    "core_strategy": {
        "manager_id": "core_strategy",
        "summary_text": "실보유가 목표보다 크게 낮습니다.",
        "key_points": ["실보유 31.59%", "목표 100.00%"],
        "warnings": ["리밸런싱 gap이 큽니다."],
        "recommended_actions": ["장마감 기준 추가 매수 검토"],
        "generated_at": "2026-03-06T22:30:00+00:00",
        "source_version": "wealth:2026-03-06",
        "stale": False,
    },
    "stock_research": {
        "manager_id": "stock_research",
        "summary_text": "후보 1개를 유지 중입니다.",
        "key_points": ["후보 1개"],
        "warnings": [],
        "recommended_actions": ["NVDA 후속 리서치 정리"],
        "generated_at": "2026-03-06T22:30:00+00:00",
        "source_version": "wealth:2026-03-06",
        "stale": False,
    },
    "cash_debt": {
        "manager_id": "cash_debt",
        "summary_text": "부채가 현금보다 큽니다.",
        "key_points": ["현금 1,500,000원", "부채 2,000,000원"],
        "warnings": ["순유동성이 음수입니다."],
        "recommended_actions": ["현금 방어 여력 점검"],
        "generated_at": "2026-03-06T22:30:00+00:00",
        "source_version": "wealth:2026-03-06",
        "stale": True,
    },
}


def test_build_home_inbox_prioritizes_action_stale_and_cash_warnings() -> None:
    items = build_home_inbox(
        snapshot=SNAPSHOT,
        manual_inputs=MANUAL_PAYLOAD,
        manager_summaries=SUMMARIES,
    )

    assert items[0]["manager_id"] == "core_strategy"
    assert items[0]["severity"] == "high"
    assert "목표 100.00%" in items[0]["detail"]
    assert any(item["manager_id"] == "cash_debt" and item["severity"] == "high" for item in items)
    assert any(item["manager_id"] == "stock_research" and item["severity"] == "medium" for item in items)
