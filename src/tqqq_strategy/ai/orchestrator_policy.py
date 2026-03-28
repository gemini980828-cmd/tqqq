from __future__ import annotations

from typing import Any, Mapping


INTENT_RULES: tuple[dict[str, Any], ...] = (
    {
        "key": "default_priority",
        "label": "portfolio_priority",
        "source_manager_id": "core_strategy",
        "priority": 0,
        "tokens": ("전체", "요약", "정리", "포트폴리오", "자산", "우선순위"),
        "support_keys": ("action",),
    },
    {
        "key": "action",
        "label": "action",
        "source_manager_id": "core_strategy",
        "priority": 10,
        "tokens": ("액션", "해야", "매수", "매도", "체결", "비중", "리밸런싱"),
        "support_keys": (),
    },
    {
        "key": "risk",
        "label": "risk",
        "source_manager_id": "core_strategy",
        "priority": 20,
        "tokens": ("리스크", "위험", "안전", "손절", "변동성"),
        "support_keys": (),
    },
    {
        "key": "cash",
        "label": "cash",
        "source_manager_id": "cash_debt",
        "priority": 30,
        "tokens": ("현금", "유동성", "여력", "가용", "예수금", "부채"),
        "support_keys": (),
    },
    {
        "key": "stock_research",
        "label": "stock_research",
        "source_manager_id": "stock_research",
        "priority": 40,
        "tokens": ("개별주", "주식", "종목", "워치리스트", "watchlist"),
        "support_keys": (),
    },
    {
        "key": "recent_changes",
        "label": "recent_changes",
        "source_manager_id": "core_strategy",
        "priority": 45,
        "tokens": ("최근", "변화", "바뀌", "이벤트", "변경"),
        "support_keys": (),
    },
    {
        "key": "comparison",
        "label": "comparison",
        "source_manager_id": "core_strategy",
        "priority": 15,
        "tokens": ("비교", "대비", "관계", "충돌"),
        "support_keys": ("action", "cash"),
    },
    {
        "key": "real_estate",
        "label": "real_estate",
        "source_manager_id": "real_estate",
        "priority": 50,
        "tokens": ("부동산", "단지", "아파트", "매물", "전세", "실거주"),
        "support_keys": (),
    },
)


QUICK_PROMPTS: tuple[str, ...] = (
    "오늘 가장 중요한 액션은?",
    "지금 우선순위를 요약해줘",
    "현금 여력이 충분한가?",
    "지금 리스크 상태는 어때?",
)


def export_orchestrator_policy() -> dict[str, Any]:
    return {
        "quick_prompts": list(QUICK_PROMPTS),
        "intent_rules": [
            {
                "key": str(rule["key"]),
                "label": str(rule["label"]),
                "source_manager_id": str(rule["source_manager_id"]),
                "priority": int(rule["priority"]),
                "tokens": list(rule["tokens"]),
                "support_keys": list(rule["support_keys"]),
            }
            for rule in INTENT_RULES
        ],
    }


def _normalize_policy(policy: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    raw_rules = list((policy or {}).get("intent_rules") or [])
    if not raw_rules:
        return [dict(rule) for rule in INTENT_RULES]
    normalized: list[dict[str, Any]] = []
    for rule in raw_rules:
        normalized.append(
            {
                "key": str(rule.get("key") or ""),
                "label": str(rule.get("label") or rule.get("key") or ""),
                "source_manager_id": str(rule.get("source_manager_id") or "core_strategy"),
                "priority": int(999 if rule.get("priority") is None else rule.get("priority")),
                "tokens": tuple(str(token) for token in (rule.get("tokens") or [])),
                "support_keys": tuple(str(token) for token in (rule.get("support_keys") or [])),
            }
        )
    return normalized


def classify_question(question: str, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    prompt = str(question or "").strip()
    rules = _normalize_policy(policy)
    matches: list[dict[str, Any]] = []

    for rule in sorted(rules, key=lambda item: int(item["priority"])):
        if any(token and token in prompt for token in rule["tokens"]):
            matches.append(rule)

    if not matches:
        matches = [next(rule for rule in rules if rule["key"] == "default_priority")]

    brief_keys: list[str] = []
    source_manager_ids: list[str] = []
    for rule in matches:
        key = str(rule["key"])
        if key not in brief_keys:
            brief_keys.append(key)
        source_manager_id = str(rule["source_manager_id"])
        if source_manager_id not in source_manager_ids:
            source_manager_ids.append(source_manager_id)
        for support_key in rule["support_keys"]:
            if support_key not in brief_keys:
                brief_keys.append(support_key)

    primary_intent = brief_keys[0] if brief_keys else "default_priority"
    return {
        "question": prompt,
        "brief_keys": brief_keys or ["default_priority"],
        "primary_intent": primary_intent,
        "source_manager_ids": source_manager_ids or ["core_strategy"],
    }
