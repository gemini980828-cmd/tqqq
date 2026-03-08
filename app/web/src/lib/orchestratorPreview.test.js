import test from 'node:test'
import assert from 'node:assert/strict'

import { buildPreviewReply } from './orchestratorPreview.js'

const snapshot = {
  orchestrator_briefs: {
    action: '현재 가장 중요한 액션은 매수이며 전략 목표 비중은 95.0%입니다.',
    cash: '현금 여력은 현금 1,500,000원, 부채 0원, 유동성 비중 13.37% 기준으로 점검하면 됩니다.',
    risk: '현재 리스크 계기판은 vol20=2.54 (green), spy200_dist=107.94 (green) 상태입니다.',
    stock_research: '개별주 매니저 기준으로는 관심종목 1개를 추적 중입니다.',
    real_estate: '부동산 매니저 기준으로는 관심 단지 1개를 팔로잉 중입니다.',
    default_priority: '현재 캐시된 Home inbox와 manager summary를 기준으로 전체 우선순위는 코어전략 점검 → 현금 여력 확인 순서입니다.',
  },
}

test('buildPreviewReply returns null for blank prompt', () => {
  assert.equal(buildPreviewReply(snapshot, '   '), null)
})

test('buildPreviewReply joins backend-owned briefs without reconstructing raw snapshot logic', () => {
  const reply = buildPreviewReply(snapshot, '오늘 가장 중요한 액션과 현금 여력을 알려줘')

  assert.ok(reply)
  assert.match(reply.answer, /95.0%/)
  assert.match(reply.answer, /1,500,000원/)
  assert.deepEqual(reply.sourceManagers, ['core_strategy', 'cash_debt'])
  assert.equal(reply.metadata.mode, 'cache_first_preview')
})
