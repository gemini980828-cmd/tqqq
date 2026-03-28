from __future__ import annotations

from tqqq_strategy.ai.stock_research_status import normalize_stock_status
from tqqq_strategy.stock_research.types import ResearchFeatureSnapshot, ResearchUniverseEntry



def build_feature_snapshot(entry: ResearchUniverseEntry) -> ResearchFeatureSnapshot:
    normalized_status = normalize_stock_status(entry.raw_status)
    overlap_level = "high" if entry.is_held else "low"
    priority = "high" if normalized_status == "후보" else "medium" if normalized_status == "관찰" else "low"
    has_memo = bool(entry.memo.strip())
    return ResearchFeatureSnapshot(
        symbol=entry.symbol,
        normalized_status=normalized_status,
        overlap_level=overlap_level,
        has_memo=has_memo,
        priority=priority,
        recency_label="manual",
        has_catalyst=False,
        as_of=entry.as_of,
    )
