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

SAFE_EVENT_FIELDS = (
    "id",
    "date",
    "type",
    "title",
    "detail",
    "category",
    "severity",
    "source_manager_id",
    "entity_type",
    "entity_id",
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


def _safe_event(event: Mapping[str, Any]) -> dict[str, Any]:
    return {field: event.get(field, "" if field != "severity" else "info") for field in SAFE_EVENT_FIELDS}


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
        "priority_actions": [dict(item) for item in list(snapshot.get("priority_actions") or [])[:5]],
        "cross_manager_alerts": [dict(item) for item in list(snapshot.get("cross_manager_alerts") or [])[:5]],
        "manager_summaries": manager_summaries,
        "event_timeline": [_safe_event(dict(item)) for item in list(snapshot.get("event_timeline") or [])[:5]],
        "orchestrator_prompt_starters": [
            dict(item) for item in list(snapshot.get("orchestrator_prompt_starters") or [])[:4]
        ],
        "report_highlights": [dict(item) for item in list(snapshot.get("report_highlights") or [])[:4]],
        "compare_data": {
            "manager_pairs": [dict(item) for item in list(dict(snapshot.get("compare_data") or {}).get("manager_pairs") or [])[:4]],
            "holding_overlap": [
                dict(item) for item in list(dict(snapshot.get("compare_data") or {}).get("holding_overlap") or [])[:4]
            ],
            "conflicting_recommendations": [
                dict(item)
                for item in list(dict(snapshot.get("compare_data") or {}).get("conflicting_recommendations") or [])[:4]
            ],
        },
        "orchestrator_policy": dict(snapshot.get("orchestrator_policy") or {}),
        "ops_log": dict(snapshot.get("ops_log") or {}),
        "meta": {
            "manual_source_version": str(dict(snapshot.get("meta") or {}).get("manual_source_version", "")),
            "summary_source_version": str(dict(snapshot.get("meta") or {}).get("summary_source_version", "")),
        },
    }
