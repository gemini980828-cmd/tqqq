from tqqq_strategy.wealth.derived import build_manager_cards, build_wealth_overview, summarize_core_strategy_position


MANUAL_PAYLOAD = {
    "positions": [
        {
            "account_id": "samsung-core",
            "asset_id": "tqqq-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "name": "ProShares UltraPro QQQ",
            "quantity": 120.0,
            "avg_cost_krw": 76000,
            "market_price_krw": 81000,
            "market_value_krw": 9720000,
        },
        {
            "account_id": "samsung-growth",
            "asset_id": "nvda-growth",
            "manager_id": "stock_research",
            "symbol": "NVDA",
            "name": "NVIDIA",
            "quantity": 5.0,
            "avg_cost_krw": 1180000,
            "market_price_krw": 1210000,
            "market_value_krw": 6050000,
        },
    ],
    "cash_debt": [
        {"entry_id": "cash-main", "kind": "cash", "label": "투자대기현금", "balance_krw": 15000000},
        {"entry_id": "loan-margin", "kind": "debt", "label": "마이너스통장", "balance_krw": 2000000},
    ],
    "stock_watchlist": [{"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI 인프라 핵심 수혜"}],
    "property_watchlist": [{"property_id": "apt-1", "name": "마포래미안푸르지오", "region": "서울 마포구", "status": "관심"}],
}


def test_build_wealth_overview_aggregates_net_worth() -> None:
    overview = build_wealth_overview(MANUAL_PAYLOAD)

    assert overview["invested_krw"] == 15770000
    assert overview["investable_assets_krw"] == 15770000
    assert overview["cash_krw"] == 15000000
    assert overview["debt_krw"] == 2000000
    assert overview["net_worth_krw"] == 28770000


def test_summarize_core_strategy_position_compares_actual_vs_target() -> None:
    summary = summarize_core_strategy_position(MANUAL_PAYLOAD, target_weight_pct=95.0)

    assert summary["symbol"] == "TQQQ"
    assert round(summary["actual_weight_pct"], 2) == 31.59
    assert round(summary["gap_pct"], 2) == -63.41
    assert summary["quantity"] == 120.0
    assert summary["target_value_krw"] == 29231500
    assert summary["rebalance_gap_krw"] == 19511500
    assert summary["rebalance_action"] == "buy"


def test_build_manager_cards_counts_watch_items() -> None:
    cards = build_manager_cards(MANUAL_PAYLOAD, target_weight_pct=95.0)

    assert [card["manager_id"] for card in cards] == [
        "core_strategy",
        "stock_research",
        "real_estate",
        "cash_debt",
    ]
    assert cards[1]["headline"] == "관심종목 1개"
    assert cards[2]["headline"] == "관심 단지 1개"
    assert cards[3]["summary"] == "현금 15,000,000원"
