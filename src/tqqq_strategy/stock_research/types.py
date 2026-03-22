from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchDecisionRecord:
    symbol: str
    as_of: str
    engine_version: str
    feature_snapshot_id: str
    final_score: float
    status: str


@dataclass(frozen=True)
class ResearchUniverseEntry:
    idea_id: str
    symbol: str
    raw_status: str
    memo: str
    is_held: bool
    as_of: str


@dataclass(frozen=True)
class ResearchFeatureSnapshot:
    symbol: str
    normalized_status: str
    overlap_level: str
    has_memo: bool
    priority: str
    recency_label: str
    has_catalyst: bool
    as_of: str
