from __future__ import annotations

import pandas as pd

from tqqq_strategy.experiments.overlay_candidates import (
    SoftOverheatOverlay,
    apply_soft_overheat_buffer,
    slice_aligned_weight,
)


def test_soft_overheat_buffer_caps_high_exposure_until_exit() -> None:
    base_weight = pd.Series([0.95, 1.0, 1.0, 0.95, 0.95])
    dist200 = pd.Series([125.0, 126.5, 127.0, 124.0, 122.5])

    adjusted = apply_soft_overheat_buffer(
        base_weight,
        dist200,
        SoftOverheatOverlay(enter_dist=126.0, exit_dist=123.0, cap_weight=0.90),
    )

    assert adjusted.tolist() == [0.95, 0.90, 0.90, 0.90, 0.95]


def test_soft_overheat_buffer_ignores_low_risk_weights() -> None:
    base_weight = pd.Series([0.10, 0.80, 0.90, 0.95])
    dist200 = pd.Series([140.0, 140.0, 140.0, 140.0])

    adjusted = apply_soft_overheat_buffer(
        base_weight,
        dist200,
        SoftOverheatOverlay(enter_dist=126.0, exit_dist=123.0, cap_weight=0.90),
    )

    assert adjusted.tolist() == [0.10, 0.80, 0.90, 0.90]


def test_slice_aligned_weight_keeps_window_row_order() -> None:
    weight = pd.Series([0.1, 0.2, 0.3, 0.4])
    mask = pd.Series([False, True, False, True])

    sliced = slice_aligned_weight(weight, mask)

    assert sliced.tolist() == [0.2, 0.4]
    assert sliced.index.tolist() == [0, 1]
