from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from tqqq_strategy.ops.alert_message import AlertContext, build_alert_message
from tqqq_strategy.ops.alert_triggers import TriggerReport, compute_triggers, skipped_report
from tqqq_strategy.ops.idempotency import build_alert_key
from tqqq_strategy.ops.order_plan import (
    Alloc,
    OrderPlan,
    is_contribution_day,
    is_first_session_of_year,
    plan_orders,
)
from tqqq_strategy.ops.telegram_alert import send_telegram_message
from tqqq_strategy.signal.final_engine import (
    CORE_SHARE,
    FINAL_RUNTIME_SIGNAL_PATH,
    GLD_FIXED_WEIGHT,
    STRATEGY_NAME,
    compute_engine_snapshot,
)

SignalRow = dict[str, str]
SenderFn = Callable[..., dict]
REQUIRED_SIGNAL_COLUMNS = {"time", "S2_code", "S2_weight"}
REQUIRED_DATA_COLUMNS = {"time", "QQQ종가", "TQQQ종가", "SPY종가", "원달러환율"}


def _read_signal_rows(signal_csv_path: Path) -> list[SignalRow]:
    with signal_csv_path.open("r", encoding="utf-8-sig", newline="") as fp:
        reader = csv.DictReader(fp)
        missing = REQUIRED_SIGNAL_COLUMNS.difference(set(reader.fieldnames or []))
        if missing:
            raise ValueError(f"signal csv missing required columns: {sorted(missing)}")
        rows = [row for row in reader]

    if len(rows) < 2:
        raise ValueError("signal csv must include at least two rows")

    return rows


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


def _row_weights(row: SignalRow, signal_weight: float) -> Alloc:
    """(TQQQ, SGOV, GLD) target weights from raw signal p; falls back to 0.90*p / 0.90*(1-p) / 0.10 for legacy CSVs."""
    try:
        tqqq = float(row["tqqq_weight"])
        sgov = float(row["sgov_weight"])
        gld = float(row["gld_weight"])
    except (KeyError, TypeError, ValueError):
        p = min(max(signal_weight, 0.0), 1.0)
        tqqq = p * CORE_SHARE
        sgov = (1.0 - p) * CORE_SHARE
        gld = GLD_FIXED_WEIGHT
    return tqqq, sgov, gld


def _weight_or_nan(row: SignalRow) -> float:
    try:
        return float(row["S2_weight"])
    except (KeyError, TypeError, ValueError):
        return float("nan")


def _run_start(weights: list[float], *, invested: bool) -> int:
    """Index where the current run of p>0 (invested) or p=0 (cash) begins, ending at the last row."""
    idx = len(weights) - 1
    while idx > 0 and _is_invested(weights[idx - 1]) == invested:
        idx -= 1
    return idx


def _is_invested(weight: float) -> bool:
    return weight > 1e-9


def _close_on(market_df: pd.DataFrame, date_str: str) -> float | None:
    hits = market_df.index[market_df["date"] == date_str].tolist()
    if not hits:
        return None
    value = market_df.loc[hits[-1], "TQQQ종가"]
    return float(value) if pd.notna(value) else None


def _action_name(plan: OrderPlan, *, p_now: float) -> str:
    if plan.trade is not None:
        return plan.trade.kind
    if plan.contribution is not None:
        return "contribution"
    if plan.gold_rebalance is not None:
        return "gold_rebalance"
    return "hold" if _is_invested(p_now) else "wait"


