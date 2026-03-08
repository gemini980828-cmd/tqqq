from __future__ import annotations

import json
from pathlib import Path

from tqqq_strategy.ai.orchestrator_audit import append_orchestrator_audit


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
