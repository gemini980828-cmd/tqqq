from tqqq_strategy.experiments.phase2_oos import passes_oos_retention


def test_oos_retention_pass_when_ratio_above_threshold() -> None:
    r = passes_oos_retention(0.20, 0.16, threshold=0.70)
    assert r.passed
    assert r.retention >= 0.70
