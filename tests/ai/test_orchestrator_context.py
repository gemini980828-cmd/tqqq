from tqqq_strategy.ai.orchestrator_context import build_orchestrator_context


SNAPSHOT = {
    "action_hero": {
        "action": "매수",
        "target_weight_pct": 95.0,
        "reason_summary": "추세 조건 유지",
        "updated_at": "2026-01-30T00:00:00",
    },
    "wealth_overview": {
        "net_worth_krw": 12000000,
        "cash_krw": 1500000,
        "debt_krw": 0,
        "invested_krw": 10500000,
    },
    "liquidity_summary": {
        "cash_krw": 1500000,
        "debt_krw": 0,
        "net_liquidity_krw": 1500000,
        "liquidity_ratio_pct": 12.5,
    },
    "risk_gauges": {
        "vol20": {"value": 2.3, "threshold": 5.9, "status": "green"},
        "spy200_dist": {"value": 103.2, "threshold": 97.75, "status": "green"},
    },
    "manager_summaries": {
        "core_strategy": {
            "manager_id": "core_strategy",
            "summary_text": "실보유 86.63% / 목표 95.00%",
            "key_points": ["실보유 86.63%", "목표 95.00%"],
            "warnings": ["리밸런싱 gap 8.37%p"],
            "recommended_actions": ["장마감 기준 비중 점검"],
            "generated_at": "2026-01-30T00:00:00",
            "source_version": "wealth_manual.json:2026-01-30:abc",
            "stale": False,
        }
    },
    "home_inbox": [
        {
            "id": "core-action",
            "manager_id": "core_strategy",
            "severity": "high",
            "title": "오늘 액션 확인",
            "detail": "코어전략 목표 비중 95% 확인",
            "recommended_action": "장마감 기준 주문 판단",
        }
    ],
    "event_timeline": [
        {"date": "2026-01-30", "type": "비중 변경", "detail": "90% → 95% 조정"}
    ],
    "ops_log": {
        "run_id": "daily-2026-01-30",
        "alert_key": "2026-01-30:0.90->0.95",
        "last_success_at": "2026-01-30T00:00:00",
    },
    "meta": {
        "manual_source_version": "wealth_manual.json",
        "summary_source_version": "wealth_manual.json:2026-01-30:abc",
    },
    "raw_market_rows": [{"too": "long"}],
    "manual_inputs": {"positions": [{"symbol": "TQQQ"}]},
}


def test_build_orchestrator_context_keeps_only_cached_cross_domain_state() -> None:
    context = build_orchestrator_context(SNAPSHOT, question="오늘 뭐 해야 해?")

    assert context["question"] == "오늘 뭐 해야 해?"
    assert context["action_hero"]["action"] == "매수"
    assert context["wealth_overview"]["cash_krw"] == 1500000
    assert context["liquidity_summary"]["liquidity_ratio_pct"] == 12.5
    assert context["manager_summaries"]["core_strategy"]["summary_text"].startswith("실보유")
    assert context["home_inbox"][0]["severity"] == "high"
    assert context["event_timeline"][0]["type"] == "비중 변경"
    assert "raw_market_rows" not in context
    assert "manual_inputs" not in context


def test_build_orchestrator_context_trims_manager_summary_to_prompt_safe_fields() -> None:
    context = build_orchestrator_context(SNAPSHOT, question="현금 여력은?")

    summary = context["manager_summaries"]["core_strategy"]
    assert set(summary) == {
        "manager_id",
        "summary_text",
        "key_points",
        "warnings",
        "recommended_actions",
        "generated_at",
        "stale",
    }
