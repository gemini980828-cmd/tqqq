from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from tqqq_strategy.experiments.phase2_oos import cagr_from_equity, passes_oos_retention
from tqqq_strategy.experiments.phase2_runner import _simulate_equity
from tqqq_strategy.experiments.tqqq_uplift import (
    apply_overheat_buffer,
    apply_reentry_ramp,
    select_strict_candidates,
    summarize_selection,
)


DATA_CSV = Path("data/user_input.csv")
SIGNAL_CSV = Path("reports/signals_s1_s2_s3_user_original.csv")
PHASE2_TRIALS_CSV = Path("experiments/trials_all.csv")
OUT_DIR = Path("experiments")


def evaluate_weight_series(price_df: pd.DataFrame, weights: pd.Series, *, one_way_bps: float = 5.0, initial_krw: float = 100_000_000) -> dict:
    eq_pre, eq_after, total_tax = _simulate_equity(price_df[["time", "TQQQ종가"]], weights.reset_index(drop=True), one_way_bps, initial_krw)
    all_df = pd.DataFrame({"time": price_df["time"], "eq_pre": eq_pre.values, "eq_after": eq_after.values})
    is_df, oos_df = all_df.iloc[: int(len(all_df) * 0.7)], all_df.iloc[int(len(all_df) * 0.7) :]
    is_cagr = cagr_from_equity(is_df["eq_after"].reset_index(drop=True))
    oos_cagr = cagr_from_equity(oos_df["eq_after"].reset_index(drop=True))
    oos = passes_oos_retention(is_cagr, oos_cagr, threshold=0.70)
    return {
        "pretax_cagr": cagr_from_equity(all_df["eq_pre"].reset_index(drop=True)),
        "aftertax_cagr": cagr_from_equity(all_df["eq_after"].reset_index(drop=True)),
        "pretax_mdd": float((all_df["eq_pre"] / all_df["eq_pre"].cummax() - 1).min()),
        "aftertax_mdd": float((all_df["eq_after"] / all_df["eq_after"].cummax() - 1).min()),
        "is_aftertax_cagr": is_cagr,
        "oos_aftertax_cagr": oos_cagr,
        "oos_retention": oos.retention,
        "oos_pass": oos.passed,
        "total_tax_paid_krw": total_tax,
        "rows": int(len(all_df)),
        "turnover": float(weights.fillna(0.0).diff().abs().sum()),
    }


