from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tqqq_strategy.experiments.overlay_candidates import (  # noqa: E402
    SoftOverheatOverlay,
    apply_soft_overheat_buffer,
    slice_aligned_weight,
)
from tqqq_strategy.experiments.phase2_config import Phase2Params  # noqa: E402
from tqqq_strategy.experiments.phase2_runner import _compute_signal  # noqa: E402

sys.path.append(str(ROOT / "ops" / "scripts"))
import run_reference_backtest as ref  # noqa: E402


def cagr(eq: pd.Series) -> float:
    years = len(eq) / 252
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1) if years > 0 else 0.0


def mdd(eq: pd.Series) -> float:
    return float((eq / eq.cummax() - 1).min())


def simulate_metrics(
    df: pd.DataFrame,
    weight: pd.Series,
    one_way_bps: float,
    initial_krw: float,
) -> tuple[dict[str, float | bool], pd.Series, pd.Series]:
    idx = df["time"]
    fx = pd.Series(1300.0, index=idx)
    eq_pre, eq_after, ledger = ref.simulate_portfolio(
        prices_usd=df["TQQQ종가"].astype(float).set_axis(idx),
        fx_krw_per_usd=fx,
        target_weight=pd.Series(weight.values, index=idx),
        initial_capital_krw=initial_krw,
        cost_oneway=one_way_bps / 10000.0,
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )

    cut = int(len(eq_after) * 0.7)
    is_eq = eq_after.iloc[:cut].reset_index(drop=True)
    oos_eq = eq_after.iloc[cut:].reset_index(drop=True)
    is_cagr = cagr(is_eq)
    oos_cagr = cagr(oos_eq)
    retention = 0.0 if is_cagr <= 0 else oos_cagr / is_cagr

    turnover_units = float(weight.diff().abs().fillna(weight.iloc[0]).sum())
    total_tax_paid_krw = float(ledger[ledger["year"].notna()]["tax_paid_krw"].sum()) if "year" in ledger.columns else 0.0

    return (
        {
            "pretax_cagr": cagr(eq_pre),
            "aftertax_cagr": cagr(eq_after),
            "pretax_mdd": mdd(eq_pre),
            "aftertax_mdd": mdd(eq_after),
            "is_aftertax_cagr": is_cagr,
            "oos_aftertax_cagr": oos_cagr,
            "oos_retention": retention,
            "oos_pass": retention >= 0.70,
            "turnover_units": turnover_units,
            "total_tax_paid_krw": total_tax_paid_krw,
        },
        eq_pre,
        eq_after,
    )


def load_phase2_best_signal(data: pd.DataFrame, best_path: Path) -> pd.Series:
    best = json.loads(best_path.read_text(encoding="utf-8"))
    params = Phase2Params(**json.loads(best["params_json"]))
    weight, _codes = _compute_signal(data.reset_index(drop=True), params)
    return weight.astype(float)


def evaluate_trials(
    data: pd.DataFrame,
    orig_weight: pd.Series,
    phase2_weight: pd.Series,
    one_way_bps: float,
    initial_krw: float,
) -> tuple[pd.DataFrame, dict[str, float | bool], dict[str, float | bool]]:
    orig_metrics, _, _ = simulate_metrics(data, orig_weight, one_way_bps, initial_krw)
    phase2_metrics, _, _ = simulate_metrics(data, phase2_weight, one_way_bps, initial_krw)

    rows: list[dict[str, float | bool | str | int]] = []
    for enter in [126.0, 127.0, 128.0, 129.0, 130.0]:
        for exit_ in [120.0, 121.0, 122.0, 123.0]:
            if enter <= exit_:
                continue
            for cap in [0.90, 0.925, 0.95]:
                overlay = SoftOverheatOverlay(enter_dist=enter, exit_dist=exit_, cap_weight=cap)
                adjusted = apply_soft_overheat_buffer(
                    phase2_weight,
                    data["TQQQ200일 이격도"],
                    overlay,
                )
                metrics, _eq_pre, _eq_after = simulate_metrics(data, adjusted, one_way_bps, initial_krw)
                rows.append(
                    {
                        "overlay_type": "soft_overheat_buffer",
                        "overlay_json": json.dumps(asdict(overlay), ensure_ascii=False, sort_keys=True),
                        "active_days": int((adjusted < phase2_weight).sum()),
                        **metrics,
                        "delta_aftertax_cagr_vs_orig": float(metrics["aftertax_cagr"] - orig_metrics["aftertax_cagr"]),
                        "delta_pretax_mdd_vs_orig": float(metrics["pretax_mdd"] - orig_metrics["pretax_mdd"]),
                        "delta_aftertax_mdd_vs_orig": float(metrics["aftertax_mdd"] - orig_metrics["aftertax_mdd"]),
                        "delta_aftertax_cagr_vs_phase2": float(metrics["aftertax_cagr"] - phase2_metrics["aftertax_cagr"]),
                        "delta_pretax_mdd_vs_phase2": float(metrics["pretax_mdd"] - phase2_metrics["pretax_mdd"]),
                    }
                )

    return pd.DataFrame(rows), orig_metrics, phase2_metrics


