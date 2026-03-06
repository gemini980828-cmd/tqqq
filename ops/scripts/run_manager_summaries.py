from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tqqq_strategy.ai.manager_jobs import refresh_manager_summaries
from tqqq_strategy.wealth.manual_inputs import DEFAULT_MANUAL_TRUTH_PATH
from tqqq_strategy.wealth.summary_store import DEFAULT_SUMMARY_STORE_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh deterministic manager summaries")
    parser.add_argument("--signals", default="reports/signals_s1_s2_s3_user_original.csv")
    parser.add_argument("--data", default="data/user_input.csv")
    parser.add_argument("--metrics", default="reports/backtest_metrics_primary.csv")
    parser.add_argument("--state", default="reports/daily_telegram_alert_state.json")
    parser.add_argument("--equity", default="reports/backtest_equity_primary.csv")
    parser.add_argument("--manual-truth", default=str(DEFAULT_MANUAL_TRUTH_PATH))
    parser.add_argument("--summary-store", default=str(DEFAULT_SUMMARY_STORE_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = refresh_manager_summaries(
        signal_csv_path=args.signals,
        data_csv_path=args.data,
        metrics_csv_path=args.metrics,
        state_path=args.state,
        equity_csv_path=args.equity,
        manual_truth_path=args.manual_truth,
        summary_store_path=args.summary_store,
    )
    print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
