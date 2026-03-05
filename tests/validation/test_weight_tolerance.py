from tqqq_strategy.validation.golden_diff import within_tolerance


def test_within_tolerance_true_within_boundary() -> None:
    assert within_tolerance(0.9500, 0.9491, tol=0.001) is True


def test_within_tolerance_true_at_exact_boundary() -> None:
    assert within_tolerance(1.0, 0.875, tol=0.125) is True


def test_within_tolerance_false_outside_boundary() -> None:
    assert within_tolerance(0.9500, 0.9488, tol=0.001) is False


def test_within_tolerance_uses_default_tolerance() -> None:
    assert within_tolerance(0.9500, 0.9491) is True
