from __future__ import annotations

import json
from typing import Any

import pandas as pd


def apply_reentry_ramp(
    weights: pd.Series,
    *,
    hold_days: int,
    cap_weight: float,
    min_cash_days: int,
    cash_threshold: float = 0.10,
    trigger_weight: float = 0.95,
) -> pd.Series:
    out = weights.astype(float).copy()
    values = out.to_numpy(copy=True)
    i = 1
    while i < len(values):
        if values[i - 1] <= cash_threshold and values[i] >= trigger_weight:
            j = i - 1
            cash_days = 0
            while j >= 0 and values[j] <= cash_threshold:
                cash_days += 1
                j -= 1
            if cash_days >= min_cash_days:
                end = min(len(values), i + hold_days)
                for k in range(i, end):
                    if values[k] >= cap_weight:
                        values[k] = min(values[k], cap_weight)
                i = end
                continue
        i += 1
    return pd.Series(values, index=out.index, name=out.name)


def apply_overheat_buffer(
    weights: pd.Series,
    dist200: pd.Series,
    *,
    enter_dist: float,
    exit_dist: float,
    trim_to: float,
    min_base_weight: float = 0.95,
) -> pd.Series:
    out = weights.astype(float).copy()
    d = dist200.astype(float).reindex(out.index)
    armed = False
    values = out.to_numpy(copy=True)
    dist_values = d.to_numpy(copy=False)
    for i, weight in enumerate(values):
        dist = dist_values[i]
        if pd.notna(dist) and weight >= min_base_weight and dist >= enter_dist:
            armed = True
        elif armed and pd.notna(dist) and dist <= exit_dist:
            armed = False

        if armed and weight > trim_to:
            values[i] = trim_to
    return pd.Series(values, index=out.index, name=out.name)


def select_strict_candidates(
    trials: pd.DataFrame,
    *,
    baseline_aftertax_cagr: float,
    baseline_pretax_mdd: float,
) -> pd.DataFrame:
    if len(trials) == 0:
        return trials.copy()

    out = trials.copy()
    out["strict_pass"] = (
        (out["aftertax_cagr"] >= baseline_aftertax_cagr)
        & (out["pretax_mdd"] >= baseline_pretax_mdd)
        & out["oos_pass"].fillna(False).astype(bool)
    )
    passed = out[out["strict_pass"]].copy()
    if len(passed) == 0:
        return passed
    return passed.sort_values(["pretax_mdd", "aftertax_cagr"], ascending=[False, False]).reset_index(drop=True)


def summarize_selection(
    trials: pd.DataFrame,
    *,
    baseline_aftertax_cagr: float,
    baseline_pretax_mdd: float,
) -> dict[str, Any]:
    passed = select_strict_candidates(
        trials,
        baseline_aftertax_cagr=baseline_aftertax_cagr,
        baseline_pretax_mdd=baseline_pretax_mdd,
    )
    if len(passed) > 0:
        best = passed.iloc[0].to_dict()
        return {
            "status": "strict_pass",
            "selected": json.loads(json.dumps(best, default=str)),
            "strict_pass_count": int(len(passed)),
        }

    out = trials.copy()
    out["delta_cagr"] = out["aftertax_cagr"] - baseline_aftertax_cagr
    out["delta_mdd"] = out["pretax_mdd"] - baseline_pretax_mdd
    near = out[out["oos_pass"].fillna(False).astype(bool) & (out["delta_mdd"] > 0)].copy()
    if len(near) > 0:
        near = near.sort_values(["delta_cagr", "pretax_mdd"], ascending=[False, False]).reset_index(drop=True)
        near_miss = near.iloc[0].to_dict()
    else:
        near_miss = None

    return {
        "status": "baseline_keep",
        "reason": "no candidate satisfied strict MDD-first gate without harming CAGR",
        "strict_pass_count": 0,
        "near_miss": json.loads(json.dumps(near_miss, default=str)) if near_miss is not None else None,
    }
