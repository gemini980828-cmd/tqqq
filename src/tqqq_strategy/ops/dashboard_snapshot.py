from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tqqq_strategy.ai.inbox_builder import build_home_inbox
from tqqq_strategy.ai.orchestrator_audit import DEFAULT_ORCHESTRATOR_AUDIT_PATH, build_orchestrator_insights
from tqqq_strategy.ai.orchestrator_brief import build_orchestrator_briefs
from tqqq_strategy.ai.orchestrator_context import build_orchestrator_context
from tqqq_strategy.ai.orchestrator_policy import export_orchestrator_policy
from tqqq_strategy.ai.stock_research_status import normalize_stock_status
from tqqq_strategy.wealth import (
    DEFAULT_SUMMARY_STORE_PATH,
    build_core_strategy_position,
    build_liquidity_summary,
    build_manager_cards,
    build_summary_source_version,
    build_wealth_overview,
    load_manual_inputs,
    load_summary_store,
)

DEFAULT_MANUAL_INPUTS_PATH = Path("data/manual/wealth_manual.json")
MANAGER_SCREEN_MAP = {
    "core_strategy": "managers/core_strategy",
    "stock_research": "managers/stock_research",
    "real_estate": "managers/real_estate",
    "cash_debt": "managers/cash_debt",
}


def _status_lower_better(value: float, threshold: float, amber_ratio: float = 0.85) -> str:
    if pd.isna(value):
        return "red"
    if value >= threshold:
        return "red"
    if value >= threshold * amber_ratio:
        return "amber"
    return "green"


def _status_higher_better(value: float, threshold: float, amber_ratio: float = 1.03) -> str:
    if pd.isna(value):
        return "red"
    if value <= threshold:
        return "red"
    if value <= threshold * amber_ratio:
        return "amber"
    return "green"


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _build_reason_summary(action: str, target_weight_pct: float, dist200: float, vol20: float, spy200: float) -> str:
    if action == "매수":
        return f"추세 강화로 비중 확대 (Dist200 {dist200:.2f}, Vol20 {vol20:.2f}%)"
    if action == "매도":
        if target_weight_pct <= 0:
            return f"리스크 조건으로 현금 전환 (Vol20 {vol20:.2f}% / SPY200 {spy200:.2f})"
        return f"리스크 관리 차원 감량 (목표 비중 {target_weight_pct:.0f}%)"
    return f"추세 조건 유지 (Dist200 {dist200:.2f} / SPY200 {spy200:.2f})"


def _build_condition_pass_rate(row: pd.Series, vol20: float, dist200: float, spy200: float) -> str:
    checks = [
        vol20 < 5.9 if pd.notna(vol20) else False,
        spy200 > 97.75 if pd.notna(spy200) else False,
        dist200 >= 101.0 if pd.notna(dist200) else False,
        (
            float(row.get("QQQ3일선", float("nan"))) > float(row.get("QQQ161일선", float("nan")))
            if pd.notna(row.get("QQQ3일선")) and pd.notna(row.get("QQQ161일선"))
            else False
        ),
        dist200 < 139.0 if pd.notna(dist200) else False,
        vol20 < 6.0 if pd.notna(vol20) else False,
    ]
    return f"{sum(1 for item in checks if item)}/{len(checks)}"


def _default_next_run_at(latest_date: pd.Timestamp) -> str:
    normalized = pd.Timestamp(latest_date)
    next_day = normalized.date() + timedelta(days=1)
    return datetime(next_day.year, next_day.month, next_day.day, 22, 30, tzinfo=timezone.utc).isoformat()


