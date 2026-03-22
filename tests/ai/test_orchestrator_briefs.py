from __future__ import annotations

from tqqq_strategy.ai.orchestrator_brief import build_orchestrator_briefs
from tqqq_strategy.ai.orchestrator_context import build_orchestrator_context


SNAPSHOT = {
    "action_hero": {
        "action": "매수",
        "target_weight_pct": 95.0,
        "reason_summary": "추세 조건 유지",
        "updated_at": "2026-01-30T00:00:00",
    },
    "wealth_overview": {
        "cash_krw": 1_500_000,
        "debt_krw": 0,
        "net_worth_krw": 11_220_000,
    },
    "liquidity_summary": {
        "cash_krw": 1_500_000,
        "debt_krw": 0,
        "liquidity_ratio_pct": 13.37,
    },
    "risk_gauges": {
        "vol20": {"value": 2.54, "threshold": 5.9, "status": "green"},
        "spy200_dist": {"value": 107.94, "threshold": 97.75, "status": "green"},
        "tqqq_dist200": {"value": 117.8, "threshold": 101.0, "status": "green"},
    },
    "home_inbox": [
        {
            "id": "core-action",
            "manager_id": "core_strategy",
            "severity": "high",
            "title": "코어전략 액션 확인",
            "detail": "전략 목표 비중 95%를 유지하세요.",
        }
    ],
    "manager_summaries": {
        "stock_research": {
            "manager_id": "stock_research",
            "summary_text": "관심종목 1개",
            "key_points": ["관심종목 1개"],
            "warnings": [],
            "recommended_actions": ["관심종목 신규 발굴"],
            "generated_at": "2026-01-30T00:00:00",
            "source_version": "wealth_manual.json:2026-01-30:abc123",
            "stale": False,
        },
        "real_estate": {
            "manager_id": "real_estate",
            "summary_text": "관심 단지 1개",
            "key_points": ["관심 단지 1개"],
            "warnings": [],
            "recommended_actions": ["검토 단지 체크리스트 업데이트"],
            "generated_at": "2026-01-30T00:00:00",
            "source_version": "wealth_manual.json:2026-01-30:abc123",
            "stale": False,
        },
    },
    "event_timeline": [
        {
            "id": "event-core-rebalance",
            "date": "2026-01-30",
            "type": "비중 변경",
            "title": "코어 비중 확대",
            "detail": "10.00% → 95.00% 조정",
            "category": "allocation",
            "severity": "high",
            "source_manager_id": "core_strategy",
            "entity_type": "position",
            "entity_id": "tqqq-core",
        }
    ],
    "report_highlights": [
        {
            "id": "report-core-gap",
            "title": "코어전략 리밸런싱 점검",
            "summary": "실제 비중과 목표 비중 차이가 남아 있습니다.",
            "severity": "medium",
            "manager_ids": ["core_strategy"],
        }
    ],
    "compare_data": {
        "manager_pairs": [{"pair_id": "core-vs-cash", "manager_ids": ["core_strategy", "cash_debt"]}],
        "holding_overlap": [{"overlap_id": "core-vs-research", "left_manager_id": "core_strategy", "right_manager_id": "stock_research", "shared_symbols": ["NVDA"]}],
        "conflicting_recommendations": [{"conflict_id": "core-vs-cash", "manager_ids": ["core_strategy", "cash_debt"], "detail": "전략 액션과 현금 방어 여력을 함께 봐야 합니다."}],
    },
}


def test_build_orchestrator_briefs_emits_backend_owned_sections() -> None:
    context = build_orchestrator_context(SNAPSHOT, question="오늘 뭐 해야 해?")

    briefs = build_orchestrator_briefs(context)

    assert set(briefs) == {
        "action",
        "cash",
        "risk",
        "stock_research",
        "real_estate",
        "recent_changes",
        "comparison",
        "report",
        "default_priority",
    }
    assert "95.0%" in briefs["action"]
    assert "1,500,000원" in briefs["cash"]
    assert "vol20" in briefs["risk"].lower()
    assert "관심종목 1개" in briefs["stock_research"]
    assert "코어 비중 확대" in briefs["recent_changes"]
    assert "공통" in briefs["comparison"]
    assert "코어전략 리밸런싱 점검" in briefs["report"]
