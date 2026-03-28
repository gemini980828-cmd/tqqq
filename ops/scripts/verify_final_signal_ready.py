from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tqqq_strategy.ops.signal_preflight import verify_signal_ready
from tqqq_strategy.signal.final_engine import FINAL_RUNTIME_SIGNAL_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify final runtime signal freshness and shape")
    parser.add_argument("--signal-csv", default=str(FINAL_RUNTIME_SIGNAL_PATH))
    parser.add_argument("--data-csv", default="data/user_input.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = verify_signal_ready(signal_csv_path=args.signal_csv, data_csv_path=args.data_csv)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
