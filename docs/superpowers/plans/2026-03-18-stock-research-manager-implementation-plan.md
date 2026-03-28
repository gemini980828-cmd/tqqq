# Stock Research Manager Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** scaffold-only 상태인 Stock Research Manager를 점수순 watchlist + 차트 중심 상세 workspace + 최소 backend summary contract 정합성을 갖춘 usable manager surface로 구현한다.

**Architecture:** backend는 stock_research 상태 정규화와 기존 summary/inbox contract 정합성만 최소 보강하고, 실제 manager workspace의 상세 분석 데이터는 frontend static fixture + adapter로 파생한다. UI는 `StockResearchManager.tsx`를 얇은 조립 파일로 만들고, header / watchlist / detail / mini-chart를 분리 컴포넌트로 나눠서 차트 중심 C안 workspace를 구성한다. 단, 이번 구현은 **기능 동작 우선 / UI 야심 최소화**를 원칙으로 하며, 새 시각 실험 대신 기존 자산관리 대시보드의 카드 톤·간격·색 위계를 그대로 따라간다.

**Tech Stack:** Python 3.12 + pytest, React 19 + TypeScript 5.9, Node built-in test runner (`node --test`), Vite, ESLint

---

## File Structure

### Backend / contracts

- Create: `src/tqqq_strategy/ai/stock_research_status.py`
  - stock_research 상태 정규화와 candidate 판별의 단일 source
- Modify: `src/tqqq_strategy/ai/manager_jobs.py:31-101`
  - stock_research summary builder가 정규화 규칙을 사용하도록 변경
- Modify: `src/tqqq_strategy/ai/inbox_builder.py:83-96`
  - stock_research inbox candidate 판별이 정규화 규칙을 사용하도록 변경
- Modify: `tests/ai/test_manager_jobs.py`
  - legacy 상태(`매수후보`, `검토`)가 summary count에 반영되는지 보호
- Modify: `tests/ai/test_inbox_builder.py`
  - legacy 상태도 stock_research inbox item 생성 조건에 포함되는지 보호
- Create: `tests/ai/test_stock_research_status.py`
  - 상태 정규화 helper 단위 테스트

### Frontend model / fixture

- Create: `app/web/src/types/stockResearch.ts`
  - `StockResearchStatus`, `StockResearchItemViewModel`, `StockResearchViewModel` 등 frontend-only types
- Create: `app/web/src/lib/stockResearchFixture.js`
  - symbol-keyed static fixture source
- Create: `app/web/src/lib/stockResearchFixture.d.ts`
  - fixture module typing
- Create: `app/web/src/lib/stockResearchWorkspace.js`
  - fixture → view model adapter, local summary derivation, selection helpers
- Create: `app/web/src/lib/stockResearchWorkspace.d.ts`
  - adapter public typing
- Create: `app/web/src/lib/stockResearchWorkspace.test.js`
  - node:test 기반 adapter regression tests

### Frontend UI

- Create: `app/web/src/components/stock-research/StockResearchHeader.tsx`
  - manager 내부 header summary + stale badge
- Create: `app/web/src/components/stock-research/StockResearchWatchlist.tsx`
  - score순 리스트, held badge, status pill, selection UI
- Create: `app/web/src/components/stock-research/StockResearchMiniChart.tsx`
  - dependency-free SVG/div 차트
- Create: `app/web/src/components/stock-research/StockResearchDetail.tsx`
  - judgment header + chart + macro/options/memo/capture cards
- Modify: `app/web/src/pages/managers/StockResearchManager.tsx:1-18`
  - scaffold 제거, local state + adapter + child components 조립

### Review / tracking

- Modify: `tasks/todo.md`
  - 진행 체크 및 review evidence 기록

---

## Chunk 1: Backend contracts + frontend model foundation

### Task 1: Normalize stock research statuses once and reuse everywhere

**Files:**
- Create: `src/tqqq_strategy/ai/stock_research_status.py`
- Modify: `src/tqqq_strategy/ai/manager_jobs.py:31-101`
- Modify: `src/tqqq_strategy/ai/inbox_builder.py:83-96`
- Create: `tests/ai/test_stock_research_status.py`
- Modify: `tests/ai/test_manager_jobs.py`
- Modify: `tests/ai/test_inbox_builder.py`

