from tqqq_strategy.data.ingest_stooq import normalize_stooq_row
from tqqq_strategy.data.ingest_yf import normalize_yf_row
from tqqq_strategy.data.schema import (
    CANONICAL_REQUIRED_COLUMNS,
    DEFAULT_IS_TRADING_DAY,
    DEFAULT_SESSION_TYPE,
    DEFAULT_TIMEZONE,
)


def test_normalize_yf_row_minimal_contract() -> None:
    row = normalize_yf_row("TQQQ", "2024-01-02", 50.0, 49.5)

    assert set(row.keys()) == set(CANONICAL_REQUIRED_COLUMNS)
    assert row["date"] == "2024-01-02"
    assert row["symbol"] == "TQQQ"
    assert row["close"] == 50.0
    assert row["source"] == "yfinance"
    assert row["adj_close"] == 49.5
    assert row["tz"] == DEFAULT_TIMEZONE
    assert row["session_type"] == DEFAULT_SESSION_TYPE
    assert row["is_trading_day"] is DEFAULT_IS_TRADING_DAY


def test_normalize_stooq_row_sets_canonical_meta_and_adj_close() -> None:
    row = normalize_stooq_row("TQQQ", "2024-01-02", 50.0)

    assert set(row.keys()) == set(CANONICAL_REQUIRED_COLUMNS)
    assert row["date"] == "2024-01-02"
    assert row["symbol"] == "TQQQ"
    assert row["close"] == 50.0
    assert row["source"] == "stooq"
    assert row["adj_close"] == 50.0
    assert row["tz"] == DEFAULT_TIMEZONE
    assert row["session_type"] == DEFAULT_SESSION_TYPE
    assert row["is_trading_day"] is DEFAULT_IS_TRADING_DAY
