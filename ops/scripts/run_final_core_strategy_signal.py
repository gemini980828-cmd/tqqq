from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tqqq_strategy.signal.final_engine import (  # noqa: E402
    DEFAULT_PHASE2_BEST_CONFIG_PATH,
    FINAL_RUNTIME_SIGNAL_PATH,
    compute_final_signal_table,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build promoted core-strategy runtime signal CSV")
    parser.add_argument("--data-csv", default="data/user_input.csv")
    parser.add_argument("--best-config", default=str(DEFAULT_PHASE2_BEST_CONFIG_PATH))
    parser.add_argument("--out", default=str(FINAL_RUNTIME_SIGNAL_PATH))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    frame = compute_final_signal_table(data=data, best_config_path=args.best_config)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"Saved final runtime signal to {out}")


if __name__ == "__main__":
    main()
