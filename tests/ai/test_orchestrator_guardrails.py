from __future__ import annotations

import json

import pytest

from app.api.main import build_orchestrator_reply
from tqqq_strategy.ai.orchestrator_context import build_orchestrator_context
from tqqq_strategy.ai.orchestrator_service import run_orchestrator


SNAPSHOT = {
    "action_hero": {
        "action": "매수",
        "target_weight_pct": 95.0,
        "reason_summary": "추세 조건 유지",
        "updated_at": "2026-01-30T00:00:00",
    },
    "wealth_overview": {
        "invested_krw": 9_720_000,
        "cash_krw": 1_500_000,
        "debt_krw": 0,
        "net_worth_krw": 11_220_000,
    },
    "liquidity_summary": {
        "cash_krw": 1_500_000,
        "debt_krw": 0,
        "net_liquidity_krw": 1_500_000,
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
            "recommended_action": "장마감 전 비중 확인",
        }
    ],
    "manager_summaries": {
        "core_strategy": {
            "manager_id": "core_strategy",
            "summary_text": "실보유 86.63% / 목표 95.00%",
            "key_points": ["실보유 86.63%", "목표 95.00%"],
            "warnings": ["목표 대비 괴리 8.37%p"],
            "recommended_actions": ["현재 전략 비중 유지"],
            "generated_at": "2026-01-30T00:00:00",
            "source_version": "wealth_manual.json:2026-01-30:abc123",
            "stale": False,
        },
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
        "cash_debt": {
            "manager_id": "cash_debt",
            "summary_text": "현금 1,500,000원 / 부채 0원",
            "key_points": ["현금 1,500,000원"],
            "warnings": [],
            "recommended_actions": ["현금/부채 현황 유지"],
            "generated_at": "2026-01-30T00:00:00",
            "source_version": "wealth_manual.json:2026-01-30:abc123",
            "stale": False,
        },
    },
    "event_timeline": [{"date": "2026-01-30", "type": "비중 변경", "detail": "10.00% → 95.00% 조정"}],
    "ops_log": {"run_id": "daily-2026-01-30", "alert_key": "2026-01-30:1->950"},
    "meta": {"summary_source_version": "wealth_manual.json:2026-01-30:abc123"},
}


def test_run_orchestrator_requires_explicit_user_trigger() -> None:
    context = build_orchestrator_context(SNAPSHOT)

    with pytest.raises(ValueError, match="explicit"):
        run_orchestrator(question="오늘 뭐 해야 해?", context=context, trigger="page_load")


def test_run_orchestrator_returns_cache_first_cross_domain_answer() -> None:
    context = build_orchestrator_context(SNAPSHOT)

    reply = run_orchestrator(question="오늘 가장 중요한 액션과 현금 여력을 같이 알려줘", context=context, trigger="user_submit")

    assert reply["guardrails"]["explicit_only"] is True
    assert reply["guardrails"]["live_ai_used"] is False
    assert "95%" in reply["answer"]
    assert "1,500,000원" in reply["answer"]
    assert reply["highlights"]
    assert reply["metadata"]["mode"] == "cache_first"
    assert reply["metadata"]["source_manager_count"] >= 1
    assert reply["primary_intent"] == "action"
    assert {"action", "cash"}.issubset(set(reply["brief_keys_used"]))


def test_run_orchestrator_can_reference_cross_domain_manager_summaries() -> None:
    context = build_orchestrator_context(SNAPSHOT)

    reply = run_orchestrator(question="TQQQ와 개별주 중 어디가 우선인가?", context=context, trigger="user_submit")

    assert "관심종목 1개" in reply["answer"]
    assert "stock_research" in reply["source_manager_ids"]


def test_run_orchestrator_uses_default_priority_for_generic_portfolio_question() -> None:
    context = build_orchestrator_context(SNAPSHOT)

    reply = run_orchestrator(question="지금 우선순위를 전체적으로 요약해줘", context=context, trigger="user_submit")

    assert reply["primary_intent"] == "default_priority"
    assert reply["brief_keys_used"][:2] == ["default_priority", "action"]
    assert "전체 우선순위" in reply["answer"]


def test_api_build_orchestrator_reply_uses_snapshot_payload_without_live_generation() -> None:
    reply = build_orchestrator_reply("지금 우선순위가 뭐야?", payload=SNAPSHOT, audit_path=None)

    assert reply["guardrails"]["live_ai_used"] is False
    assert reply["context_meta"]["summary_source_version"] == "wealth_manual.json:2026-01-30:abc123"
    assert reply["question"] == "지금 우선순위가 뭐야?"


def test_api_build_orchestrator_reply_writes_audit_row_when_enabled(tmp_path) -> None:
    audit_path = tmp_path / "orchestrator_audit.jsonl"

    reply = build_orchestrator_reply("지금 리스크 상태는 어때?", payload=SNAPSHOT, audit_path=str(audit_path))

    rows = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["question"] == reply["question"]
    assert payload["guardrails"]["explicit_only"] is True
