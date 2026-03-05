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
