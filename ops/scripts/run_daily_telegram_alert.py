from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping

from tqqq_strategy.ops.daily_job import run_daily_signal_alert
from tqqq_strategy.ops.signal_preflight import verify_signal_ready
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_contribution_env(
    env: Mapping[str, str | None],
) -> tuple[int | None, int | None]:
    """(monthly KRW amount, day of month 1-31) from CORE_MONTHLY_CONTRIBUTION_KRW / CORE_CONTRIBUTION_DAY.

    Unset/empty/invalid values become None (invalid ones warn on stderr). Callers use the pair only when both are set.
    """
    amount: int | None = None
    day: int | None = None

    raw_amount = (
        (env.get("CORE_MONTHLY_CONTRIBUTION_KRW") or "").strip().replace(",", "")
    )
    if raw_amount:
        try:
            amount = int(raw_amount)
            if amount <= 0:
                raise ValueError("must be positive")
        except ValueError:
            print(
                "warning: invalid CORE_MONTHLY_CONTRIBUTION_KRW ignored",
                file=sys.stderr,
            )
            amount = None

    raw_day = (env.get("CORE_CONTRIBUTION_DAY") or "").strip()
    if raw_day:
        try:
            day = int(raw_day)
            if not 1 <= day <= 31:
                raise ValueError("must be 1-31")
        except ValueError:
            print("warning: invalid CORE_CONTRIBUTION_DAY ignored", file=sys.stderr)
            day = None

    return amount, day


def _parse_alert_style(env: Mapping[str, str | None]) -> str:
    """ALERT_STYLE (classic|hybrid); unset/empty -> classic, invalid -> classic with a stderr warning."""
    raw = (env.get("ALERT_STYLE") or "").strip().lower()
    if not raw:
        return "classic"
    if raw in {"classic", "hybrid"}:
        return raw
    print(
        f"warning: invalid ALERT_STYLE {raw!r} ignored (using classic)", file=sys.stderr
    )
    return "classic"


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

    verify_signal_ready(signal_csv_path=args.signal_csv, data_csv_path=args.data_csv)

    contribution_krw, contribution_day = _parse_contribution_env(os.environ)
    if contribution_krw is None or contribution_day is None:
        contribution_krw, contribution_day = None, None

    result = run_daily_signal_alert(
        signal_csv_path=args.signal_csv,
        data_csv_path=args.data_csv,
        state_path=args.state_path,
        bot_token=bot_token,
        chat_id=chat_id,
        dry_run=dry_run,
        contribution_krw=contribution_krw,
        contribution_day=contribution_day,
        style=_parse_alert_style(os.environ),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if (
        (not result.get("sent", False))
        and (not result.get("skipped", False))
        and (not dry_run)
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
