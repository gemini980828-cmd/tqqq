from __future__ import annotations

import argparse
from pathlib import Path

from tqqq_strategy.experiments.upgrade_experiments import run_upgrade_experiments


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-csv", type=Path, default=Path("data/user_input.csv"))
    ap.add_argument("--baseline-signal-csv", type=Path, default=Path("reports/signals_s1_s2_s3_user_original.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("experiments/upgrade"))
    args = ap.parse_args()

    summary = run_upgrade_experiments(
        data_csv=args.data_csv,
        baseline_signal_csv=args.baseline_signal_csv,
        out_dir=args.out_dir,
    )

    print("saved:", args.out_dir / "upgrade_candidates_raw.csv")
    print("saved:", args.out_dir / "upgrade_ranked.csv")
    print("saved:", args.out_dir / "upgrade_summary.json")
    print("strict_candidate_count:", summary["strict_candidate_count"])
    print("strict_oos_candidate_count:", summary["strict_oos_candidate_count"])
    print("best_overall:", summary["best_overall"]["name"] if summary["best_overall"] else None)
    print("best_strict:", summary["best_strict"]["name"] if summary["best_strict"] else None)
    print("best_strict_oos:", summary["best_strict_oos"]["name"] if summary["best_strict_oos"] else None)


if __name__ == "__main__":
    main()
