import test from 'node:test'
import assert from 'node:assert/strict'

import {
  getStockResearchDetailSummary,
  getStockResearchItemBadge,
  getStockResearchItemScore,
  resolveStockResearchWorkspace,
} from './stockResearchDashboard.js'

test('resolveStockResearchWorkspace returns snapshot workspace when available', () => {
  const workspace = resolveStockResearchWorkspace({
    stock_research_workspace: {
      generated_at: '2026-03-22T00:00:00Z',
      filters: {
        total_count: 1,
        held_count: 0,
        candidate_count: 0,
        observe_count: 1,
        status_counts: { 전체: 1, 탐색: 0, 관찰: 1, 후보: 0, 보류: 0, 제외: 0 },
      },
      queue: [],
      items: [
        {
          idea_id: 'stock-nvda',
          symbol: 'NVDA',
          company_name: 'NVIDIA',
          status: '관찰',
          memo: 'AI 수혜 지속 모니터링',
          is_held: false,
          overlap_level: 'low',
          priority: 'medium',
          priority_reason: '관찰 상태 유지',
          next_action: 'NVDA 후속 리서치 업데이트',
          generated_at: '2026-03-22T00:00:00Z',
        },
      ],
      compare_seed: { primary_symbol: 'NVDA', candidate_symbols: [], default_mode: 'fit' },
    },
  })

  assert.equal(workspace.generated_at, '2026-03-22T00:00:00Z')
  assert.equal(workspace.items[0].symbol, 'NVDA')
})

test('resolveStockResearchWorkspace returns empty aligned workspace when snapshot workspace is missing', () => {
  const workspace = resolveStockResearchWorkspace({
    manager_summaries: {
      stock_research: {
        generated_at: '2026-03-22T09:00:00Z',
      },
    },
  })

  assert.equal(workspace.generated_at, '2026-03-22T09:00:00Z')
  assert.deepEqual(workspace.queue, [])
  assert.deepEqual(workspace.items, [])
  assert.deepEqual(workspace.filters.status_counts, { 전체: 0, 탐색: 0, 관찰: 0, 후보: 0, 보류: 0, 제외: 0 })
})

test('getStockResearchItemBadge uses actual status instead of treating every unheld name as a new candidate', () => {
  assert.equal(
    getStockResearchItemBadge({ status: '관찰', is_held: false }),
    '관찰 종목',
  )
  assert.equal(
    getStockResearchItemBadge({ status: '후보', is_held: false }),
    '신규 편입 후보',
  )
  assert.equal(
    getStockResearchItemBadge({ status: '관찰', is_held: true }),
    '보유 종목',
  )
})

test('getStockResearchItemScore prefers real score data and falls back predictably', () => {
  assert.equal(getStockResearchItemScore({ score: 68, priority: 'medium' }), 68)
  assert.equal(getStockResearchItemScore({ priority: 'high' }), 88)
  assert.equal(getStockResearchItemScore({ priority: 'medium' }), 65)
  assert.equal(getStockResearchItemScore({ priority: 'low' }), 45)
})

test('getStockResearchDetailSummary builds generic copy from workspace fields', () => {
  assert.match(
    getStockResearchDetailSummary({
      symbol: 'NVDA',
      status: '관찰',
      priority_reason: '관찰 상태 유지',
      recent_status_change: '관찰 유지',
      memo: 'AI 수혜 지속 모니터링',
    }),
    /NVDA.*관찰/,
  )
})
