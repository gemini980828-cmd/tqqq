from tqqq_strategy.wealth.derived import build_core_strategy_position, build_liquidity_summary, build_manager_cards


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
    "transactions": [
        {
            "transaction_id": "tx-1",
            "account_id": "samsung-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "side": "buy",
            "quantity": 3.0,
            "price_krw": 80000,
            "total_value_krw": 240000,
            "traded_at": "2026-03-05T09:00:00+00:00",
        },
        {
            "transaction_id": "tx-2",
            "account_id": "samsung-growth",
            "manager_id": "stock_research",
            "symbol": "NVDA",
            "side": "buy",
            "quantity": 1.0,
            "price_krw": 1200000,
            "total_value_krw": 1200000,
            "traded_at": "2026-03-04T09:00:00+00:00",
        },
    ],
}

SUMMARY_CACHE = {
    "core_strategy": {
        "manager_id": "core_strategy",
        "summary_text": "목표 비중 대비 실보유가 부족하여 증액이 필요합니다.",
        "key_points": ["실보유 31.59%", "목표 95.00%"],
        "warnings": ["리밸런싱 gap이 큽니다."],
        "recommended_actions": ["장마감 기준 추가 매수 검토"],
        "generated_at": "2026-03-06T10:30:00+00:00",
        "source_version": "wealth:2026-03-06",
        "stale": False,
    }
}


def test_build_liquidity_summary_calculates_cash_debt_and_net_liquidity() -> None:
    liquidity = build_liquidity_summary(MANUAL_PAYLOAD)

    assert liquidity == {
        "cash_krw": 15000000,
        "debt_krw": 2000000,
        "net_liquidity_krw": 13000000,
        "liquidity_ratio_pct": 48.75,
    }


def test_build_manager_cards_prefers_cached_summary_metadata_when_available() -> None:
    cards = build_manager_cards(
        MANUAL_PAYLOAD,
        target_weight_pct=95.0,
        summary_by_manager=SUMMARY_CACHE,
    )

    assert cards[0]["manager_id"] == "core_strategy"
    assert cards[0]["summary"] == SUMMARY_CACHE["core_strategy"]["summary_text"]
    assert cards[0]["recommended_action"] == "장마감 기준 추가 매수 검토"
    assert cards[0]["warning_count"] == 1
    assert cards[0]["stale"] is False
    assert cards[1]["headline"] == "관심종목 1개"


def test_build_core_strategy_position_includes_transaction_metadata() -> None:
    position = build_core_strategy_position(MANUAL_PAYLOAD, target_weight_pct=95.0)

    assert position["transaction_count"] == 1
    assert position["last_traded_at"] == "2026-03-05T09:00:00+00:00"
