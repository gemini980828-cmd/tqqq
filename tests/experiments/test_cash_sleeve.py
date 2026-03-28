from __future__ import annotations

import pandas as pd
import sys

sys.path.append("ops/scripts")
import run_reference_backtest as ref

from tqqq_strategy.experiments.cash_sleeve import (
    build_daily_yield_series_from_annual_returns,
    build_parking_mask,
    simulate_with_taxed_cash_sleeve,
    CashSleeveConfig,
)


def test_build_parking_mask_immediate_switch() -> None:
    weight = pd.Series([1.0, 0.9, 0.9, 1.0, 0.8])

    mask = build_parking_mask(weight, threshold_days=0)

    assert mask.tolist() == [False, True, True, False, True]


def test_build_parking_mask_waits_until_threshold_is_met() -> None:
    weight = pd.Series([1.0, 0.9, 0.9, 0.9, 1.0, 0.8, 0.8])

    mask = build_parking_mask(weight, threshold_days=2)

    assert mask.tolist() == [False, False, True, True, False, False, True]


def test_build_daily_yield_series_from_annual_returns_respects_inception() -> None:
    dates = pd.to_datetime(["2020-05-20", "2020-05-26", "2020-12-31", "2021-01-04"])
    daily = build_daily_yield_series_from_annual_returns(
        pd.Series(dates),
        annual_returns={2020: 0.01, 2021: 0.02},
        inception_date="2020-05-26",
    )

    assert daily.iloc[0] == 0.0
    assert daily.iloc[1] > 0.0
    assert daily.iloc[2] > 0.0
    assert daily.iloc[3] > 0.0


def test_build_parking_mask_can_limit_to_full_cash_only() -> None:
    weight = pd.Series([1.0, 0.1, 0.0, 0.0, 0.9, 0.0])

    mask = build_parking_mask(weight, threshold_days=0, eligible_max_weight=0.0)

    assert mask.tolist() == [False, False, True, True, False, True]


def test_taxed_cash_sleeve_matches_reference_when_sleeve_disabled() -> None:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    prices_usd = pd.Series([10.0, 11.0, 10.5, 12.0], index=idx)
    fx = pd.Series([1300.0, 1300.0, 1300.0, 1300.0], index=idx)
    weight = pd.Series([0.0, 1.0, 0.0, 1.0], index=idx)

    ref_pre, ref_after, _ = ref.simulate_portfolio(
        prices_usd=prices_usd,
        fx_krw_per_usd=fx,
        target_weight=weight,
        initial_capital_krw=100_000_000.0,
        cost_oneway=0.0005,
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )

    pre, after, _ = simulate_with_taxed_cash_sleeve(
        prices_krw=prices_usd * fx,
        target_weight=weight,
        initial_capital_krw=100_000_000.0,
        tqqq_cost_oneway=0.0005,
        sleeve=CashSleeveConfig(threshold_days=9999, annual_yield=0.0, sleeve_cost_oneway=0.0),
        annual_deduction_krw=2_500_000.0,
        tax_rate=0.22,
    )

    assert pre.round(10).tolist() == ref_pre.round(10).tolist()
    assert after.round(10).tolist() == ref_after.round(10).tolist()
