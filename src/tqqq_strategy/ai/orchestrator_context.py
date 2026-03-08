from __future__ import annotations

from typing import Any, Mapping

SAFE_SUMMARY_FIELDS = (
    "manager_id",
    "summary_text",
    "key_points",
    "warnings",
    "recommended_actions",
    "generated_at",
    "stale",
)


def _safe_summary(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "manager_id": str(summary.get("manager_id", "")),
        "summary_text": str(summary.get("summary_text", "")),
        "key_points": [str(item) for item in summary.get("key_points", [])],
        "warnings": [str(item) for item in summary.get("warnings", [])],
        "recommended_actions": [str(item) for item in summary.get("recommended_actions", [])],
        "generated_at": str(summary.get("generated_at", "")),
        "stale": bool(summary.get("stale", False)),
    }


def build_orchestrator_context(snapshot: Mapping[str, Any], question: str | None = None) -> dict[str, Any]:
    manager_summaries = {
        str(manager_id): _safe_summary(summary)
        for manager_id, summary in dict(snapshot.get("manager_summaries") or {}).items()
        if isinstance(summary, Mapping)
    }

    return {
        "question": str(question or ""),
        "action_hero": dict(snapshot.get("action_hero") or {}),
        "wealth_overview": dict(
            snapshot.get("wealth_overview")
            or dict(snapshot.get("wealth_home") or {}).get("overview")
            or {}
        ),
        "liquidity_summary": dict(snapshot.get("liquidity_summary") or {}),
        "risk_gauges": dict(snapshot.get("risk_gauges") or {}),
        "home_inbox": [dict(item) for item in list(snapshot.get("home_inbox") or [])[:5]],
        "manager_summaries": manager_summaries,
        "event_timeline": [dict(item) for item in list(snapshot.get("event_timeline") or [])[:5]],
        "ops_log": dict(snapshot.get("ops_log") or {}),
        "meta": {
            "manual_source_version": str(dict(snapshot.get("meta") or {}).get("manual_source_version", "")),
            "summary_source_version": str(dict(snapshot.get("meta") or {}).get("summary_source_version", "")),
        },
    }
