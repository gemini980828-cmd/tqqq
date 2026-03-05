from typing import Any


REQUIRED_BLOCK_KEYS = (
    "header",
    "position_change",
    "reason",
    "market_summary",
    "ops_log",
)


def build_dashboard_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key, {}) for key in REQUIRED_BLOCK_KEYS}
