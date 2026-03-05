"""Canonical data schema requirements for strategy inputs."""

CANONICAL_PRIMARY_KEY_COLUMNS: tuple[str, str] = ("date", "symbol")
CANONICAL_PRICE_COLUMNS: tuple[str, str] = ("close", "adj_close")
CANONICAL_META_COLUMNS: tuple[str, str, str, str] = (
    "source",
    "tz",
    "session_type",
    "is_trading_day",
)

CANONICAL_REQUIRED_COLUMNS: tuple[str, ...] = (
    *CANONICAL_PRIMARY_KEY_COLUMNS,
    *CANONICAL_PRICE_COLUMNS,
    *CANONICAL_META_COLUMNS,
)

DEFAULT_TIMEZONE = "America/New_York"
DEFAULT_SESSION_TYPE = "RTH"
DEFAULT_IS_TRADING_DAY = True
