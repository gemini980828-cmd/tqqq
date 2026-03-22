import pandas as pd

from tqqq_strategy.experiments.tqqq_uplift import (
    apply_overheat_buffer,
    apply_reentry_ramp,
    select_strict_candidates,
    summarize_selection,
)


def test_apply_reentry_ramp_caps_first_high_days_after_cash_spell() -> None:
    weights = pd.Series([0.0, 0.0, 0.0, 1.0, 0.95, 0.95, 0.1])

    got = apply_reentry_ramp(weights, hold_days=2, cap_weight=0.8, min_cash_days=3)

    assert got.tolist() == [0.0, 0.0, 0.0, 0.8, 0.8, 0.95, 0.1]


def test_apply_overheat_buffer_arms_and_releases_on_exit_threshold() -> None:
    weights = pd.Series([1.0, 1.0, 1.0, 1.0, 0.95])
    dist200 = pd.Series([140.0, 150.0, 149.0, 144.0, 143.0])

    got = apply_overheat_buffer(weights, dist200, enter_dist=150.0, exit_dist=145.0, trim_to=0.9)

    assert got.tolist() == [1.0, 0.9, 0.9, 1.0, 0.95]


def test_select_strict_candidates_filters_cagr_harm_and_sorts_mdd_first() -> None:
    trials = pd.DataFrame(
        [
            {"candidate_id": "best", "aftertax_cagr": 0.3865, "pretax_mdd": -0.39, "oos_pass": True},
            {"candidate_id": "worse_mdd", "aftertax_cagr": 0.39, "pretax_mdd": -0.41, "oos_pass": True},
            {"candidate_id": "cagr_harm", "aftertax_cagr": 0.38, "pretax_mdd": -0.38, "oos_pass": True},
            {"candidate_id": "oos_fail", "aftertax_cagr": 0.39, "pretax_mdd": -0.38, "oos_pass": False},
        ]
    )

    got = select_strict_candidates(trials, baseline_aftertax_cagr=0.3860, baseline_pretax_mdd=-0.4047)

    assert got["candidate_id"].tolist() == ["best"]


def test_summarize_selection_returns_near_miss_when_no_strict_pass() -> None:
    trials = pd.DataFrame(
        [
            {"candidate_id": "mdd_up_small_drag", "aftertax_cagr": 0.3855, "pretax_mdd": -0.4000, "oos_pass": True},
            {"candidate_id": "mdd_up_big_drag", "aftertax_cagr": 0.3800, "pretax_mdd": -0.3900, "oos_pass": True},
        ]
    )

    summary = summarize_selection(trials, baseline_aftertax_cagr=0.3860, baseline_pretax_mdd=-0.4047)

    assert summary["status"] == "baseline_keep"
    assert summary["near_miss"]["candidate_id"] == "mdd_up_small_drag"
