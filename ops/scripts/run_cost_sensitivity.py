from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def calc_curve(price: pd.Series, weight: pd.Series, one_way_bps: float) -> pd.Series:
    r = price.pct_change().fillna(0.0)
    eq = [1.0]
    prev_w = 0.0
    fee = one_way_bps / 10000.0
    for i in range(1, len(price)):
        gross = eq[-1] * (1 + float(weight.iloc[i - 1]) * float(r.iloc[i]))
        turnover = abs(float(weight.iloc[i]) - prev_w)
        net = gross * (1 - turnover * fee)
        eq.append(net)
        prev_w = float(weight.iloc[i])
    return pd.Series(eq, index=price.index)


def stats(eq: pd.Series) -> tuple[float, float]:
    years = len(eq) / 252
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1
    mdd = (eq / eq.cummax() - 1).min()
    return float(cagr), float(mdd)


def main(data_csv: Path, signal_csv: Path, out_csv: Path) -> None:
    data = pd.read_csv(data_csv)
    sig = pd.read_csv(signal_csv)
    df = pd.merge(data[["time", "TQQQ종가"]], sig[["time", "S2_weight"]], on="time", how="inner")

    rows = []
    for bps in [3, 5, 7, 10, 15]:
        eq = calc_curve(df["TQQQ종가"], df["S2_weight"], bps)
        cagr, mdd = stats(eq)
        rows.append({"one_way_bps": bps, "CAGR": cagr, "MDD": mdd, "end_equity": float(eq.iloc[-1])})

    out = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    print(out.to_string(index=False))
    print(f"saved: {out_csv}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", default="data/user_input.csv")
    ap.add_argument("--signal-csv", default="reports/signals_s1_s2_s3_user_original.csv")
    ap.add_argument("--out-csv", default="reports/cost_sensitivity_s2.csv")
    args = ap.parse_args()
    main(Path(args.data_csv), Path(args.signal_csv), Path(args.out_csv))
