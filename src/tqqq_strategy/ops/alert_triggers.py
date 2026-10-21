"""Distance-to-trigger numbers for the daily alert (pure functions; no I/O).

Price distances are exact for the NEXT close with the moving average moving along with it:
for an N-day MA and target ratio r (price / MA, as a fraction) the close P that lands on the ratio is
`P = r * S / (N - r)` where S is the sum of the previous N-1 closes.
Vol lock and RSI re-entry are not price-expressible and are described in words.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

MINUS = "−"
_CODE_WEIGHTS = {0: 0.0, 1: 0.10, 2: 1.00, 3: 0.90, 4: 0.80, 5: 0.05}


@dataclass(frozen=True)
class TriggerReport:
    headline: str | None
    detail_lines: tuple[str, ...]


def code_to_weight(code: int) -> float:
    """Signal code -> weight (same table as the strategy reference)."""
    if code in _CODE_WEIGHTS:
        return _CODE_WEIGHTS[code]
    if code >= 100:
        return float(min(max(code / 1000.0, 0.0), 1.0))
    return 0.0


def fmt_num(value: float, decimals: int = 2) -> str:
    """Up to `decimals` decimals with trailing zeros stripped (97.75, 5.9, 139)."""
    text = f"{value:.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def fmt_signed_pct(pct: float, decimals: int = 1) -> str:
    """Signed percent with U+2212 for negatives: +5.2% / −7.8%."""
    text = f"{abs(pct):.{decimals}f}"
    if float(text) == 0.0:
        return f"{text}%"
    return f"{'+' if pct > 0 else MINUS}{text}%"


def _closes(values: Sequence[float] | np.ndarray, n: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if len(arr) < n - 1 or n < 2:
        raise ValueError("not enough history")
    return arr


def next_close_for_ratio(
    closes: Sequence[float] | np.ndarray, n: int, ratio: float
) -> float:
    """Next close P such that P / MA_n(next) == ratio (fraction, e.g. 0.9979), the MA including P."""
    arr = _closes(closes, n)
    s = float(arr[-(n - 1) :].sum())
    return ratio * s / (n - ratio)


def next_qqq_close_for_trend_cross(
    qqq: Sequence[float] | np.ndarray, short: int = 3, long: int = 161
) -> float:
    """Next QQQ close P where 3MA == 161MA; the 3MA is above the 161MA for P strictly above it.

    (short*S_{long-1} - long*S_{short-1}) / (long - short), S_k = sum of the last k existing closes.
    """
    arr = _closes(qqq, long)
    s_long = float(arr[-(long - 1) :].sum())
    s_short = float(arr[-(short - 1) :].sum())
    return (short * s_long - long * s_short) / (long - short)


def _pct_to(price: float, current: float) -> float:
    return (price / current - 1.0) * 100.0


def _fmt_usd(value: float) -> str:
    return f"${value:,.2f}"


def skipped_report() -> TriggerReport:
    return TriggerReport(headline=None, detail_lines=("조건 거리: 계산 생략",))


def compute_triggers(
    state: dict[str, Any],
    *,
    p_now: float,
    params: Any,
    tqqq: Sequence[float] | np.ndarray,
    spy: Sequence[float] | np.ndarray,
    qqq: Sequence[float] | np.ndarray,
) -> TriggerReport:
    """Headline + detail lines for the current engine state.

    Never raises: any failure (short history, engine state out of sync with the signal CSV) yields
    no headline and a single "조건 거리: 계산 생략" detail line.
    """
    try:
        return _compute_triggers(
            state, p_now=p_now, params=params, tqqq=tqqq, spy=spy, qqq=qqq
        )
    except Exception:  # noqa: BLE001 - alert must still go out without trigger distances
        return skipped_report()


def _compute_triggers(
    state: dict[str, Any],
    *,
    p_now: float,
    params: Any,
    tqqq: Sequence[float] | np.ndarray,
    spy: Sequence[float] | np.ndarray,
    qqq: Sequence[float] | np.ndarray,
) -> TriggerReport:
    if not state.get("ready", True):
        return skipped_report()
    if abs(code_to_weight(int(state["assetCode"])) - p_now) > 1e-6:
        return skipped_report()

    t = np.asarray(tqqq, dtype=float)
    q = np.asarray(qqq, dtype=float)
    t_now = float(t[-1])
    q_now = float(q[-1])
    spy_now = float(np.asarray(spy, dtype=float)[-1])

    dist200 = float(state["dist200"])
    spy_dist = float(state["spyDist200"])
    v20_pct = float(state["v20"]) * 100.0
    vol_thr_pct = float(params.vol_threshold) * 100.0
    q_rsi = float(state["q_rsi"])

    exit_price = next_close_for_ratio(t, 200, params.dist200_exit / 100.0)
    enter_price = next_close_for_ratio(t, 200, params.dist200_enter / 100.0)
    qqq_cross = next_qqq_close_for_trend_cross(q, 3, 161)
    qqq_trend_up = float(q[-3:].mean()) > float(q[-161:].mean())
    spy_exit_price = next_close_for_ratio(spy, 200, params.spy_exit / 100.0)
    spy_enter_price = next_close_for_ratio(spy, 200, params.spy_enter / 100.0)

    invested = p_now > 1e-9
    if invested:
        return _invested_report(
            state,
            p_now=p_now,
            params=params,
            t=t,
            t_now=t_now,
            q_now=q_now,
            spy_now=spy_now,
            dist200=dist200,
            spy_dist=spy_dist,
            v20_pct=v20_pct,
            vol_thr_pct=vol_thr_pct,
            exit_price=exit_price,
            qqq_cross=qqq_cross,
            qqq_trend_up=qqq_trend_up,
            spy_exit_price=spy_exit_price,
        )
    return _cash_report(
        state,
        params=params,
        t=t,
        t_now=t_now,
        q_now=q_now,
        spy_now=spy_now,
        dist200=dist200,
        spy_dist=spy_dist,
        v20_pct=v20_pct,
        vol_thr_pct=vol_thr_pct,
        q_rsi=q_rsi,
        enter_price=enter_price,
        qqq_cross=qqq_cross,
        qqq_trend_up=qqq_trend_up,
        spy_enter_price=spy_enter_price,
    )


def _invested_report(
    state: dict[str, Any],
    *,
    p_now: float,
    params: Any,
    t: np.ndarray,
    t_now: float,
    q_now: float,
    spy_now: float,
    dist200: float,
    spy_dist: float,
    v20_pct: float,
    vol_thr_pct: float,
    exit_price: float,
    qqq_cross: float,
    qqq_trend_up: bool,
    spy_exit_price: float,
) -> TriggerReport:
    lines: list[str] = []
    headline: str | None = None

    stop_price = float("nan")
    full_entry = float(state.get("fullEntryClose", float("nan")))
    stop_active = (
        bool(getattr(params, "use_principal_stop", True))
        and code_to_weight(int(state["assetCode"])) >= 0.80 - 1e-9
        and not math.isnan(full_entry)
    )
    if stop_active:
        stop_price = full_entry * float(params.principal_stop_pct)

    if state["above200Hyst"]:
        after = "10%로 축소" if qqq_trend_up else "전량 매도"
        exit_pct = _pct_to(exit_price, t_now)
        lines.append(
            f"TQQQ/200일선 {dist200:.1f}% ({fmt_num(params.dist200_exit)}% 미만 → {after}, {fmt_signed_pct(exit_pct)})"
        )
        candidates = [exit_price]
        if stop_active:
            candidates.append(stop_price)
        nearest = max(candidates)
        headline = f"매도선까지 {fmt_signed_pct(_pct_to(nearest, t_now))}"
    else:
        # partial (10%) position held on the QQQ short-term trend only
        cross_pct = _pct_to(qqq_cross, q_now)
        lines.append(
            f"QQQ 3일선/161일선 (3일선이 아래로 내려가면 전량 매도, QQQ {fmt_signed_pct(cross_pct)})"
        )
        lines.append(
            f"TQQQ/200일선 {dist200:.1f}% ({fmt_num(params.dist200_enter)}% 이상 → 100% 진입)"
        )
        headline = f"매도선까지 QQQ {fmt_signed_pct(cross_pct)}"

    if stop_active:
        lines.append(
            f"손절선 {_fmt_usd(stop_price)} (진입가의 {fmt_num(params.principal_stop_pct * 100, 1)}%, "
            f"{fmt_signed_pct(_pct_to(stop_price, t_now))})"
        )

    if state["spyBull"]:
        spy_pct = _pct_to(spy_exit_price, spy_now)
        lines.append(
            f"SPY/200일선 {spy_dist:.1f}% ({fmt_num(params.spy_exit)}% 미만 → 전량 매도, SPY {fmt_signed_pct(spy_pct)})"
        )
    lines.append(
        f"20일 변동성 {v20_pct:.1f}% ({fmt_num(vol_thr_pct, 1)}% 이상 → 전량 매도)"
    )

    lines.extend(_overheat_and_tp10_lines(state, params=params, t=t, t_now=t_now))
    return TriggerReport(headline=headline, detail_lines=tuple(lines))


def _overheat_and_tp10_lines(
    state: dict[str, Any], *, params: Any, t: np.ndarray, t_now: float
) -> list[str]:
    lines: list[str] = []
    stage = int(state["overheatStage"])
    enters = [
        params.overheat1_enter,
        params.overheat2_enter,
        params.overheat3_enter,
        params.overheat4_enter,
    ]
    if stage < 4 and (stage > 0 or int(state["baseCode"]) == 2):
        enter = float(enters[stage])
        price = next_close_for_ratio(t, 200, enter / 100.0)
        action = (
            "전량 매도" if stage == 3 else ("추가 매도" if stage > 0 else "일부 매도")
        )
        lines.append(
            f"과열 감량 {fmt_num(enter)}% ({fmt_signed_pct(_pct_to(price, t_now))} 상승 시 {action})"
        )
    if stage > 0:
        exits = [
            params.overheat1_exit,
            params.overheat2_exit,
            params.overheat3_exit,
            params.overheat4_exit,
        ]
        lines.append(
            f"과열 감량 {stage}단계 진행 중 (TQQQ/200일선 {fmt_num(exits[stage - 1])}% 이하로 내려오면 완화)"
        )

    tp_entry = float(state.get("tp10EntryClose", float("nan")))
    if (
        state.get("tp10CycleActive")
        and not state.get("tp10Reduced")
        and not math.isnan(tp_entry)
    ):
        tp_price = tp_entry * (1.0 + float(params.tp10_trigger))
        lines.append(
            f"익절 감량 {_fmt_usd(tp_price)} (진입 종가 대비 {fmt_signed_pct(params.tp10_trigger * 100, 0)}, "
            f"{fmt_signed_pct(_pct_to(tp_price, t_now))} → {fmt_num(params.tp10_cap * 100, 0)}%로 감량)"
        )
    return lines


def _cash_report(
    state: dict[str, Any],
    *,
    params: Any,
    t: np.ndarray,
    t_now: float,
    q_now: float,
    spy_now: float,
    dist200: float,
    spy_dist: float,
    v20_pct: float,
    vol_thr_pct: float,
    q_rsi: float,
    enter_price: float,
    qqq_cross: float,
    qqq_trend_up: bool,
    spy_enter_price: float,
) -> TriggerReport:
    """Cash: list every blocking condition, headline is the first blocker in priority order."""
    lines: list[str] = []
    blockers: list[str] = []
    rsi_thr = float(params.rsi_reentry_thr)

    rsi_blocked = bool(state["reentryLock"]) and not (
        not math.isnan(q_rsi) and q_rsi >= rsi_thr
    )
    if state["reentryLock"]:
        mark = "✗" if rsi_blocked else "✓"
        lines.append(
            f"{mark} 손절 후 재진입 잠금: QQQ RSI {q_rsi:.1f} ({fmt_num(rsi_thr)} 이상 필요)"
        )
    if rsi_blocked:
        blockers.append(f"재진입: QQQ RSI {fmt_num(rsi_thr)} 이상 (현재 {q_rsi:.1f})")

    vol_blocked = bool(state["locked"])
    lines.append(
        f"{'✗' if vol_blocked else '✓'} 20일 변동성 {v20_pct:.1f}% ({fmt_num(vol_thr_pct, 1)}% 미만 필요)"
    )
    if vol_blocked:
        blockers.append(
            f"재진입: 20일 변동성 {fmt_num(vol_thr_pct, 1)}% 미만 (현재 {v20_pct:.1f}%)"
        )

    spy_blocked = not state["spyBull"]
    spy_pct = _pct_to(spy_enter_price, spy_now)
    spy_suffix = f", SPY {fmt_signed_pct(spy_pct)}" if spy_blocked else ""
    lines.append(
        f"{'✗' if spy_blocked else '✓'} SPY/200일선 {spy_dist:.1f}% ({fmt_num(params.spy_enter)}% 이상 필요{spy_suffix})"
    )
    if spy_blocked:
        blockers.append(f"재진입까지 SPY {fmt_signed_pct(spy_pct)}")

    stage = int(state["overheatStage"])
    if stage == 4:
        release_price = next_close_for_ratio(t, 200, params.overheat4_exit / 100.0)
        rel_pct = _pct_to(release_price, t_now)
        lines.append(
            f"✗ 과열 잠금: TQQQ/200일선 {dist200:.1f}% ({fmt_num(params.overheat4_exit)}% 이하로 내려와야 해제, "
            f"{fmt_signed_pct(rel_pct)})"
        )
        blockers.append(f"재진입까지 TQQQ {fmt_signed_pct(rel_pct)} (과열 해제)")

    trend_ok = bool(state["above200Hyst"]) or qqq_trend_up
    enter_pct = _pct_to(enter_price, t_now)
    cross_pct = _pct_to(qqq_cross, q_now)
    # distances only for unmet conditions; a met condition's "distance" would point the wrong way
    enter_gap = "" if state["above200Hyst"] else f", TQQQ {fmt_signed_pct(enter_pct)}"
    cross_gap = "" if qqq_trend_up else f", QQQ {fmt_signed_pct(cross_pct)}"
    lines.append(
        f"{'✓' if state['above200Hyst'] else '✗'} TQQQ/200일선 {dist200:.1f}% "
        f"({fmt_num(params.dist200_enter)}% 이상 → 100% 진입{enter_gap})"
    )
    lines.append(
        f"{'✓' if qqq_trend_up else '✗'} QQQ 3일선 > 161일선 (→ 10% 진입{cross_gap})"
    )
    if not trend_ok:
        if abs(cross_pct) < abs(enter_pct):
            blockers.append(f"재진입까지 QQQ {fmt_signed_pct(cross_pct)}")
        else:
            blockers.append(f"재진입까지 TQQQ {fmt_signed_pct(enter_pct)}")

    headline = blockers[0] if blockers else None
    return TriggerReport(headline=headline, detail_lines=tuple(lines))
