from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from tqqq_strategy.experiments.phase2_config import Phase2Params, coarse_grid, fine_grid
from tqqq_strategy.experiments.phase2_oos import cagr_from_equity, passes_oos_retention, split_is_oos
from tqqq_strategy.experiments.phase2_runner import _compute_signal, _simulate_equity, evaluate_candidate


def apply_reentry_ramp(
    weight: pd.Series,
    entry_floor: float = 0.8,
    prior_cap: float = 0.1,
    first_day_cap: float = 0.8,
) -> pd.Series:
    out = weight.astype(float).copy()
    if out.empty:
        return out
    for i in range(1, len(out)):
        if float(out.iloc[i - 1]) <= prior_cap and float(out.iloc[i]) >= entry_floor:
            out.iloc[i] = min(float(out.iloc[i]), first_day_cap)
    return out


def apply_cooldown_after_high_exit(
    weight: pd.Series,
    high_floor: float = 0.8,
    exit_cap: float = 0.1,
    cooldown_days: int = 1,
    reentry_cap: float = 0.5,
) -> pd.Series:
    out = weight.astype(float).copy()
    if out.empty:
        return out
    last_high_exit = -10_000
    prev = float(out.iloc[0])
    for i in range(1, len(out)):
        cur = float(out.iloc[i])
        if prev >= high_floor and cur <= exit_cap:
            last_high_exit = i
        if cur >= high_floor and (i - last_high_exit) <= cooldown_days:
            out.iloc[i] = min(cur, reentry_cap)
        prev = float(out.iloc[i])
    return out


def apply_overheat_reserve(
    weight: pd.Series,
    dist200: pd.Series,
    min_weight: float = 0.95,
    dist_threshold: float = 118.0,
    reserve_cap: float = 0.98,
) -> pd.Series:
    out = weight.astype(float).copy()
    mask = (out >= min_weight) & (dist200.astype(float) >= dist_threshold)
    out.loc[mask] = out.loc[mask].clip(upper=reserve_cap)
    return out


def evaluate_weight_candidate(
    *,
    name: str,
    family: str,
    data: pd.DataFrame,
    weight: pd.Series,
    initial_krw: float = 100_000_000,
    one_way_bps: float = 5.0,
) -> dict[str, float | str | bool]:
    weight = weight.astype(float).reset_index(drop=True)
    pre, after, tax = _simulate_equity(data[["time", "TQQQ종가"]], weight, one_way_bps, initial_krw)
    all_df = pd.DataFrame({"time": data["time"].values, "eq_pre": pre.values, "eq_after": after.values})
    is_df, oos_df = split_is_oos(all_df, oos_ratio=0.3)
    is_cagr = cagr_from_equity(is_df["eq_after"].reset_index(drop=True))
    oos_cagr = cagr_from_equity(oos_df["eq_after"].reset_index(drop=True))
    oos = passes_oos_retention(is_cagr, oos_cagr, threshold=0.70)
    turnover = float(weight.diff().abs().fillna(0.0).sum())
    return {
        "name": name,
        "family": family,
        "pretax_cagr": cagr_from_equity(all_df["eq_pre"].reset_index(drop=True)),
        "aftertax_cagr": cagr_from_equity(all_df["eq_after"].reset_index(drop=True)),
        "pretax_mdd": float((all_df["eq_pre"] / all_df["eq_pre"].cummax() - 1).min()),
        "aftertax_mdd": float((all_df["eq_after"] / all_df["eq_after"].cummax() - 1).min()),
        "is_aftertax_cagr": is_cagr,
        "oos_aftertax_cagr": oos_cagr,
        "oos_retention": oos.retention,
        "oos_pass": oos.passed,
        "total_tax_paid_krw": tax,
        "turnover": turnover,
        "rows": int(len(data)),
    }


def rank_candidates(
    candidates: pd.DataFrame,
    *,
    baseline_aftertax_cagr: float,
    baseline_pretax_mdd: float,
) -> pd.DataFrame:
    ranked = candidates.copy()
    ranked["delta_aftertax_cagr"] = ranked["aftertax_cagr"] - baseline_aftertax_cagr
    ranked["delta_pretax_mdd"] = ranked["pretax_mdd"] - baseline_pretax_mdd
    ranked["strict_pass"] = (ranked["delta_aftertax_cagr"] >= 0.0) & (ranked["delta_pretax_mdd"] > 0.0)
    ranked["strict_oos_pass"] = ranked["strict_pass"] & ranked["oos_pass"].fillna(False)
    ranked["near_miss"] = (ranked["delta_pretax_mdd"] > 0.0) | (ranked["delta_aftertax_cagr"] >= 0.0)
    ranked = ranked.sort_values(
        ["strict_oos_pass", "strict_pass", "delta_pretax_mdd", "delta_aftertax_cagr", "oos_retention"],
        ascending=[False, False, False, False, False],
    ).reset_index(drop=True)
    return ranked


def _load_baseline_signal(signal_csv: Path) -> pd.DataFrame:
    sig = pd.read_csv(signal_csv, parse_dates=["time"])
    return sig[["time", "S2_weight"]].rename(columns={"S2_weight": "weight"})


