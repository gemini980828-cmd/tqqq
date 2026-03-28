from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "ops" / "scripts"))

from tqqq_strategy.experiments.cash_sleeve import (  # noqa: E402
    CashSleeveConfig,
    build_daily_yield_series_from_annual_returns,
    cagr,
    mdd,
    simulate_with_taxed_cash_sleeve,
)
from tqqq_strategy.experiments.phase2_config import Phase2Params  # noqa: E402
from tqqq_strategy.experiments.phase2_runner import _compute_signal  # noqa: E402
import run_reference_backtest as ref  # noqa: E402


SGOV_ANNUAL_TOTAL_RETURN = {
    2020: 0.0004,
    2021: 0.0004,
    2022: 0.0158,
    2023: 0.0512,
    2024: 0.0527,
    2025: 0.0424,
    2026: 0.0354,
}
SWEEP_ANNUAL_RETURN = {year: max(ret - 0.005, 0.0) for year, ret in SGOV_ANNUAL_TOTAL_RETURN.items()}
INCEPTION = "2020-05-26"


def eval_reference(weight: pd.Series, prices_usd: pd.Series, fx: pd.Series) -> dict[str, float]:
    eq_pre, eq_after, ledger = ref.simulate_portfolio(
        prices_usd=prices_usd,
        fx_krw_per_usd=fx,
        target_weight=weight,
        initial_capital_krw=100_000_000.0,
        cost_oneway=5 / 10000.0,
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )
    return {
        "pretax_cagr": cagr(eq_pre),
        "aftertax_cagr": cagr(eq_after),
        "pretax_mdd": mdd(eq_pre),
        "aftertax_mdd": mdd(eq_after),
        "ending_multiple": float(eq_after.iloc[-1]),
        "tax_paid_krw": float(ledger[ledger["year"].notna()]["tax_paid_krw"].sum()),
    }


def eval_taxed_sweep(weight: pd.Series, prices_krw: pd.Series, daily_yield: pd.Series) -> dict[str, float]:
    eq_pre, eq_after, ledger = simulate_with_taxed_cash_sleeve(
        prices_krw=prices_krw,
        target_weight=weight,
        initial_capital_krw=100_000_000.0,
        tqqq_cost_oneway=5 / 10000.0,
        sleeve=CashSleeveConfig(threshold_days=0, annual_yield=0.0, sleeve_cost_oneway=0.0, eligible_max_weight=0.999999),
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
        sleeve_daily_yield=daily_yield,
    )
    detail = ledger[ledger["date"].notna()].copy()
    return {
        "pretax_cagr": cagr(eq_pre),
        "aftertax_cagr": cagr(eq_after),
        "pretax_mdd": mdd(eq_pre),
        "aftertax_mdd": mdd(eq_after),
        "ending_multiple": float(eq_after.iloc[-1]),
        "tax_paid_krw": float(ledger[ledger.get("year").notna()]["tax_paid_krw"].sum()) if "year" in ledger.columns else 0.0,
        "parking_days": float(detail["parking_active"].sum()),
    }


def main() -> None:
    data = pd.read_csv("data/user_input.csv", parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    orig_sig = pd.read_csv("reports/signals_s1_s2_s3_user_original.csv", parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    overlay_sig = pd.read_csv("experiments/overlay_best_signal.csv", parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    best = json.loads(Path("experiments/best_config.json").read_text(encoding="utf-8"))
    phase2_params = Phase2Params(**json.loads(best["params_json"]))
    phase2_weight, _ = _compute_signal(data.copy(), phase2_params)

    idx = data["time"]
    prices_usd = data["TQQQ종가"].astype(float).set_axis(idx)
    prices_krw = (data["TQQQ종가"].astype(float) * 1300.0).set_axis(idx)
    fx = pd.Series(1300.0, index=idx)
    sweep_daily = build_daily_yield_series_from_annual_returns(data["time"], SWEEP_ANNUAL_RETURN, INCEPTION)

    orig_weight = orig_sig["S2_weight"].astype(float).set_axis(idx)
    overlay_weight = overlay_sig["S2_weight"].astype(float).set_axis(idx)
    phase2_weight = pd.Series(phase2_weight.values, index=idx)

    rows = []
    rows.append({"scenario": "baseline_orig", **eval_reference(orig_weight, prices_usd, fx)})
    rows.append({"scenario": "soft_overheat_buffer", **eval_reference(overlay_weight, prices_usd, fx)})
    rows.append({"scenario": "phase2_best", **eval_reference(phase2_weight, prices_usd, fx)})
    rows.append({"scenario": "phase2_best_plus_sweep_taxed", **eval_taxed_sweep(phase2_weight, prices_krw, sweep_daily)})

    out = pd.DataFrame(rows)
    Path("experiments").mkdir(exist_ok=True)
    out.to_csv("experiments/phase2_sweep_taxed_compare.csv", index=False)
    print(out.to_string(index=False))
    print("saved: experiments/phase2_sweep_taxed_compare.csv")


if __name__ == "__main__":
    main()
