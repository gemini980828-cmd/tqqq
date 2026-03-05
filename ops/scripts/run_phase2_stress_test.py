from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tqqq_strategy.experiments.phase2_config import Phase2Params
from tqqq_strategy.experiments.phase2_oos import split_is_oos, cagr_from_equity, passes_oos_retention
from tqqq_strategy.experiments.phase2_runner import _compute_signal, _simulate_equity


def eval_on_df(df: pd.DataFrame, p: Phase2Params, one_way_bps: float = 5.0, initial_krw: float = 100_000_000) -> dict:
    w, _ = _compute_signal(df.reset_index(drop=True), p)
    pre, after, tax = _simulate_equity(df[["time", "TQQQ종가"]].reset_index(drop=True), w, one_way_bps, initial_krw)

    all_df = pd.DataFrame({"time": df["time"].values, "eq_pre": pre.values, "eq_after": after.values})
    is_df, oos_df = split_is_oos(all_df, oos_ratio=0.3)

    pretax_cagr = cagr_from_equity(all_df["eq_pre"].reset_index(drop=True))
    aftertax_cagr = cagr_from_equity(all_df["eq_after"].reset_index(drop=True))
    pretax_mdd = float((all_df["eq_pre"] / all_df["eq_pre"].cummax() - 1).min())

    is_cagr = cagr_from_equity(is_df["eq_after"].reset_index(drop=True))
    oos_cagr = cagr_from_equity(oos_df["eq_after"].reset_index(drop=True))
    oos = passes_oos_retention(is_cagr, oos_cagr, threshold=0.70)

    return {
        "pretax_cagr": pretax_cagr,
        "aftertax_cagr": aftertax_cagr,
        "pretax_mdd": pretax_mdd,
        "oos_retention": oos.retention,
        "oos_pass": oos.passed,
        "total_tax_paid_krw": tax,
        "rows": len(df),
    }


def main() -> None:
    data = pd.read_csv("data/user_input.csv", parse_dates=["time"]).sort_values("time").reset_index(drop=True)

    baseline = Phase2Params(
        vol_threshold=0.059,
        dist200_enter=101.00,
        dist200_exit=100.00,
        slope_thr=0.1100,
        tp10_trigger=0.10,
        tp10_cap=0.95,
        overheat1_enter=139.0,
        overheat2_enter=146.0,
        overheat3_enter=149.0,
        overheat4_enter=151.0,
    )

    best = json.loads(Path("experiments/best_config.json").read_text(encoding="utf-8"))
    best_p = Phase2Params(**json.loads(best["params_json"]))

    windows = [
        ("2011-2014", "2011-06-23", "2014-12-31"),
        ("2015-2018", "2015-01-01", "2018-12-31"),
        ("2019-2022", "2019-01-01", "2022-12-31"),
        ("2023-2026", "2023-01-01", "2026-01-30"),
        ("FULL", "2011-06-23", "2026-01-30"),
    ]

    rows = []
    for label, s, e in windows:
        sub = data[(data["time"] >= s) & (data["time"] <= e)].copy().reset_index(drop=True)
        if len(sub) < 260:
            continue
        b = eval_on_df(sub, baseline)
        x = eval_on_df(sub, best_p)
        rows.append({
            "window": label,
            "start": s,
            "end": e,
            "baseline_aftertax_cagr": b["aftertax_cagr"],
            "best_aftertax_cagr": x["aftertax_cagr"],
            "delta_aftertax_cagr": x["aftertax_cagr"] - b["aftertax_cagr"],
            "baseline_mdd": b["pretax_mdd"],
            "best_mdd": x["pretax_mdd"],
            "baseline_oos_pass": b["oos_pass"],
            "best_oos_pass": x["oos_pass"],
            "baseline_oos_retention": b["oos_retention"],
            "best_oos_retention": x["oos_retention"],
            "rows": len(sub),
        })

    out = pd.DataFrame(rows)
    Path("experiments").mkdir(exist_ok=True)
    out.to_csv("experiments/stress_test_windows.csv", index=False)

    robust_up = int((out["delta_aftertax_cagr"] > 0).sum())
    robust_down = int((out["delta_aftertax_cagr"] <= 0).sum())

    summary = {
        "windows": int(len(out)),
        "improved_windows": robust_up,
        "not_improved_windows": robust_down,
        "avg_delta_aftertax_cagr": float(out["delta_aftertax_cagr"].mean()),
        "min_delta_aftertax_cagr": float(out["delta_aftertax_cagr"].min()),
        "max_delta_aftertax_cagr": float(out["delta_aftertax_cagr"].max()),
    }
    Path("experiments/stress_test_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(out.to_string(index=False))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
