from __future__ import annotations

from typing import Any, Mapping

from tqqq_strategy.ai.stock_research_status import is_candidate_status

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_MANAGER_PRIORITY = {
    "core_strategy": 0,
    "cash_debt": 1,
    "stock_research": 2,
    "real_estate": 3,
}


def _push_item(
    items: list[dict[str, str]],
    *,
    item_id: str,
    manager_id: str,
    severity: str,
    title: str,
    detail: str,
    recommended_action: str = "",
    stale: bool = False,
) -> None:
    items.append(
        {
            "id": item_id,
            "manager_id": manager_id,
            "severity": severity,
            "title": title,
            "detail": detail,
            "recommended_action": recommended_action,
            "stale": "true" if stale else "false",
        }
    )


def build_home_inbox(
    *,
    snapshot: Mapping[str, Any],
    manual_inputs: dict[str, list[dict[str, Any]]],
    manager_summaries: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    action_hero = dict(snapshot.get("action_hero") or {})
    core_actuals = dict(snapshot.get("core_strategy_actuals") or snapshot.get("core_strategy_position") or {})
    wealth_overview = dict(snapshot.get("wealth_overview") or {})

    action = str(action_hero.get("action") or "유지")
    target_weight_pct = float(action_hero.get("target_weight_pct") or 0.0)
    actual_weight_pct = float(core_actuals.get("actual_weight_pct") or 0.0)
    rebalance_gap_krw = int(round(float(core_actuals.get("rebalance_gap_krw") or 0.0)))
    core_summary = dict(manager_summaries.get("core_strategy") or {})

    if action != "유지" or abs(target_weight_pct - actual_weight_pct) >= 5.0:
        _push_item(
            items,
            item_id="core_strategy-action",
            manager_id="core_strategy",
            severity="high",
            title=f"코어전략 {action} 점검",
            detail=f"실보유 {actual_weight_pct:.2f}% / 목표 {target_weight_pct:.2f}% / 리밸런싱 gap {rebalance_gap_krw:,}원",
            recommended_action=str((core_summary.get("recommended_actions") or [""])[0]),
            stale=bool(core_summary.get("stale")),
        )

    cash_krw = int(round(float(wealth_overview.get("cash_krw") or 0.0)))
    debt_krw = int(round(float(wealth_overview.get("debt_krw") or 0.0)))
    cash_summary = dict(manager_summaries.get("cash_debt") or {})
    cash_warnings = [str(item) for item in cash_summary.get("warnings", [])]
    if cash_summary.get("stale") or debt_krw >= cash_krw or cash_warnings:
        _push_item(
            items,
            item_id="cash_debt-guardrail",
            manager_id="cash_debt",
            severity="high",
            title="현금/부채 방어 여력 재점검",
            detail=f"현금 {cash_krw:,}원 / 부채 {debt_krw:,}원" + (f" / {cash_warnings[0]}" if cash_warnings else ""),
            recommended_action=str((cash_summary.get("recommended_actions") or [""])[0]),
            stale=bool(cash_summary.get("stale")),
        )

    stock_candidates = [row for row in manual_inputs.get("stock_watchlist", []) if is_candidate_status(row.get("status"))]
    stock_summary = dict(manager_summaries.get("stock_research") or {})
    if stock_candidates or stock_summary.get("recommended_actions"):
        first_action = str((stock_summary.get("recommended_actions") or [""])[0])
        _push_item(
            items,
            item_id="stock_research-candidates",
            manager_id="stock_research",
            severity="medium",
            title="개별주 후보 리서치",
            detail=first_action or f"후보 {len(stock_candidates)}개가 대기 중입니다.",
            recommended_action=first_action,
            stale=bool(stock_summary.get("stale")),
        )

    property_candidates = [row for row in manual_inputs.get("property_watchlist", []) if str(row.get("status", "")).strip() in {"검토", "우선검토"}]
    real_estate_summary = dict(manager_summaries.get("real_estate") or {})
    if property_candidates or real_estate_summary.get("recommended_actions"):
        first_action = str((real_estate_summary.get("recommended_actions") or [""])[0])
        _push_item(
            items,
            item_id="real_estate-review",
            manager_id="real_estate",
            severity="medium",
            title="부동산 검토 큐 확인",
            detail=first_action or f"검토 상태 단지 {len(property_candidates)}개를 정리하세요.",
            recommended_action=first_action,
            stale=bool(real_estate_summary.get("stale")),
        )

    for manager_id, summary in manager_summaries.items():
        if manager_id in {"core_strategy", "cash_debt", "stock_research", "real_estate"}:
            continue
        if not summary.get("stale"):
            continue
        _push_item(
            items,
            item_id=f"{manager_id}-stale",
            manager_id=manager_id,
            severity="medium",
            title=f"{manager_id} summary 갱신 필요",
            detail="저장된 manager summary가 stale 상태입니다.",
            recommended_action=str((summary.get("recommended_actions") or [""])[0]),
            stale=True,
        )

    items.sort(key=lambda item: (_SEVERITY_ORDER[item["severity"]], _MANAGER_PRIORITY.get(item["manager_id"], 99), item["title"]))
    return items[:5]
