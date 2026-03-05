# TODO - Serena / Context7 / Playwright setup

- [x] Confirm install target type (MCP vs skill) and map each tool
- [x] Install missing runtime prerequisites (uv for Serena)
- [x] Register MCP servers in Codex config for Serena, Context7, Playwright
- [x] (Optional) Install Playwright skill from GitHub curated skills
- [x] Verify installation with `codex mcp list` and per-server `codex mcp get`

## Review
- Added MCP servers:
  - `serena` → `uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context codex`
  - `context7` → `npx -y @upstash/context7-mcp@latest`
  - `playwright` → `npx -y @playwright/mcp@latest`
- Installed Playwright skill from GitHub curated skills into `~/.codex/skills/playwright`
- Verified all 3 servers appear as `enabled` in `codex mcp list`

---

# TODO - TQQQ 전략 고도화 (Brainstorming)

- [x] (1) 프로젝트 컨텍스트 탐색 (파일/문서/변경이력)
- [x] (2) 명확화 질문 1개씩 진행 (목표/제약/성공기준)
- [x] (3) 2~3개 접근안 + 트레이드오프 제시
- [x] (4) 섹션별 설계안 제시 및 사용자 승인 획득
- [x] (5) 설계 문서 작성 (`docs/plans/YYYY-MM-DD-<topic>-design.md`)
- [x] (6) writing-plans 단계로 전환

## Review (진행중)
- TradingView 코드 로드 완료(1297 lines)
- 핵심 엔진 블록 위치 확인:
  - RTH 종가 이벤트: `tradingview.txt:302-315`
  - 상태 업데이트/의사결정: `tradingview.txt:402-688`
  - 텔레그램 알림 출력: `tradingview.txt:1137-1297`

- 아키텍처 재검토 요청 반영: 누락 가능 항목(시간대/세금 환산/데이터 정합/알림 멱등성/실험 거버넌스) 점검 예정


## 설계 섹션 승인 현황
- [x] 섹션1: 전체 아키텍처(2안+3전환 트리거)
- [x] 섹션2: 데이터 계약 & 정합성
- [x] 섹션3: 신호엔진/백테스트/검증 게이트
- [x] 섹션4: 2차 실험 프레임
- [x] 섹션5: 3차 운영자동화/웹앱 (텔레그램 UI 매핑 포함)

- 텔레그램 샘플 UI 반영 요구 확인: `9551781008_192159903_f42a776fa8b229fbdd2105c6cd411d85.webp`

## 작성된 산출물
- `docs/plans/2026-03-05-tqqq-strategy-design.md`
- `docs/plans/2026-03-05-tqqq-strategy-implementation-plan.md`

## 구현 진행 (Subagent-Driven)
- [x] Task 1: 프로젝트 골격 및 테스트 환경 부트스트랩
- [x] Task 2: 데이터 계약(canonical schema) 및 품질검사
- [x] Task 3: 원천 수집기(stooq/yfinance)
- [x] Task 4: Pine 동치 신호엔진 v1
- [x] Task 5: 백테스트 비용/세금 모듈 스캐폴드

### Task 2 Execution Plan (canonical schema + quality)
- [x] Add failing tests for canonical validation (missing columns, duplicate date+symbol)
- [x] Implement schema constants in `src/tqqq_strategy/data/schema.py`
- [x] Implement `validate_canonical(df) -> (ok, errs)` in `src/tqqq_strategy/data/quality.py`
- [x] Run targeted tests and capture results

### Task 2 Review
- Added canonical requirement constants in `schema.py` (date,symbol,close,adj_close,source,tz,session_type,is_trading_day).
- Implemented `validate_canonical(df)` for required-column checks and duplicate `(date,symbol)` rejection.
- Added TDD tests including duplicate rejection assertion containing "duplicate".
- Verified with `uv run --with pytest pytest -q tests/data/test_schema_quality.py` (3 passed).


### Task 3 Execution Plan (ingest normalizers)
- [x] Add minimal normalizer modules for yfinance/stooq canonical rows
- [x] Add ingest contract tests (including required normalize_yf_row example)
- [x] Run targeted data tests and capture results

