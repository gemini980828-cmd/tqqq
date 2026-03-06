from __future__ import annotations

from typing import Any

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


def build_dashboard_snapshot(payload: dict[str, Any] | None = None, **snapshot_kwargs: Any) -> dict[str, Any]:
    base_payload = dict(payload or {})
    if not payload:
        base_payload.update(generate_dashboard_snapshot(**snapshot_kwargs))
    return {
        key: base_payload.get(key, {}) if key != "event_timeline" else base_payload.get(key, [])
        for key in REQUIRED_BLOCK_KEYS
    }
