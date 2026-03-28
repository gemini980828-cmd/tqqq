"""Stock research engine package."""

from tqqq_strategy.stock_research.features import build_feature_snapshot
from tqqq_strategy.stock_research.types import ResearchDecisionRecord, ResearchFeatureSnapshot, ResearchUniverseEntry
from tqqq_strategy.stock_research.universe import build_research_universe

__all__ = [
    "ResearchDecisionRecord",
    "ResearchFeatureSnapshot",
    "ResearchUniverseEntry",
    "build_feature_snapshot",
    "build_research_universe",
]
