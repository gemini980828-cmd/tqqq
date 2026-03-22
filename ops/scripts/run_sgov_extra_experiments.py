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


SGOV_ANNUAL_TOTAL_RETURN = {
    2020: 0.0004,
    2021: 0.0004,
    2022: 0.0158,
    2023: 0.0512,
    2024: 0.0527,
    2025: 0.0424,
    2026: 0.0354,
}
SGOV_INCEPTION = "2020-05-26"
SWEEP_ANNUAL_RETURN = {year: max(ret - 0.005, 0.0) for year, ret in SGOV_ANNUAL_TOTAL_RETURN.items()}


def run_case(
    *,
    name: str,
    prices_krw: pd.Series,
    target_weight: pd.Series,
    initial_krw: float,
    tqqq_cost_oneway_bps: float,
    cfg: CashSleeveConfig,
    daily_yield: pd.Series | None,
    out_dir: Path,
) -> dict[str, float | int | str]:
    eq, ledger = simulate_with_cash_sleeve(
        prices_krw=prices_krw,
        target_weight=target_weight,
        initial_capital_krw=initial_krw,
        tqqq_cost_oneway=tqqq_cost_oneway_bps / 10000.0,
        sleeve=cfg,
        sleeve_daily_yield=daily_yield,
    )
    ledger.to_csv(out_dir / f"{name}_ledger.csv", index=False)
    eq.to_csv(out_dir / f"{name}_equity.csv", header=["equity"])
    return {
        "scenario": name,
        "threshold_days": cfg.threshold_days,
        "eligible_max_weight": cfg.eligible_max_weight,
        "sleeve_cost_oneway_bps": cfg.sleeve_cost_oneway * 10000.0,
        "cagr": cagr(eq),
        "mdd": mdd(eq),
        "parking_days": int(ledger["parking_active"].sum()),
        "ending_equity_multiple": float(eq.iloc[-1]),
    }


def main(
    data_csv: Path,
    signal_csv: Path,
    overlay_signal_csv: Path,
    out_dir: Path,
    initial_krw: float,
    tqqq_cost_oneway_bps: float,
) -> None:
    data = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    signal = pd.read_csv(signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    overlay = pd.read_csv(overlay_signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)

    base_df = data.merge(signal[["time", "S2_weight"]], on="time", how="inner").sort_values("time").reset_index(drop=True)
    overlay_df = data.merge(overlay[["time", "S2_weight"]], on="time", how="inner").sort_values("time").reset_index(drop=True)

    prices_krw = (base_df["TQQQ종가"].astype(float) * 1300.0).set_axis(base_df["time"])
    base_weight = base_df["S2_weight"].astype(float).set_axis(base_df["time"])
    overlay_weight = overlay_df["S2_weight"].astype(float).set_axis(overlay_df["time"])

    sgov_daily = build_daily_yield_series_from_annual_returns(base_df["time"], SGOV_ANNUAL_TOTAL_RETURN, SGOV_INCEPTION)
    sweep_daily = build_daily_yield_series_from_annual_returns(base_df["time"], SWEEP_ANNUAL_RETURN, SGOV_INCEPTION)

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    rows.append(
        run_case(
            name="baseline_cash_orig",
            prices_krw=prices_krw,
            target_weight=base_weight,
            initial_krw=initial_krw,
            tqqq_cost_oneway_bps=tqqq_cost_oneway_bps,
            cfg=CashSleeveConfig(threshold_days=999999, annual_yield=0.0, sleeve_cost_oneway=0.0),
            daily_yield=None,
            out_dir=out_dir,
        )
    )
    rows.append(
        run_case(
            name="full_cash_only_sgov_orig",
            prices_krw=prices_krw,
            target_weight=base_weight,
            initial_krw=initial_krw,
            tqqq_cost_oneway_bps=tqqq_cost_oneway_bps,
            cfg=CashSleeveConfig(threshold_days=0, annual_yield=0.0, sleeve_cost_oneway=0.0001, eligible_max_weight=0.0),
            daily_yield=sgov_daily,
            out_dir=out_dir,
        )
    )
    rows.append(
        run_case(
            name="sweep_immediate_orig",
            prices_krw=prices_krw,
            target_weight=base_weight,
            initial_krw=initial_krw,
            tqqq_cost_oneway_bps=tqqq_cost_oneway_bps,
            cfg=CashSleeveConfig(threshold_days=0, annual_yield=0.0, sleeve_cost_oneway=0.0, eligible_max_weight=0.999999),
            daily_yield=sweep_daily,
            out_dir=out_dir,
        )
    )
    rows.append(
        run_case(
            name="overlay_only_cash",
            prices_krw=prices_krw,
            target_weight=overlay_weight,
            initial_krw=initial_krw,
            tqqq_cost_oneway_bps=tqqq_cost_oneway_bps,
            cfg=CashSleeveConfig(threshold_days=999999, annual_yield=0.0, sleeve_cost_oneway=0.0),
            daily_yield=None,
            out_dir=out_dir,
        )
    )
    rows.append(
        run_case(
            name="overlay_plus_limited_sgov",
            prices_krw=prices_krw,
            target_weight=overlay_weight,
            initial_krw=initial_krw,
            tqqq_cost_oneway_bps=tqqq_cost_oneway_bps,
            cfg=CashSleeveConfig(threshold_days=5, annual_yield=0.0, sleeve_cost_oneway=0.0001, eligible_max_weight=0.0),
            daily_yield=sgov_daily,
            out_dir=out_dir,
        )
    )

    summary = pd.DataFrame(rows)
    summary.to_csv(out_dir / "sgov_extra_summary.csv", index=False)
    print(summary.to_string(index=False))
    print(f"saved: {out_dir / 'sgov_extra_summary.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", type=Path, default=Path("data/user_input.csv"))
    ap.add_argument("--signal-csv", type=Path, default=Path("reports/signals_s1_s2_s3_user_original.csv"))
    ap.add_argument("--overlay-signal-csv", type=Path, default=Path("experiments/overlay_best_signal.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("experiments/sgov_extra"))
    ap.add_argument("--initial-krw", type=float, default=100_000_000.0)
    ap.add_argument("--tqqq-cost-oneway-bps", type=float, default=5.0)
    args = ap.parse_args()
    main(
        data_csv=args.data_csv,
        signal_csv=args.signal_csv,
        overlay_signal_csv=args.overlay_signal_csv,
        out_dir=args.out_dir,
        initial_krw=args.initial_krw,
        tqqq_cost_oneway_bps=args.tqqq_cost_oneway_bps,
    )
