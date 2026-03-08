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

### Phase 3 Task A-2 - WebP 알림 포맷 정합

- [x] WebP 샘플(9551781008\_...webp) 알림 블록/문구 구조 매핑
- [x] `daily_job.py` 메시지 구성 로직을 샘플 수준으로 확장 (포지션/사유/시장요약/운영로그)
- [x] `run_daily_telegram_alert.py`에 `--data-csv` 인자 추가
- [x] ops 테스트 보강 및 회귀 통과 확인

### Phase 3 Task A-2 Review

- 메시지 포맷을 샘플 기준으로 강화:
  - `현재 포지션`, `교체 포지션`, `신호코드 전환`, `손익여부`, `로스 컷`
  - `📈 시장 데이터 요약` 내 50/100/200 이격도, 기울기 조건, SPY 필터, RSI 상태, 3캔들 이모지, 환율
  - 가격/손익 방향 이모지(🟢/🔴/⚪) 반영
- CLI 인자 확장:
  - `ops/scripts/run_daily_telegram_alert.py --data-csv <path>`
- 검증:
  - `UV_CACHE_DIR=.uv-cache uv run --offline --with pytest pytest -q tests/ops/test_telegram_alert.py tests/ops/test_daily_job.py` → `6 passed`
  - `UV_CACHE_DIR=.uv-cache uv run --offline --with pytest pytest -q` → `25 passed`
  - dry-run 실행으로 실제 메시지 렌더 확인 (`2026-01-30` 샘플)

### Phase 3 Task A-3 - GitHub Actions 서버 자동발송 전환