### Task 3 Review
- Created `ingest_yf.py` with `normalize_yf_row(...)` returning canonical fields including `tz`, `session_type`, `is_trading_day`.
- Created `ingest_stooq.py` with `normalize_stooq_row(...)` and `adj_close=close` defaulting for stooq rows.
- Added `tests/data/test_ingest_contract.py` covering the required yfinance contract example and stooq canonical defaults.
- Verified with `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/data/test_ingest_contract.py tests/data/test_schema_quality.py` (5 passed).


### Task 4 Execution Plan (signal engine v1)
- [x] Add priority test for lock override
- [x] Implement minimal `decide_code(...)` in `engine_v1.py`
- [x] Add minimal signal params constants in `params.py`
- [x] Run targeted signal test and capture result

### Task 4 Review
- Added `src/tqqq_strategy/signal/engine_v1.py` with priority decision flow from plan spec.
- Added `src/tqqq_strategy/signal/params.py` for minimal action/overheat constants used by v1 engine.
- Added `tests/signal/test_engine_v1_priority.py` asserting lock has highest priority (`code == 0`).

### Task 5 Execution Plan (backtest cost/tax)
- [x] Add failing test for KR overseas tax function behavior
- [x] Implement minimal KR overseas tax function in `src/tqqq_strategy/backtest/tax_kr.py`
- [x] Create minimal runner scaffold file required by plan (`src/tqqq_strategy/backtest/runner.py`)
- [x] Run targeted backtest tax tests and capture result

### Task 5 Review
- Added `tests/backtest/test_cost_tax.py` first and confirmed initial failure (`ModuleNotFoundError`) before implementation.
- Implemented `apply_korean_overseas_tax(realized_profit_krw: float) -> float` exactly per plan in `src/tqqq_strategy/backtest/tax_kr.py`.
- Added required scaffold file `src/tqqq_strategy/backtest/runner.py` for Task 5 scope.
- Verified with `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/backtest/test_cost_tax.py` (2 passed).

### Task 6 Execution Plan (validation tolerance)
- [x] Add failing tolerance test in `tests/validation/test_weight_tolerance.py`
- [x] Implement minimal `within_tolerance(...)` in `src/tqqq_strategy/validation/golden_diff.py`
- [x] Create `reports/.gitkeep`
- [x] Run targeted validation test and capture result


### Task 6 Review
- Added failing test first in `tests/validation/test_weight_tolerance.py` and confirmed import failure before implementation.
- Implemented minimal `within_tolerance` in `src/tqqq_strategy/validation/golden_diff.py` using `abs(expected - actual) <= tol`.
- Added required `reports/.gitkeep`.
- Verified with `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/validation/test_weight_tolerance.py` (4 passed).

### Task 7 Execution Plan (WFO OOS gate)
- [x] Add failing test in `tests/experiments/test_oos_gate.py`
- [x] Implement minimal `passes_oos_gate(...)` in `src/tqqq_strategy/experiments/wfo.py`
- [x] Run targeted experiment test and capture result


### Task 7 Review
- Added failing test first in `tests/experiments/test_oos_gate.py` and confirmed initial `ModuleNotFoundError` before implementation.
- Implemented minimal `passes_oos_gate(...)` in `src/tqqq_strategy/experiments/wfo.py` with `is_score <= 0` guard and ratio gate comparison.
- Verified with `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/experiments/test_oos_gate.py` (2 passed).

### Task 8 Execution Plan (telegram snapshot contract)
- [x] Add failing contract test in `tests/contracts/test_telegram_blocks.py`
- [x] Implement minimal `build_dashboard_snapshot(payload: dict)` in `app/api/main.py`
- [x] Create required scaffold files for web page and schema contract
- [x] Run target contract test and capture fail/pass evidence


### Task 8 Review
- Added failing contract test first in `tests/contracts/test_telegram_blocks.py` and captured initial import failure for missing `app` module path.
- Implemented minimal `build_dashboard_snapshot(payload)` in `app/api/main.py` returning required block keys.
- Created required Task 8 files: `app/web/src/pages/Dashboard.tsx` and `app/contracts/telegram_snapshot.schema.json`.
- Verified target test with `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_telegram_blocks.py` (1 passed).

