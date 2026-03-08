from __future__ import annotations

import json
from pathlib import Path

from tqqq_strategy.ai.orchestrator_audit import append_orchestrator_audit, build_orchestrator_insights


def test_append_orchestrator_audit_writes_jsonl_row(tmp_path: Path) -> None:
    audit_path = tmp_path / "orchestrator_audit.jsonl"

    append_orchestrator_audit(
        audit_path,
        question="오늘 가장 중요한 액션은?",
        reply={
            "answer": "현재 가장 중요한 액션은 매수입니다.",
            "source_manager_ids": ["core_strategy"],
            "metadata": {"mode": "cache_first", "question_chars": 14, "source_manager_count": 1},
            "guardrails": {"explicit_only": True, "live_ai_used": False, "trigger": "user_submit"},
        },
        context_meta={"summary_source_version": "wealth_manual.json:2026-01-30:abc123"},
    )

    rows = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(rows) == 1
    payload = json.loads(rows[0])
    assert payload["question"] == "오늘 가장 중요한 액션은?"
    assert payload["source_manager_ids"] == ["core_strategy"]
    assert payload["metadata"]["mode"] == "cache_first"
    assert payload["context_meta"]["summary_source_version"] == "wealth_manual.json:2026-01-30:abc123"


def test_build_orchestrator_insights_summarizes_recent_usage(tmp_path: Path) -> None:
    audit_path = tmp_path / "orchestrator_audit.jsonl"

    append_orchestrator_audit(
        audit_path,
        question="지금 우선순위를 요약해줘",
        reply={
            "answer": "1순위 판단: 코어전략 점검",
            "source_manager_ids": ["core_strategy"],
            "metadata": {
                "mode": "cache_first",
                "question_chars": 13,
                "source_manager_count": 1,
                "primary_intent": "default_priority",
            },
            "guardrails": {"explicit_only": True, "live_ai_used": False, "trigger": "user_submit"},
        },
        context_meta={"summary_source_version": "wealth_manual.json:2026-01-30:abc123"},
    )
    append_orchestrator_audit(
        audit_path,
        question="현금 여력이 충분한가?",
        reply={
            "answer": "1순위 판단: 현금 여력 점검",
            "source_manager_ids": ["cash_debt"],
            "metadata": {
                "mode": "cache_first",
                "question_chars": 12,
                "source_manager_count": 1,
                "primary_intent": "cash",
            },
            "guardrails": {"explicit_only": True, "live_ai_used": False, "trigger": "user_submit"},
        },
        context_meta={"summary_source_version": "wealth_manual.json:2026-01-30:abc123"},
    )

    summary = build_orchestrator_insights(audit_path)

    assert summary["total_questions"] == 2
    assert summary["last_question_at"]
    assert summary["top_intents"][0]["intent"] in {"cash", "default_priority"}
    assert summary["recent_questions"][0]["question"] == "현금 여력이 충분한가?"
