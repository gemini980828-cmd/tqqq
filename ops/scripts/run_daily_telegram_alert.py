from __future__ import annotations

import argparse
import json
import os
import sys

from tqqq_strategy.ops.daily_job import run_daily_signal_alert
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signal-csv", default=str(FINAL_RUNTIME_SIGNAL_PATH))
    ap.add_argument("--data-csv", default="data/user_input.csv")
    ap.add_argument("--state-path", default="reports/daily_telegram_alert_state.json")
    args = ap.parse_args()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        dry_run = True
    else:
        dry_run = _parse_bool(os.getenv("TELEGRAM_DRY_RUN"), default=False)

    result = run_daily_signal_alert(
        signal_csv_path=args.signal_csv,
        data_csv_path=args.data_csv,
        state_path=args.state_path,
        bot_token=bot_token,
        chat_id=chat_id,
        dry_run=dry_run,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if (not result.get("sent", False)) and (not result.get("skipped", False)) and (not dry_run):
        sys.exit(1)


if __name__ == "__main__":
    main()
