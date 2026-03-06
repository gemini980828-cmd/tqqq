# Implementation Plan — Action-First Dashboard MVP (2026-03-06)

## Objective
승인된 Action-First 대시보드 설계를 코드로 구현한다.

## Phase 1. Backend snapshot 확장
### Task 1
- `app/api/main.py`에 `build_dashboard_snapshot` 확장
- 반환 구조: `action_hero`, `kpi_cards`, `risk_gauges`, `event_timeline`, `ops_log`

### Task 2
- `src/tqqq_strategy/ops/dashboard_snapshot.py` 신설
- CSV/JSON 입력을 읽어 대시보드 snapshot 생성
- 이벤트 라벨링 규칙 구현

### Task 3
- 계약 테스트 추가
  - `tests/contracts/test_dashboard_snapshot_v2.py`
  - 필수 키/자료형/이벤트 최소 1건 생성 검증

## Phase 2. Frontend Dashboard 페이지 구현
### Task 4
- `app/web/src/pages/Dashboard.tsx`를 실제 UI로 구현
- 섹션별 컴포넌트:
  - ActionHero
  - KpiRow
  - RiskGaugeRow
  - EventTimeline
  - OpsLogAccordion

### Task 5
- 최소 반응형 대응
  - desktop: 2~3열 카드
  - mobile: 단일열 스택

## Phase 3. Data wiring / UX polish
### Task 6
- mock snapshot 또는 로컬 API 연결
- 무액션/액션 상태 각각 렌더 확인

### Task 7
- 상태색 규칙 적용 (Green/Amber/Red)
- `N/A` fallback UI 적용

## Phase 4. Verification
### Task 8
- 테스트 실행
  - `UV_CACHE_DIR=.uv-cache uv run --with pytest pytest -q`
- 프론트 정적 타입/빌드 점검(가능 범위)
- 샘플 스냅샷 2개(무액션/액션)로 수동 시각 검증

## Acceptance Criteria
1. 대시보드 첫 화면에서 오늘 액션/목표비중/핵심사유가 즉시 확인된다.
2. KPI 4개(세후 CAGR/MDD/1M 수익/조건 충족률)가 렌더된다.
3. 리스크 계기판 3개(Vol20/SPY200/Dist200)가 임계값 포함으로 표시된다.
4. 하단 이벤트 타임라인에 비중변경/재진입/강제청산/TP10 이벤트가 표시된다.
5. 운영 로그(run_id/alert_key)가 접이식으로 표시된다.
6. 계약 테스트 및 전체 회귀 테스트가 통과한다.

## Risk / Mitigation
- 데이터 파일 시점 불일치 → snapshot 생성시 latest-date 정규화
- 이벤트 라벨 오분류 → 규칙 기반 단위 테스트로 보호
- UI 정보 과밀 → 무액션일 요약 뷰를 기본값으로 유지
