from tqqq_strategy.experiments.phase2_config import Phase2Params, validate_candidate


def test_validate_candidate_rejects_bad_hysteresis() -> None:
    p = Phase2Params(
        vol_threshold=0.059,
        dist200_enter=100.0,
        dist200_exit=100.1,
        slope_thr=0.11,
        tp10_trigger=0.10,
        tp10_cap=0.95,
        overheat1_enter=139.0,
        overheat2_enter=146.0,
        overheat3_enter=149.0,
        overheat4_enter=151.0,
    )
    ok, errs = validate_candidate(p)
    assert not ok
    assert any("dist200_enter" in e for e in errs)
