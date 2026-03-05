from __future__ import annotations

import json
from pathlib import Path
import pandas as pd


def main() -> None:
    t1 = pd.read_csv("experiments/trials.csv")
    t2 = pd.read_csv("experiments/trials_fine.csv") if Path("experiments/trials_fine.csv").exists() else pd.DataFrame()
    all_trials = pd.concat([t1, t2], ignore_index=True)
    all_trials.to_csv("experiments/trials_all.csv", index=False)

    passed = all_trials[(all_trials["mdd_pass"]) & (all_trials["oos_pass"])].copy()
    passed = passed.sort_values(["aftertax_cagr", "pretax_mdd"], ascending=[False, False])
    passed.to_csv("experiments/passed_leaderboard.csv", index=False)

    best = None
    if len(passed) > 0:
        best = passed.iloc[0].to_dict()
    else:
        best = {
            "status": "baseline_keep",
            "reason": "no candidate passed hard gates",
        }

    Path("experiments").mkdir(exist_ok=True)
    Path("experiments/best_config.json").write_text(json.dumps(best, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved experiments/passed_leaderboard.csv")
    print("saved experiments/best_config.json")


if __name__ == "__main__":
    main()
