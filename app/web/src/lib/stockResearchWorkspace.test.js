import test from 'node:test'
import assert from 'node:assert/strict'

import {
  FALLBACK_STOCK_RESEARCH_GENERATED_AT,
  buildStockResearchViewModel,
  calculateBuyPriorityScore,
  deriveStockResearchHeaderState,
  filterStockResearchItems,
  normalizeResearchStatus,
  rederiveStockResearchViewModel,
} from './stockResearchWorkspace.js'
import { STOCK_RESEARCH_FIXTURE } from './stockResearchFixture.js'

test('normalizeResearchStatus maps legacy statuses into the five-state model', () => {
  assert.equal(normalizeResearchStatus('매수후보'), '후보')
  assert.equal(normalizeResearchStatus('검토'), '후보')
  assert.equal(normalizeResearchStatus(undefined), '탐색')
  assert.equal(normalizeResearchStatus('관찰'), '관찰')
})

test('calculateBuyPriorityScore applies weighted math and held clamps', () => {
  assert.equal(
    calculateBuyPriorityScore(
      { stock_quality_raw: 88, portfolio_fit_raw: 82, concentration_penalty: 9 },
      false,
      null,
    ),
    76,
  )

  assert.equal(
    calculateBuyPriorityScore(
      { stock_quality_raw: 72, portfolio_fit_raw: 41, concentration_penalty: 12 },
      true,
      '축소 검토',
    ),
    29,
  )

  assert.equal(
    calculateBuyPriorityScore(
      { stock_quality_raw: 80, portfolio_fit_raw: 70, concentration_penalty: 0 },
      true,
      '보유 유지',
    ),
    69,
  )
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

test('buildStockResearchViewModel derives fixture-backed summary fields deterministically', () => {
  const model = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: STOCK_RESEARCH_FIXTURE,
  })

  assert.deepEqual(model.top_candidates, ['NVDA'])
  assert.equal(model.items[0].symbol, 'NVDA')
  assert.equal(model.items.at(-1).display_judgment, '축소 검토')
  assert.match(model.summary_line, /상위 후보 1개 추적 중/)
  assert.equal(model.warning_line, 'AI 반도체 노출이 이미 높습니다.')
  assert.deepEqual(model.status_counts, { 탐색: 0, 관찰: 2, 후보: 1, 보류: 0, 제외: 0 })
  assert.equal(model.generated_at, 'fixture:stock-research')
  assert.equal(model.generated_at, FALLBACK_STOCK_RESEARCH_GENERATED_AT)
})

