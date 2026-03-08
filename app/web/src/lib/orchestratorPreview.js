function pushUnique(items, value) {
  if (value && !items.includes(value)) items.push(value)
}

function pickBriefKeys(prompt) {
  const wantsAction = ['액션', '해야', '우선', '중요'].some((token) => prompt.includes(token))
  const wantsCash = ['현금', '유동성', '여력'].some((token) => prompt.includes(token))
  const wantsRisk = ['리스크', '위험', '안전'].some((token) => prompt.includes(token))

  const keys = []
  if (wantsAction || (!wantsCash && !wantsRisk)) keys.push('action')
  if (wantsCash) keys.push('cash')
  if (wantsRisk) keys.push('risk')
  if (prompt.includes('개별주') || prompt.includes('주식')) keys.push('stock_research')
  if (prompt.includes('부동산')) keys.push('real_estate')
  if (!keys.length) keys.push('default_priority')
  return keys
}

const BRIEF_SOURCE_MANAGERS = {
  action: 'core_strategy',
  cash: 'cash_debt',
  risk: 'core_strategy',
  stock_research: 'stock_research',
  real_estate: 'real_estate',
  default_priority: 'core_strategy',
}

export function buildPreviewReply(snapshot, question) {
  const prompt = String(question ?? '').trim()
  if (!prompt) return null

  const briefs = snapshot?.orchestrator_briefs ?? {}
  const briefKeys = pickBriefKeys(prompt)
  const answerParts = []
  const highlights = []
  const sourceManagers = []

  for (const key of briefKeys) {
    const brief = String(briefs[key] ?? '').trim()
    if (!brief) continue
    answerParts.push(brief)
    pushUnique(highlights, brief.length <= 48 ? brief : `${brief.slice(0, 45)}...`)
    pushUnique(sourceManagers, BRIEF_SOURCE_MANAGERS[key] ?? 'core_strategy')
  }

  if (!answerParts.length && briefs.default_priority) {
    answerParts.push(String(briefs.default_priority))
    pushUnique(highlights, 'Cache-first summary')
    pushUnique(sourceManagers, 'core_strategy')
  }

  return {
    answer: answerParts.join(' '),
    highlights,
    sourceManagers,
    metadata: {
      mode: 'cache_first_preview',
      questionChars: prompt.length,
      sourceManagerCount: sourceManagers.length,
    },
  }
}