- [ ] **Step 1: Write the failing helper tests first**

```python
from tqqq_strategy.ai.stock_research_status import normalize_stock_status, is_candidate_status

def test_normalize_stock_status_maps_legacy_values() -> None:
    assert normalize_stock_status("매수후보") == "후보"
    assert normalize_stock_status("검토") == "후보"
    assert normalize_stock_status("") == "탐색"

def test_is_candidate_status_accepts_normalized_candidates() -> None:
    assert is_candidate_status("후보") is True
    assert is_candidate_status("매수후보") is True
    assert is_candidate_status("검토") is True
    assert is_candidate_status("관찰") is False
```

- [ ] **Step 2: Run the helper tests and confirm import failure**

Run:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_stock_research_status.py
```

Expected: FAIL with `ModuleNotFoundError` or missing symbol error for `tqqq_strategy.ai.stock_research_status`

- [ ] **Step 3: Implement the minimal shared helper**

```python
NORMALIZED_CANDIDATE_STATUSES = {"후보"}
LEGACY_STATUS_MAP = {
    "매수후보": "후보",
    "검토": "후보",
    "관찰": "관찰",
    "후보": "후보",
    "보류": "보류",
    "제외": "제외",
}

def normalize_stock_status(raw: str | None) -> str:
    key = str(raw or "").strip()
    return LEGACY_STATUS_MAP.get(key, "탐색")

def is_candidate_status(raw: str | None) -> bool:
    return normalize_stock_status(raw) in NORMALIZED_CANDIDATE_STATUSES
```

- [ ] **Step 4: Update stock summary builder to use normalized counting**

Implementation notes:

```python
watchlist = list(manual_inputs.get("stock_watchlist", []))
normalized = [normalize_stock_status(row.get("status")) for row in watchlist]
candidate_count = sum(1 for status in normalized if status == "후보")
observe_count = sum(1 for status in normalized if status == "관찰")
first_candidate = next(
    (str(row.get("symbol")) for row in watchlist if normalize_stock_status(row.get("status")) == "후보"),
    None,
)
```

- [ ] **Step 5: Update home inbox builder to use the same candidate rule**

Implementation notes:

```python
stock_candidates = [
    row for row in manual_inputs.get("stock_watchlist", [])
    if is_candidate_status(row.get("status"))
]
```

- [ ] **Step 6: Add/adjust regression tests for summary and inbox**

In `tests/ai/test_manager_jobs.py`, add one legacy candidate row:

```python
{"idea_id": "stock-3", "symbol": "AAPL", "status": "매수후보", "memo": "legacy candidate"}
```

In `tests/ai/test_inbox_builder.py`, replace the current stock row with a non-candidate and add a legacy-only candidate row:

```python
{"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "not candidate anymore"},
{"idea_id": "stock-3", "symbol": "AAPL", "status": "매수후보", "memo": "legacy candidate"},
# update SUMMARIES["stock_research"]["recommended_actions"] to ["AAPL 후속 리서치 정리"]
```

Expected assertions:

```python
assert records["stock_research"]["key_points"] == ["관심종목 3개", "후보 2개", "관찰 1개"]
stock_item = next(item for item in items if item["manager_id"] == "stock_research")
assert "AAPL" in stock_item["detail"] or "AAPL" in stock_item["recommended_action"]
```

- [ ] **Step 7: Run the targeted backend test set**

Run:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q \
  tests/ai/test_stock_research_status.py \
  tests/ai/test_manager_jobs.py \
  tests/ai/test_inbox_builder.py \
  tests/wealth/test_derived_snapshots.py
```

Expected: all listed tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/tqqq_strategy/ai/stock_research_status.py \
  src/tqqq_strategy/ai/manager_jobs.py \
  src/tqqq_strategy/ai/inbox_builder.py \
  tests/ai/test_stock_research_status.py \
  tests/ai/test_manager_jobs.py \
  tests/ai/test_inbox_builder.py
git commit -m "feat: normalize stock research statuses"
```

### Task 2: Build a frontend-only Stock Research workspace model with fixture-backed detail data

**Files:**
- Create: `app/web/src/types/stockResearch.ts`
- Create: `app/web/src/lib/stockResearchFixture.js`
- Create: `app/web/src/lib/stockResearchFixture.d.ts`
- Create: `app/web/src/lib/stockResearchWorkspace.js`
- Create: `app/web/src/lib/stockResearchWorkspace.d.ts`
- Create: `app/web/src/lib/stockResearchWorkspace.test.js`

- [ ] **Step 1: Write the failing node tests before implementation**

```js
import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildStockResearchViewModel,
  normalizeResearchStatus,
} from './stockResearchWorkspace.js'

