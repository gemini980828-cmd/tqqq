from __future__ import annotations

from typing import Any, Mapping


def _format_krw(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    return f"{int(round(numeric)):,}원"


def _append_unique(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _summary_text(summaries: Mapping[str, Any], manager_id: str) -> str:
    summary = dict(summaries.get(manager_id) or {})
    return str(summary.get("summary_text") or "").strip()


def run_orchestrator(
    *,
    question: str,
    context: Mapping[str, Any],
    trigger: str = "user_submit",
) -> dict[str, Any]:
    if trigger != "user_submit" or not str(question).strip():
        raise ValueError("Orchestrator requires explicit user action")

    prompt = str(question).strip()
    normalized = prompt.lower()
    action_hero = dict(context.get("action_hero") or {})
    wealth_overview = dict(context.get("wealth_overview") or {})
    liquidity = dict(context.get("liquidity_summary") or {})
    risk_gauges = dict(context.get("risk_gauges") or {})
    home_inbox = list(context.get("home_inbox") or [])
    summaries = dict(context.get("manager_summaries") or {})

    highlights: list[str] = []
    source_manager_ids: list[str] = []
    answer_parts: list[str] = []

    wants_action = any(token in prompt for token in ("액션", "해야", "우선", "중요"))
    wants_cash = any(token in prompt for token in ("현금", "유동성", "여력"))
    wants_risk = any(token in prompt for token in ("리스크", "위험", "안전"))

    if wants_action or not (wants_cash or wants_risk):
        action = str(action_hero.get("action") or "유지")
        target_weight = action_hero.get("target_weight_pct")
        reason = str(action_hero.get("reason_summary") or "")
        answer_parts.append(f"현재 가장 중요한 액션은 {action}이며 전략 목표 비중은 {target_weight}%입니다.")
        if reason:
            answer_parts.append(f"근거는 {reason} 입니다.")
        if home_inbox:
            inbox_item = dict(home_inbox[0])
            answer_parts.append(f"가장 앞선 inbox는 '{inbox_item.get('title', '오늘 액션')}'이며 {inbox_item.get('detail', '')}")
        _append_unique(highlights, f"Action {action}")
        _append_unique(source_manager_ids, "core_strategy")

    if wants_cash:
        cash_krw = liquidity.get("cash_krw", wealth_overview.get("cash_krw"))
        debt_krw = liquidity.get("debt_krw", wealth_overview.get("debt_krw"))
        liquidity_ratio = liquidity.get("liquidity_ratio_pct")
        answer_parts.append(
            f"현금 여력은 현금 {_format_krw(cash_krw)}, 부채 {_format_krw(debt_krw)}, 유동성 비중 {liquidity_ratio}% 기준으로 점검하면 됩니다."
        )
        _append_unique(highlights, f"Cash {_format_krw(cash_krw)}")
        _append_unique(source_manager_ids, "cash_debt")

    if wants_risk:
        risk_notes = []
        for key in ("vol20", "spy200_dist", "tqqq_dist200"):
            payload = dict(risk_gauges.get(key) or {})
            if not payload:
                continue
            risk_notes.append(f"{key}={payload.get('value')} ({payload.get('status')})")
        if risk_notes:
            answer_parts.append("현재 리스크 계기판은 " + ", ".join(risk_notes) + " 상태입니다.")
            _append_unique(highlights, risk_notes[0])
        _append_unique(source_manager_ids, "core_strategy")

    if "개별주" in prompt or "주식" in prompt:
        stock_summary = _summary_text(summaries, "stock_research")
        if stock_summary:
            answer_parts.append(f"개별주 매니저 기준으로는 {stock_summary}")
            _append_unique(highlights, stock_summary)
        _append_unique(source_manager_ids, "stock_research")
    if "부동산" in prompt:
        estate_summary = _summary_text(summaries, "real_estate")
        if estate_summary:
            answer_parts.append(f"부동산 매니저 기준으로는 {estate_summary}")
            _append_unique(highlights, estate_summary)
        _append_unique(source_manager_ids, "real_estate")

    if not answer_parts:
        answer_parts.append("현재 캐시된 Home inbox와 manager summary를 기준으로 전체 상태는 안정적이며, 우선순위는 코어전략 점검 → 현금 여력 확인 순서입니다.")
        _append_unique(highlights, "Cache-first summary")
        _append_unique(source_manager_ids, "core_strategy")

    if not highlights and home_inbox:
        inbox_item = dict(home_inbox[0])
        _append_unique(highlights, str(inbox_item.get("title", "Home inbox")))

    return {
        "question": prompt,
        "answer": " ".join(part for part in answer_parts if part),
        "highlights": highlights,
        "source_manager_ids": source_manager_ids,
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
