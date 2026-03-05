from __future__ import annotations

from pathlib import Path
import pandas as pd

from tqqq_strategy.experiments.phase2_config import coarse_grid
from tqqq_strategy.experiments.phase2_runner import evaluate_candidate


def main() -> None:
    candidates = coarse_grid()
    rows = []
    for i, c in enumerate(candidates, 1):
        res = evaluate_candidate(Path("data/user_input.csv"), c)
        res["trial_id"] = f"coarse_{i:04d}"
        rows.append(res)
        if i % 100 == 0:
            print(f"processed {i}/{len(candidates)}")

    out = pd.DataFrame(rows)
    Path("experiments").mkdir(exist_ok=True)
    out.to_csv("experiments/trials.csv", index=False)
    print(f"saved experiments/trials.csv rows={len(out)}")


if __name__ == "__main__":
    main()