test('normalizeResearchStatus maps legacy statuses into the five-state model', () => {
  assert.equal(normalizeResearchStatus('매수후보'), '후보')
  assert.equal(normalizeResearchStatus('검토'), '후보')
  assert.equal(normalizeResearchStatus(undefined), '탐색')
})

test('buildStockResearchViewModel sorts non-empty items by score and auto-selects the top row', () => {
  const model = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: {
      BBB: {
        id: 'b',
        symbol: 'BBB',
        company_name: 'BBB',
        status: '관찰',
        primary_reason: 'fallback',
        is_held: false,
        hold_action: null,
        display_judgment: '매수 후보',
        score_drivers: [],
        risk_flags: [],
        sector_overlap_flags: [],
        overlap_details: [],
        scoring_breakdown: { stock_quality_raw: 50, portfolio_fit_raw: 50, concentration_penalty: 0 },
        chart_series: [],
        chart_markers: [],
        price_zones: [],
        chart_notes: [],
        macro_summary: '',
        options_summary: '',
        memo: '',
        next_action: '',
        captures: [],
      },
      AAA: {
        id: 'a',
        symbol: 'AAA',
        company_name: 'AAA',
        status: '후보',
        primary_reason: 'better',
        is_held: false,
        hold_action: null,
        display_judgment: '매수 후보',
        score_drivers: [],
        risk_flags: [],
        sector_overlap_flags: [],
        overlap_details: [],
        scoring_breakdown: { stock_quality_raw: 90, portfolio_fit_raw: 90, concentration_penalty: 0 },
        chart_series: [],
        chart_markers: [],
        price_zones: [],
        chart_notes: [],
        macro_summary: '',
        options_summary: '',
        memo: '',
        next_action: '',
        captures: [],
      },
    },
  })
  assert.equal(model.selected_item_id, 'a')
  assert.equal(model.items[0].symbol, 'AAA')
})
```

- [ ] **Step 2: Run the node tests and confirm they fail**

Run:

```bash
cd app/web && node --test src/lib/stockResearchWorkspace.test.js
```

Expected: FAIL with module not found for `stockResearchWorkspace.js`

- [ ] **Step 3: Define the frontend-only types exactly once**

Include at minimum:

```ts
export type StockResearchStatus = '탐색' | '관찰' | '후보' | '보류' | '제외'
export type StockResearchJudgment = '매수 후보' | '추가매수 후보' | '보유 유지' | '축소 검토' | '제외'
export type StockChartPoint = { date: string; close: number; ma20?: number; ma50?: number }
export type StockChartMarker = { kind: 'earnings' | 'risk' | 'memo'; date: string; label: string }
export type StockPriceZone = { label: string; value: number }
export type StockCaptureThumb = { id: string; label: string; image_url: string }
export type StockOverlapDetail = {
  type: 'sector' | 'theme' | 'holding'
  label: string
  matched_symbol?: string
  impact: 'low' | 'medium' | 'high'
  reason: string
}
export type StockResearchItemViewModel = {
  id: string
  symbol: string
  company_name: string
  status: StockResearchStatus
  buy_priority_score: number
  primary_reason: string
  score_drivers: string[]
  is_held: boolean
  hold_action: '추가매수 후보' | '보유 유지' | '축소 검토' | null
  display_judgment: StockResearchJudgment
  risk_flags: string[]
  sector_overlap_flags: string[]
  overlap_details: StockOverlapDetail[]
  scoring_breakdown: {
    stock_quality_raw: number
    portfolio_fit_raw: number
    concentration_penalty: number
  }
  chart_series: StockChartPoint[]
  chart_markers: StockChartMarker[]
  price_zones: StockPriceZone[]
  chart_notes: string[]
  macro_summary: string
  options_summary: string
  memo: string
  next_action: string
  captures: StockCaptureThumb[]
}
export type StockResearchViewModel = {
  generated_at: string
  items: StockResearchItemViewModel[]
  selected_item_id: string | null
  status_counts: Record<StockResearchStatus, number>
  top_candidates: string[]
  summary_line: string
  warning_line: string | null
}

