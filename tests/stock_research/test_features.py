from tqqq_strategy.stock_research.features import build_feature_snapshot
from tqqq_strategy.stock_research.types import ResearchUniverseEntry


def test_build_feature_snapshot_derives_overlap_priority_inputs() -> None:
    entry = ResearchUniverseEntry(
        idea_id="stock-1",
        symbol="NVDA",
        raw_status="관찰",
        memo="AI 수혜 지속 모니터링",
        is_held=False,
        as_of="2026-01-30T00:00:00",
    )

    snapshot = build_feature_snapshot(entry)

    assert snapshot.symbol == "NVDA"
    assert snapshot.overlap_level == "low"
    assert snapshot.has_memo is True
