from __future__ import annotations

import numpy as np
import pytest

from tqqq_strategy.ops.alert_triggers import (
    compute_triggers,
    fmt_num,
    fmt_signed_pct,
    next_close_for_ratio,
    next_qqq_close_for_trend_cross,
)
from tqqq_strategy.signal.final_engine import (
    PROJECT_ROOT,
    _build_basic_params,
    _load_module,
    load_phase2_best_params,
)

REF = _load_module(
    PROJECT_ROOT / "ops/scripts/user_original_reference.py",
    "user_original_reference_trigger_test",
)
PARAMS = _build_basic_params(
    REF, load_phase2_best_params(PROJECT_ROOT / "experiments/best_config.json"), 101.19
)


def _walk(n: int, start: float, seed: int, vol: float = 0.02) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return start * np.exp(np.cumsum(rng.normal(0.0, vol, n)))


def _state(**over) -> dict:
    base = {
        "ready": True,
        "locked": False,
        "spyBull": True,
        "above200Hyst": True,
        "overheatStage": 0,
        "fullEntryClose": float("nan"),
        "reentryLock": False,
        "tp10CycleActive": False,
        "tp10Reduced": False,
        "tp10EntryClose": float("nan"),
        "assetCode": 2,
        "baseCode": 2,
        "v20": 0.03,
        "dist200": 108.0,
        "spyDist200": 105.0,
        "q_rsi": 55.0,
        "dist_slope": 0.1,
    }
    base.update(over)
    return base


@pytest.mark.parametrize("n", [3, 20, 200])
@pytest.mark.parametrize("ratio", [0.9979, 0.9775, 1.0119, 1.39, 1.18])
def test_next_close_for_ratio_round_trip(n: int, ratio: float) -> None:
    closes = _walk(300, 60.0, seed=3)
    price = next_close_for_ratio(closes, n, ratio)

    extended = np.append(closes, price)
    realised = price / extended[-n:].mean()

    assert abs(realised - ratio) <= 1e-9


def test_next_qqq_close_for_trend_cross_is_the_3ma_161ma_crossing() -> None:
    closes = _walk(400, 500.0, seed=11, vol=0.01)
    price = next_qqq_close_for_trend_cross(closes)

    def gap(p: float) -> float:
        ext = np.append(closes, p)
        return float(ext[-3:].mean() - ext[-161:].mean())

    assert abs(gap(price)) < 1e-9 * price
    assert gap(price * 1.001) > 0
    assert gap(price * 0.999) < 0


def test_invested_headline_is_nearest_sell_line_below_price() -> None:
    tqqq = np.full(300, 100.0)
    spy = np.full(300, 500.0)
    qqq = np.full(300, 400.0)
    exit_price = next_close_for_ratio(tqqq, 200, PARAMS.dist200_exit / 100.0)

    # stop (entry * 0.941) well below the 200MA exit -> headline is the 200MA line
    far = compute_triggers(
        _state(fullEntryClose=104.0),
        p_now=1.0,
        params=PARAMS,
        tqqq=tqqq,
        spy=spy,
        qqq=qqq,
    )
    assert (
        far.headline
        == f"매도선까지 {fmt_signed_pct((exit_price / 100.0 - 1.0) * 100.0)}"
    )

    # stop (entry * 0.941 = 99.93) between the 200MA exit and the price -> headline is the stop
    stop = 106.2 * PARAMS.principal_stop_pct
    assert exit_price < stop < 100.0
    near = compute_triggers(
        _state(fullEntryClose=106.2),
        p_now=1.0,
        params=PARAMS,
        tqqq=tqqq,
        spy=spy,
        qqq=qqq,
    )
    assert near.headline == f"매도선까지 {fmt_signed_pct((stop / 100.0 - 1.0) * 100.0)}"
    assert any(line.startswith("손절선 $99.93") for line in near.detail_lines)


def test_invested_detail_lines_use_engine_params() -> None:
    tqqq = np.full(300, 100.0)
    report = compute_triggers(
        _state(fullEntryClose=90.0, dist200=108.0, spyDist200=105.0, v20=0.029),
        p_now=1.0,
        params=PARAMS,
        tqqq=tqqq,
        spy=np.full(300, 500.0),
        qqq=np.linspace(300.0, 400.0, 300),
    )
    text = "\n".join(report.detail_lines)

    assert "TQQQ/200일선 108.0% (99.79% 미만 → 10%로 축소," in text
    assert "(진입가의 94.1%," in text
    assert "SPY/200일선 105.0% (97.75% 미만 → 전량 매도, SPY" in text
    assert "20일 변동성 2.9% (5.9% 이상 → 전량 매도)" in text
    assert "과열 감량 139% (" in text and "상승 시 일부 매도)" in text


