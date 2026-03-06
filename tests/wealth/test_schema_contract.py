from pathlib import Path
import json

import pytest

from tqqq_strategy.wealth.manual_inputs import load_manual_truth
from tqqq_strategy.wealth.schema import (
    SUMMARY_REQUIRED_FIELDS,
    validate_entity_records,
    validate_summary_record,
)


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
        }
    ],
    "cash_debt": [
        {"entry_id": "cash-main", "kind": "cash", "label": "투자예수금", "balance_krw": 1500000},
    ],
    "stock_watchlist": [
        {"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI 인프라 핵심 수혜"},
    ],
    "property_watchlist": [
        {"property_id": "apt-1", "name": "마포래미안푸르지오", "region": "서울 마포구", "status": "검토"},
    ],
    "transactions": [
        {
            "transaction_id": "tx-1",
            "account_id": "samsung-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "side": "buy",
            "quantity": 10.0,
            "price_krw": 81000,
            "total_value_krw": 810000,
            "traded_at": "2026-03-06T22:30:00+00:00",
        }
    ],
}


ALTERNATE_MANUAL_PAYLOAD = {
    "positions": [
        {
            "account_id": "samsung-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "quantity": "10",
            "avg_cost_usd": "50",
            "market_price_usd": "55",
            "fx_rate_krw": "1400",
        }
    ],
    "cash_debt": [
        {"id": "cash-1", "kind": "cash", "name": "투자예수금", "balance_krw": "1,500,000"},
    ],
    "stock_watchlist": [
        {"item_id": "nvda", "symbol": "NVDA", "status": "관찰", "note": "AI 인프라"},
    ],
    "property_watchlist": [
        {"item_id": "apt-1", "name": "래미안", "region": "서울", "status": "검토"},
    ],
    "transactions": [
        {
            "id": "tx-alias-1",
            "account_id": "samsung-core",
            "manager_id": "core_strategy",
            "symbol": "TQQQ",
            "side": "buy",
            "quantity": "2",
            "price_usd": "55",
            "fx_rate_krw": "1400",
            "traded_at": "2026-03-06T22:30:00+00:00",
        }
    ],
}


def test_validate_entity_records_rejects_missing_required_fields() -> None:
    invalid = [{"symbol": "TQQQ", "quantity": 10.0}]
    with pytest.raises(ValueError, match="account_id"):
        validate_entity_records("positions", invalid)


def test_summary_required_fields_are_defined() -> None:
    assert SUMMARY_REQUIRED_FIELDS == {
        "manager_id",
        "generated_at",
        "source_version",
        "stale",
        "summary_text",
    }


def test_validate_summary_record_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="summary_text"):
        validate_summary_record({"manager_id": "core_strategy"})


def test_load_manual_truth_from_json_file(tmp_path: Path) -> None:
    path = tmp_path / "wealth_manual.json"
    path.write_text(json.dumps(MANUAL_PAYLOAD, ensure_ascii=False), encoding="utf-8")

    loaded = load_manual_truth(path)

    assert loaded["positions"][0]["symbol"] == "TQQQ"
    assert loaded["cash_debt"][0]["kind"] == "cash"
    assert loaded["stock_watchlist"][0]["status"] == "관찰"
    assert loaded["property_watchlist"][0]["name"] == "마포래미안푸르지오"
    assert loaded["transactions"][0]["transaction_id"] == "tx-1"


def test_load_manual_truth_normalizes_alias_fields_and_usd_values(tmp_path: Path) -> None:
    path = tmp_path / "wealth_manual.json"
    path.write_text(json.dumps(ALTERNATE_MANUAL_PAYLOAD, ensure_ascii=False), encoding="utf-8")

    loaded = load_manual_truth(path)

    assert loaded["positions"][0]["asset_id"] == "core_strategy:TQQQ"
    assert loaded["positions"][0]["avg_cost_krw"] == 70000.0
    assert loaded["positions"][0]["market_price_krw"] == 77000.0
    assert loaded["positions"][0]["market_value_krw"] == 770000.0
    assert loaded["cash_debt"][0]["entry_id"] == "cash-1"
    assert loaded["cash_debt"][0]["label"] == "투자예수금"
    assert loaded["stock_watchlist"][0]["idea_id"] == "nvda"
    assert loaded["stock_watchlist"][0]["memo"] == "AI 인프라"
    assert loaded["property_watchlist"][0]["property_id"] == "apt-1"
    assert loaded["transactions"][0]["transaction_id"] == "tx-alias-1"
    assert loaded["transactions"][0]["price_krw"] == 77000.0
    assert loaded["transactions"][0]["total_value_krw"] == 154000.0


def test_load_manual_truth_missing_file_returns_empty_collections(tmp_path: Path) -> None:
    loaded = load_manual_truth(tmp_path / "missing.json")

    assert loaded == {
        "positions": [],
        "cash_debt": [],
        "stock_watchlist": [],
        "property_watchlist": [],
        "transactions": [],
    }