export type StockResearchHeaderState = {
  top_candidates: string[]
  summary_line: string
  warning_line: string | null
  is_stale: boolean
}
```

- [ ] **Step 4: Add a small but realistic static fixture**

Create a **symbol-keyed object** with at least three symbols:

```js
export const STOCK_RESEARCH_FIXTURE = {
  NVDA: {
    id: 'stock-nvda',
    symbol: 'NVDA',
    company_name: 'NVIDIA',
    status: '후보',
    primary_reason: '추세 유지 + 성장성 + 포트 적합도 우수',
    is_held: false,
    hold_action: null,
    display_judgment: '매수 후보',
    score_drivers: ['성장 모멘텀', '섹터 중복'],
    risk_flags: ['반도체 섹터 중복 높음'],
    sector_overlap_flags: ['반도체 중복 높음'],
    scoring_breakdown: { stock_quality_raw: 88, portfolio_fit_raw: 82, concentration_penalty: 9 },
    chart_series: [{ date: '2026-03-10', close: 118 }, { date: '2026-03-11', close: 121 }],
    chart_markers: [{ kind: 'earnings', date: '2026-03-15', label: '실적' }],
    price_zones: [{ label: '지지', value: 112 }],
    chart_notes: ['20일선 위', '실적 전 변동성 확대'],
    macro_summary: '금리 안정과 성장주 선호가 이어지는 구간입니다.',
    options_summary: '실적 전 IV 상승이 관찰됩니다.',
    memo: 'AI 인프라 핵심 수혜 여부 추적',
    next_action: '실적 발표 후 가이던스 확인',
    captures: [{ id: 'nvda-chart', label: '차트 캡처', image_url: '/vite.svg' }],
    overlap_details: [{ type: 'sector', label: '반도체', impact: 'high', reason: 'AI 반도체 노출이 이미 높습니다.' }],
  },
  AMZN: {
    id: 'stock-amzn',
    symbol: 'AMZN',
    company_name: 'Amazon',
    status: '관찰',
    primary_reason: '중복은 낮지만 아직 확신은 부족',
    is_held: false,
    hold_action: null,
    display_judgment: '매수 후보',
    score_drivers: ['중복 낮음'],
    risk_flags: [],
    sector_overlap_flags: [],
    scoring_breakdown: { stock_quality_raw: 68, portfolio_fit_raw: 74, concentration_penalty: 2 },
    chart_series: [{ date: '2026-03-10', close: 201 }, { date: '2026-03-11', close: 204 }],
    chart_markers: [],
    price_zones: [{ label: '저항', value: 210 }],
    chart_notes: ['박스권 상단 접근'],
    macro_summary: '소비 둔화 우려와 클라우드 방어력이 혼재합니다.',
    options_summary: '옵션시장 이벤트 프리미엄은 제한적입니다.',
    memo: '클라우드 성장률 재확인 필요',
    next_action: '다음 실적 전 체크포인트 정리',
    captures: [],
    overlap_details: [],
  },
  AAPL: {
    id: 'stock-aapl',
    symbol: 'AAPL',
    company_name: 'Apple',
    status: '관찰',
    primary_reason: '품질은 괜찮지만 보유 비중과 집중도가 부담',
    is_held: true,
    hold_action: '축소 검토',
    display_judgment: '축소 검토',
    score_drivers: ['보유중', '테마 중복'],
    risk_flags: ['대형 기술주 편중'],
    sector_overlap_flags: ['대형 기술주 편중'],
    scoring_breakdown: { stock_quality_raw: 72, portfolio_fit_raw: 41, concentration_penalty: 12 },
    chart_series: [{ date: '2026-03-10', close: 188 }, { date: '2026-03-11', close: 186 }],
    chart_markers: [{ kind: 'risk', date: '2026-03-11', label: '비중 경고' }],
    price_zones: [{ label: '리스크', value: 185 }],
    chart_notes: ['상단 탄력 둔화'],
    macro_summary: '시장 우호에도 개별 비중 부담이 큽니다.',
    options_summary: '업사이드 기대보다 방어적 포지션이 많습니다.',
    memo: '추가 비중 확대는 보류',
    next_action: '비중 축소 조건 정의',
    captures: [{ id: 'aapl-note', label: '메모 캡처', image_url: '/vite.svg' }],
    overlap_details: [{ type: 'holding', label: '대형 기술주', matched_symbol: 'MSFT', impact: 'high', reason: '기존 보유와 성격이 유사합니다.' }],
  },
}
```

- [ ] **Step 5: Implement the adapter and deterministic derivation rules**

Required functions:

```js
export function normalizeResearchStatus(raw) {
  const key = String(raw ?? '').trim()
  if (key === '매수후보' || key === '검토') return '후보'
  if (key === '관찰' || key === '후보' || key === '보류' || key === '제외') return key
  return '탐색'
}

