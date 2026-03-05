from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd


def load_py(py_csv: Path, col: str) -> pd.DataFrame:
    df = pd.read_csv(py_csv)
    if "time" not in df.columns:
        raise ValueError("python csv requires 'time' column")
    if col not in df.columns:
        raise ValueError(f"python csv missing column: {col}")
    out = df[["time", col]].copy()
    out.columns = ["time", "py_weight"]
    out["time"] = pd.to_datetime(out["time"])
    return out


def load_tv(tv_csv: Path, col: str) -> pd.DataFrame:
    df = pd.read_csv(tv_csv)
    time_candidates = [c for c in df.columns if c.lower() in {"time", "date", "datetime", "timestamp"}]
    if not time_candidates:
        raise ValueError("tv csv needs one of columns: time/date/datetime/timestamp")
    tcol = time_candidates[0]
    if col not in df.columns:
        raise ValueError(f"tv csv missing column: {col}")
    out = df[[tcol, col]].copy()
    out.columns = ["time", "tv_weight"]
    out["time"] = pd.to_datetime(out["time"])
    return out


def compare(py_df: pd.DataFrame, tv_df: pd.DataFrame, tol: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = py_df.merge(tv_df, on="time", how="inner").sort_values("time").reset_index(drop=True)
    m["delta"] = (m["py_weight"] - m["tv_weight"]).abs()
    mism = m[m["delta"] > tol].copy()
    return m, mism


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--py-csv", required=True)
    ap.add_argument("--tv-csv", required=True)
    ap.add_argument("--py-col", default="S2_weight")
    ap.add_argument("--tv-col", default="weight")
    ap.add_argument("--tol", type=float, default=0.001)
    ap.add_argument("--out", default="reports/weight_diff_report.csv")
    args = ap.parse_args()

    py_df = load_py(Path(args.py_csv), args.py_col)
    tv_df = load_tv(Path(args.tv_csv), args.tv_col)

    merged, mism = compare(py_df, tv_df, args.tol)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    mism.to_csv(out, index=False)

    total = len(merged)
    bad = len(mism)
    hit = 0.0 if total == 0 else (1 - bad / total) * 100.0

    print(f"rows_compared={total}")
    print(f"mismatches={bad}")
    print(f"match_rate={hit:.2f}%")
    print(f"max_delta={merged['delta'].max() if total else float('nan')}")
    print(f"saved={out}")


if __name__ == "__main__":
    main()
