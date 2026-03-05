from tqqq_strategy.experiments.wfo import passes_oos_gate


def test_passes_oos_gate_threshold() -> None:
    assert passes_oos_gate(is_score=1.0, oos_score=0.7)
    assert not passes_oos_gate(is_score=1.0, oos_score=0.69)


def test_passes_oos_gate_rejects_non_positive_is_score() -> None:
    assert not passes_oos_gate(is_score=0.0, oos_score=1.0)
    assert not passes_oos_gate(is_score=-1.0, oos_score=1.0)
