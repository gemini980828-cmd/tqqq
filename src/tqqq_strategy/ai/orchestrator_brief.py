from __future__ import annotations

from typing import Any, Mapping


def _format_krw(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "N/A"
    return f"{int(round(numeric)):,}원"


def _summary_text(summaries: Mapping[str, Any], manager_id: str) -> str:
    summary = dict(summaries.get(manager_id) or {})
    return str(summary.get("summary_text") or "").strip()


def build_orchestrator_briefs(context: Mapping[str, Any]) -> dict[str, str]:
    action_hero = dict(context.get("action_hero") or {})
    wealth_overview = dict(context.get("wealth_overview") or {})
    liquidity = dict(context.get("liquidity_summary") or {})
    risk_gauges = dict(context.get("risk_gauges") or {})
    home_inbox = list(context.get("home_inbox") or [])
    summaries = dict(context.get("manager_summaries") or {})

    action = str(action_hero.get("action") or "유지")
    target_weight = action_hero.get("target_weight_pct", "N/A")
    reason = str(action_hero.get("reason_summary") or "").strip()
    inbox_item = dict(home_inbox[0]) if home_inbox else {}

    action_brief = f"현재 가장 중요한 액션은 {action}이며 전략 목표 비중은 {target_weight}%입니다."
    if reason:
        action_brief += f" 근거는 {reason} 입니다."
    if inbox_item:
        action_brief += f" 가장 앞선 inbox는 '{inbox_item.get('title', '오늘 액션')}'이며 {inbox_item.get('detail', '')}"

    cash_krw = liquidity.get("cash_krw", wealth_overview.get("cash_krw"))
    debt_krw = liquidity.get("debt_krw", wealth_overview.get("debt_krw"))
    liquidity_ratio = liquidity.get("liquidity_ratio_pct", "N/A")
    cash_brief = (
        f"현금 여력은 현금 {_format_krw(cash_krw)}, 부채 {_format_krw(debt_krw)}, "
        f"유동성 비중 {liquidity_ratio}% 기준으로 점검하면 됩니다."
    )

    risk_notes = []
    for key in ("vol20", "spy200_dist", "tqqq_dist200"):
        payload = dict(risk_gauges.get(key) or {})
        if not payload:
            continue
        risk_notes.append(f"{key}={payload.get('value')} ({payload.get('status')})")
    risk_brief = (
        "현재 리스크 계기판은 " + ", ".join(risk_notes) + " 상태입니다."
        if risk_notes
        else "현재 리스크 계기판 데이터가 충분하지 않습니다."
    )

    stock_summary = _summary_text(summaries, "stock_research")
    stock_brief = (
        f"개별주 매니저 기준으로는 {stock_summary}"
        if stock_summary
        else "개별주 매니저는 현재 cached summary 기준으로 큰 경보가 없습니다."
    )

    estate_summary = _summary_text(summaries, "real_estate")
    estate_brief = (
        f"부동산 매니저 기준으로는 {estate_summary}"
        if estate_summary
        else "부동산 매니저는 현재 cached summary 기준으로 큰 경보가 없습니다."
    )

    default_priority = "현재 캐시된 Home inbox와 manager summary를 기준으로 전체 우선순위는 코어전략 점검 → 현금 여력 확인 순서입니다."

    return {
        "action": action_brief,
        "cash": cash_brief,
        "risk": risk_brief,
        "stock_research": stock_brief,
        "real_estate": estate_brief,
        "default_priority": default_priority,
    }
