from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _round_krw(value: float) -> int:
    return int(round(value))


def _position_market_value_krw(row: Mapping[str, Any]) -> float:
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


def build_liquidity_summary(manual_inputs: dict[str, list[dict[str, Any]]]) -> dict[str, float | int]:
    overview = build_wealth_overview(manual_inputs)
    denominator = float(overview["invested_krw"] + overview["cash_krw"])
    liquidity_ratio_pct = (float(overview["cash_krw"]) / denominator) * 100.0 if denominator else 0.0
    return {
        "cash_krw": overview["cash_krw"],
        "debt_krw": overview["debt_krw"],
        "net_liquidity_krw": overview["cash_krw"] - overview["debt_krw"],
        "liquidity_ratio_pct": round(liquidity_ratio_pct, 2),
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
        "transactions_total": len(manual_inputs.get("transactions", [])),
    }


def _base_manager_cards(manual_inputs: dict[str, list[dict[str, Any]]], target: float) -> list[dict[str, Any]]:
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


def build_manager_cards(
    manual_inputs: dict[str, list[dict[str, Any]]],
    target_weight_pct: float | None = None,
    summary_by_manager: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    target = 0.0 if target_weight_pct is None else target_weight_pct
    summaries = summary_by_manager or {}
    enriched_cards: list[dict[str, Any]] = []

    for card in _base_manager_cards(manual_inputs, target):
        summary = summaries.get(card["manager_id"])
        if not summary:
            enriched_cards.append(card)
            continue

        warnings = [str(item) for item in summary.get("warnings", [])]
        actions = [str(item) for item in summary.get("recommended_actions", [])]
        enriched_cards.append(
            {
                **card,
                "status": "stale" if bool(summary.get("stale")) else card["status"],
                "summary": str(summary.get("summary_text") or card["summary"]),
                "warning_count": len(warnings),
                "recommended_action": actions[0] if actions else "",
                "stale": bool(summary.get("stale")),
                "generated_at": str(summary.get("generated_at") or ""),
                "warnings": warnings,
                "key_points": [str(item) for item in summary.get("key_points", [])],
            }
        )
    return enriched_cards


def build_summary_source_version(
    manual_inputs: dict[str, list[dict[str, Any]]],
    as_of: str,
    source_label: str | None = None,
) -> str:
    payload = json.dumps(manual_inputs, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    date_token = str(as_of)[:10]
    if source_label:
        return f"{source_label}:{date_token}:{digest}"
    return f"{date_token}:{digest}"