export function calculateBuyPriorityScore(breakdown, isHeld, holdAction) {
  const base = Math.round(Math.max(0, Math.min(100, breakdown.stock_quality_raw * 0.6 + breakdown.portfolio_fit_raw * 0.4 - breakdown.concentration_penalty)))
  if (!isHeld) return base
  if (holdAction === '추가매수 후보') return base
  if (holdAction === '보유 유지') return Math.max(50, Math.min(69, base))
  if (holdAction === '축소 검토') return Math.max(0, Math.min(29, base))
  return base
}

export function deriveStockResearchHeaderState(snapshot, items) {
  // top_candidates: 후보 or held+추가매수후보, score desc, max 3 symbols
  // warning_line: overlap high -> first risk flag -> null
  // summary_line: 후보 있으면 `상위 후보 {n}개 추적 중` + warning suffix, 없으면 `후보 없음, 관찰 종목 중심으로 관리 중`
  // is_stale: wealth_home.manager_cards[] stock_research stale -> top-level manager_cards[] stale -> manager_summaries.stock_research.stale
}

export function buildStockResearchViewModel({ snapshot, fixtureBySymbol }) {
  // Object.values(fixtureBySymbol) -> normalize -> score derive -> sort desc
  // status_counts must always include all five keys: 탐색/관찰/후보/보류/제외
  // selected_item_id defaults to first sorted item or null
  // generated_at: wealth_home.updated_at -> manager_summaries.stock_research.generated_at -> fixture constant timestamp
}
```

Critical behavior:

- sort by derived `buy_priority_score` descending
- `selected_item_id` defaults to first sorted item or `null`
- `generated_at` precedence:
  - `snapshot.wealth_home?.updated_at`
  - else `snapshot.manager_summaries?.stock_research?.generated_at`
  - else fixture constant timestamp
- `status_counts` must always be seeded as:
  - `{ 탐색: 0, 관찰: 0, 후보: 0, 보류: 0, 제외: 0 }`
  - then increment actual normalized statuses
- `top_candidates` includes:
  - `status === '후보'`
  - or `is_held && display_judgment === '추가매수 후보'`
  - sorted by `buy_priority_score` descending
  - capped at 3 symbols
- `warning_line` precedence:
  - first `overlap_details` item with `impact === 'high'`
  - else first `risk_flags` entry
  - else `null`
- `summary_line` generation:
  - if `top_candidates.length > 0` -> `상위 후보 {n}개 추적 중`
  - append `, ${warning_line}` when warning exists
  - else `후보 없음, 관찰 종목 중심으로 관리 중`
- stale derivation follows the spec precedence:
  - `wealth_home.manager_cards[]` stock_research stale
  - else top-level `manager_cards[]` stock_research stale
  - plus `manager_summaries.stock_research.stale`
- fallback behavior:
  - snapshot missing entirely -> use fixture-only view model, stale false
  - missing `manager_summaries.stock_research` -> keep fixture-derived summary/header, no crash
  - missing stock_research manager card -> keep workspace rendering, stale falls back to summary only

- [ ] **Step 6: Expand the node tests to lock the regression behavior**

Assert at minimum:

```js
assert.equal(calculateBuyPriorityScore(
  { stock_quality_raw: 88, portfolio_fit_raw: 82, concentration_penalty: 9 },
  false,
  null,
), 76)
assert.equal(calculateBuyPriorityScore(
  { stock_quality_raw: 72, portfolio_fit_raw: 41, concentration_penalty: 12 },
  true,
  '축소 검토',
), 29)
assert.deepEqual(model.top_candidates, ['NVDA'])
assert.equal(model.items[0].symbol, 'NVDA')
assert.equal(model.items.at(-1).display_judgment, '축소 검토')
assert.match(model.summary_line, /상위 후보/)
assert.equal(model.warning_line, 'AI 반도체 노출이 이미 높습니다.')
assert.deepEqual(model.status_counts, { 탐색: 0, 관찰: 2, 후보: 1, 보류: 0, 제외: 0 })
assert.equal(model.generated_at, 'fixture:stock-research')
assert.equal(deriveStockResearchHeaderState({}, []).summary_line, '후보 없음, 관찰 종목 중심으로 관리 중')
assert.equal(deriveStockResearchHeaderState({}, []).warning_line, null)
```

- [ ] **Step 7: Run the frontend model test**

Run:

```bash
cd app/web && node --test src/lib/stockResearchWorkspace.test.js
cd app/web && npm run lint
cd app/web && npm run build
```

Expected:

- node test PASS
- lint exits 0
- build exits 0

- [ ] **Step 8: Commit**

```bash
git add app/web/src/types/stockResearch.ts \
  app/web/src/lib/stockResearchFixture.js \
  app/web/src/lib/stockResearchFixture.d.ts \
  app/web/src/lib/stockResearchWorkspace.js \
  app/web/src/lib/stockResearchWorkspace.d.ts \
  app/web/src/lib/stockResearchWorkspace.test.js
