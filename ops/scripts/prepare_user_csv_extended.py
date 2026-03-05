from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


def build_synth_tqqq(qqq_close: pd.Series, base_price: float = 100.0) -> pd.Series:
    r = qqq_close.pct_change().fillna(0.0)
    synth_r = 3.0 * r
    synth = [base_price]
    for i in range(1, len(qqq_close)):
        nxt = synth[-1] * (1.0 + float(synth_r.iloc[i]))
        synth.append(max(nxt, 0.01))
    return pd.Series(synth, index=qqq_close.index)


def main(start: str, end: str, out_csv: Path) -> None:
    raw = yf.download(["QQQ", "SPY", "TQQQ"], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError("No data downloaded")

    qqq = raw[("Close", "QQQ")].astype(float)
    spy = raw[("Close", "SPY")].astype(float)
    tqqq_actual = raw[("Close", "TQQQ")].astype(float)

    synth = build_synth_tqqq(qqq, base_price=100.0)

    first_actual_idx = tqqq_actual.dropna().index.min()
    tqqq = synth.copy()
    if first_actual_idx is not None:
        tqqq.loc[first_actual_idx:] = tqqq_actual.loc[first_actual_idx:]
        # scale pre-live synthetic level to connect smoothly at first actual day
        prev_idx = tqqq.index[tqqq.index < first_actual_idx]
        if len(prev_idx) > 0:
            anchor_prev = prev_idx[-1]
            scale = float(tqqq_actual.loc[first_actual_idx]) / float(synth.loc[first_actual_idx]) if synth.loc[first_actual_idx] != 0 else 1.0
            tqqq.loc[:anchor_prev] = synth.loc[:anchor_prev] * scale

    df = pd.DataFrame({
        "time": qqq.index,
        "QQQ종가": qqq,
        "TQQQ종가": tqqq,
        "SPY종가": spy,
    }).dropna().reset_index(drop=True)

    df["QQQ3일선"] = df["QQQ종가"].rolling(3, min_periods=3).mean()
    df["QQQ161일선"] = df["QQQ종가"].rolling(161, min_periods=161).mean()
    df["TQQQ200일선"] = df["TQQQ종가"].rolling(200, min_periods=200).mean()
    df["SPY200일선"] = df["SPY종가"].rolling(200, min_periods=200).mean()
    df["TQQQ200일 이격도"] = (df["TQQQ종가"] / df["TQQQ200일선"]) * 100.0

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"saved: {out_csv}")
    print(df[["time", "QQQ종가", "TQQQ종가", "SPY종가"]].head(3).to_string(index=False))
    print(df[["time", "QQQ종가", "TQQQ종가", "SPY종가"]].tail(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2000-01-03")
    ap.add_argument("--end", default="2026-01-31")
    ap.add_argument("--out", default="data/user_input_2000_ext.csv")
    args = ap.parse_args()
    main(args.start, args.end, Path(args.out))
