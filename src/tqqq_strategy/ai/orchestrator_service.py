from __future__ import annotations

from typing import Any, Mapping

from tqqq_strategy.ai.orchestrator_brief import build_orchestrator_briefs


BRIEF_SOURCE_MANAGERS = {
    "action": "core_strategy",
    "cash": "cash_debt",
    "risk": "core_strategy",
    "stock_research": "stock_research",
    "real_estate": "real_estate",
    "default_priority": "core_strategy",
}


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _pick_brief_keys(prompt: str) -> list[str]:
    wants_action = any(token in prompt for token in ("액션", "해야", "우선", "중요"))
    wants_cash = any(token in prompt for token in ("현금", "유동성", "여력"))
    wants_risk = any(token in prompt for token in ("리스크", "위험", "안전"))

    keys: list[str] = []
    if wants_action or not (wants_cash or wants_risk):
        keys.append("action")
    if wants_cash:
        keys.append("cash")
    if wants_risk:
        keys.append("risk")
    if "개별주" in prompt or "주식" in prompt:
        keys.append("stock_research")
    if "부동산" in prompt:
        keys.append("real_estate")
    if not keys:
        keys.append("default_priority")
    return keys


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
    brief_keys = _pick_brief_keys(prompt)
    highlights: list[str] = []
    source_manager_ids: list[str] = []
    answer_parts: list[str] = []

    for key in brief_keys:
        brief = str(briefs.get(key) or "").strip()
        if not brief:
            continue
        answer_parts.append(brief)
        _append_unique(highlights, brief if len(brief) <= 48 else brief[:45] + "...")
        _append_unique(source_manager_ids, BRIEF_SOURCE_MANAGERS.get(key, "core_strategy"))

    if not answer_parts:
        fallback = str(briefs.get("default_priority") or "")
        answer_parts.append(fallback)
        _append_unique(highlights, "Cache-first summary")
        _append_unique(source_manager_ids, "core_strategy")

    return {
        "question": prompt,
        "answer": " ".join(part for part in answer_parts if part),
        "highlights": highlights,
        "source_manager_ids": source_manager_ids,
        "brief_keys_used": brief_keys,
        "guardrails": {
            "explicit_only": True,
            "live_ai_used": False,
            "trigger": trigger,
        },
        "metadata": {
            "mode": "cache_first",
            "question_chars": len(prompt),
            "source_manager_count": len(source_manager_ids),
        },
    }