def _evaluate_phase2_family(data_csv: Path) -> pd.DataFrame:
    data = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    coarse_rows: list[dict] = []
    coarse_candidates = coarse_grid()
    for i, candidate in enumerate(coarse_candidates, start=1):
        weight, _codes = _compute_signal(data, candidate)
        row = evaluate_weight_candidate(
            name=f"A/coarse/{i:04d}",
            family="A",
            data=data,
            weight=weight,
        )
        row["params_json"] = json.dumps(asdict(candidate), ensure_ascii=False, sort_keys=True)
        gate_row = evaluate_candidate(data_csv, candidate)
        row["mdd_pass"] = gate_row["mdd_pass"]
        coarse_rows.append(row)

    coarse_df = pd.DataFrame(coarse_rows)
    top_seed_json = coarse_df.sort_values("aftertax_cagr", ascending=False).head(10)["params_json"].tolist()
    fine_seeds = [Phase2Params(**json.loads(raw)) for raw in top_seed_json]
    fine_rows: list[dict] = []
    for i, candidate in enumerate(fine_grid(fine_seeds), start=1):
        weight, _codes = _compute_signal(data, candidate)
        row = evaluate_weight_candidate(
            name=f"A/fine/{i:04d}",
            family="A",
            data=data,
            weight=weight,
        )
        row["params_json"] = json.dumps(asdict(candidate), ensure_ascii=False, sort_keys=True)
        gate_row = evaluate_candidate(data_csv, candidate)
        row["mdd_pass"] = gate_row["mdd_pass"]
        fine_rows.append(row)

    return pd.concat([coarse_df, pd.DataFrame(fine_rows)], ignore_index=True)


def run_upgrade_experiments(
    *,
    data_csv: Path,
    baseline_signal_csv: Path,
    out_dir: Path,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    base_sig = _load_baseline_signal(baseline_signal_csv)
    merged = data.merge(base_sig, on="time", how="inner").sort_values("time").reset_index(drop=True)
    baseline = evaluate_weight_candidate(name="baseline", family="baseline", data=merged, weight=merged["weight"])

    phase2_df = _evaluate_phase2_family(data_csv)
    top_phase2 = phase2_df.sort_values("aftertax_cagr", ascending=False).head(3)

    overlay_rows = [
        evaluate_weight_candidate(
            name="C/reentry_ramp_0.8",
            family="C",
            data=merged,
            weight=apply_reentry_ramp(merged["weight"], first_day_cap=0.8),
        ),
        evaluate_weight_candidate(
            name="C/cooldown_1d_cap_0.5",
            family="C",
            data=merged,
            weight=apply_cooldown_after_high_exit(merged["weight"], cooldown_days=1, reentry_cap=0.5),
        ),
        evaluate_weight_candidate(
            name="B/overheat_reserve_115_0.98",
            family="B",
            data=merged,
            weight=apply_overheat_reserve(merged["weight"], merged["TQQQ200일 이격도"], dist_threshold=115.0, reserve_cap=0.98),
        ),
        evaluate_weight_candidate(
            name="B/overheat_reserve_118_0.98",
            family="B",
            data=merged,
            weight=apply_overheat_reserve(merged["weight"], merged["TQQQ200일 이격도"], dist_threshold=118.0, reserve_cap=0.98),
        ),
    ]

    for _, row in top_phase2.iterrows():
        candidate = Phase2Params(**json.loads(row["params_json"]))
        weight, _codes = _compute_signal(data, candidate)
        seeded = data.copy()
        seeded["weight"] = weight.reset_index(drop=True)
        phase2_name = str(row["name"])
        overlay_rows.append(
            evaluate_weight_candidate(
                name=f"C/{phase2_name}/reentry_ramp_0.8",
                family="C-on-A",
                data=seeded,
                weight=apply_reentry_ramp(seeded["weight"], first_day_cap=0.8),
            )
        )
        overlay_rows.append(
            evaluate_weight_candidate(
                name=f"B/{phase2_name}/overheat_reserve_118_0.98",
                family="B-on-A",
                data=seeded,
                weight=apply_overheat_reserve(seeded["weight"], seeded["TQQQ200일 이격도"], dist_threshold=118.0, reserve_cap=0.98),
            )
        )

    candidates = pd.concat([pd.DataFrame([baseline]), phase2_df, pd.DataFrame(overlay_rows)], ignore_index=True)
    ranked = rank_candidates(
        candidates,
        baseline_aftertax_cagr=float(baseline["aftertax_cagr"]),
        baseline_pretax_mdd=float(baseline["pretax_mdd"]),
    )

    ranked.to_csv(out_dir / "upgrade_ranked.csv", index=False)
    candidates.to_csv(out_dir / "upgrade_candidates_raw.csv", index=False)

    strict_df = ranked[ranked["strict_pass"]].copy()
    strict_oos_df = ranked[ranked["strict_oos_pass"]].copy()
    summary = {
        "baseline": baseline,
        "strict_candidate_count": int(len(strict_df)),
        "strict_oos_candidate_count": int(len(strict_oos_df)),
        "best_overall": ranked.iloc[0].to_dict() if len(ranked) else None,
        "best_strict": strict_df.iloc[0].to_dict() if len(strict_df) else None,
        "best_strict_oos": strict_oos_df.iloc[0].to_dict() if len(strict_oos_df) else None,
        "family_counts": ranked["family"].value_counts().to_dict(),
    }
    (out_dir / "upgrade_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
