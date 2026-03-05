from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from tqqq_strategy.experiments.phase2_config import Phase2Params
from tqqq_strategy.experiments.phase2_oos import split_is_oos, cagr_from_equity, passes_oos_retention


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _compute_signal(df: pd.DataFrame, p: Phase2Params) -> pd.Series:
    user_mod = _load_module(Path("ops/scripts/user_original_reference.py"), "user_original_reference")
    params = user_mod.BasicParams(
        vol_threshold=p.vol_threshold,
        dist200_enter=p.dist200_enter,
        dist200_exit=p.dist200_exit,
        slope_thr=p.slope_thr,
        tp10_trigger=p.tp10_trigger,
        tp10_cap=p.tp10_cap,
        overheat1_enter=p.overheat1_enter,
        overheat2_enter=p.overheat2_enter,
        overheat3_enter=p.overheat3_enter,
        overheat4_enter=p.overheat4_enter,
    )
    codes, weights = user_mod.compute_basic_strategy(
        df["time"].to_numpy(),
        df["QQQ종가"].to_numpy(),
        df["QQQ3일선"].to_numpy(),
        df["QQQ161일선"].to_numpy(),
        df["TQQQ종가"].to_numpy(),
        df["TQQQ200일선"].to_numpy(),
        df["SPY종가"].to_numpy(),
        df["SPY200일선"].to_numpy(),
        params,
    )
    return pd.Series(weights, index=df.index), pd.Series(codes, index=df.index)


def _simulate_equity(price_df: pd.DataFrame, weight: pd.Series, one_way_bps: float, initial_krw: float) -> tuple[pd.Series, pd.Series, float]:
    ref = _load_module(Path("ops/scripts/run_reference_backtest.py"), "run_reference_backtest")
    idx_df = price_df.copy().set_index("time")
    fx = pd.Series(1300.0, index=idx_df.index)
    eq_pre, eq_after, ledger = ref.simulate_portfolio(
        prices_usd=idx_df["TQQQ종가"],
        fx_krw_per_usd=fx,
        target_weight=weight.set_axis(idx_df.index),
        initial_capital_krw=initial_krw,
        cost_oneway=one_way_bps / 10000.0,
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )
    total_tax = float(ledger[ledger["year"].notna()]["tax_paid_krw"].sum()) if "year" in ledger.columns else 0.0
    return eq_pre, eq_after, total_tax


def evaluate_candidate(
    data_csv: Path,
    candidate: Phase2Params,
    one_way_bps: float = 5.0,
    initial_krw: float = 100_000_000,
    mdd_gate: float = -0.50,
    oos_gate: float = 0.70,
) -> dict:
    df = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    w, _codes = _compute_signal(df, candidate)

    pre, after, tax = _simulate_equity(df[["time", "TQQQ종가"]], w, one_way_bps, initial_krw)

    all_df = pd.DataFrame({"time": df["time"], "eq_pre": pre.values, "eq_after": after.values})
    is_df, oos_df = split_is_oos(all_df, oos_ratio=0.3)

    is_cagr = cagr_from_equity(is_df["eq_after"].reset_index(drop=True))
    oos_cagr = cagr_from_equity(oos_df["eq_after"].reset_index(drop=True))
    oos = passes_oos_retention(is_cagr, oos_cagr, threshold=oos_gate)

    pretax_cagr = cagr_from_equity(all_df["eq_pre"].reset_index(drop=True))
    aftertax_cagr = cagr_from_equity(all_df["eq_after"].reset_index(drop=True))
    pretax_mdd = float((all_df["eq_pre"] / all_df["eq_pre"].cummax() - 1).min())

    return {
        "params_json": json.dumps(asdict(candidate), ensure_ascii=False, sort_keys=True),
        "pretax_cagr": pretax_cagr,
        "aftertax_cagr": aftertax_cagr,
        "pretax_mdd": pretax_mdd,
        "mdd_pass": pretax_mdd >= mdd_gate,
        "is_aftertax_cagr": is_cagr,
        "oos_aftertax_cagr": oos_cagr,
        "oos_retention": oos.retention,
        "oos_pass": oos.passed,
        "total_tax_paid_krw": tax,
        "rows": int(len(df)),
    }