- [x] GitHub Actions 스케줄 워크플로 추가 (`.github/workflows/daily-telegram.yml`)
- [x] workflow_dispatch 수동 실행 경로 추가
- [x] 필수 secrets 검증 단계 추가 (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- [x] 운영 runbook 추가 (`docs/runbooks/github-actions-telegram.md`)
- [ ] GitHub 저장소 secrets 등록 후 수동 실행 1회 확인 (사용자 측)

### Phase 3 Task A-3 Review

- 일일 자동발송 워크플로 작성 완료:
  - 데이터 준비 → 원본 신호 생성 → 텔레그램 발송
  - 스케줄: `30 22 * * 1-5` (UTC)
  - 아티팩트 업로드로 실행 결과 추적 가능
- 사용자 수동작업 최소화:
  - GitHub Actions repository secret 2개만 등록하면 동작

### Phase 3 Task A-4 - Telegram UX 고도화 (액션 우선/체크리스트)

- [x] 액션 배너를 최상단에 추가 (`[액션 없음]` / `[매매 필요]`)
- [x] 신호코드 raw 전환 대신 읽기 쉬운 신호 라벨 적용
- [x] 손익 표시 분리 (일간 수익 vs 진입가 대비)
- [x] 로스컷 절대값 표시 (`$xx.xx | 진입가×0.941`)
- [x] 사유 섹션을 조건 체크리스트(✅/⬜/⚠/🚨)로 전환
- [x] 상태파일 확장 (`position_weight`, `entry_price`, `entry_date`, `tp10_done`)
- [x] ops 테스트 확장 및 회귀 통과 확인

### Phase 3 Task A-4 Review

- 구현 파일:
  - `src/tqqq_strategy/ops/daily_job.py`
  - `src/tqqq_strategy/ops/telegram_alert.py`
  - `tests/ops/test_daily_job.py`
  - `tests/ops/test_telegram_alert.py`
- 핵심 개선:
  - 메시지 최상단에서 액션 필요 여부를 즉시 판단 가능
  - 코드 전환(`2->2`) 대신 신호 라벨 표기
  - 진입가 상태 기반 손익/로스컷 절대값 제공
  - 조건 체크리스트로 사유 설명력 향상
- 검증:
  - `UV_CACHE_DIR=.uv-cache uv run --with pytest pytest -q tests/ops/test_telegram_alert.py tests/ops/test_daily_job.py` → `7 passed`
  - `UV_CACHE_DIR=.uv-cache uv run --with pytest pytest -q` → `26 passed`

### Phase 3 Task A-5 - 피드백 라운드 2 (계기판형/액션유무 분리)

- [x] 액션 유무에 따라 템플릿 분리 (무액션=요약형, 액션=상세형)
- [x] 임계값 병기 라인으로 변경 (`Vol20`, `SPY200`, `Dist200`)
- [x] 중복 라인 제거 (`현재/교체/코드전환` 반복 축소)
- [x] 50/100일 이격도 제거 (비매매 핵심 지표 제외)
- [x] 운영 로그 원본 포맷 유지 (`run_id`, `alert_key`, `dry_run`)
- [x] 테스트 보강/회귀 통과

### Phase 3 Task A-5 Review

- 핵심 반영:
  - 무액션일: 짧은 요약 템플릿 + 핵심 체크 3개
  - 액션일: 상세 템플릿 + 체크리스트 + 시장요약
  - 수치+임계값 계기판형 표기 유지
- 검증:
  - `UV_CACHE_DIR=.uv-cache uv run --with pytest pytest -q tests/ops/test_telegram_alert.py tests/ops/test_daily_job.py` → `8 passed`
  - `UV_CACHE_DIR=.uv-cache uv run --with pytest pytest -q` → `27 passed`

### Dashboard MVP Brainstorming (Action-First + Risk)

- [x] 목적 확정: A(오늘 액션 판단) + B(성과/리스크 모니터링)
- [x] 레이아웃 확정: Action Hero 상단 + KPI + 리스크 계기판 + 이벤트 타임라인 + 운영로그
- [x] 이벤트 타임라인 포함 확정
- [x] 설계 문서 작성: `docs/plans/2026-03-06-dashboard-action-first-design.md`
- [x] 구현 계획 문서 작성: `docs/plans/2026-03-06-dashboard-action-first-implementation-plan.md`

### Dashboard MVP Execution (Task 1-8)

- [x] Task 1: `app/api/main.py`의 `build_dashboard_snapshot` 확장
- [x] Task 2: `ops/dashboard_snapshot.py` 데이터 연동 MVP 구현
- [x] Task 3: `test_dashboard_snapshot_v2.py` 계약 테스트 통과
- [x] Task 4~5: `app/web/src/pages/Dashboard.tsx` 컴포넌트(ActionHero, KpiRow, RiskGauge, Timeline 등) 및 반응형 구현
- [x] Task 6~7: Mock 데이터 기반 wiring 및 컬러코드/fallback(`N/A`) 구현
- [x] Task 8: 코드 테스트 회귀 검증 완료 (28 passed)

### Dashboard MVP Review

- **Backend**: API 계약 테스트를 추가하고 `build_dashboard_snapshot`이 텔레그램 호환성과 MVP Dashboard(단일 화면) 요구사항을 모두 충족하도록 확장함.
- **Frontend**: `Dashboard.tsx`에 Action-First UX, Institutional Styling (Dark mode, 최소한의 텍스트 기반) 적용. 화면 상단에 명확하게 ActionHero 계기판, KPI, Risk 게이지가 모두 반응형으로 표현됨.


---

# TODO - Frontend dashboard UI polish (Worker 2)

- [x] Inspect current dashboard structure and ownership scope
- [x] Strengthen action hero and support mock state switching
- [x] Add KPI accent borders and improved typography/spacing
- [x] Add visible risk gauge progress bars and status badges
- [x] Enrich mock event timeline with 3-5 items per state
- [x] Verify web app build and document results

## Review

- Updated `app/web/src/pages/Dashboard.tsx` with a stronger action hero, KPI accent cards, status-badge risk gauges with progress bars, richer mock timelines, and URL-driven mock state support (`?mock=action-needed` / `?mock=no-action`).
- Updated `app/web/src/index.css` to apply Inter typography, dark background treatment, and cleaner global spacing primitives.
- Verified frontend build with `npm run build` in `app/web`.

---

# TODO - Worker 1 Dashboard Snapshot Backend

- [x] Inspect current snapshot/API contract code and available CSV/JSON inputs
- [x] Implement real-input dashboard snapshot generator in `src/tqqq_strategy/ops/dashboard_snapshot.py`
- [x] Wire `app/api/main.py` to normalize/generate the snapshot contract
- [x] Update contract tests for required keys and event timeline coverage using temp sample files
- [x] Run targeted contract tests and record results

## Review
- Snapshot generator now reads local CSV/JSON inputs (signals/data/metrics/state, optional equity) and derives action hero, KPI cards, risk gauges, event timeline, and ops log without mocks.
- API builder now accepts generation kwargs and preserves the required telegram/dashboard contract keys.
- Verified targeted contract tests with `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_telegram_blocks.py` (`4 passed`).

### Dashboard MVP Finalization (Live Snapshot Wiring)

- [x] 실데이터 snapshot generator를 static dashboard JSON export까지 연결
- [x] 프론트 App에서 `/dashboard_snapshot.json` fetch 후 live snapshot 우선 사용
- [x] Risk gauge 진행바/상태 배지/KPI accent/이벤트 뱃지 polish 반영
- [x] dashboard snapshot export, frontend build, 전체 pytest 검증 완료

### Dashboard MVP Finalization Review

- 추가 구현:
  - `ops/scripts/export_dashboard_snapshot.py`로 `app/web/public/dashboard_snapshot.json` 생성 경로 확정
  - `app/web/src/App.tsx`에서 live snapshot fetch + mock fallback 연결
  - `app/web/src/pages/Dashboard.tsx`에 action/no-action 분기, stronger risk bar, event badge, ops summary 강화
- 검증:
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_telegram_blocks.py` → `4 passed`
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q` → `30 passed`
  - `python3 ops/scripts/export_dashboard_snapshot.py` → `app/web/public/dashboard_snapshot.json` 생성 확인
  - `npm run build` (`app/web`) → production build 성공

---

# TODO - Wealth Management System Design / Planning

- [x] 투자운영 중심 자산관리 시스템 방향 재정의
- [x] 웹 레퍼런스 기반 추가 모듈 후보 정리
- [x] 1안 vs 3안 비교 후 절충안 확정
- [x] AI 구조 확정 (manager summaries + real-time orchestrator)
- [x] 데이터 truth / 비용정책 / 홈 UX / MVP 범위 확정
- [x] 설계 문서 작성 (`docs/plans/2026-03-06-wealth-management-system-design.md`)
- [x] 구현 계획 문서 작성 (`docs/plans/2026-03-06-wealth-management-system-implementation-plan.md`)

## Review

- 자산관리 시스템을 `Home / Managers / Research / Inbox / Reports` 구조로 재정의했다.
- 내부 구조는 자산 카탈로그형, 사용자 노출은 매니저형 감성을 유지하는 절충안을 채택했다.
- MVP 기준 매니저는 `Core Strategy(TQQQ) / Stocks / Real Estate / Cash & Debt`로 확정했다.
- AI 구조는 `배치/이벤트 기반 manager summaries + 사용자 요청 시 실시간 orchestrator chat`으로 확정했다.
- 비용 통제 원칙(B)을 문서화했다: 페이지 로드시 AI 호출 금지, cached summary 우선, deep analysis는 명시적 요청 기반.
- 다음 실행 문서는 `docs/plans/2026-03-06-wealth-management-system-implementation-plan.md` 기준으로 진행한다.

---

# TODO - Wealth Management System Step 1 (Foundation)

- [x] Stream A: app shell / navigation skeleton 구현
- [x] Stream B: wealth schema + manual truth inputs + 최소 derived helper 구현
- [x] Stream D: 기존 TQQQ dashboard를 Core Strategy Manager로 승격
- [x] Snapshot/API를 step-1 shell에 맞게 연결
- [x] pytest / lint / build 검증
- [x] 리뷰 기록 및 커밋

## Review

- Stream A (app shell / navigation)
  - `app/web/src/App.tsx`를 `Home / Managers / Research / Inbox / Reports` 다중 라우팅 구조로 확장했다.
  - `TopNav`, `ManagerCard`, `OrchestratorPanel`, `Managers`, `ManagersLayout` 및 manager shell 페이지를 추가했다.
  - 기존 TQQQ 단일 대시보드는 `CoreStrategyManager` 내부에서 재사용하도록 이동했다.
- Stream B (wealth truth foundation)
  - `src/tqqq_strategy/wealth/`에 `schema.py`, `manual_inputs.py`, `derived.py`, `__init__.py`를 추가했다.
  - 수동 truth 입력(`data/manual/wealth_manual.json`)을 기준으로 positions / cash_debt / stock_watchlist / property_watchlist를 canonical 형태로 정규화한다.
  - derived helper로 `build_wealth_overview`, `build_core_strategy_position`, `build_manager_cards`를 제공한다.
- Stream D (snapshot / API wiring)
  - `src/tqqq_strategy/ops/dashboard_snapshot.py`가 기존 action-first snapshot에 `wealth_home`, `wealth_overview`, `manager_cards`, `core_strategy_actuals`, `meta`를 함께 생성하도록 확장되었다.
  - `app/api/main.py`와 `ops/scripts/export_dashboard_snapshot.py`가 step-1 wealth fields를 정규화/내보내도록 갱신되었다.
  - `app/web/public/dashboard_snapshot.json`을 실데이터 기준으로 재생성했다.
- 검증
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q` → `41 passed`
  - `python3 ops/scripts/export_dashboard_snapshot.py` → `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`
  - `cd app/web && npm run lint` → `LINT_OK`
  - `cd app/web && npm run build` → production build 성공

---

# TODO - Wealth Management Step 1.5 Hardening

- [x] Task 1: Core Strategy Manager에서 Dashboard embedded 모드 완전 적용
- [x] Task 2: Home에 recent activity + inbox preview 추가
- [x] Task 3: frontend snapshot 타입 단일화
- [x] Task 4: Step 2 범위(`transactions`, `summary_store`) 문서/체크리스트 명시
- [x] Task 5: Step 1.5 전체 검증 및 review 기록

## Review (완료)

- Task 1~3 재검증 결과:
  - `CoreStrategyManager.tsx`는 `Dashboard`를 `embedded` 모드로 렌더링한다.
  - `Home.tsx`는 `recent activity`와 `inbox preview`를 포함해 desk 역할을 수행한다.
  - frontend snapshot 타입은 `app/web/src/types/appSnapshot.ts` 중심으로 공유되고 `Dashboard.tsx`는 alias로 재사용한다.
- Task 4 문서 정리:
  - `docs/plans/2026-03-06-wealth-management-system-implementation-plan.md`에 Step 2 이월 범위를 명시했다.
  - `transactions`, `assets/accounts`, `summary_store`, stale/fresh summary metadata, manager batch summary jobs를 Step 2 선행 의존성으로 분리했다.
- 검증:
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/wealth/test_schema_contract.py tests/wealth/test_derived_foundation.py tests/wealth/test_step1_dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_wealth_home_snapshot_step1.py` → `13 passed`
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q` → `41 passed`
  - `python3 ops/scripts/export_dashboard_snapshot.py` → `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`
  - `cd app/web && npm run lint` → `LINT_OK`
  - `cd app/web && npm run build` → production build 성공

## Step 2 Preconditions

- `transactions` truth contract는 Step 2에서 추가한다.
- `assets/accounts` 분리 canonical entity는 Step 2에서 판단/도입한다.
- `summary_store` + stale/fresh manager cache는 Step 2 첫 작업으로 선행한다.
- Home inbox 자동 합성은 Step 2의 manager summary jobs 이후 연결한다.



---

# TODO - Wealth Management Step 2 (Manager Summaries + Inbox)

- [x] Task 1: `summary_store` foundation + cached summary contract/tests 구현
- [x] Task 2: manager summary batch jobs(`manager_jobs.py`, `run_manager_summaries.py`) 구현
- [x] Task 3: Home inbox builder + snapshot export integration 구현
- [x] Task 4: Step 2 focused/full verification 및 review 기록

### Step 2 Task 2 - Manager Summary Batch Jobs

- [x] Confirm RED state for `tests/ai/test_manager_jobs.py`
- [x] Implement deterministic manager summary builders in `src/tqqq_strategy/ai/manager_jobs.py`
- [x] Add package/script wiring (`src/tqqq_strategy/ai/__init__.py`, `ops/scripts/run_manager_summaries.py`)
- [x] Run targeted pytest + script smoke and capture exact results

### Step 2 Task 2 Review

- Fresh verification (this session): `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_manager_jobs.py` → `2 passed`.
- Fresh CLI smoke (this session): `python3 ops/scripts/run_manager_summaries.py --signals <tmp>/signals.csv --data <tmp>/data.csv --metrics <tmp>/metrics.csv --state <tmp>/state.json --manual-truth <tmp>/wealth_manual.json --summary-store <tmp>/manager_summaries.json` → exit 0, wrote four manager summaries.
- RED 확인: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_manager_jobs.py`에서 `ModuleNotFoundError: No module named 'tqqq_strategy.ai.manager_jobs'`로 실패를 확인했다.
- Step 2 선행조건으로 `transactions` canonical support와 `build_liquidity_summary`/summary-source helper를 추가하고 관련 테스트(`tests/wealth/test_schema_contract.py`, `tests/wealth/test_derived_snapshots.py`)를 보강했다.
- 구현 파일: `src/tqqq_strategy/ai/__init__.py`, `src/tqqq_strategy/ai/manager_jobs.py`, `ops/scripts/run_manager_summaries.py`, `tests/ai/test_manager_jobs.py`.
- 검증: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_schema_contract.py tests/wealth/test_derived_snapshots.py tests/wealth/test_summary_store.py tests/ai/test_manager_jobs.py` → `15 passed`; 스크립트 smoke run → `SCRIPT_SMOKE_OK`.

### Step 2 Task 3/4 - Home Inbox + Snapshot Export Integration

- [x] Add deterministic Home inbox builder (`src/tqqq_strategy/ai/inbox_builder.py`) with severity ordering
- [x] Extend dashboard snapshot / API contract with `home_inbox`, `manager_summaries`, `liquidity_summary`, `summary_source_version`
- [x] Refresh manager summaries before `ops/scripts/export_dashboard_snapshot.py` writes the public snapshot
- [x] Wire Home inbox preview + manager card affordances on the frontend shell
- [x] Run focused/full verification and capture results

### Step 2 Task 3/4 Review

- Added `src/tqqq_strategy/ai/inbox_builder.py` and `tests/ai/test_inbox_builder.py` so Home inbox items are synthesized from core-strategy action/gap, cash-debt guardrails, and stock/real-estate review states.
- Extended `src/tqqq_strategy/ops/dashboard_snapshot.py` to load cached manager summaries, compute `liquidity_summary`, expose `manager_summaries`, `home_inbox`, and persist `summary_source_version` in `meta`.
- Updated `app/api/main.py`, `app/web/src/types/appSnapshot.ts`, `app/web/src/pages/Home.tsx`, and `app/web/src/components/ManagerCard.tsx` so the shell consumes cached inbox items and richer manager-card metadata.
- `ops/scripts/export_dashboard_snapshot.py` now refreshes manager summaries before writing `app/web/public/dashboard_snapshot.json`; `.github/workflows/daily-telegram.yml` now runs the refresh/export path and uploads the summary cache + snapshot artifact.
- Verification:
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_schema_contract.py tests/wealth/test_derived_snapshots.py tests/wealth/test_summary_store.py tests/ai/test_manager_jobs.py tests/ai/test_inbox_builder.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_wealth_home_snapshot_step1.py` → `19 passed`
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q` → `51 passed`
  - `python3 ops/scripts/run_manager_summaries.py` → exit 0, four manager summaries printed
  - `python3 ops/scripts/export_dashboard_snapshot.py` → `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`
- Final hardening: `summary_source_version`를 signal as-of date 기준으로 정규화해 export 직후에도 manager summary cache가 `stale: false`로 유지되도록 맞췄다.
  - `cd app/web && npm run lint` → exit 0
  - `cd app/web && npm run build` → production build 성공

---

# TODO - Wealth Management Step 2.5 Housekeeping

- [x] Task 1: generated summary artifact ignore rule 추가
- [x] Task 2: dashboard snapshot 기본 `next_run_at`를 deterministic 하게 고정
- [x] Task 3: summary refresh/export freshness regression test 추가
- [x] Task 4: workflow/UI status 문구 drift 정리
- [x] Task 5: 검증 및 review 기록

## Review

- `.gitignore`에 `reports/wealth_manager_summaries.json`를 추가해 Step 2 summary cache가 로컬 작업트리를 오염시키지 않도록 정리했다.
- `src/tqqq_strategy/ops/dashboard_snapshot.py`의 기본 `next_run_at`를 현재 시각이 아니라 latest signal date 기준(`+1 day @ 22:30 UTC`)으로 계산하게 바꿔 exported snapshot이 deterministic 하게 유지되도록 했다.
- `tests/contracts/test_dashboard_snapshot_v2.py`에 refresh → generate 흐름 회귀 테스트를 추가해 `summary_source_version`이 signal as-of date 기준으로 맞고, exported snapshot의 manager summaries가 `stale: false` 상태를 유지함을 검증했다.
- `.github/workflows/daily-telegram.yml`가 실제로 `reports/wealth_manager_summaries.json`과 `app/web/public/dashboard_snapshot.json`을 아티팩트로 업로드하도록 맞췄다.
- `OrchestratorPanel`, `Managers`, 각 manager shell의 stale `Step 1` 문구를 `Step 2 Ready` / summary cache 연동 상태 기준으로 정리했다.
- 검증:
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/ai/test_manager_jobs.py tests/ai/test_inbox_builder.py tests/wealth/test_summary_store.py tests/wealth/test_derived_snapshots.py` → `13 passed`
  - `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q` → `52 passed`
  - `python3 ops/scripts/run_manager_summaries.py` → exit 0, 4개 manager summary refresh 확인
  - `python3 ops/scripts/export_dashboard_snapshot.py` → `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`
  - exported snapshot check → `next_run_at=2026-01-31T22:30:00+00:00`, all manager summaries `stale: false`
  - `cd app/web && npm run lint` → exit 0
  - `cd app/web && npm run build` → production build 성공
