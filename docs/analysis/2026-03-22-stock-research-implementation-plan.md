# Stock Research 고도화 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `StockResearchManager`를 현재의 hybrid workbench에서 한 단계 더 끌어올려, Screener + Detail + Compare + Evidence 흐름이 실제로 이어지는 주식 리서치 작업대로 완성한다.

**Architecture:** backend는 `stock_research_workspace`를 중심으로 리스트/큐/비교 seed/evidence seed를 점진적으로 확장하고, 프론트는 이를 workbench skeleton으로 소비한다. 상세 패널의 풍부한 차트/뉴스/기관 브리프는 초기에는 hybrid(backend seed + fixture augmentation)로 연결하고, 이후 실제 데이터 소스로 단계적 대체를 전제로 설계한다.

**Tech Stack:** Python snapshot pipeline (`src/tqqq_strategy/ops/dashboard_snapshot.py`, `app/api/main.py`), React + TypeScript (`app/web/src/pages/managers/StockResearchManager.tsx`, `components/stock-research/*`), Node test + pytest 검증

---

## Scope

이번 계획서의 범위는 아래 4개 축입니다.

1. **Screener-like 리스트 고도화**
2. **Compare slot 실제 기능화**
3. **Evidence layer 추가**
   - 차트
   - 주요 뉴스
   - 기관/수급 브리프
4. **Queue → List → Detail → Action 흐름 정교화**

비범위:
- 완전한 뉴스 크롤러/실시간 데이터 파이프라인
- 완전한 기관 보유 데이터 플랫폼
- 새로운 디자인 시스템 구축
- Research 탭 전체 재설계

---

## File Map

### Backend — Modify
- `app/api/main.py`
  - snapshot top-level 기본 블록에 Stock Research 확장 seed 추가
- `src/tqqq_strategy/ops/dashboard_snapshot.py`
  - `stock_research_workspace` 확장
  - evidence seed 생성
  - compare seed 상세화
- `src/tqqq_strategy/ai/stock_research_status.py`
  - 상태 분류 보강 시 수정

### Backend — Test
- `tests/contracts/test_dashboard_snapshot_v2.py`
- `tests/ai/test_manager_jobs.py`
- `tests/ai/test_stock_research_status.py`

### Frontend — Modify
- `app/web/src/pages/managers/StockResearchManager.tsx`
- `app/web/src/components/stock-research/StockResearchQueue.tsx`
- `app/web/src/components/stock-research/StockResearchWatchlist.tsx`
- `app/web/src/components/stock-research/StockResearchDetail.tsx`
- `app/web/src/components/stock-research/StockResearchHeader.tsx`
- `app/web/src/lib/stockResearchWorkspace.js`
- `app/web/src/lib/stockResearchWorkspace.d.ts`
- `app/web/src/types/appSnapshot.ts`
- `app/web/src/types/stockResearch.ts`

### Frontend — Create
- `app/web/src/components/stock-research/StockResearchComparePanel.tsx`
- `app/web/src/components/stock-research/StockResearchEvidencePanel.tsx`
- `app/web/src/components/stock-research/StockResearchNewsList.tsx`
- `app/web/src/components/stock-research/StockResearchFlowBar.tsx`

### Frontend — Test
- `app/web/src/lib/stockResearchWorkspace.test.js`

---

## Chunk 1: Backend workspace seed 확장

### Task 1. `stock_research_workspace` evidence seed shape 정의

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Modify: `app/api/main.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`

- [ ] **Step 1: Write the failing test**

`tests/contracts/test_dashboard_snapshot_v2.py`에 아래 기대를 추가:

```python
assert "evidence" in snap["stock_research_workspace"]
assert "chart" in snap["stock_research_workspace"]["evidence"]
assert "news" in snap["stock_research_workspace"]["evidence"]
assert "flow" in snap["stock_research_workspace"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py
```

Expected:
- FAIL with missing `evidence` / `flow`

- [ ] **Step 3: Write minimal implementation**

`_build_stock_research_workspace(...)` 안에 아래 형태 추가:

```python
"flow": {
  "pipeline": ["탐색", "관찰", "후보", "보류", "제외"],
  "active_stage": "...",
},
"evidence": {
  "chart": {...},
  "news": [...],
  "institutional_flow": {...},
}
```

- [ ] **Step 4: Run test to verify it passes**

Run same pytest command.

- [ ] **Step 5: Commit**

```bash
git add app/api/main.py src/tqqq_strategy/ops/dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py
git commit -m "Add stock research workspace evidence seed"
```

---