### Task 9 Execution Plan (ops idempotency key)
- [x] Add failing test first with exact `build_alert_key` contract
- [x] Implement minimal `build_alert_key(date_str, prev_code, new_code)`
- [x] Create minimal non-empty `daily_job.py` scaffold
- [x] Run targeted ops test and capture output

### Task 9 Review
- Added `tests/ops/test_idempotency.py` first with the exact required contract and confirmed initial failure: `ModuleNotFoundError: No module named 'tqqq_strategy.ops'`.
- Implemented `build_alert_key(date_str, prev_code, new_code)` in `src/tqqq_strategy/ops/idempotency.py` as `f"{date_str}:{prev_code}->{new_code}"`.
- Added minimal non-empty scaffold file `src/tqqq_strategy/ops/daily_job.py`.
- Verified with `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ops/test_idempotency.py` (`1 passed`).

### Task 10 Execution Plan (integration verification)
- [x] Add runbook checklist doc at `docs/runbooks/backtest-and-ops-checklist.md`
- [x] Run full test suite (`pytest -q`)
- [x] Run validation module entry (`python -m tqqq_strategy.validation.golden_diff`)
- [x] Record verification evidence in review notes

### Task 10 Review
- Added `docs/runbooks/backtest-and-ops-checklist.md` with required operational verification checklist items.
- Verified full test suite with `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q` (`17 passed`).
- Verified validation module entry with `PYTHONPATH=src python3 -m tqqq_strategy.validation.golden_diff` (exit 0).

### Backtest Run Execution Plan (Primary window)
- [x] Add executable backtest runner script using current reference strategy logic
- [x] Run primary window backtest (2011-06-23 ~ 2026-01-30 close) and export metrics/equity
- [x] Extend metrics beyond CAGR/MDD (risk-adjusted and path metrics)
- [ ] Review outputs with user and calibrate assumptions (tax/fill/slippage/data-source)

### Backtest Tax Model Recalibration Review
- Replaced simplified year-end equity tax approximation with realized-gain based annual tax ledger model in `ops/scripts/run_reference_backtest.py`.
- Tax model now applies 22% only to annual realized gains above 2.5M KRW deduction, based on sell transactions and moving average cost basis.
- Added FX-aware execution valuation using `KRW=X` close series and exported `reports/backtest_tax_ledger_primary.csv`.
- Re-ran primary window (2011-06-23~2026-01-30): CAGR 35.07%, AfterTaxCAGR 32.16%, MDD -34.22%.
- Verified regressions: `UV_CACHE_DIR=.uv-cache uv run --offline --with pytest pytest -q` (17 passed).

### No-TV Alternative Validation (Signal QA path)
- [x] Added no-TV validation harness: `ops/scripts/generate_no_tv_validation_report.py`
- [x] Added cost sensitivity runner: `ops/scripts/run_cost_sensitivity.py`
- [x] Generated reports:
  - `reports/no_tv_validation_summary.json`
  - `reports/no_tv_transition_replay.csv`
  - `reports/cost_sensitivity_s2.csv`
- [x] Verified test baseline remains green (`17 passed`)

### After-tax Sensitivity Run (S2)
- [x] Added runner `ops/scripts/run_aftertax_sensitivity.py` (bps × initial capital)
- [x] Generated `reports/aftertax_sensitivity_s2.csv`
- [x] Re-verified baseline tests (`17 passed`)
- [x] Enhanced after-tax sensitivity report with tax-event-aware risk fields (`aftertax_mdd_raw`, `aftertax_mdd_ex_taxday`, `tax_event_days`)

### User-Original Signal Engine Backtest (Enforced)
- [x] Re-ran using `reports/signals_s1_s2_s3_user_original.csv` as the only signal source
- [x] Generated summary: `reports/user_signal_backtest_summary.csv`
- [x] Generated after-tax sensitivity on user signal: `reports/aftertax_sensitivity_user_signal_s2.csv`