git commit -m "feat: add stock research workspace model"
```

---

## Chunk 2: Stock Research UI assembly + verification

Prerequisite: Chunk 2는 Chunk 1에서 만든 `stockResearchWorkspace.*`, `stockResearchFixture.*`, `stockResearch.ts`가 이미 존재한다는 전제에서 진행한다.

### Task 3: Replace the scaffold page with a chart-first manager workspace

**Files:**
- Create: `app/web/src/components/stock-research/StockResearchHeader.tsx`
- Create: `app/web/src/components/stock-research/StockResearchWatchlist.tsx`
- Create: `app/web/src/components/stock-research/StockResearchMiniChart.tsx`
- Create: `app/web/src/components/stock-research/StockResearchDetail.tsx`
- Modify: `app/web/src/lib/stockResearchWorkspace.js`
- Modify: `app/web/src/lib/stockResearchWorkspace.d.ts`
- Modify: `app/web/src/lib/stockResearchWorkspace.test.js`
- Modify: `app/web/src/pages/managers/StockResearchManager.tsx:1-18`

- [ ] **Step 1: Add a concrete page assembly acceptance checklist to `tasks/todo.md` before coding**

Write this checklist into the task notes / implementation scratchpad and treat it as the page-level acceptance gate:

- async snapshot load after first render must refresh header seed data
- default selected row must open the top-scored symbol
- detail panel status action must update watchlist row + header counts
- memo / next action edits must stay local to the manager route

Because this repo has no React test runner, these behaviors are locked by Task 2 adapter tests plus lint/build/manual verification here.

- [ ] **Step 2: Implement a thin page shell that only wires state and data**

Target shape:

```tsx
export default function StockResearchManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const initialModel = useMemo(() => buildStockResearchViewModel({ snapshot, fixtureBySymbol: STOCK_RESEARCH_FIXTURE }), [snapshot])
  const [model, setModel] = useState(initialModel)
  useEffect(() => {
    setModel(buildStockResearchViewModel({ snapshot, fixtureBySymbol: STOCK_RESEARCH_FIXTURE }))
  }, [snapshot])
  const managerCard =
    snapshot?.wealth_home?.manager_cards?.find((card) => card.manager_id === 'stock_research') ??
    snapshot?.manager_cards?.find((card) => card.manager_id === 'stock_research')
  const managerSummary = snapshot?.manager_summaries?.stock_research
  const selected = model.items.find((item) => item.id === model.selected_item_id) ?? null
  const headerState = useMemo(() => deriveStockResearchHeaderState(snapshot, model.items), [snapshot, model.items])
  // select / status / memo / next-action handlers
}
```

Keep `StockResearchManager.tsx` responsible only for:

- model initialization
- snapshot change sync (`useEffect`)
- header seed sourcing:
  - `wealth_home.manager_cards[]` stock_research 우선
  - 없으면 top-level `manager_cards[]`
  - `managerSummary`는 `manager_summaries.stock_research`
- local state update handlers
- component composition

- [ ] **Step 3: Implement `StockResearchHeader.tsx`**

Render:

- manager title
- `summary_line`
- `warning_line` when present
- 상위 후보 1개 강조 카드 (`top_candidates[0]`)
- backend summary seed:
  - `managerCard.headline` as short seed line
  - `managerCard.summary` or `managerSummary.summary_text` as secondary copy
- 오늘의 다음 액션 1개 (`managerCard.recommended_action` or first summary action)
- top candidate symbols
- status counts
- stale badge when `headerState.is_stale`

Example interface:

```tsx
export function StockResearchHeader({
  model,
  headerState,
  managerCard,
  managerSummary,
}: {
  model: StockResearchViewModel
  headerState: StockResearchHeaderState
  managerCard?: ManagerCardSummary
  managerSummary?: ManagerSummaryRecord
}) { /* ... */ }
```

- [ ] **Step 4: Implement `StockResearchWatchlist.tsx`**

Render one selectable row per item with:

- symbol / company name
- score
- status pill
- held badge
- one-line reason
- risk/driver chips
- empty watchlist copy: `관심종목이 없습니다. 새 후보를 추가하세요.`

Required props:

```tsx
type Props = {
  items: StockResearchItemViewModel[]
  selectedItemId: string | null
  onSelect: (itemId: string) => void
  onStatusChange: (itemId: string, nextStatus: StockResearchStatus) => void
}
```

- [ ] **Step 5: Implement `StockResearchMiniChart.tsx` without new dependencies**

Use a simple inline SVG:

```tsx
export function StockResearchMiniChart({
  series,
  markers,
}: {
  series: StockChartPoint[]
  markers: StockChartMarker[]
}) {
  // polyline + marker dots/labels; show fallback copy on empty
}
```

Empty-state rule:

- if no series → render `차트 데이터 없음`

- [ ] **Step 6: Implement `StockResearchDetail.tsx`**

Render blocks in this order:

1. judgment header (`buy_priority_score`, `display_judgment`, `primary_reason`, breakdown)
2. chart block (mini chart + `chart_markers` + zones + notes)
3. macro / options / risk cards
4. memo textarea + next-action textarea
5. captures strip
6. overlap detail list

Required props:

```tsx
type Props = {
  item: StockResearchItemViewModel | null
  onStatusChange: (itemId: string, nextStatus: StockResearchStatus) => void
  onMemoChange: (itemId: string, nextMemo: string) => void
  onNextActionChange: (itemId: string, nextAction: string) => void
}
```

Fallback rules:

- no selected item → `종목을 선택하면 상세 분석이 열립니다.`
- empty captures → `캡처 없음`
- empty overlap details → `중복 경고 없음`
- status action UI must expose at least `탐색 / 관찰 / 후보 / 보류 / 제외`

- [ ] **Step 7: Wire local state updates in the page**

Implement:

```tsx
onSelect(itemId)
onStatusChange(itemId, nextStatus)
onMemoChange(itemId, nextMemo)
onNextActionChange(itemId, nextAction)
```

State rules:

- use a pure helper from `app/web/src/lib/stockResearchWorkspace.js`, e.g.

```js
export function rederiveStockResearchViewModel({ snapshot, previousModel, updater }) {
  // apply updater to items -> recompute score sort -> recompute status_counts/top_candidates/summary_line/warning_line
}
```

- update `items`
- recompute sorted order if status changes
- recompute `display_judgment`, `status_counts`, `top_candidates`, `summary_line`, `warning_line`
- keep the currently open `selected_item_id` if that item still exists after re-sort
- do **not** mutate `snapshot`
- add/update a node:test case in `stockResearchWorkspace.test.js` that proves re-derive after status change updates ordering + counts + summary

- [ ] **Step 8: Run frontend verification**

Run:

```bash
cd app/web && node --test src/lib/stockResearchWorkspace.test.js
cd app/web && npm run lint
cd app/web && npm run build
```

Expected:

- node test PASS
- lint exits 0
- build exits 0

- [ ] **Step 9: Commit**

```bash
git add app/web/src/pages/managers/StockResearchManager.tsx \
  app/web/src/lib/stockResearchWorkspace.js \
  app/web/src/lib/stockResearchWorkspace.d.ts \
  app/web/src/lib/stockResearchWorkspace.test.js \
  app/web/src/components/stock-research/StockResearchHeader.tsx \
  app/web/src/components/stock-research/StockResearchWatchlist.tsx \
  app/web/src/components/stock-research/StockResearchMiniChart.tsx \
  app/web/src/components/stock-research/StockResearchDetail.tsx
