#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/juwon/tqqq/.worktrees/backtest-parity-v1"
LOG_DIR="$ROOT/logs"
LOCK_DIR="$ROOT/.locks"
LOCK_FILE="$LOCK_DIR/daily_close_alert.lock"

mkdir -p "$LOG_DIR" "$LOCK_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] another daily_close_alert run is in progress; skipping"
  exit 0
fi

if [[ -f /home/juwon/.config/tqqq/telegram.env ]]; then
  # shellcheck disable=SC1091
  source /home/juwon/.config/tqqq/telegram.env
fi

END_DATE="$(python3 - <<'PY'
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
ny_today = datetime.now(ZoneInfo('America/New_York')).date()
print((ny_today + timedelta(days=1)).isoformat())
PY
)"

cd "$ROOT"

UV_CACHE_DIR=.uv-cache uv run python ops/scripts/prepare_user_csv.py \
  --start 2011-06-23 \
  --end "$END_DATE" \
  --out data/user_input.csv

UV_CACHE_DIR=.uv-cache uv run python ops/scripts/user_original_reference.py

PYTHONPATH=src .venv/bin/python ops/scripts/run_daily_telegram_alert.py \
  --signal-csv reports/signals_s1_s2_s3_user_original.csv \
  --state-path reports/daily_telegram_alert_state.json