def _build_event_timeline(signals: pd.DataFrame, limit: int = 5) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    recent = signals.tail(90).reset_index(drop=True)
    for i in range(1, len(recent)):
        prev = float(recent.iloc[i - 1]["S2_weight"])
        current = float(recent.iloc[i]["S2_weight"])
        if abs(prev - current) < 1e-12:
            continue
        date = recent.iloc[i]["time"].strftime("%Y-%m-%d")
        if prev <= 1e-9 and current > 1e-9:
            event_type = "재진입"
            detail = f"{prev * 100:.2f}% → {current * 100:.2f}% 진입"
            severity = "high"
        elif prev > 1e-9 and current <= 1e-9:
            event_type = "강제청산"
            detail = f"{prev * 100:.2f}% → 0.00% 전환"
            severity = "high"
        elif abs(prev - 1.0) < 1e-9 and abs(current - 0.95) < 1e-9:
            event_type = "TP10"
            detail = "100% → 95% 감량"
            severity = "medium"
        else:
            event_type = "비중 변경"
            detail = f"{prev * 100:.2f}% → {current * 100:.2f}% 조정"
            severity = "medium"
        timeline.append(
            {
                "id": f"event-core-strategy-{date}-{i}",
                "date": date,
                "type": event_type,
                "title": f"코어전략 {event_type}",
                "detail": detail,
                "category": "allocation",
                "severity": severity,
                "source_manager_id": "core_strategy",
                "entity_type": "position",
                "entity_id": "tqqq-core",
            }
        )
    return list(reversed(timeline[-limit:]))


def _severity_rank(value: str) -> int:
    return {"high": 0, "medium": 1, "low": 2, "info": 3}.get(str(value), 9)