def build_weight(
    phase2_weight: pd.Series,
    dist200: pd.Series,
    overlay: SoftOverheatOverlay,
) -> pd.Series:
    return apply_soft_overheat_buffer(phase2_weight, dist200, overlay)


def window_comparison(
    data: pd.DataFrame,
    orig_weight: pd.Series,
    candidate_weight: pd.Series,
    one_way_bps: float,
    initial_krw: float,
) -> pd.DataFrame:
    windows = [
        ("2011-2014", "2011-06-23", "2014-12-31"),
        ("2015-2018", "2015-01-01", "2018-12-31"),
        ("2019-2022", "2019-01-01", "2022-12-31"),
        ("2023-2026", "2023-01-01", "2026-01-30"),
        ("FULL", "2011-06-23", "2026-01-30"),
    ]
    rows: list[dict[str, float | str]] = []
    for label, start, end in windows:
        mask = (data["time"] >= start) & (data["time"] <= end)
        sub = data[mask].copy().reset_index(drop=True)
        sub_orig = slice_aligned_weight(orig_weight, mask)
        sub_cand = slice_aligned_weight(candidate_weight, mask)
        orig_metrics, _, _ = simulate_metrics(sub, sub_orig, one_way_bps, initial_krw)
        cand_metrics, _, _ = simulate_metrics(sub, sub_cand, one_way_bps, initial_krw)
        rows.append(
            {
                "window": label,
                "orig_aftertax_cagr": float(orig_metrics["aftertax_cagr"]),
                "cand_aftertax_cagr": float(cand_metrics["aftertax_cagr"]),
                "delta_aftertax_cagr": float(cand_metrics["aftertax_cagr"] - orig_metrics["aftertax_cagr"]),
                "orig_pretax_mdd": float(orig_metrics["pretax_mdd"]),
                "cand_pretax_mdd": float(cand_metrics["pretax_mdd"]),
                "delta_pretax_mdd": float(cand_metrics["pretax_mdd"] - orig_metrics["pretax_mdd"]),
            }
        )
    return pd.DataFrame(rows)


def cost_sensitivity(
    data: pd.DataFrame,
    orig_weight: pd.Series,
    candidate_weight: pd.Series,
    initial_krw: float,
) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    for bps in [3.0, 5.0, 7.0, 10.0, 15.0]:
        orig_metrics, _, _ = simulate_metrics(data, orig_weight, bps, initial_krw)
        cand_metrics, _, _ = simulate_metrics(data, candidate_weight, bps, initial_krw)
        rows.append(
            {
                "one_way_bps": bps,
                "orig_aftertax_cagr": float(orig_metrics["aftertax_cagr"]),
                "cand_aftertax_cagr": float(cand_metrics["aftertax_cagr"]),
                "delta_aftertax_cagr": float(cand_metrics["aftertax_cagr"] - orig_metrics["aftertax_cagr"]),
                "orig_pretax_mdd": float(orig_metrics["pretax_mdd"]),
                "cand_pretax_mdd": float(cand_metrics["pretax_mdd"]),
                "delta_pretax_mdd": float(cand_metrics["pretax_mdd"] - orig_metrics["pretax_mdd"]),
            }
        )
    return pd.DataFrame(rows)


