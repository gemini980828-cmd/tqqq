from __future__ import annotations

import pandas as pd

from tqqq_strategy.experiments.overlay_candidates import SoftOverheatOverlay
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH, build_final_signal_frame


def test_build_final_signal_frame_uses_129_entry_and_123_exit_hysteresis() -> None:
    time = pd.to_datetime(["2026-03-03", "2026-03-04", "2026-03-05", "2026-03-06"])
    base_weight = pd.Series([1.0, 1.0, 1.0, 1.0])
    dist200 = pd.Series([128.5, 129.1, 125.0, 122.5])

    frame = build_final_signal_frame(
        time=time,
        base_weight=base_weight,
        dist200=dist200,
        overlay=SoftOverheatOverlay(enter_dist=129.0, exit_dist=123.0, cap_weight=0.90),
    )

    assert frame["S2_weight"].tolist() == [1.0, 0.9, 0.9, 1.0]
    assert frame["S2_code"].tolist() == [2, 3, 3, 2]
    assert frame["buffer_active"].tolist() == [False, True, True, False]


def test_build_final_signal_frame_does_not_cap_sub_95pct_base_weights() -> None:
    time = pd.to_datetime(["2026-03-03", "2026-03-04"])
    base_weight = pd.Series([0.90, 0.95])
    dist200 = pd.Series([140.0, 128.0])

    frame = build_final_signal_frame(
        time=time,
        base_weight=base_weight,
        dist200=dist200,
        overlay=SoftOverheatOverlay(enter_dist=129.0, exit_dist=123.0, cap_weight=0.90),
    )

    assert frame["S2_weight"].tolist() == [0.90, 0.95]
    assert frame["buffer_active"].tolist() == [False, False]


def test_final_runtime_signal_path_points_to_promoted_engine_report() -> None:
    assert str(FINAL_RUNTIME_SIGNAL_PATH) == "reports/signals_core_strategy_final.csv"