def _build_priority_actions(
    home_inbox: list[dict[str, Any]],
    manager_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in home_inbox:
        manager_id = str(item.get("manager_id") or "core_strategy")
        actions.append(
            {
                "id": str(item.get("id") or f"priority-{manager_id}"),
                "title": str(item.get("title") or "우선 액션"),
                "detail": str(item.get("detail") or ""),
                "severity": str(item.get("severity") or "medium"),
                "manager_id": manager_id,
                "source": "home_inbox",
                "recommended_action": str(item.get("recommended_action") or ""),
                "goto_screen": MANAGER_SCREEN_MAP.get(manager_id, "home"),
            }
        )

    for card in manager_cards:
        warnings = [str(item) for item in card.get("warnings", [])]
        if not warnings:
            continue
        manager_id = str(card.get("manager_id") or "core_strategy")
        actions.append(
            {
                "id": f"priority-{manager_id}-warning",
                "title": str(card.get("headline") or card.get("title") or manager_id),
                "detail": warnings[0],
                "severity": "high" if card.get("warning_count") else "medium",
                "manager_id": manager_id,
                "source": "manager_summary",
                "recommended_action": str(card.get("recommended_action") or ""),
                "goto_screen": MANAGER_SCREEN_MAP.get(manager_id, "home"),
            }
        )

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(actions, key=lambda row: (_severity_rank(str(row.get("severity"))), str(row.get("manager_id")))):
        identifier = str(item["id"])
        if identifier in seen:
            continue
        seen.add(identifier)
        unique.append(item)
    return unique[:6]


def _build_cross_manager_alerts(
    manager_summaries: dict[str, dict[str, Any]],
    liquidity_summary: dict[str, Any],
    risk_gauges: dict[str, Any],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    risk_statuses = {
        key: str(dict(payload).get("status") or "info")
        for key, payload in risk_gauges.items()
        if isinstance(payload, dict)
    }
    if any(status in {"amber", "red"} for status in risk_statuses.values()):
        alerts.append(
            {
                "id": "alert-risk-review",
                "title": "리스크 계기판 재점검",
                "detail": "변동성/이격도 상태가 경계 구간이어서 현금 여력과 함께 점검이 필요합니다.",
                "severity": "high" if "red" in risk_statuses.values() else "medium",
                "manager_ids": ["core_strategy", "cash_debt"],
                "entity_type": "portfolio",
                "entity_id": "wealth-desk",
            }
        )

    if float(liquidity_summary.get("debt_krw") or 0.0) > 0:
        alerts.append(
            {
                "id": "alert-liquidity-debt",
                "title": "현금/부채 동시 점검",
                "detail": "부채가 남아 있어 전략 액션 전에 현금 방어 여력을 함께 확인해야 합니다.",
                "severity": "medium",
                "manager_ids": ["cash_debt", "core_strategy"],
                "entity_type": "cash",
                "entity_id": "net-liquidity",
            }
        )

    for manager_id, summary in manager_summaries.items():
        warnings = [str(item) for item in summary.get("warnings", [])]
        if not warnings:
            continue
        alerts.append(
            {
                "id": f"alert-{manager_id}",
                "title": f"{manager_id} 경고",
                "detail": warnings[0],
                "severity": "medium",
                "manager_ids": [manager_id],
                "entity_type": "manager",
                "entity_id": manager_id,
            }
        )

    alerts.sort(key=lambda row: (_severity_rank(str(row["severity"])), row["id"]))
    return alerts[:6]


def _build_research_candidates(manual_inputs: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for record in manual_inputs.get("stock_watchlist", []):
        status = str(record.get("status") or "미분류")
        candidates.append(
            {
                "idea_id": str(record.get("idea_id") or ""),
                "symbol": str(record.get("symbol") or ""),
                "status": status,
                "memo": str(record.get("memo") or ""),
                "priority": "high" if status == "후보" else "medium" if status == "관찰" else "low",
                "priority_reason": "후속 검토 필요" if status in {"후보", "관찰"} else "관찰 상태 유지",
                "manager_id": "stock_research",
                "next_action": f"{str(record.get('symbol') or '').upper()} 후속 리서치 업데이트".strip(),
            }
        )
    return candidates


def _stock_priority_rank(status: str, is_held: bool) -> tuple[int, int]:
    normalized = normalize_stock_status(status)
    if normalized == "후보" and not is_held:
        return (0, 0)
    if normalized == "후보" and is_held:
        return (1, 0)
    if normalized == "관찰":
        return (2, 0 if not is_held else 1)
    if normalized == "보류":
        return (3, 0)
    if normalized == "제외":
        return (5, 0)
    return (4, 0)


def _stock_score(status: str, is_held: bool, overlap_level: str) -> int:
    normalized = normalize_stock_status(status)
    base = {
        "후보": 84,
        "관찰": 68,
        "보류": 45,
        "제외": 20,
        "탐색": 35,
    }.get(normalized, 35)
    if is_held:
        base -= 6
    if overlap_level == "high":
        base -= 8
    return max(0, min(base, 100))


def _stock_risk_level(is_held: bool, overlap_level: str, status: str) -> str:
    normalized = normalize_stock_status(status)
    if is_held and overlap_level == "high":
        return "high"
    if normalized in {"관찰", "후보"}:
        return "medium"
    return "low"


def _build_stock_research_workspace(
    manual_inputs: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> dict[str, Any]:
    positions = list(manual_inputs.get("positions", []))
    held_symbols = {str(position.get("symbol") or "") for position in positions if str(position.get("symbol") or "")}
    watchlist = list(manual_inputs.get("stock_watchlist", []))

    items: list[dict[str, Any]] = []
    for record in watchlist:
        symbol = str(record.get("symbol") or "")
        normalized_status = normalize_stock_status(record.get("status"))
        is_held = symbol in held_symbols
        overlap_level = "high" if is_held else "low"
        priority_reason = "기존 보유와 별개로 신규 편입 검토 필요" if normalized_status == "후보" and not is_held else (
            "기존 보유 포지션과 함께 비중 판단 필요" if is_held else "관찰 상태 유지"
        )
        items.append(
            {
                "idea_id": str(record.get("idea_id") or symbol.lower()),
                "symbol": symbol,
                "company_name": symbol,
                "status": normalized_status,
                "memo": str(record.get("memo") or ""),
                "is_held": is_held,
                "overlap_level": overlap_level,
                "score": _stock_score(normalized_status, is_held, overlap_level),
                "risk_level": _stock_risk_level(is_held, overlap_level, normalized_status),
                "recent_status_change": f"{normalized_status} 유지",
                "priority": "high" if normalized_status == "후보" else "medium" if normalized_status == "관찰" else "low",
                "priority_reason": priority_reason,
                "next_action": f"{symbol} 후속 리서치 업데이트".strip(),
                "generated_at": generated_at,
            }
        )

    items.sort(key=lambda item: (_stock_priority_rank(str(item["status"]), bool(item["is_held"])), str(item["symbol"])))

    status_counts = {"전체": len(items), "탐색": 0, "관찰": 0, "후보": 0, "보류": 0, "제외": 0}
    held_count = 0
    for item in items:
        status_counts[str(item["status"])] = status_counts.get(str(item["status"]), 0) + 1
        if item["is_held"]:
            held_count += 1

    queue = [
        {
            "id": f"stock-queue-{item['idea_id']}",
            "symbol": item["symbol"],
            "title": f"{item['symbol']} 리서치 우선순위 점검",
            "reason": item["priority_reason"],
            "severity": item["priority"],
            "status": item["status"],
            "is_held": item["is_held"],
            "score": item["score"],
            "age_label": "방금 전",
            "next_action": item["next_action"],
        }
        for item in items[:5]
    ]

    compare_candidates = [item["symbol"] for item in items[1:4]]
    lead_symbol = items[0]["symbol"] if items else ""
    lead_item = items[0] if items else {}
    return {
        "generated_at": generated_at,
        "filters": {
            "total_count": len(items),
            "held_count": held_count,
            "candidate_count": status_counts["후보"],
            "observe_count": status_counts["관찰"],
            "status_counts": status_counts,
        },
        "queue": queue,
        "items": items,
        "flow": {
            "pipeline": ["탐색", "관찰", "후보", "보류", "제외"],
            "active_stage": str(lead_item.get("status") or "탐색"),
            "stage_counts": status_counts,
        },
        "evidence": {
            "chart": {
                "symbol": lead_symbol,
                "timeframe": "1M",
                "signal": "관찰 유지" if str(lead_item.get("status") or "") == "관찰" else "후보 점검",
            },
            "news": [
                {
                    "id": f"news-{lead_symbol.lower() or 'stock'}-1",
                    "symbol": lead_symbol,
                    "title": f"{lead_symbol} 최근 핵심 이벤트 점검" if lead_symbol else "최근 핵심 이벤트 점검",
                    "summary": str(lead_item.get("priority_reason") or "후속 리서치 이유를 점검합니다."),
                    "category": "research",
                    "published_at": generated_at,
                }
            ] if lead_symbol else [],
            "institutional_flow": {
                "symbol": lead_symbol,
                "stance": "positive" if str(lead_item.get("priority") or "") == "high" else "neutral",
                "confidence": "high" if str(lead_item.get("priority") or "") == "high" else "medium",
                "summary": "기관/수급 브리프는 후속 실데이터 연동 전까지 seed 기반 요약을 사용합니다.",
            },
        },
        "compare_seed": {
            "primary_symbol": lead_symbol,
            "candidate_symbols": compare_candidates,
            "default_mode": "fit",
        },
    }


def _build_orchestrator_prompt_starters(policy: dict[str, Any]) -> list[dict[str, Any]]:
    starters: list[dict[str, Any]] = []
    for index, prompt in enumerate(list(policy.get("quick_prompts") or []), start=1):
        normalized = str(prompt)
        intent = "default_priority"
        source_manager_ids = ["core_strategy"]
        if "현금" in normalized or "유동성" in normalized:
            intent = "cash"
            source_manager_ids = ["cash_debt"]
        elif "리스크" in normalized:
            intent = "risk"
        starters.append(
            {
                "id": f"prompt-{index}",
                "label": normalized.replace("?", ""),
                "prompt": normalized,
                "source_manager_ids": source_manager_ids,
                "intent": intent,
            }
        )
    return starters


def _build_report_highlights(
    action_hero: dict[str, Any],
    manager_cards: list[dict[str, Any]],
    cross_manager_alerts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    highlights: list[dict[str, Any]] = [
        {
            "id": "report-action-hero",
            "title": f"오늘 전략 액션: {action_hero.get('action', '유지')}",
            "summary": str(action_hero.get("reason_summary") or ""),
            "severity": "high" if str(action_hero.get("action")) in {"매수", "매도"} else "medium",
            "manager_ids": ["core_strategy"],
            "updated_at": str(action_hero.get("updated_at") or ""),
        }
    ]
    for card in manager_cards:
        if not card.get("warning_count"):
            continue
        highlights.append(
            {
                "id": f"report-{card['manager_id']}",
                "title": str(card.get("headline") or card.get("title") or card["manager_id"]),
                "summary": str(card.get("summary") or ""),
                "severity": "medium",
                "manager_ids": [str(card["manager_id"])],
                "updated_at": str(card.get("generated_at") or action_hero.get("updated_at") or ""),
            }
        )
    for alert in cross_manager_alerts[:2]:
        highlights.append(
            {
                "id": f"report-{alert['id']}",
                "title": str(alert["title"]),
                "summary": str(alert["detail"]),
                "severity": str(alert["severity"]),
                "manager_ids": list(alert["manager_ids"]),
                "updated_at": str(action_hero.get("updated_at") or ""),
            }
        )
    return highlights[:6]


def _build_manager_events(
    event_timeline: list[dict[str, Any]],
    manager_summaries: dict[str, dict[str, Any]],
    updated_at: str,
    manual_inputs: dict[str, list[dict[str, Any]]],
    liquidity_summary: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    manager_events: dict[str, list[dict[str, Any]]] = {manager_id: [] for manager_id in manager_summaries}
    for event in event_timeline:
        manager_id = str(event.get("source_manager_id") or "core_strategy")
        manager_events.setdefault(manager_id, []).append(dict(event))
    for manager_id, summary in manager_summaries.items():
        warnings = [str(item) for item in summary.get("warnings", [])]
        if warnings:
            manager_events.setdefault(manager_id, []).append(
                {
                    "id": f"summary-warning-{manager_id}",
                    "date": updated_at[:10],
                    "type": "summary_warning",
                    "title": f"{manager_id} 경고",
                    "detail": warnings[0],
                    "category": "warning",
                    "severity": "medium",
                    "source_manager_id": manager_id,
                    "entity_type": "manager",
                    "entity_id": manager_id,
                }
            )

    stock_watchlist = list(manual_inputs.get("stock_watchlist", []))
    if stock_watchlist:
        top_stock = stock_watchlist[0]
        manager_events.setdefault("stock_research", []).append(
            {
                "id": f"stock-research-watch-{top_stock.get('idea_id') or top_stock.get('symbol')}",
                "date": updated_at[:10],
                "type": "candidate_update",
                "title": f"{top_stock.get('symbol', '후보')} 리서치 추적",
                "detail": str(top_stock.get("memo") or f"상태 {top_stock.get('status') or '미분류'}"),
                "category": "research",
                "severity": "medium" if str(top_stock.get("status") or "") in {"관찰", "후보", "매수후보"} else "low",
                "source_manager_id": "stock_research",
                "entity_type": "stock",
                "entity_id": str(top_stock.get("symbol") or top_stock.get("idea_id") or ""),
            }
        )

    property_watchlist = list(manual_inputs.get("property_watchlist", []))
    if property_watchlist:
        top_property = property_watchlist[0]
        manager_events.setdefault("real_estate", []).append(
            {
                "id": f"real-estate-watch-{top_property.get('property_id') or top_property.get('name')}",
                "date": updated_at[:10],
                "type": "property_review",
                "title": f"{top_property.get('name', '관심 단지')} 검토 상태",
                "detail": f"현재 상태 {top_property.get('status') or '미분류'} / 지역 {top_property.get('region') or 'N/A'}",
                "category": "property",
                "severity": "medium" if str(top_property.get("status") or "") in {"검토", "우선검토"} else "low",
                "source_manager_id": "real_estate",
                "entity_type": "property",
                "entity_id": str(top_property.get("property_id") or ""),
            }
        )

    manager_events.setdefault("cash_debt", []).append(
        {
            "id": "cash-debt-liquidity",
            "date": updated_at[:10],
            "type": "liquidity_status",
            "title": "현금/부채 점검",
            "detail": f"순유동성 {int(liquidity_summary.get('net_liquidity_krw') or 0):,}원 / 유동성 비중 {float(liquidity_summary.get('liquidity_ratio_pct') or 0):.2f}%",
            "category": "liquidity",
            "severity": "high" if int(liquidity_summary.get("net_liquidity_krw") or 0) < 0 else "medium",
            "source_manager_id": "cash_debt",
            "entity_type": "cash",
            "entity_id": "net-liquidity",
        }
    )

    for events in manager_events.values():
        events.sort(key=lambda item: (str(item.get("date") or ""), str(item.get("id") or "")), reverse=True)
    return manager_events


def _build_compare_data(
    manager_cards: list[dict[str, Any]],
    manual_inputs: dict[str, list[dict[str, Any]]],
    manager_summaries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    pair_ids = [
        ("core_strategy", "cash_debt"),
        ("core_strategy", "stock_research"),
        ("stock_research", "real_estate"),
    ]
    manager_pairs = [
        {
            "pair_id": f"{left}-vs-{right}",
            "manager_ids": [left, right],
            "headlines": {
                left: next((str(card.get("headline") or "") for card in manager_cards if card["manager_id"] == left), ""),
                right: next((str(card.get("headline") or "") for card in manager_cards if card["manager_id"] == right), ""),
            },
        }
        for left, right in pair_ids
    ]
    watchlist_symbols = [str(row.get("symbol") or "") for row in manual_inputs.get("stock_watchlist", []) if str(row.get("symbol") or "")]
    holding_overlap = [
        {
            "overlap_id": "core-vs-research-watchlist",
            "left_manager_id": "core_strategy",
            "right_manager_id": "stock_research",
            "shared_symbols": watchlist_symbols[:3],
        }
    ]
    conflicting_recommendations = []
    if manager_summaries.get("core_strategy", {}).get("warnings") and manager_summaries.get("cash_debt", {}).get("warnings"):
        conflicting_recommendations.append(
            {
                "conflict_id": "core-vs-cash",
                "manager_ids": ["core_strategy", "cash_debt"],
                "detail": "전략 액션과 현금/부채 방어 여력을 함께 확인해야 합니다.",
            }
        )
    if manager_summaries.get("stock_research", {}).get("recommended_actions") and manager_summaries.get("real_estate", {}).get("recommended_actions"):
        conflicting_recommendations.append(
            {
                "conflict_id": "research-vs-real-estate-focus",
                "manager_ids": ["stock_research", "real_estate"],
                "detail": "개별주 후보 리서치와 부동산 검토 큐가 동시에 열려 있어 우선순위 정리가 필요합니다.",
            }
        )
    return {
        "manager_pairs": manager_pairs,
        "holding_overlap": holding_overlap,
        "conflicting_recommendations": conflicting_recommendations,
    }


def _build_home_discovery(
    priority_actions: list[dict[str, Any]],
    cross_manager_alerts: list[dict[str, Any]],
    prompt_starters: list[dict[str, Any]],
    report_highlights: list[dict[str, Any]],
) -> dict[str, Any]:
    headline = priority_actions[0]["title"] if priority_actions else "오늘 우선순위를 확인하세요."
    return {
        "headline": headline,
        "priority_action_ids": [str(item["id"]) for item in priority_actions[:3]],
        "cross_manager_alert_ids": [str(item["id"]) for item in cross_manager_alerts[:3]],
        "prompt_ids": [str(item["id"]) for item in prompt_starters[:4]],
        "report_highlight_ids": [str(item["id"]) for item in report_highlights[:3]],
    }


def generate_dashboard_snapshot(
    signal_csv_path: Path | str = Path("reports/signals_s1_s2_s3_user_original.csv"),
    data_csv_path: Path | str = Path("data/user_input.csv"),
    metrics_csv_path: Path | str = Path("reports/backtest_metrics_primary.csv"),
    state_path: Path | str = Path("reports/daily_telegram_alert_state.json"),
    equity_csv_path: Path | str = Path("reports/backtest_equity_primary.csv"),
    manual_inputs_path: Path | str | None = None,
    manual_truth_path: Path | str | None = None,
    summary_store_path: Path | str = DEFAULT_SUMMARY_STORE_PATH,
    audit_path: Path | str = DEFAULT_ORCHESTRATOR_AUDIT_PATH,
) -> dict[str, Any]:
    signal_csv = Path(signal_csv_path)
    data_csv = Path(data_csv_path)
    metrics_csv = Path(metrics_csv_path)
    state_file = Path(state_path)
    equity_csv = Path(equity_csv_path)
    summary_store = Path(summary_store_path)
    audit_file = Path(audit_path)

    signals = pd.read_csv(signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    market = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    metrics = pd.read_csv(metrics_csv)
    equity = pd.read_csv(equity_csv, parse_dates=["date"]).sort_values("date").reset_index(drop=True) if equity_csv.exists() else pd.DataFrame()
    state = _read_optional_json(state_file)
    resolved_manual_path = Path(manual_truth_path or manual_inputs_path or DEFAULT_MANUAL_INPUTS_PATH)
    manual_inputs = load_manual_inputs(resolved_manual_path)

    latest_signal = signals.iloc[-1]
    prev_signal = signals.iloc[-2] if len(signals) >= 2 else latest_signal
    latest_date = latest_signal["time"]
    market_row = market.loc[market["time"] == latest_date]
    market_latest = market_row.iloc[-1] if not market_row.empty else market.iloc[-1]

    target_weight = float(latest_signal["S2_weight"])
    prev_weight = float(prev_signal["S2_weight"])
    action = "유지"
    if target_weight > prev_weight + 1e-9:
        action = "매수"
    elif target_weight < prev_weight - 1e-9:
        action = "매도"

    tqqq_close = float(market_latest["TQQQ종가"])
    spy_close = float(market_latest["SPY종가"])
    spy_ma200 = float(market_latest["SPY200일선"])
    tqqq_ma200 = float(market_latest["TQQQ200일선"])
    vol20_series = market["TQQQ종가"].pct_change().rolling(20, min_periods=20).std(ddof=1) * 100.0
    vol20 = float(vol20_series.iloc[int(market_latest.name)]) if pd.notna(vol20_series.iloc[int(market_latest.name)]) else float("nan")
    spy200_dist = (spy_close / spy_ma200) * 100.0 if spy_ma200 else float("nan")
    tqqq_dist200 = (tqqq_close / tqqq_ma200) * 100.0 if tqqq_ma200 else float("nan")

    month_1_return_pct = float("nan")
    if not equity.empty and "taxed_equity" in equity.columns and len(equity) >= 22:
        month_1_return_pct = (float(equity["taxed_equity"].iloc[-1]) / float(equity["taxed_equity"].iloc[-22]) - 1.0) * 100.0

    metrics_row = metrics.iloc[0] if not metrics.empty else pd.Series(dtype=float)
    condition_pass_rate = _build_condition_pass_rate(market_latest, vol20, tqqq_dist200, spy200_dist)
    default_next_run = _default_next_run_at(latest_date)

    wealth_overview = build_wealth_overview(manual_inputs)
    liquidity_summary = build_liquidity_summary(manual_inputs)
    summary_source_version = build_summary_source_version(
        manual_inputs,
        latest_date.isoformat(),
        source_label=resolved_manual_path.name,
    )
    manager_summaries = load_summary_store(summary_store, expected_source_version=summary_source_version)

    home_overview = {
        "invested_krw": wealth_overview["invested_krw"],
        "investable_assets_krw": wealth_overview["investable_assets_krw"],
        "cash_krw": wealth_overview["cash_krw"],
        "debt_krw": wealth_overview["debt_krw"],
        "net_worth_krw": wealth_overview["net_worth_krw"],
    }
    core_strategy_position = build_core_strategy_position(manual_inputs, target_weight_pct=round(target_weight * 100.0, 2))
    manager_cards = build_manager_cards(
        manual_inputs,
        target_weight_pct=round(target_weight * 100.0, 2),
        summary_by_manager=manager_summaries,
    )

    snapshot = {
        "action_hero": {
            "action": action,
            "target_weight_pct": round(target_weight * 100.0, 2),
            "reason_summary": _build_reason_summary(action, target_weight * 100.0, tqqq_dist200, vol20, spy200_dist),
            "updated_at": latest_date.isoformat(),
        },
        "kpi_cards": {
            "cagr_pct": round(float(metrics_row.get("AfterTaxCAGR", float("nan"))) * 100.0, 2),
            "mdd_pct": round(float(metrics_row.get("MDD", float("nan"))) * 100.0, 2),
            "month_1_return_pct": round(month_1_return_pct, 2) if pd.notna(month_1_return_pct) else float("nan"),
            "condition_pass_rate": condition_pass_rate,
        },
        "risk_gauges": {
            "vol20": {"value": round(vol20, 2), "threshold": 5.9, "status": _status_lower_better(vol20, 5.9)},
            "spy200_dist": {"value": round(spy200_dist, 2), "threshold": 97.75, "status": _status_higher_better(spy200_dist, 97.75)},
            "tqqq_dist200": {"value": round(tqqq_dist200, 2), "threshold": 101.0, "status": _status_higher_better(tqqq_dist200, 101.0)},
        },
        "event_timeline": _build_event_timeline(signals),
        "ops_log": {
            "run_id": f"daily-{latest_date.strftime('%Y-%m-%d')}",
            "alert_key": str(state.get("last_alert_key") or f"{latest_date.strftime('%Y-%m-%d')}:{prev_weight}->{target_weight}"),
            "last_success_at": str(state.get("last_sent_at") or latest_date.isoformat()),
            "next_run_at": str(state.get("next_run_at") or default_next_run),
        },
        "wealth_home": {
            "overview": home_overview,
            "manager_cards": manager_cards,
            "updated_at": latest_date.isoformat(),
        },
        "wealth_overview": wealth_overview,
        "liquidity_summary": liquidity_summary,
        "manager_cards": manager_cards,
        "manager_summaries": manager_summaries,
        "core_strategy_position": core_strategy_position,
        "core_strategy_actuals": core_strategy_position,
        "meta": {
            "manual_source_version": resolved_manual_path.name,
            "summary_source_version": summary_source_version,
            "summary_store_path": str(summary_store),
            "signal_updated_at": latest_date.isoformat(),
            "market_updated_at": pd.Timestamp(market_latest["time"]).isoformat(),
            "audit_available": audit_file.exists(),
        },
    }

    home_inbox = build_home_inbox(
        snapshot=snapshot,
        manual_inputs=manual_inputs,
        manager_summaries=manager_summaries,
    )
    snapshot["home_inbox"] = home_inbox
    snapshot["wealth_home"]["inbox_preview"] = home_inbox[:3]
    snapshot["orchestrator_briefs"] = build_orchestrator_briefs(build_orchestrator_context(snapshot))
    snapshot["orchestrator_policy"] = export_orchestrator_policy()
    snapshot["orchestrator_insights"] = build_orchestrator_insights(audit_file)
    snapshot["priority_actions"] = _build_priority_actions(home_inbox, manager_cards)
    snapshot["cross_manager_alerts"] = _build_cross_manager_alerts(manager_summaries, liquidity_summary, snapshot["risk_gauges"])
    snapshot["research_candidates"] = _build_research_candidates(manual_inputs)
    snapshot["stock_research_workspace"] = _build_stock_research_workspace(
        manual_inputs,
        str(latest_date.isoformat()),
    )
    snapshot["orchestrator_prompt_starters"] = _build_orchestrator_prompt_starters(snapshot["orchestrator_policy"])
    snapshot["report_highlights"] = _build_report_highlights(
        snapshot["action_hero"],
        manager_cards,
        snapshot["cross_manager_alerts"],
    )
    snapshot["manager_events"] = _build_manager_events(
        snapshot["event_timeline"],
        manager_summaries,
        str(latest_date.isoformat()),
        manual_inputs,
        liquidity_summary,
    )
    snapshot["compare_data"] = _build_compare_data(manager_cards, manual_inputs, manager_summaries)
    snapshot["home_discovery"] = _build_home_discovery(
        snapshot["priority_actions"],
        snapshot["cross_manager_alerts"],
        snapshot["orchestrator_prompt_starters"],
        snapshot["report_highlights"],
    )
    return snapshot
