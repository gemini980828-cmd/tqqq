const FALLBACK_POLICY = {
  intent_rules: [
    {
      key: 'default_priority',
      source_manager_id: 'core_strategy',
      priority: 0,
      tokens: ['전체', '요약', '정리', '포트폴리오', '자산', '상황', '우선순위'],
      support_keys: ['action'],
    },
    {
      key: 'action',
      source_manager_id: 'core_strategy',
      priority: 10,
      tokens: ['액션', '해야', '매수', '매도', '체결', '비중', '리밸런싱'],
      support_keys: [],
    },
    {
      key: 'risk',
      source_manager_id: 'core_strategy',
      priority: 20,
      tokens: ['리스크', '위험', '안전', '손절', '변동성'],
      support_keys: [],
    },
    {
      key: 'cash',
      source_manager_id: 'cash_debt',
      priority: 30,
      tokens: ['현금', '유동성', '여력', '가용', '예수금', '부채'],
      support_keys: [],
    },
    {
      key: 'stock_research',
      source_manager_id: 'stock_research',
      priority: 40,
      tokens: ['개별주', '주식', '종목', '워치리스트', 'watchlist'],
      support_keys: [],
    },
    {
      key: 'real_estate',
      source_manager_id: 'real_estate',
      priority: 50,
      tokens: ['부동산', '단지', '아파트', '매물', '전세', '실거주'],
      support_keys: [],
    },
  ],
}

function pushUnique(items, value) {
  if (value && !items.includes(value)) items.push(value)
}

function normalizePolicy(snapshot) {
  return snapshot?.orchestrator_policy?.intent_rules?.length ? snapshot.orchestrator_policy : FALLBACK_POLICY
}

function classifyPrompt(prompt, snapshot) {
  const policy = normalizePolicy(snapshot)
  const matches = [...policy.intent_rules]
    .sort((left, right) => left.priority - right.priority)
    .filter((rule) => rule.tokens.some((token) => prompt.includes(token)))

  const activeRules = matches.length
    ? matches
    : policy.intent_rules.filter((rule) => rule.key === 'default_priority')

  const briefKeys = []
  const sourceManagers = []

  for (const rule of activeRules) {
    pushUnique(briefKeys, rule.key)
    pushUnique(sourceManagers, rule.source_manager_id ?? 'core_strategy')
    for (const supportKey of rule.support_keys ?? []) pushUnique(briefKeys, supportKey)
  }

  return {
    briefKeys: briefKeys.length ? briefKeys : ['default_priority'],
    primaryIntent: briefKeys[0] ?? 'default_priority',
    sourceManagers: sourceManagers.length ? sourceManagers : ['core_strategy'],
  }
}

export function buildPreviewReply(snapshot, question) {
  const prompt = String(question ?? '').trim()
  if (!prompt) return null

  const briefs = snapshot?.orchestrator_briefs ?? {}
  const classification = classifyPrompt(prompt, snapshot)
  const briefKeys = classification.briefKeys
  const answerParts = []
  const highlights = []
  const sourceManagers = [...classification.sourceManagers]

  for (const key of briefKeys) {
    const brief = String(briefs[key] ?? '').trim()
    if (!brief) continue
    answerParts.push(brief)
    pushUnique(highlights, brief.length <= 48 ? brief : `${brief.slice(0, 45)}...`)
  }

  if (!answerParts.length && briefs.default_priority) {
    answerParts.push(String(briefs.default_priority))
    pushUnique(highlights, 'Cache-first summary')
    pushUnique(sourceManagers, 'core_strategy')
  }

  const answer =
    answerParts.length > 1 ? `1순위 판단: ${answerParts[0]}\n\n보조 판단: ${answerParts.slice(1).join(' ')}` : answerParts.join(' ')

  return {
    answer,
    highlights,
    sourceManagers,
    briefKeysUsed: briefKeys,
    primaryIntent: classification.primaryIntent,
    metadata: {
      mode: 'cache_first',
      question_chars: prompt.length,
      source_manager_count: sourceManagers.length,
      primary_intent: classification.primaryIntent,
    },
  }
}
