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
from tqqq_strategy.ops.telegram_alert import send_telegram_message
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH
from tqqq_strategy.wealth import DEFAULT_MANUAL_TRUTH_PATH, build_core_strategy_position, load_manual_truth

SignalRow = dict[str, str]
SenderFn = Callable[..., dict]
REQUIRED_SIGNAL_COLUMNS = {"time", "S2_code", "S2_weight"}
REQUIRED_DATA_COLUMNS = {"time", "QQQ종가", "TQQQ종가", "SPY종가", "원달러환율"}


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


def _format_krw(value: float) -> str:
    return f"{int(round(float(value))):,}원"


def _format_usd(value: float) -> str:
    return f"${float(value):,.2f}"


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


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
    manual_truth_path: Path | str = DEFAULT_MANUAL_TRUTH_PATH,
    bot_token: str | None = None,
    chat_id: str | None = None,
    dry_run: bool = False,
    sender: SenderFn = send_telegram_message,
) -> dict:
    signal_csv = Path(signal_csv_path)
    data_csv = Path(data_csv_path)
    state_file = Path(state_path)
    manual_path = Path(manual_truth_path)

    prev_row, new_row = _read_last_two_rows(signal_csv)
    market_df = _read_market_data(data_csv)
    manual_inputs = load_manual_truth(manual_path)

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
    fx_now = float(latest["원달러환율"]) if "원달러환율" in latest and pd.notna(latest["원달러환율"]) else float("nan")

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
    positions = [row for row in manual_inputs.get("positions", []) if str(row.get("manager_id") or "") == "core_strategy"]
    primary = positions[0] if positions else {}
    inferred_fx = float(primary.get("market_price_krw") or 0.0) / tqqq_close if tqqq_close and float(primary.get("market_price_krw") or 0.0) > 0 else float("nan")
    if np.isnan(fx_now) or fx_now <= 0:
        fx_now = inferred_fx if pd.notna(inferred_fx) and inferred_fx > 0 else 1.0
    close_krw = tqqq_close * fx_now

    manual_inputs_live = dict(manual_inputs)
    live_positions = []
    for row in manual_inputs.get("positions", []):
        if str(row.get("manager_id") or "") == "core_strategy":
            updated = dict(row)
            updated["market_price_krw"] = close_krw
            updated["market_value_krw"] = float(row.get("quantity", 0.0)) * close_krw
            live_positions.append(updated)
        else:
            live_positions.append(dict(row))
    manual_inputs_live["positions"] = live_positions

    target_weight_pct = round(new_weight * 100.0, 2)
    base_target_pct = round(float(new_row.get("base_weight") or new_weight) * 100.0, 2)
    buffer_active = _is_truthy(new_row.get("buffer_active")) or base_target_pct > target_weight_pct + 1e-9
    core_position = build_core_strategy_position(manual_inputs_live, target_weight_pct=target_weight_pct)
    actual_weight_pct = float(core_position["actual_weight_pct"])
    rebalance_gap_krw = float(core_position["rebalance_gap_krw"])
    rebalance_action = str(core_position["rebalance_action"])
    current_value_krw = float(core_position["market_value_krw"])
    quantity = float(core_position["quantity"])
    order_qty = int(round(abs(rebalance_gap_krw) / close_krw)) if close_krw > 0 else 0
    order_value_krw = order_qty * close_krw
    order_value_usd = order_qty * tqqq_close
    asset_change_krw = quantity * (tqqq_close - tqqq_prev) * fx_now

    if rebalance_action == "buy" and order_qty > 0:
        judgment = "매수"
        judgment_emoji = "🟢"
    elif rebalance_action == "sell" and order_qty > 0:
        judgment = "감량"
        judgment_emoji = "🟠"
    else:
        judgment = "유지"
        judgment_emoji = "🟢"

    if buffer_active and target_weight_pct < base_target_pct:
        summary = f"기본 엔진 목표 {base_target_pct:.0f}%보다 완충이 우선돼 최종 목표는 {target_weight_pct:.0f}%입니다."
    else:
        summary = f"기본 엔진 목표 {target_weight_pct:.0f}% 유지, 과열 완충은 비활성입니다."

    lines = [
        f"[ {date_str} ] 코어전략 운영브리프",
        "",
        f"{judgment_emoji} 오늘 판단: {judgment}",
        f"목표 비중: {target_weight_pct:.0f}%",
    ]

    if order_qty > 0 and rebalance_action in {"buy", "sell"}:
        verb = "매수" if rebalance_action == "buy" else "매도"
        lines += [
            "",
            "🛒 실행 액션",
            f"- TQQQ {order_qty}주 {verb}",
            f"- 기준가: 오늘 종가 {_format_usd(tqqq_close)}",
            f"- 예상 주문금액: {_format_usd(order_value_usd)} (약 {_format_krw(order_value_krw)})",
        ]
    else:
        lines += ["", "🛒 실행 액션: 오늘은 주문 없음"]

    lines += [
        "",
        "요약:",
        summary,
        "",
        "📊 오늘 시장 / 내 자산",
        f"- TQQQ 종가: {_format_usd(tqqq_close)} ({_emoji_from_sign(tqqq_day_pct)} {_format_pct(tqqq_day_pct)})",
        f"- 내 TQQQ 자산 변화: {_emoji_from_sign(asset_change_krw)} {_format_krw(asset_change_krw)}",
        f"- 현재 평가금액: {_format_krw(current_value_krw)}",
        "",
        "──────────",
        "기술리포트",
        f"- 기본/최종 목표: {base_target_pct:.0f}% / {target_weight_pct:.0f}%",
        f"- 완충: {'ON' if buffer_active else 'OFF'} (129 / 123{' , cap 90%' if buffer_active else ''})",
        f"- Dist200 / SPY200 / Vol20: {dist200:.2f} / {spy_dist200:.2f} / {vol20:.2f}%",
        f"- signal code: {prev_code} → {new_code}",
    ]
    if new_weight >= 0.8 and entry_price is not None:
        lines.append(f"- 로스컷 감시: {_format_usd(stop_price)}")

    message = "\n".join(lines)

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
