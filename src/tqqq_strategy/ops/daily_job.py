from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from tqqq_strategy.ops.idempotency import build_alert_key
from tqqq_strategy.ops.telegram_alert import format_s2_change_message, send_telegram_message

SignalRow = dict[str, str]
SenderFn = Callable[..., dict]
REQUIRED_SIGNAL_COLUMNS = {"time", "S2_code", "S2_weight"}


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


def run_daily_signal_alert(
    *,
    signal_csv_path: Path | str = Path("reports/signals_s1_s2_s3_user_original.csv"),
    state_path: Path | str = Path("reports/daily_telegram_alert_state.json"),
    bot_token: str | None = None,
    chat_id: str | None = None,
    dry_run: bool = False,
    sender: SenderFn = send_telegram_message,
) -> dict:
    signal_csv = Path(signal_csv_path)
    state_file = Path(state_path)

    prev_row, new_row = _read_last_two_rows(signal_csv)
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

    message = format_s2_change_message(
        date_str=date_str,
        prev_code=prev_code,
        prev_weight=prev_weight,
        new_code=new_code,
        new_weight=new_weight,
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
