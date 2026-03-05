from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def rsi_wilder(close: pd.Series, length: int = 14) -> pd.Series:
    ch = close.diff()
    up = ch.clip(lower=0)
    dn = (-ch).clip(lower=0)
    au = up.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    ad = dn.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = au / ad
    return 100 - 100 / (1 + rs)


def main(data_csv: Path, signal_csv: Path, out_dir: Path) -> None:
    data = pd.read_csv(data_csv, parse_dates=["time"])
    sig = pd.read_csv(signal_csv, parse_dates=["time"])

    df = data.merge(sig[["time", "S2_weight", "S2_code"]], on="time", how="inner").sort_values("time")

    df["t_ret"] = df["TQQQ종가"].pct_change()
    df["vol20"] = df["t_ret"].rolling(20, min_periods=20).std(ddof=1)
    df["spy_dist200"] = (df["SPY종가"] / df["SPY200일선"]) * 100.0
    df["rsi14"] = rsi_wilder(df["QQQ종가"], 14)
    df["weight_changed"] = df["S2_weight"].diff().abs().fillna(0) > 1e-12

    allowed = {0.0, 0.05, 0.1, 0.8, 0.9, 0.95, 1.0}
    bad_weights = ~df["S2_weight"].round(4).isin(allowed)

    # strongest deterministic rule in priority chain
    vol_lock_rows = df["vol20"] >= 0.059
    vol_lock_viol = vol_lock_rows & (df["S2_weight"] > 1e-12)

    transitions = df[df["weight_changed"]].copy()
    transitions["prev_weight"] = df["S2_weight"].shift(1)
    transitions = transitions[
        [
            "time",
            "prev_weight",
            "S2_weight",
            "S2_code",
            "TQQQ종가",
            "TQQQ200일 이격도",
            "vol20",
            "spy_dist200",
            "rsi14",
        ]
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    transitions.to_csv(out_dir / "no_tv_transition_replay.csv", index=False)

    summary = {
        "rows": int(len(df)),
        "date_from": str(df["time"].min().date()),
        "date_to": str(df["time"].max().date()),
        "allowed_weight_violations": int(bad_weights.sum()),
        "vol_lock_rows": int(vol_lock_rows.sum()),
        "vol_lock_violations": int(vol_lock_viol.sum()),
        "transition_count": int(len(transitions)),
        "weight_distribution": {str(k): int(v) for k, v in df["S2_weight"].value_counts().sort_index().items()},
    }
    (out_dir / "no_tv_validation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"saved: {out_dir / 'no_tv_validation_summary.json'}")
    print(f"saved: {out_dir / 'no_tv_transition_replay.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", default="data/user_input.csv")
    ap.add_argument("--signal-csv", default="reports/signals_s1_s2_s3_user_original.csv")
    ap.add_argument("--out-dir", default="reports")
    args = ap.parse_args()
    main(Path(args.data_csv), Path(args.signal_csv), Path(args.out_dir))
