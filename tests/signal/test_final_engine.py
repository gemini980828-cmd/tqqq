from __future__ import annotations

import json

import numpy as np
import pandas as pd

from tqqq_strategy.signal.final_engine import (
    DEFAULT_DIST_CAP,
    FINAL_RUNTIME_SIGNAL_PATH,
    STRATEGY_NAME,
    SoftOverheatOverlay,
    build_final_signal_frame,
    compute_final_signal_table,
    split_residual,
)


def test_build_final_signal_frame_has_no_overlay_by_default() -> None:
    time = pd.to_datetime(["2026-03-03", "2026-03-04", "2026-03-05"])
    base_weight = pd.Series([1.0, 1.0, 0.97])
    dist200 = pd.Series([128.5, 135.0, 140.0])

    frame = build_final_signal_frame(time=time, base_weight=base_weight, dist200=dist200)

    assert frame["S2_weight"].tolist() == [1.0, 1.0, 0.97]
    assert frame["buffer_active"].tolist() == [False, False, False]


def test_build_final_signal_frame_legacy_overlay_still_uses_129_enter_123_exit() -> None:
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
    assert frame["buffer_active"].tolist() == [False, True, True, False]


def test_split_residual_is_sgov75_gld25_of_one_minus_tqqq() -> None:
    sgov, gld = split_residual(pd.Series([1.0, 0.97, 0.10, 0.0]))

    assert sgov.tolist() == [0.0, 0.0225, 0.675, 0.75]
    assert gld.tolist() == [0.0, 0.0075, 0.225, 0.25]


def test_build_final_signal_frame_adds_sgov_gld_columns_and_keeps_legacy_ones() -> None:
    frame = build_final_signal_frame(
        time=pd.to_datetime(["2026-03-03", "2026-03-04"]),
        base_weight=pd.Series([0.0, 0.97]),
        dist200=pd.Series([95.0, 110.0]),
    )

    for col in ("time", "S2_code", "S2_weight", "base_weight", "buffer_active", "dist200", "sgov_weight", "gld_weight"):
        assert col in frame.columns
    assert frame["sgov_weight"].tolist() == [0.75, 0.0225]
    assert frame["gld_weight"].tolist() == [0.25, 0.0075]
    assert np.allclose(frame["S2_weight"] + frame["sgov_weight"] + frame["gld_weight"], 1.0)


def _synthetic_market(n: int = 420, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    qqq = 100.0 * np.exp(np.cumsum(rng.normal(0.0006, 0.01, n)))
    spy = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.008, n)))
    tqqq = 50.0 * np.exp(np.cumsum(3.0 * rng.normal(0.0006, 0.01, n)))
    return pd.DataFrame(
        {
            "time": pd.bdate_range("2024-01-01", periods=n),
            "QQQ종가": qqq,
            "TQQQ종가": tqqq,
            "SPY종가": spy,
        }
    )


def test_compute_final_signal_table_uses_b0_dz_params_without_overlay() -> None:
    table = compute_final_signal_table(_synthetic_market())

    assert DEFAULT_DIST_CAP == 101.19
    params = json.loads(table["phase2_params_json"].iloc[0])
    assert params["dist_cap"] == 101.19
    assert params["dist200_enter"] == 101.19
    assert params["tp10_cap"] == 0.97
    assert table["overlay_json"].iloc[0] == "null"
    assert not table["buffer_active"].any()
    assert (table["S2_weight"] == table["base_weight"]).all()
    assert table["strategy_name"].iloc[0] == STRATEGY_NAME == "B0_DZ + G1 (SGOV75/GLD25)"
    assert np.allclose(table["S2_weight"] + table["sgov_weight"] + table["gld_weight"], 1.0)


def test_final_runtime_signal_path_points_to_promoted_engine_report() -> None:
    assert str(FINAL_RUNTIME_SIGNAL_PATH) == "reports/signals_core_strategy_final.csv"
