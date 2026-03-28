# Suggested commands
## Python / backend
- Run targeted tests: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q <tests...>`
- Run all tests: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q`
- Py compile key modules: `python3 -m py_compile <files...>`
- Export dashboard snapshot: `PYTHONPATH=src python3 ops/scripts/export_dashboard_snapshot.py`
- Refresh manager summaries: `PYTHONPATH=src python3 ops/scripts/run_manager_summaries.py`
- Run reference backtest: `mkdir -p .yfinance-cache && UV_CACHE_DIR=.uv-cache uv run python ops/scripts/run_reference_backtest.py --start 2011-06-23 --end 2026-01-31 --out-dir reports`
- Daily telegram alert script: `PYTHONPATH=src .venv/bin/python ops/scripts/run_daily_telegram_alert.py`

## Frontend
- Build: `cd app/web && npm run build`
- Lint: `cd app/web && npm run lint`
- Dev server: `cd app/web && npm run dev`
- Preview: `cd app/web && npm run preview`
- Static serve dist: `python3 -m http.server 4175 -d app/web/dist`

## General Linux helpers
- `git status --short`
- `rg <pattern>` / `grep -R`
- `find <path> -name '<mask>'`
- `ls -la`
- `cd <dir>`
- `sed -n '1,200p' <file>`

## MCP / environment checks
- `codex mcp list`
- `omx status`
- `omx doctor`