def main(data_csv: Path, signal_csv: Path, best_config: Path, out_dir: Path, one_way_bps: float, initial_krw: float) -> None:
    data = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    signal = pd.read_csv(signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    orig_weight = signal["S2_weight"].astype(float)
    phase2_weight = load_phase2_best_signal(data, best_config)

    trials, orig_metrics, phase2_metrics = evaluate_trials(data, orig_weight, phase2_weight, one_way_bps, initial_krw)
    winners = trials[
        (trials["delta_aftertax_cagr_vs_orig"] >= 0.0)
        & (trials["delta_pretax_mdd_vs_orig"] > 0.0)
        & (trials["oos_pass"])
    ].copy()
    winners = winners.sort_values(["delta_pretax_mdd_vs_orig", "delta_aftertax_cagr_vs_orig"], ascending=[False, False])

    out_dir.mkdir(parents=True, exist_ok=True)
    trials.to_csv(out_dir / "overlay_improvement_trials.csv", index=False)
    winners.to_csv(out_dir / "overlay_improvement_winners.csv", index=False)

    summary: dict[str, object] = {
        "baseline_original": orig_metrics,
        "baseline_phase2_best": phase2_metrics,
        "winner_count": int(len(winners)),
    }

    if len(winners) == 0:
        best_payload = {"status": "baseline_keep", "reason": "no overlay passed full gates"}
        (out_dir / "overlay_improvement_best.json").write_text(json.dumps(best_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "overlay_improvement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(best_payload, ensure_ascii=False, indent=2))
        return

    best_row = winners.iloc[0].to_dict()
    overlay = SoftOverheatOverlay(**json.loads(best_row["overlay_json"]))
    candidate_weight = build_weight(phase2_weight, data["TQQQ200일 이격도"], overlay)
    pd.DataFrame({"time": data["time"], "S2_weight": candidate_weight}).to_csv(out_dir / "overlay_best_signal.csv", index=False)

    cost_df = cost_sensitivity(data, orig_weight, candidate_weight, initial_krw)
    cost_df.to_csv(out_dir / "overlay_best_cost_sensitivity.csv", index=False)

    window_df = window_comparison(data, orig_weight, candidate_weight, one_way_bps, initial_krw)
    window_df.to_csv(out_dir / "overlay_best_window_comparison.csv", index=False)

    summary["selected_overlay"] = best_row
    summary["cost_sensitivity_file"] = str(out_dir / "overlay_best_cost_sensitivity.csv")
    summary["window_comparison_file"] = str(out_dir / "overlay_best_window_comparison.csv")

    (out_dir / "overlay_improvement_best.json").write_text(json.dumps(best_row, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "overlay_improvement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("saved:", out_dir / "overlay_improvement_trials.csv")
    print("saved:", out_dir / "overlay_improvement_winners.csv")
    print("saved:", out_dir / "overlay_improvement_best.json")
    print("saved:", out_dir / "overlay_best_signal.csv")
    print("saved:", out_dir / "overlay_best_cost_sensitivity.csv")
    print("saved:", out_dir / "overlay_best_window_comparison.csv")
    print(json.dumps(best_row, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", type=Path, default=Path("data/user_input.csv"))
    ap.add_argument("--signal-csv", type=Path, default=Path("reports/signals_s1_s2_s3_user_original.csv"))
    ap.add_argument("--best-config", type=Path, default=Path("experiments/best_config.json"))
    ap.add_argument("--out-dir", type=Path, default=Path("experiments"))
    ap.add_argument("--one-way-bps", type=float, default=5.0)
    ap.add_argument("--initial-krw", type=float, default=100_000_000.0)
    args = ap.parse_args()
    main(args.data_csv, args.signal_csv, args.best_config, args.out_dir, args.one_way_bps, args.initial_krw)