### Phase 2 Brainstorming Finalization
- [x] 목표/가드레일 확정 (세후 CAGR 우선, MDD -50% 이내)
- [x] 접근안 확정 (Grid + 안정성 게이트)
- [x] 설계 문서 작성: `docs/plans/2026-03-06-performance-improvement-design.md`
- [x] 구현 계획 문서 작성: `docs/plans/2026-03-06-performance-improvement-implementation-plan.md`

### Phase 2 Execution (Task1~Task7) - Autopilot
- [x] Task1: `src/tqqq_strategy/experiments/phase2_config.py` 구현 (grid + 제약검증)
- [x] Task2: `src/tqqq_strategy/experiments/phase2_runner.py` 구현 (원본 신호엔진 기반 후보 평가)
- [x] Task3: `src/tqqq_strategy/experiments/phase2_oos.py` 구현 (IS/OOS 분할 + 유지율 게이트)
- [x] Task4: `ops/scripts/run_phase2_coarse.py` 실행 -> `experiments/trials.csv` (64 rows)
- [x] Task5: `ops/scripts/run_phase2_fine.py` 실행 -> `experiments/trials_fine.csv` (90 rows)
- [x] Task6: `ops/scripts/select_phase2_best.py` 실행 -> `experiments/passed_leaderboard.csv`, `experiments/best_config.json`
- [x] Task7: 단위테스트 추가/검증 (`tests/experiments/test_phase2_constraints.py`, `tests/experiments/test_phase2_oos.py`)

### Phase 2 Key Result
- baseline(after-tax CAGR): 38.60%
- best(after-tax CAGR): 39.81%
- delta: +1.22%p
- hard gates: MDD pass, OOS retention pass(0.704)

### Phase 2 Overfitting Stress Test
- [x] Added window stress script: `ops/scripts/run_phase2_stress_test.py`
- [x] Generated: `experiments/stress_test_windows.csv`, `experiments/stress_test_summary.json`
- [x] Result: best config improved after-tax CAGR in 5/5 windows (avg +0.80%p)
- [x] User-requested pre-2011 stress window added and executed (`PRE2011: 2010-02-11~2011-06-22`)
- [x] Extended window report generated on `data/user_input_2000.csv`: `experiments/pre2011_stress_test_windows.csv`, `experiments/pre2011_stress_test_summary.json`
- [x] Extended stress test to earlier windows with synthetic pre-live dataset (`data/user_input_2000_ext.csv`)
- [x] Generated `experiments/ext2000_stress_test_windows.csv` and `experiments/ext2000_stress_test_summary.json`

### Phase 3 Task A - Telegram Daily Signal Alert
- [x] Implement telegram sender module (message formatter + HTTP send + dry-run)
- [x] Implement daily job orchestration (latest signal read + idempotency key + send)
- [x] Add tests for formatter/idempotency/no-duplicate behavior
- [x] Add CLI script for manual daily run and verify pytest green

### Phase 3 Task A Review
- Added `src/tqqq_strategy/ops/telegram_alert.py` with stdlib `urllib` Telegram send and dry-run support.
- Replaced `src/tqqq_strategy/ops/daily_job.py` with latest/previous signal read, idempotency key generation via `build_alert_key`, duplicate-skip state handling, and S2 transition message generation.
- Added CLI `ops/scripts/run_daily_telegram_alert.py` to read `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_DRY_RUN` and print result JSON (defaults to dry-run when token/chat is missing).
- Added tests: `tests/ops/test_telegram_alert.py`, `tests/ops/test_daily_job.py`.
- Verification:
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/ops/test_telegram_alert.py tests/ops/test_daily_job.py` → `3 passed in 0.03s`
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ops` → `4 passed in 0.02s`
- Follow-up hardening after code review:
  - dry-run no longer persists idempotency state
  - CLI exits non-zero on real send failure
  - required CSV column validation added
  - atomic state-file write via temp+replace
  - extra tests added (dry-run no-persist, missing-column error)
- [x] Added market-close automation wrapper: `ops/scripts/run_daily_close_alert.sh`
- [x] Registered user crontab (KST Tue-Sat 05:20 & 06:20) with idempotent duplicate protection
