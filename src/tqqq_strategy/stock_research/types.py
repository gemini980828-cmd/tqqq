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
