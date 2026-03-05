from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import yfinance as yf


def main(start: str, end: str, out_csv: Path):
    raw = yf.download(["QQQ", "TQQQ", "SPY"], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError("No data downloaded")

    df = pd.DataFrame({
        "time": raw.index,
        "QQQ종가": raw[("Close", "QQQ")].astype(float),
        "TQQQ종가": raw[("Close", "TQQQ")].astype(float),
        "SPY종가": raw[("Close", "SPY")].astype(float),
    }).dropna().reset_index(drop=True)

    df["QQQ3일선"] = df["QQQ종가"].rolling(3, min_periods=3).mean()
    df["QQQ161일선"] = df["QQQ종가"].rolling(161, min_periods=161).mean()
    df["TQQQ200일선"] = df["TQQQ종가"].rolling(200, min_periods=200).mean()
    df["SPY200일선"] = df["SPY종가"].rolling(200, min_periods=200).mean()
    df["TQQQ200일 이격도"] = (df["TQQQ종가"] / df["TQQQ200일선"]) * 100.0

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print(f"saved: {out_csv}")
    print(df.tail(3).to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2011-06-23")
    ap.add_argument("--end", default="2026-01-31")
    ap.add_argument("--out", default="data/user_input.csv")
    args = ap.parse_args()
    main(args.start, args.end, Path(args.out))
