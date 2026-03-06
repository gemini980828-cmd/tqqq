from __future__ import annotations

from typing import Any


def _round_krw(value: float) -> int:
    return int(round(value))


def _position_market_value_krw(row: dict[str, Any]) -> float:
    if row.get("market_value_krw") is not None:
        return float(row["market_value_krw"])
    return float(row.get("quantity", 0.0)) * float(row.get("market_price_usd", 0.0)) * float(row.get("fx_rate_krw", 1.0))


def build_wealth_overview(manual_inputs: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    invested = sum(_position_market_value_krw(row) for row in manual_inputs.get("positions", []))
    cash = sum(float(row["balance_krw"]) for row in manual_inputs.get("cash_debt", []) if row.get("kind") == "cash")
    debt = sum(float(row["balance_krw"]) for row in manual_inputs.get("cash_debt", []) if row.get("kind") == "debt")
    return {
        "invested_krw": _round_krw(invested),
        "investable_assets_krw": _round_krw(invested),
        "cash_krw": _round_krw(cash),
        "debt_krw": _round_krw(debt),
        "net_worth_krw": _round_krw(invested + cash - debt),
    }


def summarize_wealth_overview(manual_inputs: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return build_wealth_overview(manual_inputs)


def build_core_strategy_position(
    manual_inputs: dict[str, list[dict[str, Any]]],
    target_weight_pct: float,
    manager_id: str = "core_strategy",
) -> dict[str, Any]:
    positions = [row for row in manual_inputs.get("positions", []) if row.get("manager_id") == manager_id]
    actual_value = sum(_position_market_value_krw(row) for row in positions)
    quantity = sum(float(row.get("quantity", 0.0)) for row in positions)
    overview = build_wealth_overview(manual_inputs)
    investable_total = float(overview["investable_assets_krw"] + overview["cash_krw"])
    actual_weight_pct = round((actual_value / investable_total) * 100.0, 2) if investable_total else 0.0
    primary = positions[0] if positions else {}
    market_price_krw = float(primary.get("market_price_krw") or float(primary.get("market_price_usd", 0.0)) * float(primary.get("fx_rate_krw", 1.0)))
    avg_cost_krw = float(primary.get("avg_cost_krw") or float(primary.get("avg_cost_usd", 0.0)) * float(primary.get("fx_rate_krw", 1.0)))
    target = round(target_weight_pct, 2)
    target_value = investable_total * (target / 100.0)
    rebalance_gap = target_value - actual_value
    gap_weight = round(target - actual_weight_pct, 2)
    if rebalance_gap > 0:
        rebalance_action = "buy"
    elif rebalance_gap < 0:
        rebalance_action = "sell"
    else:
        rebalance_action = "hold"
    return {
        "symbol": primary.get("symbol", "TQQQ"),
        "name": primary.get("name", "ProShares UltraPro QQQ"),
        "quantity": round(quantity, 4),
        "actual_value_krw": _round_krw(actual_value),
        "market_value_krw": _round_krw(actual_value),
        "market_price_krw": _round_krw(market_price_krw),
        "avg_cost_krw": _round_krw(avg_cost_krw),
        "target_weight_pct": target,
        "actual_weight_pct": actual_weight_pct,
        "gap_weight_pct": gap_weight,
        "gap_pct": round(actual_weight_pct - target, 2),
        "target_value_krw": _round_krw(target_value),
        "rebalance_gap_krw": _round_krw(rebalance_gap),
        "rebalance_action": rebalance_action,
        "investable_total_krw": _round_krw(investable_total),
    }


def summarize_core_strategy_position(manual_inputs: dict[str, list[dict[str, Any]]], target_weight_pct: float) -> dict[str, Any]:
    return build_core_strategy_position(manual_inputs, target_weight_pct)


def summarize_manager_counts(manual_inputs: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    return {
        "stocks_total": len(manual_inputs.get("stock_watchlist", [])),
        "properties_total": len(manual_inputs.get("property_watchlist", [])),
        "cash_debt_total": len(manual_inputs.get("cash_debt", [])),
        "positions_total": len(manual_inputs.get("positions", [])),
    }


def build_manager_cards(
    manual_inputs: dict[str, list[dict[str, Any]]],
    target_weight_pct: float | None = None,
) -> list[dict[str, Any]]:
    target = 0.0 if target_weight_pct is None else target_weight_pct
    counts = summarize_manager_counts(manual_inputs)
    overview = build_wealth_overview(manual_inputs)
    core_position = build_core_strategy_position(manual_inputs, target)
    return [
        {
            "manager_id": "core_strategy",
            "title": "Core Strategy",
            "label": "Core Strategy",
            "status": "live",
            "headline": f"실보유 {core_position['actual_weight_pct']:.2f}% / 목표 {core_position['target_weight_pct']:.2f}%",
            "summary": f"실보유 {core_position['actual_weight_pct']:.2f}% / 목표 {core_position['target_weight_pct']:.2f}%",
        },
        {
            "manager_id": "stock_research",
            "title": "Stock Research",
            "label": "Stock Research",
            "status": "tracking",
            "headline": f"관심종목 {counts['stocks_total']}개",
            "summary": f"관심종목 {counts['stocks_total']}개",
        },
        {
            "manager_id": "real_estate",
            "title": "Real Estate",
            "label": "Real Estate",
            "status": "tracking",
            "headline": f"관심 단지 {counts['properties_total']}개",
            "summary": f"관심 단지 {counts['properties_total']}개",
        },
        {
            "manager_id": "cash_debt",
            "title": "Cash & Debt",
            "label": "Cash & Debt",
            "status": "monitoring",
            "headline": f"현금/부채 항목 {counts['cash_debt_total']}개",
            "summary": f"현금 {overview['cash_krw']:,}원",
        },
    ]