git commit -m "feat: build stock research manager workspace"
```

### Task 4: Final integration verification and review notes

**Files:**
- Modify: `tasks/todo.md`

- [ ] **Step 1: Run the full targeted verification set**

Run:

```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q \
  tests/ai/test_stock_research_status.py \
  tests/ai/test_manager_jobs.py \
  tests/ai/test_inbox_builder.py \
  tests/wealth/test_derived_snapshots.py

cd app/web && node --test src/lib/stockResearchWorkspace.test.js
cd app/web && npm run lint
cd app/web && npm run build
```

Expected:

- pytest: all listed tests PASS
- node test: PASS
- lint/build: exit 0

- [ ] **Step 2: Manually inspect the manager route in dev/preview**

Run one of:

```bash
cd app/web && npm run dev
```

Open:

```text
http://localhost:5173/#/managers/stocks
```

or

```bash
cd app/web && npm run build
python3 -m http.server 4175 -d dist
```

Open:

```text
http://localhost:4175/#/managers/stocks
```

Manually verify:

- score순 watchlist
- chart-first detail panel
- chart event markers
- held badge
- 상태 전이 UI
- async snapshot load 후 header seed refresh
- 상태 변경 후 header summary / status counts 재계산
- 상태 변경 후 judgment / 정렬 재계산
- stale badge
- memo / next action editing
- Home / Inbox로 이동해도 local edit가 write-through 되지 않음
- route 재진입 또는 full refresh 시 local edit reset
- capture thumbnail strip
- `wealth_home.manager_cards[]` 우선 precedence
- top-level `manager_cards[]` fallback
- `manager_summaries.stock_research`가 없어도 graceful render

- [ ] **Step 3: Update `tasks/todo.md` review section**

Record:

- changed files
- simplifications made
- exact verification commands and outcomes
- remaining risks (e.g. fixture-only detail data, no persistent writes)

- [ ] **Step 4: Commit**

```bash
git add tasks/todo.md
git commit -m "docs: record stock research manager verification"
```
