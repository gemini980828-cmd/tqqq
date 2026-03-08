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
