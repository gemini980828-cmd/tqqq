from __future__ import annotations

NORMALIZED_CANDIDATE_STATUSES = {"후보"}
LEGACY_STATUS_MAP = {
    "매수후보": "후보",
    "검토": "후보",
    "관찰": "관찰",
    "후보": "후보",
    "보류": "보류",
    "제외": "제외",
}


def normalize_stock_status(raw: str | None) -> str:
    key = str(raw or "").strip()
    return LEGACY_STATUS_MAP.get(key, "탐색")


def is_candidate_status(raw: str | None) -> bool:
    return normalize_stock_status(raw) in NORMALIZED_CANDIDATE_STATUSES
