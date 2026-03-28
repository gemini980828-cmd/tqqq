from __future__ import annotations

from typing import Any, Mapping

from tqqq_strategy.ai.orchestrator_brief import build_orchestrator_briefs
from tqqq_strategy.ai.orchestrator_policy import classify_question

SCREEN_BY_INTENT = {
    "default_priority": "home",
    "action": "managers/core_strategy",
    "risk": "managers/core_strategy",
    "cash": "managers/cash_debt",
    "stock_research": "managers/stock_research",
    "real_estate": "managers/real_estate",
}


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _build_source_details(context: Mapping[str, Any], source_manager_ids: list[str]) -> list[dict[str, Any]]:
    summaries = dict(context.get("manager_summaries") or {})
    details: list[dict[str, Any]] = []
    for manager_id in source_manager_ids:
        summary = dict(summaries.get(manager_id) or {})
        details.append(
            {
                "source_manager_id": manager_id,
                "summary_text": str(summary.get("summary_text") or ""),
                "stale": bool(summary.get("stale", False)),
                "recommended_actions": [str(item) for item in summary.get("recommended_actions", [])],
            }
        )
    return details


def _resolve_next_action(context: Mapping[str, Any], source_manager_ids: list[str]) -> dict[str, Any]:
    priority_actions = [dict(item) for item in list(context.get("priority_actions") or [])]
    for manager_id in source_manager_ids:
        for action in priority_actions:
            if str(action.get("manager_id") or "") == manager_id:
                return action
    home_inbox = [dict(item) for item in list(context.get("home_inbox") or [])]
    if home_inbox:
        inbox_item = home_inbox[0]
        return {
            "recommended_action": str(inbox_item.get("recommended_action") or inbox_item.get("title") or ""),
            "goto_screen": SCREEN_BY_INTENT.get("default_priority", "home"),
        }
    return {
        "recommended_action": "",
        "goto_screen": SCREEN_BY_INTENT.get("default_priority", "home"),
    }


def _build_supporting_managers(context: Mapping[str, Any], source_manager_ids: list[str]) -> list[dict[str, Any]]:
    summaries = dict(context.get("manager_summaries") or {})
    supporting: list[dict[str, Any]] = []
    for manager_id in source_manager_ids:
        summary = dict(summaries.get(manager_id) or {})
        supporting.append(
            {
                "manager_id": manager_id,
                "summary_text": str(summary.get("summary_text") or ""),
                "stale": bool(summary.get("stale", False)),
            }
        )
    return supporting


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
    source_details = _build_source_details(context, source_manager_ids)
    next_action = _resolve_next_action(context, source_manager_ids)
    supporting_managers = _build_supporting_managers(context, source_manager_ids)
    short_answer = answer_parts[0] if answer_parts else answer

    return {
        "question": prompt,
        "answer": answer,
        "short_answer": short_answer,
        "highlights": highlights,
        "source_manager_ids": source_manager_ids,
        "source_details": source_details,
        "supporting_managers": supporting_managers,
        "next_action": str(next_action.get("recommended_action") or ""),
        "go_to_screen": str(SCREEN_BY_INTENT.get(primary_intent) or next_action.get("goto_screen") or "home"),
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
