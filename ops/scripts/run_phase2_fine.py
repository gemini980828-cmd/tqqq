from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

from tqqq_strategy.experiments.phase2_config import Phase2Params, fine_grid
from tqqq_strategy.experiments.phase2_runner import evaluate_candidate


def main() -> None:
    coarse = pd.read_csv("experiments/trials.csv")
    top = coarse.sort_values("aftertax_cagr", ascending=False).head(10)
    seeds = [Phase2Params(**json.loads(x)) for x in top["params_json"].tolist()]
    candidates = fine_grid(seeds)

    rows = []
    for i, c in enumerate(candidates, 1):
        res = evaluate_candidate(Path("data/user_input.csv"), c)
        res["trial_id"] = f"fine_{i:04d}"
        rows.append(res)

    out = pd.DataFrame(rows)
    out.to_csv("experiments/trials_fine.csv", index=False)
    print(f"saved experiments/trials_fine.csv rows={len(out)}")


if __name__ == "__main__":
    main()
