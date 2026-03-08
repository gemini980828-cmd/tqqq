from __future__ import annotations

from typing import Any, Mapping

from tqqq_strategy.ai.orchestrator_brief import build_orchestrator_briefs
from tqqq_strategy.ai.orchestrator_policy import classify_question


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def run_orchestrator(
    *,
    question: str,
    context: Mapping[str, Any],
    trigger: str = "user_submit",
) -> dict[str, Any]:
    if trigger != "user_submit" or not str(question).strip():
        raise ValueError("Orchestrator requires explicit user action")

    prompt = str(question).strip()
    briefs = build_orchestrator_briefs(context)
    policy = dict(context.get("orchestrator_policy") or {})
    classification = classify_question(prompt, policy=policy)
    brief_keys = list(classification["brief_keys"])
    highlights: list[str] = []
    source_manager_ids: list[str] = list(classification["source_manager_ids"])
    answer_parts: list[str] = []

    for key in brief_keys:
        brief = str(briefs.get(key) or "").strip()
        if not brief:
            continue
        answer_parts.append(brief)
        _append_unique(highlights, brief if len(brief) <= 48 else brief[:45] + "...")

    if not answer_parts:
        fallback = str(briefs.get("default_priority") or "")
        answer_parts.append(fallback)
        _append_unique(highlights, "Cache-first summary")
        _append_unique(source_manager_ids, "core_strategy")

    primary_intent = str(classification["primary_intent"])
    if len(answer_parts) > 1:
        answer = f"1순위 판단: {answer_parts[0]}\n\n보조 판단: {' '.join(answer_parts[1:])}"
    else:
        answer = answer_parts[0]

    return {
        "question": prompt,
        "answer": answer,
        "highlights": highlights,
        "source_manager_ids": source_manager_ids,
        "brief_keys_used": brief_keys,
        "primary_intent": primary_intent,
        "guardrails": {
            "explicit_only": True,
            "live_ai_used": False,
            "trigger": trigger,
        },
        "metadata": {
            "mode": "cache_first",
            "question_chars": len(prompt),
            "source_manager_count": len(source_manager_ids),
            "primary_intent": primary_intent,
        },
    }
