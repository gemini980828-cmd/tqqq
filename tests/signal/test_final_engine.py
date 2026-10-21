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
    split_allocation,
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


def test_split_allocation_is_90pct_signal_driven_plus_fixed_10pct_gld() -> None:
    tqqq, sgov, gld = split_allocation(pd.Series([1.0, 0.97, 0.10, 0.0]))

    assert tqqq.tolist() == [0.9, 0.873, 0.09, 0.0]
    assert sgov.tolist() == [0.0, 0.027, 0.81, 0.9]
    assert gld.tolist() == [0.1, 0.1, 0.1, 0.1]


def test_build_final_signal_frame_adds_allocation_columns_and_keeps_raw_signal() -> None:
    frame = build_final_signal_frame(
        time=pd.to_datetime(["2026-03-03", "2026-03-04"]),
        base_weight=pd.Series([0.0, 0.97]),
        dist200=pd.Series([95.0, 110.0]),
    )

    for col in ("time", "S2_code", "S2_weight", "base_weight", "buffer_active", "dist200", "tqqq_weight", "sgov_weight", "gld_weight"):
        assert col in frame.columns
    assert frame["S2_weight"].tolist() == [0.0, 0.97]  # raw signal p
    assert frame["tqqq_weight"].tolist() == [0.0, 0.873]
    assert frame["sgov_weight"].tolist() == [0.9, 0.027]
    assert frame["gld_weight"].tolist() == [0.1, 0.1]
    assert np.allclose(frame["tqqq_weight"] + frame["sgov_weight"] + frame["gld_weight"], 1.0)


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
    assert table["strategy_name"].iloc[0] == STRATEGY_NAME == "B0_DZ 90% + GLD 10%"
    assert np.allclose(table["tqqq_weight"] + table["sgov_weight"] + table["gld_weight"], 1.0)
    assert np.allclose(table["gld_weight"], 0.10)
    assert np.allclose(table["tqqq_weight"], 0.90 * table["S2_weight"])


def test_final_runtime_signal_path_points_to_promoted_engine_report() -> None:
    assert str(FINAL_RUNTIME_SIGNAL_PATH) == "reports/signals_core_strategy_final.csv"


def test_compute_basic_strategy_state_out_does_not_change_output() -> None:
    from tqqq_strategy.signal.final_engine import (
        DEFAULT_PHASE2_BEST_CONFIG_PATH,
        PROJECT_ROOT,
        _build_basic_params,
        _load_module,
        load_phase2_best_params,
    )

    ref = _load_module(PROJECT_ROOT / "ops/scripts/user_original_reference.py", "user_original_reference_state_out_test")
    data = _synthetic_market()
    ref.ensure_sma(data, "QQQ종가", 3, "QQQ3일선")
    ref.ensure_sma(data, "QQQ종가", 161, "QQQ161일선")
    ref.ensure_sma(data, "TQQQ종가", 200, "TQQQ200일선")
    ref.ensure_sma(data, "SPY종가", 200, "SPY200일선")
    params = _build_basic_params(ref, load_phase2_best_params(DEFAULT_PHASE2_BEST_CONFIG_PATH), DEFAULT_DIST_CAP)
    cols = ("time", "QQQ종가", "QQQ3일선", "QQQ161일선", "TQQQ종가", "TQQQ200일선", "SPY종가", "SPY200일선")
    args = [data[c].to_numpy() for c in cols]

    codes_a, weights_a = ref.compute_basic_strategy(*args, params)
    state: dict = {}
    codes_b, weights_b = ref.compute_basic_strategy(*args, params, state_out=state)

    assert codes_a.tolist() == codes_b.tolist()
    assert weights_a.tolist() == weights_b.tolist()
    assert state["assetCode"] == int(codes_b[-1])
    for key in (
        "locked",
        "spyBull",
        "above200Hyst",
        "overheatStage",
        "fullEntryClose",
        "reentryLock",
        "tp10CycleActive",
        "tp10Reduced",
        "tp10EntryClose",
        "baseCode",
        "v20",
        "dist200",
        "q_rsi",
        "dist_slope",
    ):
        assert key in state


def test_compute_engine_snapshot_weight_matches_last_signal_row() -> None:
    from tqqq_strategy.signal.final_engine import compute_engine_snapshot

    market = _synthetic_market()
    table = compute_final_signal_table(market)

    snapshot = compute_engine_snapshot(market)

    assert snapshot["weight"] == float(table["S2_weight"].iloc[-1])
    assert snapshot["params"].dist200_enter == 101.19
    assert snapshot["params"].spy_bear_cap == 0.0
    assert set(snapshot) == {"state", "params", "weight"}
