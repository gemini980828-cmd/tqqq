import pandas as pd

from tqqq_strategy.data.quality import validate_canonical
from tqqq_strategy.data.schema import CANONICAL_REQUIRED_COLUMNS


def _base_rows() -> list[dict]:
    return [
        {
            "date": "2026-01-02",
            "symbol": "TQQQ",
            "close": 103.0,
            "adj_close": 102.5,
            "source": "yfinance",
            "tz": "America/New_York",
            "session_type": "RTH",
            "is_trading_day": True,
        }
    ]


def test_validate_canonical_rejects_missing_required_columns() -> None:
    df = pd.DataFrame(_base_rows()).drop(columns=["is_trading_day"])

    ok, errs = validate_canonical(df)

    assert not ok
    assert any("missing" in err.lower() for err in errs)
    assert "is_trading_day" in " ".join(errs)


def test_validate_canonical_rejects_duplicate_date_symbol_rows() -> None:
    df = pd.DataFrame(_base_rows() + _base_rows())

    ok, errs = validate_canonical(df)

    assert not ok
    assert any("duplicate" in err.lower() for err in errs)


def test_required_columns_constant_contains_primary_key_columns() -> None:
    required = set(CANONICAL_REQUIRED_COLUMNS)
    assert {"date", "symbol"}.issubset(required)
