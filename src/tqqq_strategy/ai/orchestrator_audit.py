from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

DEFAULT_ORCHESTRATOR_AUDIT_PATH = Path("reports/orchestrator_audit.jsonl")


def append_orchestrator_audit(
    path: str | Path,
    *,
    question: str,
    reply: Mapping[str, Any],
    context_meta: Mapping[str, Any],
) -> None:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": str(question),
        "answer": str(reply.get("answer") or ""),
        "source_manager_ids": [str(item) for item in reply.get("source_manager_ids", [])],
        "guardrails": dict(reply.get("guardrails") or {}),
        "metadata": dict(reply.get("metadata") or {}),
        "context_meta": dict(context_meta or {}),
    }
    with audit_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_orchestrator_audit(path: str | Path) -> list[dict[str, Any]]:
    audit_path = Path(path)
    if not audit_path.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in audit_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(dict(json.loads(line)))
        except json.JSONDecodeError:
            continue
    return rows


def build_orchestrator_insights(path: str | Path, *, limit: int = 5) -> dict[str, Any]:
    rows = read_orchestrator_audit(path)
    if not rows:
        return {
            "total_questions": 0,
            "last_question_at": None,
            "top_intents": [],
            "recent_questions": [],
        }

    intent_counts: dict[str, int] = {}
    recent_questions: list[dict[str, Any]] = []
    for row in rows:
        metadata = dict(row.get("metadata") or {})
        primary_intent = str(metadata.get("primary_intent") or "default_priority")
        intent_counts[primary_intent] = intent_counts.get(primary_intent, 0) + 1
        recent_questions.append(
            {
                "timestamp": str(row.get("timestamp") or ""),
                "question": str(row.get("question") or ""),
                "primary_intent": primary_intent,
                "source_manager_ids": [str(item) for item in row.get("source_manager_ids", [])],
            }
        )

    sorted_intents = sorted(intent_counts.items(), key=lambda item: (-item[1], item[0]))
    return {
        "total_questions": len(rows),
        "last_question_at": str(recent_questions[-1]["timestamp"]),
        "top_intents": [{"intent": key, "count": value} for key, value in sorted_intents[:3]],
        "recent_questions": list(reversed(recent_questions[-limit:])),
    }