def test_rsi_lock_headline_uses_rsi_wording() -> None:
    report = compute_triggers(
        _state(
            assetCode=0, baseCode=0, above200Hyst=False, reentryLock=True, q_rsi=41.8
        ),
        p_now=0.0,
        params=PARAMS,
        tqqq=np.full(300, 100.0),
        spy=np.full(300, 500.0),
        qqq=np.full(300, 400.0),
    )

    assert report.headline == "재진입: QQQ RSI 43 이상 (현재 41.8)"
    assert any(line.startswith("✗ 손절 후 재진입 잠금") for line in report.detail_lines)


def test_vol_lock_headline_uses_vol_wording() -> None:
    report = compute_triggers(
        _state(assetCode=0, baseCode=0, locked=True, v20=0.062),
        p_now=0.0,
        params=PARAMS,
        tqqq=np.full(300, 100.0),
        spy=np.full(300, 500.0),
        qqq=np.full(300, 400.0),
    )

    assert report.headline == "재진입: 20일 변동성 5.9% 미만 (현재 6.2%)"


def test_rsi_lock_takes_priority_over_vol_lock() -> None:
    report = compute_triggers(
        _state(assetCode=0, baseCode=0, locked=True, reentryLock=True, q_rsi=40.0),
        p_now=0.0,
        params=PARAMS,
        tqqq=np.full(300, 100.0),
        spy=np.full(300, 500.0),
        qqq=np.full(300, 400.0),
    )

    assert report.headline is not None and report.headline.startswith("재진입: QQQ RSI")


def test_spy_bear_headline_shows_spy_distance() -> None:
    spy = np.full(300, 500.0)
    report = compute_triggers(
        _state(assetCode=0, baseCode=0, spyBull=False, spyDist200=96.0),
        p_now=0.0,
        params=PARAMS,
        tqqq=np.full(300, 100.0),
        spy=spy,
        qqq=np.full(300, 400.0),
    )
    target = next_close_for_ratio(spy, 200, PARAMS.spy_enter / 100.0)

    assert (
        report.headline
        == f"재진입까지 SPY {fmt_signed_pct((target / 500.0 - 1.0) * 100.0)}"
    )


def test_trend_wait_picks_nearer_of_tqqq_200ma_and_qqq_cross() -> None:
    tqqq = np.full(300, 100.0)
    # QQQ falling hard: the 3MA/161MA cross is far away -> TQQQ 200MA entry is nearer
    qqq_down = np.linspace(300.0, 100.0, 300)
    report = compute_triggers(
        _state(assetCode=0, baseCode=0, above200Hyst=False, dist200=99.0),
        p_now=0.0,
        params=PARAMS,
        tqqq=tqqq,
        spy=np.full(300, 500.0),
        qqq=qqq_down,
    )
    enter = next_close_for_ratio(tqqq, 200, PARAMS.dist200_enter / 100.0)
    assert (
        report.headline
        == f"재진입까지 TQQQ {fmt_signed_pct((enter / 100.0 - 1.0) * 100.0)}"
    )

    # TQQQ far below its 200MA entry, QQQ just below the cross -> QQQ headline
    tqqq_low = np.concatenate([np.full(299, 100.0), [60.0]])
    qqq_flat = np.concatenate([np.full(298, 400.0), [399.0, 398.0]])
    qqq_flat[-1] = 397.0
    report2 = compute_triggers(
        _state(assetCode=0, baseCode=0, above200Hyst=False, dist200=60.0),
        p_now=0.0,
        params=PARAMS,
        tqqq=tqqq_low,
        spy=np.full(300, 500.0),
        qqq=qqq_flat,
    )
    cross = next_qqq_close_for_trend_cross(qqq_flat)
    assert (
        report2.headline
        == f"재진입까지 QQQ {fmt_signed_pct((cross / 397.0 - 1.0) * 100.0)}"
    )


def test_state_out_of_sync_with_signal_skips_triggers() -> None:
    report = compute_triggers(
        _state(assetCode=2),
        p_now=0.0,
        params=PARAMS,
        tqqq=np.full(300, 100.0),
        spy=np.full(300, 500.0),
        qqq=np.full(300, 400.0),
    )

    assert report.headline is None
    assert report.detail_lines == ("조건 거리: 계산 생략",)


def test_short_history_skips_triggers_without_raising() -> None:
    report = compute_triggers(
        _state(),
        p_now=1.0,
        params=PARAMS,
        tqqq=np.full(10, 100.0),
        spy=np.full(10, 500.0),
        qqq=np.full(10, 400.0),
    )

    assert report.headline is None
    assert report.detail_lines == ("조건 거리: 계산 생략",)


def test_number_formatting_helpers() -> None:
    assert fmt_num(97.75) == "97.75"
    assert fmt_num(5.9, 1) == "5.9"
    assert fmt_num(139.0) == "139"
    assert fmt_signed_pct(-7.84) == "−7.8%"
    assert fmt_signed_pct(5.2) == "+5.2%"
    assert fmt_signed_pct(0.0) == "0.0%"
