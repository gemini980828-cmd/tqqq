from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tqqq_strategy.wealth.schema import TOP_LEVEL_COLLECTIONS, validate_collection

DEFAULT_MANUAL_TRUTH_PATH = Path("data/manual/wealth_manual.json")


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, str):
        value = value.replace(",", "")
    return float(value)


def _normalize_position(record: dict[str, Any]) -> dict[str, Any]:
    fx_rate = _coerce_float(record.get("fx_rate_krw"), default=1.0) or 1.0
    quantity = _coerce_float(record.get("quantity"))
    market_price_krw = _coerce_float(record.get("market_price_krw", record.get("market_price_usd")))
    avg_cost_krw = _coerce_float(record.get("avg_cost_krw", record.get("avg_cost_usd")))
    market_value_krw = record.get("market_value_krw")

    if record.get("market_price_usd") is not None and record.get("market_price_krw") is None:
        market_price_krw *= fx_rate
    if record.get("avg_cost_usd") is not None and record.get("avg_cost_krw") is None:
        avg_cost_krw *= fx_rate
    if market_value_krw is None and record.get("market_value_usd") is not None:
        market_value_krw = _coerce_float(record.get("market_value_usd")) * fx_rate
    if market_value_krw is None:
        market_value_krw = quantity * market_price_krw

    return {
        **record,
        "account_id": record.get("account_id", "manual-account"),
        "asset_id": record.get("asset_id", f"{record.get('manager_id', 'asset')}:{record.get('symbol', 'unknown')}"),
        "name": record.get("name", record.get("symbol", "Unknown")),
        "quantity": quantity,
        "avg_cost_krw": round(avg_cost_krw, 2),
        "market_price_krw": round(market_price_krw, 2),
        "market_value_krw": round(_coerce_float(market_value_krw), 2),
    }


def _normalize_cash_debt(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "entry_id": record.get("entry_id", record.get("id", "manual-entry")),
        "label": record.get("label", record.get("name", "Unnamed entry")),
        "balance_krw": round(_coerce_float(record.get("balance_krw")), 2),
    }


def _normalize_stock_watch(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "idea_id": record.get("idea_id", record.get("item_id", record.get("symbol", "idea"))),
        "memo": record.get("memo", record.get("note", "")),
    }


def _normalize_property_watch(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "property_id": record.get("property_id", record.get("item_id", record.get("name", "property"))),
    }


def _normalize_transaction(record: dict[str, Any]) -> dict[str, Any]:
    fx_rate = _coerce_float(record.get("fx_rate_krw"), default=1.0) or 1.0
    quantity = _coerce_float(record.get("quantity"))
    price_krw = _coerce_float(record.get("price_krw", record.get("price_usd")))
    total_value_krw = record.get("total_value_krw")

    if record.get("price_usd") is not None and record.get("price_krw") is None:
        price_krw *= fx_rate
    if total_value_krw is None and record.get("total_value_usd") is not None:
        total_value_krw = _coerce_float(record.get("total_value_usd")) * fx_rate
    if total_value_krw is None:
        total_value_krw = quantity * price_krw

    return {
        **record,
        "transaction_id": record.get("transaction_id", record.get("id", "manual-transaction")),
        "quantity": quantity,
        "price_krw": round(price_krw, 2),
        "total_value_krw": round(_coerce_float(total_value_krw), 2),
    }


def _normalize_records(collection: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if collection == "positions":
        return [_normalize_position(record) for record in records]
    if collection == "cash_debt":
        return [_normalize_cash_debt(record) for record in records]
    if collection == "stock_watchlist":
        return [_normalize_stock_watch(record) for record in records]
    if collection == "property_watchlist":
        return [_normalize_property_watch(record) for record in records]
    if collection == "transactions":
        return [_normalize_transaction(record) for record in records]
    return records


def normalize_manual_inputs(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    normalized: dict[str, list[dict[str, Any]]] = {}
    for collection in TOP_LEVEL_COLLECTIONS:
        records = payload.get(collection, []) or []
        if not isinstance(records, list):
            raise TypeError(f"{collection} must be a list")
        normalized[collection] = validate_collection(collection, _normalize_records(collection, records))
    return normalized


def load_manual_inputs(path: str | Path = DEFAULT_MANUAL_TRUTH_PATH) -> dict[str, list[dict[str, Any]]]:
    manual_path = Path(path)
    if not manual_path.exists():
        return {collection: [] for collection in TOP_LEVEL_COLLECTIONS}
    payload = json.loads(manual_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("manual inputs root must be an object")
    return normalize_manual_inputs(payload)


def load_manual_truth(path: str | Path = DEFAULT_MANUAL_TRUTH_PATH) -> dict[str, list[dict[str, Any]]]:
    return load_manual_inputs(path)
