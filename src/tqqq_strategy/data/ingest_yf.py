"""Minimal yfinance row normalization helpers."""

from __future__ import annotations

from tqqq_strategy.data.schema import (
    DEFAULT_IS_TRADING_DAY,
    DEFAULT_SESSION_TYPE,
    DEFAULT_TIMEZONE,
)


def normalize_yf_row(
    symbol: str,
    date: str,
    close: float,
    adj_close: float,
    tz: str = DEFAULT_TIMEZONE,
    session_type: str = DEFAULT_SESSION_TYPE,
    is_trading_day: bool = DEFAULT_IS_TRADING_DAY,
) -> dict[str, str | float | bool]:
    """Normalize a yfinance row to the canonical schema."""
    return {
        "date": date,
        "symbol": symbol,
        "close": close,
        "adj_close": adj_close,
        "source": "yfinance",
        "tz": tz,
        "session_type": session_type,
        "is_trading_day": is_trading_day,
    }
