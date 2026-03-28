from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from tqqq_strategy.ops.idempotency import build_alert_key
from tqqq_strategy.ops.telegram_alert import format_s2_change_message, send_telegram_message
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH

SignalRow = dict[str, str]
SenderFn = Callable[..., dict]
REQUIRED_SIGNAL_COLUMNS = {"time", "S2_code", "S2_weight"}
REQUIRED_DATA_COLUMNS = {"time", "QQQ종가", "TQQQ종가", "SPY종가"}


def _read_last_two_rows(signal_csv_path: Path) -> tuple[SignalRow, SignalRow]:
    with signal_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        missing = REQUIRED_SIGNAL_COLUMNS.difference(set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"signal csv missing required columns: {sorted(missing)}")
        rows = [row for row in reader]

    if len(rows) < 2:
        raise ValueError("signal csv must include at least two rows")

    return rows[-2], rows[-1]


def _read_market_data(data_csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(data_csv_path, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    missing = REQUIRED_DATA_COLUMNS.difference(set(df.columns))
    if missing:
        raise ValueError(f"data csv missing required columns: {sorted(missing)}")

    # ensure helper MAs
    if "QQQ3일선" not in df.columns:
        df["QQQ3일선"] = df["QQQ종가"].rolling(3, min_periods=3).mean()
    if "QQQ161일선" not in df.columns:
        df["QQQ161일선"] = df["QQQ종가"].rolling(161, min_periods=161).mean()
    if "TQQQ200일선" not in df.columns:
        df["TQQQ200일선"] = df["TQQQ종가"].rolling(200, min_periods=200).mean()
    if "SPY200일선" not in df.columns:
        df["SPY200일선"] = df["SPY종가"].rolling(200, min_periods=200).mean()

    return df


def _read_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _write_state(state_path: Path, payload: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, state_path)


def _rsi_wilder(close: pd.Series, length: int = 14) -> float:
    diff = close.diff()
    up = diff.clip(lower=0)
    down = (-diff).clip(lower=0)
    au = up.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    ad = down.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    rs = au / ad
    rsi = 100 - 100 / (1 + rs)
    return float(rsi.iloc[-1]) if len(rsi) else float("nan")


def _rolling_linreg_slope(y: np.ndarray, length: int = 45) -> float:
    if len(y) < length:
        return float("nan")
    x = np.arange(length, dtype=float)
    w = y[-length:]
    if np.isnan(w).any():
        return float("nan")
    denom = length * np.sum(x * x) - np.sum(x) ** 2
    if denom == 0:
        return float("nan")
    m = (length * np.sum(x * w) - np.sum(x) * np.sum(w)) / denom
    return float(m)


def _format_pct(v: float) -> str:
    if np.isnan(v):
        return "N/A"
    return f"{v:+.2f}%"


def _emoji_from_sign(v: float) -> str:
    if np.isnan(v):
        return "⚪"
    if v > 0:
        return "🟢"
    if v < 0:
        return "🔴"
    return "⚪"


def _rsi_state(rsi: float) -> str:
    if np.isnan(rsi):
        return "N/A"
    if rsi >= 70.0:
        return "과열"
    if rsi <= 30.0:
        return "과매도"
    return "중립"


def _position_label(weight: float) -> str:
    if weight <= 1e-9:
        return "현금"
    return f"TQQQ {weight * 100:.0f}%"


def _signal_label(*, new_weight: float, prev_weight: float, dist200: float) -> str:
    if new_weight <= 1e-9:
        return "강제 청산(0%)"
    if abs(new_weight - 0.95) < 1e-9 and prev_weight >= 0.999:
        return "익절 감량(95%)"
    if new_weight <= 0.101:
        return "부분 진입(10%)"
    if new_weight >= 0.999 and dist200 >= 101.0:
        return "풀 투자 유지"
    if abs(new_weight - prev_weight) < 1e-9:
        return f"비중 유지({new_weight * 100:.0f}%)"
    if abs(new_weight - 0.9) < 1e-9:
        return "과열 감량(90%)"
    if abs(new_weight - 0.8) < 1e-9:
        return "과열 감량(80%)"
    if abs(new_weight - 0.05) < 1e-9:
        return "과열 감량(5%)"
    return f"비중 조정({new_weight * 100:.1f}%)"


def _build_action_line(*, prev_weight: float, new_weight: float) -> str:
    delta = new_weight - prev_weight
    if abs(delta) < 1e-9:
        return f"📢 [액션 없음] {_position_label(new_weight)} 유지"
    direction = "매수" if delta > 0 else "매도"
    return f"📢 [매매 필요] {_position_label(prev_weight)} → {_position_label(new_weight)} ({direction} {abs(delta) * 100:.2f}%)"


def _build_reason_lines(
    *,
    vol20: float,
    spy_dist200: float,
    dist200: float,
    qqq3_vs161: float,
    prev_weight: float,
    new_weight: float,
    entry_price: float | None,
) -> list[str]:
    lines: list[str] = []
    vol_icon = "⬜" if np.isnan(vol20) else ("✅" if vol20 < 5.9 else "🚨")
    spy_icon = "⬜" if np.isnan(spy_dist200) else ("✅" if spy_dist200 > 97.75 else "🚨")
    dist_icon = "⬜" if np.isnan(dist200) else ("✅" if dist200 >= 101.0 else "⬜")
    lines.append(f"{vol_icon} 20일 변동성 < 5.9%: {vol20:.2f}%")
    lines.append(f"{spy_icon} SPY 200MA 필터(>97.75): {spy_dist200:.2f}")
    lines.append(f"{dist_icon} TQQQ 200일 이격도 ≥ 101%: {dist200:.2f}")
    lines.append(f"{'⬜' if dist200 < 139.0 else '✅'} 과열 감량 구간(≥139): {'미해당' if dist200 < 139.0 else f'{dist200:.2f}'}")
    tp10_hit = prev_weight >= 0.999 and abs(new_weight - 0.95) < 1e-9
    lines.append(f"{'✅' if tp10_hit else '⬜'} TP10 조건(신규100% 진입 후 +10%): {'충족' if tp10_hit else '미해당'}")
    stop_active = new_weight >= 0.8 and entry_price is not None
    lines.append("")
    lines.append(f"{'🟠' if stop_active else '⬜'} 손절 감시(고비중 & 진입가×0.941): {'활성' if stop_active else '미해당'}")
    if not np.isnan(qqq3_vs161):
        lines.append(f"{'✅' if qqq3_vs161 > 0 else '⬜'} QQQ3/161: {_format_pct(qqq3_vs161)} (> 0%)")
    return lines


def run_daily_signal_alert(
    *,
    signal_csv_path: Path | str = FINAL_RUNTIME_SIGNAL_PATH,
    data_csv_path: Path | str = Path("data/user_input.csv"),
    state_path: Path | str = Path("reports/daily_telegram_alert_state.json"),
    bot_token: str | None = None,
    chat_id: str | None = None,
    dry_run: bool = False,
    sender: SenderFn = send_telegram_message,
) -> dict:
    signal_csv = Path(signal_csv_path)
    data_csv = Path(data_csv_path)
    state_file = Path(state_path)

    prev_row, new_row = _read_last_two_rows(signal_csv)
    market_df = _read_market_data(data_csv)

    date_str = new_row["time"]
    prev_code = str(prev_row["S2_code"])
    new_code = str(new_row["S2_code"])
    try:
        prev_weight = float(prev_row["S2_weight"])
        new_weight = float(new_row["S2_weight"])
    except ValueError as exc:
        raise ValueError(
            f"invalid S2_weight value in {signal_csv}: prev={prev_row.get('S2_weight')} new={new_row.get('S2_weight')}"
        ) from exc

    key = build_alert_key(date_str, prev_code, new_code)
    state = _read_state(state_file)

    if state.get("last_alert_key") == key:
        return {
            "sent": False,
            "skipped": True,
            "reason": "duplicate_key",
            "key": key,
            "date": date_str,
            "state_path": str(state_file),
        }

    # market snapshot on same date as signal
    market_df["date"] = market_df["time"].dt.strftime("%Y-%m-%d")
    matches = market_df.index[market_df["date"] == date_str].tolist()
    if not matches:
        raise ValueError(f"date {date_str} not found in data csv {data_csv}")
    i = matches[-1]
    if i <= 0:
        raise ValueError("not enough market history for daily delta")

    hist = market_df.iloc[: i + 1].copy()
    latest = hist.iloc[-1]
    prev = hist.iloc[-2]

    tqqq_close = float(latest["TQQQ종가"])
    tqqq_prev = float(prev["TQQQ종가"])
    tqqq_day_pct = (tqqq_close / tqqq_prev - 1.0) * 100.0

    ma200 = hist["TQQQ종가"].rolling(200, min_periods=200).mean().iloc[-1]
    dist200 = (tqqq_close / ma200) * 100.0 if pd.notna(ma200) and ma200 != 0 else float("nan")

    qqq3 = float(latest["QQQ3일선"])
    qqq161 = float(latest["QQQ161일선"])
    qqq3_vs161 = (qqq3 / qqq161 - 1.0) * 100.0 if qqq161 != 0 else float("nan")

    spy_dist200 = (float(latest["SPY종가"]) / float(latest["SPY200일선"])) * 100.0 if float(latest["SPY200일선"]) != 0 else float("nan")

    vol20 = hist["TQQQ종가"].pct_change().rolling(20, min_periods=20).std(ddof=1).iloc[-1] * 100.0
    rsi14 = _rsi_wilder(hist["QQQ종가"], 14)

    last3_ret = hist["QQQ종가"].pct_change().tail(3).fillna(0.0)

    def _dot(v: float) -> str:
        return "🟢" if v > 0 else ("🔴" if v < 0 else "⚪")

    candle3 = "".join(_dot(float(v)) for v in last3_ret)

    fx_line = "원/달러 환율: N/A"
    if "원달러환율" in hist.columns and pd.notna(hist["원달러환율"].iloc[-1]):
        fx_now = float(hist["원달러환율"].iloc[-1])
        fx_prev = float(hist["원달러환율"].iloc[-2]) if pd.notna(hist["원달러환율"].iloc[-2]) else fx_now
        fx_pct = (fx_now / fx_prev - 1.0) * 100.0 if fx_prev != 0 else float("nan")
        fx_line = f"원/달러 환율: {fx_now:.2f} ({_format_pct(fx_pct)})"

    delta = new_weight - prev_weight
    holding_ratio = "N/A"
    if prev_weight > 1e-12:
        holding_ratio = f"{abs(delta) / prev_weight * 100:.2f}%"

    tqqq_vs200 = dist200 - 100.0 if pd.notna(dist200) else float("nan")
    state_entry_price = state.get("entry_price")
    entry_price: float | None = None
    if isinstance(state_entry_price, (float, int)):
        entry_price = float(state_entry_price)

    if new_weight <= 1e-9:
        entry_price = None
        entry_date = None
    elif prev_weight <= 1e-9 or new_weight > prev_weight + 1e-9 or entry_price is None:
        entry_price = tqqq_close
        entry_date = date_str
    else:
        entry_date = state.get("entry_date")

    entry_pnl = ((tqqq_close / entry_price) - 1.0) * 100.0 if entry_price and entry_price > 0 else float("nan")
    stop_price = entry_price * 0.941 if entry_price is not None else float("nan")
    tp10_done = prev_weight >= 0.999 and abs(new_weight - 0.95) < 1e-9

    price_emoji = _emoji_from_sign(tqqq_day_pct)
    pnl_emoji = _emoji_from_sign(tqqq_day_pct)
    position_emoji = "🟢" if new_weight > 0 else "🔴"
    entry_emoji = _emoji_from_sign(entry_pnl)
    loss_cut_line = "해당 없음"
    if new_weight >= 0.8 and entry_price is not None:
        loss_cut_line = f"활성 (${stop_price:.2f} | 진입가×0.941)"

    action_line = _build_action_line(prev_weight=prev_weight, new_weight=new_weight)
    signal_label = _signal_label(new_weight=new_weight, prev_weight=prev_weight, dist200=float(dist200 if pd.notna(dist200) else 0.0))

    action_needed = abs(delta) > 1e-9
    action_line = _build_action_line(prev_weight=prev_weight, new_weight=new_weight)

    position_lines = []
    if action_needed:
        position_lines = [
            f"신호: {signal_label}",
            f"비중 변경: {prev_weight * 100:.2f}% → {new_weight * 100:.2f}% (보유대비 {holding_ratio})",
            f"일간 수익: {pnl_emoji}{_format_pct(tqqq_day_pct)} (전일 종가 대비)",
            (
                f"진입가 대비: {entry_emoji}{_format_pct(entry_pnl)} (진입가 ${entry_price:.2f})"
                if entry_price is not None
                else "진입가 대비: N/A"
            ),
            f"로스컷: {loss_cut_line}",
        ]

    reason_lines_all = _build_reason_lines(
        vol20=float(vol20),
        spy_dist200=float(spy_dist200),
        dist200=float(dist200),
        qqq3_vs161=float(qqq3_vs161),
        prev_weight=float(prev_weight),
        new_weight=float(new_weight),
        entry_price=entry_price,
    )

    # 유지일은 짧게, 액션일은 풀 템플릿
    summary_checks = [
        ("⬜ Vol20: N/A (< 5.9%)" if np.isnan(vol20) else (f"✅ Vol20: {vol20:.2f}% (< 5.9%)" if vol20 < 5.9 else f"🚨 Vol20: {vol20:.2f}% (>= 5.9%)")),
        ("⬜ SPY200: N/A (> 97.75)" if np.isnan(spy_dist200) else (f"✅ SPY200: {spy_dist200:.2f} (> 97.75)" if spy_dist200 > 97.75 else f"🚨 SPY200: {spy_dist200:.2f} (<= 97.75)")),
        ("⬜ Dist200: N/A (>= 101)" if np.isnan(dist200) else (f"✅ Dist200: {dist200:.2f} (>= 101)" if dist200 >= 101.0 else f"⬜ Dist200: {dist200:.2f} (< 101)")),
    ]

    reason_lines = reason_lines_all if action_needed else summary_checks
    market_lines = []
    if action_needed:
        market_lines = [
            f"TQQQ 종가: {price_emoji}{tqqq_close:.4f}({_format_pct(tqqq_day_pct)})",
            f"TQQQ↔200일: {_format_pct(tqqq_vs200)}",
            f"QQQ3↔161: {_format_pct(qqq3_vs161)}",
            f"SPY200 이격도: {spy_dist200:.2f}",
            f"20일 변동성: {vol20:.2f}%",
            f"QQQ RSI(14): {rsi14:.2f} ({_rsi_state(rsi14)})" if pd.notna(rsi14) else "QQQ RSI(14): N/A",
            f"QQQ 3음봉: {candle3}",
            fx_line,
        ]

    ops_lines = [f"run_id: daily-{date_str}", f"alert_key: {key}", f"dry_run: {dry_run}"]

    if not action_needed:
        compact_lines = [
            f"[ {date_str} ] 일일현황보고",
            f"{action_line} | ${tqqq_close:.2f} ({pnl_emoji}{_format_pct(tqqq_day_pct)})",
        ]
        if new_weight >= 0.8 and entry_price is not None:
            compact_lines.append(f"⚠ 로스컷 ${stop_price:.2f} 감시중")
        compact_lines += ["", *summary_checks, "", f"✅ 조건 {sum(1 for x in summary_checks if x.startswith('✅'))}/{len(summary_checks)} 충족 | 다음 점검 내일 장마감", "", *ops_lines]
        message = "\n".join(compact_lines)
    else:
        message = format_s2_change_message(
            date_str=date_str,
            prev_code=prev_code,
            prev_weight=prev_weight,
            new_code=new_code,
            new_weight=new_weight,
            title="일일현황보고",
            alert_type="긴급 포지션 변경(리스크 관리) 알림",
            action_line=action_line,
            position_lines=position_lines,
            reason_lines=reason_lines,
            market_lines=market_lines,
            ops_lines=ops_lines,
        )

    send_result = sender(
        bot_token=bot_token,
        chat_id=chat_id,
        text=message,
        dry_run=dry_run,
    )

    sent = bool(send_result.get("sent"))
    if sent and (not dry_run):
        _write_state(
            state_file,
            {
                "last_alert_key": key,
                "last_sent_at": datetime.now(timezone.utc).isoformat(),
                "date": date_str,
                "position_weight": new_weight,
                "entry_price": entry_price,
                "entry_date": entry_date,
                "tp10_done": tp10_done,
            },
        )

    return {
        "sent": sent,
        "skipped": False,
        "key": key,
        "date": date_str,
        "prev_code": prev_code,
        "new_code": new_code,
        "prev_weight": prev_weight,
        "new_weight": new_weight,
        "state_path": str(state_file),
        "dry_run": dry_run,
        "message": message,
        "send_result": send_result,
    }
