from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

import sys
sys.path.append("ops/scripts")
import run_reference_backtest as ref  # noqa: E402


def calc_cagr(eq: pd.Series) -> float:
    years = len(eq) / 252
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) if years > 0 else float("nan")


def calc_mdd(eq: pd.Series) -> float:
    return float((eq / eq.cummax() - 1).min())


def main(start: str, end: str, out_csv: Path) -> None:
    raw = yf.download(["QQQ", "TQQQ", "SPY", "KRW=X"], start=start, end=end, auto_adjust=False, progress=False)
    if raw.empty:
        raise RuntimeError("No data downloaded")

    df = pd.DataFrame(index=raw.index)
    for sym in ["QQQ", "TQQQ", "SPY"]:
        df[f"{sym}_close"] = raw[("Close", sym)]
        df[f"{sym}_adj"] = raw[("Adj Close", sym)]
    df["KRWFX_close"] = raw[("Close", "KRW=X")].ffill().bfill()
    df = df.dropna().copy()

    weight = ref.compute_basic_strategy(df, ref.BasicParams(spy_bear_cap=0.0))

    rows: list[dict[str, float]] = []
    for one_way_bps in [3, 5, 7, 10, 15]:
        for initial_krw in [30_000_000, 100_000_000, 300_000_000]:
            eq_pre, eq_after, ledger = ref.simulate_portfolio(
                prices_usd=df["TQQQ_close"],
                fx_krw_per_usd=df["KRWFX_close"],
                target_weight=weight,
                initial_capital_krw=float(initial_krw),
                cost_oneway=one_way_bps / 10000.0,
                annual_deduction_krw=2_500_000.0,
                tax_rate=0.22,
            )
            pretax_cagr = calc_cagr(eq_pre)
            aftertax_cagr = calc_cagr(eq_after)
            rows.append(
                {
                    "one_way_bps": one_way_bps,
                    "initial_capital_krw": float(initial_krw),
                    "pretax_cagr": pretax_cagr,
                    "aftertax_cagr": aftertax_cagr,
                    "tax_drag_pctp": pretax_cagr - aftertax_cagr,
                    "pretax_mdd": calc_mdd(eq_pre),
                    "aftertax_mdd": calc_mdd(eq_after),
                    "total_tax_paid_krw": float(ledger[ledger["year"].notna()]["tax_paid_krw"].sum()) if "year" in ledger.columns else np.nan,
                }
            )

    out = pd.DataFrame(rows).sort_values(["initial_capital_krw", "one_way_bps"]).reset_index(drop=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_csv, index=False)
    print(out.to_string(index=False))
    print(f"saved: {out_csv}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2011-06-23")
    ap.add_argument("--end", default="2026-01-31")
    ap.add_argument("--out-csv", default="reports/aftertax_sensitivity_s2.csv")
    args = ap.parse_args()
    main(args.start, args.end, Path(args.out_csv))