### Task 2. Compare seed를 실제 비교 시작점으로 보강

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`

- [ ] **Step 1: Write the failing test**

추가 기대:

```python
compare_seed = snap["stock_research_workspace"]["compare_seed"]
assert "primary_symbol" in compare_seed
assert "candidate_symbols" in compare_seed
assert "default_mode" in compare_seed
assert compare_seed["default_mode"] in {"fit", "overlap", "action"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py
```

- [ ] **Step 3: Write minimal implementation**

예:

```python
"compare_seed": {
  "primary_symbol": ...,
  "candidate_symbols": [...],
  "default_mode": "fit",
}
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/ops/dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py
git commit -m "Seed stock research compare workflow"
```

---

### Task 3. 상태 흐름(flow)용 aggregate 추가

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`

- [ ] **Step 1: Write the failing test**

```python
flow = snap["stock_research_workspace"]["flow"]
assert flow["pipeline"] == ["탐색", "관찰", "후보", "보류", "제외"]
assert "stage_counts" in flow
assert flow["stage_counts"]["관찰"] >= 0
```

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write minimal implementation**

`filters.status_counts`를 재사용해 `flow.stage_counts` 추가

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/ops/dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py
git commit -m "Add stock research flow stage aggregates"
```

---

## Chunk 2: 프론트 Screener 고도화

### Task 4. `StockResearchWatchlist`를 실제 screener처럼 강화

**Files:**
- Modify: `app/web/src/components/stock-research/StockResearchWatchlist.tsx`
- Modify: `app/web/src/types/appSnapshot.ts`
- Test: `app/web/src/lib/stockResearchWorkspace.test.js`

- [ ] **Step 1: Write the failing test**

`stockResearchWorkspace.test.js`에 다음 기대 추가:

```js
assert.deepEqual(filtered.map((item) => item.symbol), ['AAPL'])
```

이미 존재하는 필터 테스트를 확장해:
- overlap level
- priority
- held/unheld
presets도 검증

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
node --test app/web/src/lib/stockResearchWorkspace.test.js
```

- [ ] **Step 3: Write minimal implementation**

Watchlist에 추가:
- overlap quick chips
- priority chips
- 정렬 선택
- row에 recent state / evidence hint / next action preview 유지

정렬은 최소:
- score
- 최근 업데이트
- overlap 높은순
- 리스크 높은순

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add app/web/src/components/stock-research/StockResearchWatchlist.tsx app/web/src/lib/stockResearchWorkspace.* app/web/src/types/appSnapshot.ts
git commit -m "Strengthen stock research screener interactions"
```

---

### Task 5. Queue와 리스트 선택 흐름 연결 강화

**Files:**
- Modify: `app/web/src/pages/managers/StockResearchManager.tsx`
- Modify: `app/web/src/components/stock-research/StockResearchQueue.tsx`
- Test: `app/web/src/lib/stockResearchWorkspace.test.js`

- [ ] **Step 1: Write the failing test**

테스트 추가:

```js
assert.equal(updated.selected_item_id, 'stock-nvda')
```

queue 선택 시:
- selected symbol
- visible list
- detail target
가 일관되게 유지되는지 확인

- [ ] **Step 2: Run test to verify it fails**

- [ ] **Step 3: Write minimal implementation**

반영:
- queue 클릭 → selected symbol 변경
- 필터 결과에서 선택 종목이 사라지면 fallback selection
- selected item과 compare seed 동기화

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add app/web/src/pages/managers/StockResearchManager.tsx app/web/src/components/stock-research/StockResearchQueue.tsx app/web/src/lib/stockResearchWorkspace.test.js
git commit -m "Tighten stock research queue to detail flow"
```

---

## Chunk 3: Detail panel evidence / compare 고도화

### Task 6. Detail panel에 차트/evidence 패널 연결

**Files:**
- Create: `app/web/src/components/stock-research/StockResearchEvidencePanel.tsx`
- Modify: `app/web/src/components/stock-research/StockResearchDetail.tsx`
- Modify: `app/web/src/types/appSnapshot.ts`

- [ ] **Step 1: Write the failing test**

Type-level / build-level failing condition을 먼저 만들기:
- `StockResearchDetail`이 `evidence` prop을 기대하도록 변경
- build 실패 확인

- [ ] **Step 2: Run build to verify it fails**

Run:

```bash
cd app/web && npm run build
```

- [ ] **Step 3: Write minimal implementation**

연결할 내용:
- chart summary
- institutional flow brief
- key news 2~3건

주의:
- 정보는 “큰 주연 블록”이 아니라 **판단 보조 레이어**로 배치
- 차트는 현재 상세 패널의 중심 보조 도구
- 뉴스/기관 브리프는 비교적 작은 supporting cards

- [ ] **Step 4: Run build/lint to verify it passes**

Run:

```bash
cd app/web && npm run build && npm run lint
```

- [ ] **Step 5: Commit**

```bash
git add app/web/src/components/stock-research/StockResearchDetail.tsx app/web/src/components/stock-research/StockResearchEvidencePanel.tsx app/web/src/types/appSnapshot.ts
git commit -m "Attach stock research evidence layer"
```

---

### Task 7. Compare slot을 실제 비교 패널 시작점으로 연결

**Files:**
- Create: `app/web/src/components/stock-research/StockResearchComparePanel.tsx`
- Modify: `app/web/src/components/stock-research/StockResearchDetail.tsx`
- Modify: `app/web/src/pages/managers/StockResearchManager.tsx`

- [ ] **Step 1: Write the failing test**

최소 기대:
- compare seed가 있으면 “상세 비교 뷰어 열기”가 inactive placeholder가 아님
- compare candidate symbol이 노출됨

build/test로 실패 확인

- [ ] **Step 2: Run build to verify it fails**

- [ ] **Step 3: Write minimal implementation**

반영:
- compare panel 토글 상태
- `compare_seed.primary_symbol`
- `compare_seed.candidate_symbols`
를 기반으로 초기 비교 패널 구성

이번 단계는 full compare 아님.
최소한:
- primary
- secondary
- fit / overlap / next action
3행 요약 비교면 충분

- [ ] **Step 4: Run build/lint to verify it passes**

- [ ] **Step 5: Commit**

```bash
git add app/web/src/components/stock-research/StockResearchComparePanel.tsx app/web/src/components/stock-research/StockResearchDetail.tsx app/web/src/pages/managers/StockResearchManager.tsx
git commit -m "Open stock research compare workflow"
```

---

## Chunk 4: Polish / Verification

### Task 8. 전체 Stock Research UX 검증

**Files:**
- Verify only

- [ ] **Step 1: Run workspace tests**

```bash
node --test app/web/src/lib/stockResearchWorkspace.test.js
```

- [ ] **Step 2: Run frontend build/lint**

```bash
cd app/web && npm run build && npm run lint
```

- [ ] **Step 3: Run browser smoke check**

확인 경로:
- `#/managers/stocks`

체크:
- queue 클릭 시 detail 바뀜
- 검색/필터 동작
- compare slot 열림
- evidence/news/기관 브리프 보임

- [ ] **Step 4: Document remaining gaps**

남은 미해결 항목을 적을 것:
- 실제 뉴스 데이터 소스 없음
- 실제 기관/수급 데이터 소스 없음
- chart는 hybrid/fixture 보조

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Polish stock research workbench flow"
```

---

## Verification Commands (final gate)

백엔드:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q \
  tests/contracts/test_dashboard_snapshot_v2.py \
  tests/contracts/test_dashboard_snapshot_export_freshness.py \
  tests/contracts/test_wealth_home_snapshot_step1.py \
  tests/wealth/test_derived_snapshots.py \
  tests/ai/test_stock_research_status.py \
  tests/ai/test_manager_jobs.py \
  tests/ai/test_inbox_builder.py \
  tests/ai/test_orchestrator_briefs.py \
  tests/ai/test_orchestrator_policy.py \
  tests/ai/test_orchestrator_context.py \
  tests/ai/test_orchestrator_guardrails.py
```

프론트:

```bash
node --test app/web/src/lib/stockResearchWorkspace.test.js
cd app/web && npm run build && npm run lint
```

---

## Completion Criteria

- `stock_research_workspace`가 queue / filters / items / compare seed / evidence / flow를 제공
- Stock Research 리스트가 진짜 screener-like하게 동작
- queue → list → detail → action 흐름이 끊기지 않음
- compare slot이 실제 비교 패널 시작점이 됨
- 차트/뉴스/기관 브리프가 “주연”이 아니라 판단 보조 레이어로 적절히 배치됨
- build / lint / tests 모두 통과

---

## Final Note

이번 단계의 핵심은 “Stock Research를 더 화려하게 만드는 것”이 아니라,  
**backend seed를 충분히 준비해 놓고, 프론트가 이를 실제 workbench 흐름으로 소비하도록 만드는 것**입니다.  
즉, 데모를 그대로 복제하는 것이 아니라 **Screener + Detail + Compare + Evidence 흐름을 실제 작동하는 작업대**로 완성하는 것이 목표입니다.
