from __future__ import annotations

from typing import Any

from tqqq_strategy.ai.orchestrator_context import build_orchestrator_context
from tqqq_strategy.ai.orchestrator_service import run_orchestrator
from tqqq_strategy.ops.dashboard_snapshot import generate_dashboard_snapshot


REQUIRED_BLOCK_KEYS = (
    "header",
    "position_change",
    "reason",
    "market_summary",
    "ops_log",
    "action_hero",
    "kpi_cards",
    "risk_gauges",
    "event_timeline",
)

OPTIONAL_BLOCK_DEFAULTS: dict[str, Any] = {
    "wealth_home": {},
    "wealth_overview": {},
    "liquidity_summary": {},
    "manager_cards": [],
    "manager_summaries": {},
    "home_inbox": [],
    "core_strategy_position": {},
    "core_strategy_actuals": {},
    "meta": {},
}


def build_dashboard_snapshot(payload: dict[str, Any] | None = None, **snapshot_kwargs: Any) -> dict[str, Any]:
    base_payload = dict(payload or {})
    if not payload:
        base_payload.update(generate_dashboard_snapshot(**snapshot_kwargs))

    normalized = {
        key: base_payload.get(key, {}) if key != "event_timeline" else base_payload.get(key, [])
        for key in REQUIRED_BLOCK_KEYS
    }
    for key, default in OPTIONAL_BLOCK_DEFAULTS.items():
        normalized[key] = base_payload.get(key, default)
    return normalized


def build_orchestrator_reply(
    question: str,
    *,
    payload: dict[str, Any] | None = None,
    trigger: str = "user_submit",
    **snapshot_kwargs: Any,
) -> dict[str, Any]:
    snapshot = build_dashboard_snapshot(payload, **snapshot_kwargs)
    context = build_orchestrator_context(snapshot, question=question)
    reply = run_orchestrator(question=question, context=context, trigger=trigger)
    return {
        **reply,
        "context_meta": dict(context.get("meta") or {}),
    }
