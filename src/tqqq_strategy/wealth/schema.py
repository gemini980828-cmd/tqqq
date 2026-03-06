from __future__ import annotations

from typing import Any, Iterable, Mapping

TOP_LEVEL_COLLECTIONS = (
    "positions",
    "cash_debt",
    "stock_watchlist",
    "property_watchlist",
    "transactions",
)

REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "positions": (
        "account_id",
        "asset_id",
        "manager_id",
        "symbol",
        "name",
        "quantity",
        "avg_cost_krw",
        "market_price_krw",
        "market_value_krw",
    ),
    "cash_debt": (
        "entry_id",
        "kind",
        "label",
        "balance_krw",
    ),
    "stock_watchlist": (
        "idea_id",
        "symbol",
        "status",
        "memo",
    ),
    "property_watchlist": (
        "property_id",
        "name",
        "status",
        "region",
    ),
    "transactions": (
        "transaction_id",
        "account_id",
        "manager_id",
        "symbol",
        "side",
        "quantity",
        "price_krw",
        "total_value_krw",
        "traded_at",
    ),
}

SUMMARY_REQUIRED_FIELDS = {
    "manager_id",
    "generated_at",
    "source_version",
    "stale",
    "summary_text",
}


class WealthSchemaError(ValueError):
    pass


def _missing_required_fields(record: Mapping[str, object], required_fields: Iterable[str]) -> list[str]:
    return [field for field in required_fields if field not in record or record[field] in (None, "")]


def validate_record(collection: str, record: Mapping[str, Any]) -> dict[str, Any]:
    missing = _missing_required_fields(record, REQUIRED_FIELDS[collection])
    if missing:
        raise WealthSchemaError(f"{collection} missing required fields: {', '.join(missing)}")
    return dict(record)


def validate_collection(collection: str, records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if collection not in REQUIRED_FIELDS:
        raise WealthSchemaError(f"unsupported collection: {collection}")
    return [validate_record(collection, record) for record in records]


def validate_entity_records(entity_name: str, records: Iterable[Mapping[str, object]]) -> None:
    validate_collection(entity_name, records)


def validate_summary_record(record: Mapping[str, object]) -> dict[str, object]:
    missing = _missing_required_fields(record, SUMMARY_REQUIRED_FIELDS)
    if missing:
        raise WealthSchemaError(f"summary missing required fields: {', '.join(sorted(missing))}")
    return dict(record)