test('buildStockResearchViewModel respects generated_at precedence and stale precedence fallbacks', () => {
  const fixtureBySymbol = {
    XYZ: {
      id: 'xyz',
      symbol: 'XYZ',
      company_name: 'XYZ',
      status: '검토',
      primary_reason: 'legacy candidate',
      is_held: false,
      hold_action: null,
      display_judgment: '매수 후보',
      score_drivers: [],
      risk_flags: ['요약 경고'],
      sector_overlap_flags: [],
      overlap_details: [],
      scoring_breakdown: { stock_quality_raw: 80, portfolio_fit_raw: 75, concentration_penalty: 5 },
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
  }

  const wealthHomeModel = buildStockResearchViewModel({
    snapshot: {
      wealth_home: {
        updated_at: '2026-03-19T09:00:00Z',
        manager_cards: [{ manager_id: 'stock_research', stale: true }],
      },
      manager_summaries: {
        stock_research: { stale: false, generated_at: '2026-03-18T00:00:00Z' },
      },
    },
    fixtureBySymbol,
  })

  assert.equal(wealthHomeModel.generated_at, '2026-03-19T09:00:00Z')
  assert.equal(deriveStockResearchHeaderState({
    wealth_home: { manager_cards: [{ manager_id: 'stock_research', stale: true }] },
    manager_summaries: { stock_research: { stale: false } },
  }, wealthHomeModel.items).is_stale, true)

  const topLevelCardState = deriveStockResearchHeaderState(
    {
      manager_cards: [{ manager_id: 'stock_research', stale: true }],
      manager_summaries: { stock_research: { stale: false } },
    },
    wealthHomeModel.items,
  )
  assert.equal(topLevelCardState.is_stale, true)

  const summaryFallbackModel = buildStockResearchViewModel({
    snapshot: {
      manager_summaries: {
        stock_research: { stale: true, generated_at: '2026-03-18T11:00:00Z' },
      },
    },
    fixtureBySymbol,
  })

  assert.equal(summaryFallbackModel.generated_at, '2026-03-18T11:00:00Z')
  assert.equal(deriveStockResearchHeaderState({
    manager_summaries: { stock_research: { stale: true } },
  }, summaryFallbackModel.items).is_stale, true)
})

test('deriveStockResearchHeaderState provides empty fallback state', () => {
  assert.deepEqual(deriveStockResearchHeaderState({}, []), {
    top_candidates: [],
    summary_line: '후보 없음, 관찰 종목 중심으로 관리 중',
    warning_line: null,
    is_stale: false,
  })
})

test('rederiveStockResearchViewModel updates status counts, summary, and retains selection after re-sort', () => {
  const original = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: STOCK_RESEARCH_FIXTURE,
  })

  const selectedNvda = {
    ...original,
    selected_item_id: 'stock-nvda',
  }

  const updated = rederiveStockResearchViewModel({
    snapshot: {},
    previousModel: selectedNvda,
    updater: (items) =>
      items.map((item) =>
        item.id === 'stock-nvda'
          ? { ...item, status: '제외' }
          : item,
      ),
  })

  assert.equal(updated.selected_item_id, 'stock-nvda')
  assert.equal(updated.items[0].id, 'stock-amzn')
  assert.equal(updated.items[1].id, 'stock-nvda')
  assert.equal(updated.items[1].display_judgment, '제외')
  assert.deepEqual(updated.top_candidates, [])
  assert.deepEqual(updated.status_counts, { 탐색: 0, 관찰: 2, 후보: 0, 보류: 0, 제외: 1 })
  assert.equal(updated.summary_line, '후보 없음, 관찰 종목 중심으로 관리 중')
})

test('rederiveStockResearchViewModel keeps memo and next action local without mutating previous items', () => {
  const original = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: STOCK_RESEARCH_FIXTURE,
  })

  const updated = rederiveStockResearchViewModel({
    snapshot: {},
    previousModel: original,
    updater: (items) =>
      items.map((item) =>
        item.id === 'stock-nvda'
          ? { ...item, memo: '로컬 메모', next_action: '내일 체크' }
          : item,
      ),
  })

  const originalNvda = original.items.find((item) => item.id === 'stock-nvda')
  const updatedNvda = updated.items.find((item) => item.id === 'stock-nvda')

  assert.equal(originalNvda?.memo, 'AI 인프라 핵심 수혜 여부 추적')
  assert.equal(originalNvda?.next_action, '실적 발표 후 가이던스 확인')
  assert.equal(updatedNvda?.memo, '로컬 메모')
  assert.equal(updatedNvda?.next_action, '내일 체크')
  assert.equal(updated.selected_item_id, original.selected_item_id)
})

test('buildStockResearchViewModel handles empty fixture fallback without crashing', () => {
  const model = buildStockResearchViewModel({
    snapshot: {
      manager_summaries: {},
    },
    fixtureBySymbol: {},
  })

  assert.deepEqual(model.items, [])
  assert.equal(model.selected_item_id, null)
  assert.deepEqual(model.top_candidates, [])
  assert.equal(model.summary_line, '후보 없음, 관찰 종목 중심으로 관리 중')
  assert.equal(model.warning_line, null)
  assert.deepEqual(model.status_counts, { 탐색: 0, 관찰: 0, 후보: 0, 보류: 0, 제외: 0 })
  assert.equal(model.generated_at, 'fixture:stock-research')
})

test('filterStockResearchItems applies query, status, and holding filters together', () => {
  const model = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: STOCK_RESEARCH_FIXTURE,
  })

  const filtered = filterStockResearchItems(model.items, {
    query: 'a',
    status: '관찰',
    holding: 'held',
  })

  assert.deepEqual(filtered.map((item) => item.symbol), ['AAPL'])
})

test('filterStockResearchItems keeps all items when filters are neutral', () => {
  const model = buildStockResearchViewModel({
    snapshot: {},
    fixtureBySymbol: STOCK_RESEARCH_FIXTURE,
  })

  const filtered = filterStockResearchItems(model.items, {
    query: '',
    status: '전체',
    holding: 'all',
  })

  assert.equal(filtered.length, model.items.length)
})
