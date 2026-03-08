import test from 'node:test'
import assert from 'node:assert/strict'

import { appendOrchestratorHistory, buildOrchestratorInsights, createHistoryEntry } from './orchestratorSession.js'

const reply = {
  answer: '1순위 판단: 현재 전체 우선순위는 코어전략 점검입니다.',
  sourceManagers: ['core_strategy'],
  briefKeysUsed: ['default_priority', 'action'],
  primaryIntent: 'default_priority',
  metadata: {
    mode: 'cache_first',
    question_chars: 12,
    source_manager_count: 1,
    primary_intent: 'default_priority',
  },
}

test('createHistoryEntry returns null for invalid input', () => {
  assert.equal(createHistoryEntry('', reply), null)
  assert.equal(createHistoryEntry('질문', null), null)
})

test('appendOrchestratorHistory keeps newest first and caps length', () => {
  const history = []
  for (let i = 0; i < 6; i += 1) {
    const entry = createHistoryEntry(`질문 ${i}`, { ...reply, answer: `답변 ${i}` }, `2026-03-08T00:00:0${i}Z`)
    history.push(entry)
  }

  const reduced = history.reduce((acc, entry) => appendOrchestratorHistory(acc, entry, 5), [])

  assert.equal(reduced.length, 5)
  assert.equal(reduced[0].question, '질문 5')
  assert.equal(reduced.at(-1).question, '질문 1')
})

test('buildOrchestratorInsights summarizes recent prompts and intents', () => {
  const history = [
    createHistoryEntry('지금 우선순위를 요약해줘', reply, '2026-03-08T01:00:00Z'),
    createHistoryEntry(
      '현금 여력이 충분한가?',
      {
        ...reply,
        answer: '현금 여력은 충분합니다.',
        primaryIntent: 'cash',
        metadata: { ...reply.metadata, primary_intent: 'cash' },
      },
      '2026-03-08T00:30:00Z',
    ),
    createHistoryEntry('지금 우선순위를 요약해줘', reply, '2026-03-08T00:00:00Z'),
  ]

  const insights = buildOrchestratorInsights(history)

  assert.equal(insights.total_questions, 3)
  assert.equal(insights.last_interaction_at, '2026-03-08T01:00:00Z')
  assert.equal(insights.top_intent, 'default_priority')
  assert.deepEqual(insights.recent_prompts, ['지금 우선순위를 요약해줘', '현금 여력이 충분한가?'])
  assert.deepEqual(insights.intent_mix, [
    { intent: 'default_priority', count: 2 },
    { intent: 'cash', count: 1 },
  ])
})
