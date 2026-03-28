from tqqq_strategy.stock_research.universe import build_research_universe


def test_build_research_universe_marks_held_symbols_and_preserves_watchlist_order() -> None:
    universe = build_research_universe(
        manual_inputs={
            "stock_watchlist": [
                {"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI 수혜 지속 모니터링"},
                {"idea_id": "stock-2", "symbol": "AAPL", "status": "후보", "memo": "대형 기술주 비교"},
            ],
            "positions": [
                {"symbol": "AAPL", "manager_id": "core_strategy"},
            ],
        },
        as_of="2026-01-30T00:00:00",
    )

    assert [item.symbol for item in universe] == ["NVDA", "AAPL"]
    assert universe[0].is_held is False
    assert universe[1].is_held is True
