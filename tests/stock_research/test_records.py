from tqqq_strategy.stock_research.types import ResearchDecisionRecord


def test_research_decision_record_carries_required_replay_fields() -> None:
    record = ResearchDecisionRecord(
        symbol="NVDA",
        as_of="2026-01-30T00:00:00",
        engine_version="stock-research/v1",
        feature_snapshot_id="snap-1",
        final_score=68,
        status="관찰",
    )

    assert record.symbol == "NVDA"
    assert record.engine_version == "stock-research/v1"