def build_overlay_trials(merged: pd.DataFrame) -> pd.DataFrame:
    baseline = merged["S2_weight"].astype(float)
    dist200 = merged["TQQQ200일 이격도"].astype(float)
    rows: list[dict] = []

    for hold_days in [2, 3, 5]:
        for cap_weight in [0.80, 0.90, 0.95]:
            for min_cash_days in [3, 5]:
                weight = apply_reentry_ramp(
                    baseline,
                    hold_days=hold_days,
                    cap_weight=cap_weight,
                    min_cash_days=min_cash_days,
                )
                row = evaluate_weight_series(merged, weight)
                row.update(
                    {
                        "family": "reentry_ramp",
                        "candidate_id": f"reentry_ramp:d{hold_days}:cap{cap_weight:.2f}:cash{min_cash_days}",
                        "params_json": json.dumps(
                            {
                                "hold_days": hold_days,
                                "cap_weight": cap_weight,
                                "min_cash_days": min_cash_days,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )
                rows.append(row)

    for enter_dist in [148.0, 150.0, 152.0]:
        for exit_dist in [140.0, 145.0]:
            if exit_dist >= enter_dist:
                continue
            for trim_to in [0.90, 0.95]:
                weight = apply_overheat_buffer(
                    baseline,
                    dist200,
                    enter_dist=enter_dist,
                    exit_dist=exit_dist,
                    trim_to=trim_to,
                )
                row = evaluate_weight_series(merged, weight)
                row.update(
                    {
                        "family": "overheat_buffer",
                        "candidate_id": f"overheat_buffer:e{enter_dist:.0f}:x{exit_dist:.0f}:trim{trim_to:.2f}",
                        "params_json": json.dumps(
                            {
                                "enter_dist": enter_dist,
                                "exit_dist": exit_dist,
                                "trim_to": trim_to,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        ),
                    }
                )
                rows.append(row)

    return pd.DataFrame(rows)


def load_phase2_trials() -> pd.DataFrame:
    if not PHASE2_TRIALS_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(PHASE2_TRIALS_CSV)
    keep = [
        "params_json",
        "pretax_cagr",
        "aftertax_cagr",
        "pretax_mdd",
        "mdd_pass",
        "is_aftertax_cagr",
        "oos_aftertax_cagr",
        "oos_retention",
        "oos_pass",
        "total_tax_paid_krw",
        "rows",
        "trial_id",
    ]
    out = df[keep].copy()
    out["family"] = "phase2_core"
    out["candidate_id"] = out["trial_id"].fillna("phase2")
    out["turnover"] = float("nan")
    return out


def main() -> None:
    merged = (
        pd.read_csv(DATA_CSV, parse_dates=["time"])
        .merge(pd.read_csv(SIGNAL_CSV, parse_dates=["time"])[["time", "S2_weight"]], on="time", how="inner")
        .sort_values("time")
        .reset_index(drop=True)
    )

    baseline_metrics = evaluate_weight_series(merged, merged["S2_weight"].astype(float))
    baseline_row = {
        "family": "baseline",
        "candidate_id": "baseline_s2",
        "params_json": "{}",
        **baseline_metrics,
    }

    overlay_trials = build_overlay_trials(merged)
    phase2_trials = load_phase2_trials()
    all_trials = pd.concat([phase2_trials, overlay_trials], ignore_index=True)
    all_trials["baseline_aftertax_cagr"] = baseline_row["aftertax_cagr"]
    all_trials["baseline_pretax_mdd"] = baseline_row["pretax_mdd"]
    all_trials["delta_cagr"] = all_trials["aftertax_cagr"] - baseline_row["aftertax_cagr"]
    all_trials["delta_mdd"] = all_trials["pretax_mdd"] - baseline_row["pretax_mdd"]
    all_trials["strict_pass"] = (
        (all_trials["aftertax_cagr"] >= baseline_row["aftertax_cagr"])
        & (all_trials["pretax_mdd"] >= baseline_row["pretax_mdd"])
        & all_trials["oos_pass"].fillna(False).astype(bool)
    )

    passed = select_strict_candidates(
        all_trials,
        baseline_aftertax_cagr=baseline_row["aftertax_cagr"],
        baseline_pretax_mdd=baseline_row["pretax_mdd"],
    )
    summary = summarize_selection(
        all_trials,
        baseline_aftertax_cagr=baseline_row["aftertax_cagr"],
        baseline_pretax_mdd=baseline_row["pretax_mdd"],
    )
    summary["baseline"] = baseline_row
    summary["families"] = (
        all_trials.groupby("family")["candidate_id"]
        .count()
        .rename("candidate_count")
        .reset_index()
        .to_dict(orient="records")
    )

    OUT_DIR.mkdir(exist_ok=True)
    all_trials.to_csv(OUT_DIR / "tqqq_uplift_trials.csv", index=False)
    passed.to_csv(OUT_DIR / "tqqq_uplift_passed.csv", index=False)
    (OUT_DIR / "tqqq_uplift_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(pd.DataFrame([baseline_row]).to_string(index=False))
    print(f"saved: {OUT_DIR / 'tqqq_uplift_trials.csv'}")
    print(f"saved: {OUT_DIR / 'tqqq_uplift_passed.csv'}")
    print(f"saved: {OUT_DIR / 'tqqq_uplift_summary.json'}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
