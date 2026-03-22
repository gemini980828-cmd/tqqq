from __future__ import annotations

import pandas as pd

from tqqq_strategy.experiments.upgrade_experiments import (
    apply_overheat_reserve,
    apply_reentry_ramp,
    rank_candidates,
)


def test_apply_reentry_ramp_caps_first_high_day_only() -> None:
    weight = pd.Series([0.0, 1.0, 1.0, 0.1], dtype=float)

    out = apply_reentry_ramp(weight, entry_floor=0.8, prior_cap=0.1, first_day_cap=0.8)

    assert out.tolist() == [0.0, 0.8, 1.0, 0.1]


def test_apply_overheat_reserve_caps_only_extreme_high_exposure_days() -> None:
    weight = pd.Series([0.95, 1.0, 0.90], dtype=float)
    dist200 = pd.Series([117.0, 118.0, 125.0], dtype=float)

    out = apply_overheat_reserve(weight, dist200, min_weight=0.95, dist_threshold=118.0, reserve_cap=0.98)

    assert out.tolist() == [0.95, 0.98, 0.90]


def test_rank_candidates_prefers_mdd_improvement_without_cagr_harm() -> None:
    candidates = pd.DataFrame(
        [
            {"name": "bad_cagr", "aftertax_cagr": 0.37, "pretax_mdd": -0.39, "oos_pass": True, "oos_retention": 0.75},
            {"name": "strict_winner", "aftertax_cagr": 0.39, "pretax_mdd": -0.39, "oos_pass": True, "oos_retention": 0.71},
            {"name": "mdd_worse", "aftertax_cagr": 0.40, "pretax_mdd": -0.42, "oos_pass": True, "oos_retention": 0.80},
        ]
    )

    ranked = rank_candidates(candidates, baseline_aftertax_cagr=0.385, baseline_pretax_mdd=-0.40)

    assert ranked.iloc[0]["name"] == "strict_winner"
    assert bool(ranked.iloc[0]["strict_pass"]) is True
    assert bool(ranked.loc[ranked["name"] == "bad_cagr", "strict_pass"].iloc[0]) is False
    assert bool(ranked.loc[ranked["name"] == "mdd_worse", "strict_pass"].iloc[0]) is False
