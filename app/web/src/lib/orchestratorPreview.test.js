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
  orchestrator_policy: {
    quick_prompts: ['오늘 가장 중요한 액션은?', '지금 우선순위를 요약해줘', '현금 여력이 충분한가?', '지금 리스크 상태는 어때?'],
    intent_rules: [
      { key: 'default_priority', source_manager_id: 'core_strategy', priority: 0, tokens: ['전체', '요약', '정리', '포트폴리오', '자산', '상황', '우선순위'], support_keys: ['action'] },
      { key: 'action', source_manager_id: 'core_strategy', priority: 10, tokens: ['액션', '해야', '매수', '매도', '체결', '비중', '리밸런싱'], support_keys: [] },
      { key: 'risk', source_manager_id: 'core_strategy', priority: 20, tokens: ['리스크', '위험', '안전', '손절', '변동성'], support_keys: [] },
      { key: 'cash', source_manager_id: 'cash_debt', priority: 30, tokens: ['현금', '유동성', '여력', '가용', '예수금', '부채'], support_keys: [] },
      { key: 'stock_research', source_manager_id: 'stock_research', priority: 40, tokens: ['개별주', '주식', '종목', '워치리스트', 'watchlist'], support_keys: [] },
      { key: 'real_estate', source_manager_id: 'real_estate', priority: 50, tokens: ['부동산', '단지', '아파트', '매물', '전세', '실거주'], support_keys: [] },
    ],
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
  assert.equal(reply.metadata.mode, 'cache_first')
  assert.equal(reply.metadata.primary_intent, 'action')
})

test('buildPreviewReply uses default priority path for generic overview prompts', () => {
  const reply = buildPreviewReply(snapshot, '지금 우선순위를 전체적으로 요약해줘')

  assert.ok(reply)
  assert.equal(reply.primaryIntent, 'default_priority')
  assert.deepEqual(reply.briefKeysUsed.slice(0, 2), ['default_priority', 'action'])
  assert.match(reply.answer, /1순위 판단:/)
})
