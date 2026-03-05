from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np

import sys
sys.path.append("ops/scripts")
import run_reference_backtest as ref  # provides simulate_portfolio


def metrics(eq: pd.Series) -> dict[str, float]:
    r = eq.pct_change().fillna(0.0)
    years = len(eq) / 252
    cagr = float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) if years > 0 else float("nan")
    mdd = float((eq / eq.cummax() - 1).min())
    ann_vol = float(r.std(ddof=1) * np.sqrt(252))
    sharpe = float((r.mean() * 252) / ann_vol) if ann_vol > 0 else float("nan")
    return {"CAGR": cagr, "MDD": mdd, "AnnualVol": ann_vol, "Sharpe": sharpe}


def main(data_csv: Path, signal_csv: Path, out_csv: Path, initial_krw: float, one_way_bps: float) -> None:
    data = pd.read_csv(data_csv, parse_dates=["time"])
    sig = pd.read_csv(signal_csv, parse_dates=["time"])

    df = data.merge(sig[["time", "S2_weight"]], on="time", how="inner").sort_values("time").reset_index(drop=True)
    df = df.set_index("time")

    # FX: use krw from yfinance if exists; else fixed proxy
    if "KRWFX" in df.columns:
        fx = df["KRWFX"].astype(float)
    else:
        fx = pd.Series(1300.0, index=df.index)

    eq_pre, eq_after, ledger = ref.simulate_portfolio(
        prices_usd=df["TQQQ종가"],
        fx_krw_per_usd=fx,
        target_weight=df["S2_weight"],
        initial_capital_krw=initial_krw,
        cost_oneway=one_way_bps / 10000.0,
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )

    m_pre = metrics(eq_pre)
    m_after = metrics(eq_after)
    out = {
        "engine": "user_original_signal",
        "rows": int(len(df)),
        "date_from": str(df.index.min().date()),
        "date_to": str(df.index.max().date()),
        "one_way_bps": one_way_bps,
        "initial_capital_krw": initial_krw,
        "pretax_cagr": m_pre["CAGR"],
        "aftertax_cagr": m_after["CAGR"],
        "tax_drag_pctp": m_pre["CAGR"] - m_after["CAGR"],
        "pretax_mdd": m_pre["MDD"],
        "aftertax_mdd": m_after["MDD"],
        "pretax_sharpe": m_pre["Sharpe"],
        "aftertax_sharpe": m_after["Sharpe"],
        "total_tax_paid_krw": float(ledger[ledger["year"].notna()]["tax_paid_krw"].sum()) if "year" in ledger.columns else float("nan"),
    }

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([out]).to_csv(out_csv, index=False)
    ledger.to_csv(out_csv.with_name("user_signal_tax_ledger.csv"), index=False)
    print(pd.DataFrame([out]).to_string(index=False))
    print(f"saved: {out_csv}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", default="data/user_input.csv")
    ap.add_argument("--signal-csv", default="reports/signals_s1_s2_s3_user_original.csv")
    ap.add_argument("--out-csv", default="reports/user_signal_backtest_summary.csv")
    ap.add_argument("--initial-krw", type=float, default=100_000_000)
    ap.add_argument("--one-way-bps", type=float, default=5.0)
    args = ap.parse_args()
    main(Path(args.data_csv), Path(args.signal_csv), Path(args.out_csv), args.initial_krw, args.one_way_bps)
