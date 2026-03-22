from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tqqq_strategy.experiments.cash_sleeve import (  # noqa: E402
    CashSleeveConfig,
    build_daily_yield_series_from_annual_returns,
    cagr,
    mdd,
    simulate_with_cash_sleeve,
)


ANNUAL_TOTAL_RETURN = {
    2020: 0.0004,
    2021: 0.0004,
    2022: 0.0158,
    2023: 0.0512,
    2024: 0.0527,
    2025: 0.0424,
    2026: 0.0354,
}

INCEPTION_DATE = "2020-05-26"


def run(
    data_csv: Path,
    signal_csv: Path,
    out_dir: Path,
    initial_krw: float,
    tqqq_cost_oneway_bps: float,
    sleeve_cost_oneway_bps: float,
) -> None:
    data = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    signal = pd.read_csv(signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    df = data.merge(signal[["time", "S2_weight"]], on="time", how="inner").sort_values("time").reset_index(drop=True)
    prices_krw = (df["TQQQ종가"].astype(float) * 1300.0).set_axis(df["time"])
    target_weight = df["S2_weight"].astype(float).set_axis(df["time"])
    daily_yield = build_daily_yield_series_from_annual_returns(df["time"], ANNUAL_TOTAL_RETURN, INCEPTION_DATE)

    scenarios = [
        ("baseline_cash", None),
        ("sgov_real_immediate", 0),
        ("sgov_real_after_5d", 5),
        ("sgov_real_after_10d", 10),
        ("sgov_real_after_13d", 13),
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, threshold_days in scenarios:
        cfg = CashSleeveConfig(
            threshold_days=threshold_days if threshold_days is not None else 999999,
            annual_yield=0.0,
            sleeve_cost_oneway=0.0 if threshold_days is None else sleeve_cost_oneway_bps / 10000.0,
        )
        eq, ledger = simulate_with_cash_sleeve(
            prices_krw=prices_krw,
            target_weight=target_weight,
            initial_capital_krw=initial_krw,
            tqqq_cost_oneway=tqqq_cost_oneway_bps / 10000.0,
            sleeve=cfg,
            sleeve_daily_yield=None if threshold_days is None else daily_yield,
        )
        ledger.to_csv(out_dir / f"{name}_ledger.csv", index=False)
        eq.to_csv(out_dir / f"{name}_equity.csv", header=["equity"])
        rows.append(
            {
                "scenario": name,
                "threshold_days": -1 if threshold_days is None else threshold_days,
                "sgov_inception_date": INCEPTION_DATE,
                "sleeve_cost_oneway_bps": 0.0 if threshold_days is None else sleeve_cost_oneway_bps,
                "tqqq_cost_oneway_bps": tqqq_cost_oneway_bps,
                "cagr": cagr(eq),
                "mdd": mdd(eq),
                "parking_days": int(ledger["parking_active"].sum()),
                "ending_equity_multiple": float(eq.iloc[-1]),
            }
        )

    summary = pd.DataFrame(rows).sort_values("threshold_days")
    summary.to_csv(out_dir / "sgov_realistic_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"saved: {out_dir / 'sgov_realistic_summary.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", type=Path, default=Path("data/user_input.csv"))
    ap.add_argument("--signal-csv", type=Path, default=Path("reports/signals_s1_s2_s3_user_original.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("experiments/sgov_realistic"))
    ap.add_argument("--initial-krw", type=float, default=100_000_000.0)
    ap.add_argument("--tqqq-cost-oneway-bps", type=float, default=5.0)
    ap.add_argument("--sleeve-cost-oneway-bps", type=float, default=1.0)
    args = ap.parse_args()
    run(
        data_csv=args.data_csv,
        signal_csv=args.signal_csv,
        out_dir=args.out_dir,
        initial_krw=args.initial_krw,
        tqqq_cost_oneway_bps=args.tqqq_cost_oneway_bps,
        sleeve_cost_oneway_bps=args.sleeve_cost_oneway_bps,
    )
