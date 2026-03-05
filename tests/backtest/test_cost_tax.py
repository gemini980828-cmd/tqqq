from tqqq_strategy.backtest.tax_kr import apply_korean_overseas_tax


def test_apply_korean_overseas_tax_zero_at_deduction() -> None:
    assert apply_korean_overseas_tax(2_500_000) == 0.0


def test_apply_korean_overseas_tax_applies_22pct_over_deduction() -> None:
    assert apply_korean_overseas_tax(3_000_000) == 110_000.0