def run_daily_signal_alert(
    *,
    signal_csv_path: Path | str = FINAL_RUNTIME_SIGNAL_PATH,
    data_csv_path: Path | str = Path("data/user_input.csv"),
    state_path: Path | str = Path("reports/daily_telegram_alert_state.json"),
    manual_truth_path: Path | str | None = None,  # accepted for compatibility; holdings are no longer read
    bot_token: str | None = None,
    chat_id: str | None = None,
    dry_run: bool = False,
    sender: SenderFn = send_telegram_message,
    contribution_krw: int | None = None,
    contribution_day: int | None = None,
) -> dict:
    signal_csv = Path(signal_csv_path)
    data_csv = Path(data_csv_path)
    state_file = Path(state_path)

    signal_rows = _read_signal_rows(signal_csv)
    prev_row, new_row = signal_rows[-2], signal_rows[-1]
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
    tqqq_day_pct = (tqqq_close / float(prev["TQQQ종가"]) - 1.0) * 100.0
    fx_now: float | None = None
    fx_pct: float | None = None
    if pd.notna(latest["원달러환율"]):
        fx_now = float(latest["원달러환율"])
        if pd.notna(prev["원달러환율"]) and float(prev["원달러환율"]) != 0:
            fx_pct = (fx_now / float(prev["원달러환율"]) - 1.0) * 100.0

    # entry / cash-wait dates come from the signal history (the GHA state file is not persisted between runs)
    weights = [_weight_or_nan(r) for r in signal_rows]
    invested = _is_invested(new_weight)
    run_start = _run_start(weights, invested=invested)
    run_date = signal_rows[run_start]["time"]
    entry_date: str | None = run_date if invested else None
    entry_price: float | None = _close_on(market_df, run_date) if invested else None
    cash_since: str | None = None if invested else run_date

    prev_alloc = _row_weights(prev_row, prev_weight)
    new_alloc = _row_weights(new_row, new_weight)

    try:
        snapshot = compute_engine_snapshot(hist)
        if abs(snapshot["weight"] - new_weight) > 1e-6:
            triggers: TriggerReport = skipped_report()
        else:
            triggers = compute_triggers(
                snapshot["state"],
                p_now=new_weight,
                params=snapshot["params"],
                tqqq=hist["TQQQ종가"].to_numpy(),
                spy=hist["SPY종가"].to_numpy(),
                qqq=hist["QQQ종가"].to_numpy(),
            )
    except Exception:  # noqa: BLE001 - the alert must still go out without trigger distances
        triggers = skipped_report()

    contribution_configured = contribution_krw is not None and contribution_day is not None
    contribution_session = bool(
        contribution_configured and is_contribution_day(prev_row["time"], date_str, int(contribution_day or 0))
    )
    plan = plan_orders(
        prev_alloc,
        new_alloc,
        contribution_krw=contribution_krw if contribution_configured else None,
        is_contribution_day=contribution_session,
        is_first_session_of_year=is_first_session_of_year(prev_row["time"], date_str),
    )

    message = build_alert_message(
        AlertContext(
            date_str=date_str,
            strategy_name=STRATEGY_NAME,
            p_now=new_weight,
            new_alloc=new_alloc,
            plan=plan,
            triggers=triggers,
            tqqq_close=tqqq_close,
            tqqq_day_pct=tqqq_day_pct,
            entry_date=entry_date,
            entry_close=entry_price,
            cash_since=cash_since,
            fx_now=fx_now,
            fx_pct=fx_pct,
        )
    )

    send_result = sender(
        bot_token=bot_token,
        chat_id=chat_id,
        text=message,
        dry_run=dry_run,
        parse_mode="HTML",
    )

    tp10_done = prev_weight >= 0.999 and abs(new_weight - 0.97) < 1e-9
    sent = bool(send_result.get("sent"))
    if sent and (not dry_run):
        _write_state(
            state_file,
            {
                "last_alert_key": key,
                "last_sent_at": datetime.now(timezone.utc).isoformat(),
                "date": date_str,
                "position_weight": new_weight,
                "tqqq_weight": new_alloc[0],
                "sgov_weight": new_alloc[1],
                "gld_weight": new_alloc[2],
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
        "prev_allocation": {"TQQQ": prev_alloc[0], "SGOV": prev_alloc[1], "GLD": prev_alloc[2]},
        "new_allocation": {"TQQQ": new_alloc[0], "SGOV": new_alloc[1], "GLD": new_alloc[2]},
        "strategy": STRATEGY_NAME,
        "action": _action_name(plan, p_now=new_weight),
        "contribution_session": contribution_session,
        "state_path": str(state_file),
        "dry_run": dry_run,
        "message": message,
        "send_result": send_result,
    }
