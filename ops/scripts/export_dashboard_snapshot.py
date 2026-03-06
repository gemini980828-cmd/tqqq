from __future__ import annotations

import argparse
import json
from pathlib import Path

from tqqq_strategy.ops.dashboard_snapshot import generate_dashboard_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export action-first dashboard snapshot to JSON")
    parser.add_argument("--signals", default="reports/signals_s1_s2_s3_user_original.csv")
    parser.add_argument("--data", default="data/user_input.csv")
    parser.add_argument("--metrics", default="reports/backtest_metrics_primary.csv")
    parser.add_argument("--state", default="reports/daily_telegram_alert_state.json")
    parser.add_argument("--equity", default="reports/backtest_equity_primary.csv")
    parser.add_argument("--out", default="app/web/public/dashboard_snapshot.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = generate_dashboard_snapshot(
        signal_csv_path=args.signals,
        data_csv_path=args.data,
        metrics_csv_path=args.metrics,
        state_path=args.state,
        equity_csv_path=args.equity,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved dashboard snapshot to {out_path}")


if __name__ == "__main__":
    main()
