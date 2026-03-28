from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_SIGNAL_COLUMNS = {"time", "S2_code", "S2_weight"}
REQUIRED_MARKET_COLUMNS = {"time", "QQQ종가", "TQQQ종가", "SPY종가", "원달러환율"}


def verify_signal_ready(
    *,
    signal_csv_path: str | Path,
    data_csv_path: str | Path,
) -> dict[str, object]:
    signal_path = Path(signal_csv_path)
    data_path = Path(data_csv_path)

    if not signal_path.exists():
        raise ValueError(f"signal file does not exist: {signal_path}")
    if not data_path.exists():
        raise ValueError(f"market data file does not exist: {data_path}")

    signal_df = pd.read_csv(signal_path, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    market_df = pd.read_csv(data_path, parse_dates=["time"]).sort_values("time").reset_index(drop=True)

    signal_missing = REQUIRED_SIGNAL_COLUMNS.difference(set(signal_df.columns))
    if signal_missing:
        raise ValueError(f"signal csv missing required columns: {sorted(signal_missing)}")
    market_missing = REQUIRED_MARKET_COLUMNS.difference(set(market_df.columns))
    if market_missing:
        raise ValueError(f"data csv missing required columns: {sorted(market_missing)}")
    if len(signal_df) < 2:
        raise ValueError("signal csv must include at least two rows")
    if market_df.empty:
        raise ValueError("market data csv must include at least one row")

    signal_date = pd.Timestamp(signal_df.iloc[-1]["time"]).strftime("%Y-%m-%d")
    market_date = pd.Timestamp(market_df.iloc[-1]["time"]).strftime("%Y-%m-%d")
    if signal_date != market_date:
        raise ValueError(f"signal date {signal_date} does not match latest market date {market_date}")

    return {
        "ok": True,
        "signal_date": signal_date,
        "market_date": market_date,
        "row_count": int(len(signal_df)),
        "signal_path": str(signal_path),
        "data_path": str(data_path),
    }
