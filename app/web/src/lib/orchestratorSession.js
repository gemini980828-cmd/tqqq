export const ORCHESTRATOR_HISTORY_STORAGE_KEY = 'alpha-wealth:orchestrator-history'
export const MAX_ORCHESTRATOR_HISTORY = 5

export function createHistoryEntry(question, reply, askedAt = new Date().toISOString()) {
  if (!question || !reply) return null
  return {
    id: `${askedAt}:${String(question)}`,
    question: String(question),
    answer: String(reply.answer ?? ''),
    asked_at: askedAt,
    primary_intent: String(reply.primaryIntent ?? reply.metadata?.primary_intent ?? 'default_priority'),
    source_managers: [...(reply.sourceManagers ?? [])],
    brief_keys_used: [...(reply.briefKeysUsed ?? [])],
    metadata: { ...(reply.metadata ?? {}) },
  }
}

export function appendOrchestratorHistory(history, entry, maxItems = MAX_ORCHESTRATOR_HISTORY) {
  if (!entry) return [...(history ?? [])]
  return [entry, ...(history ?? [])].slice(0, maxItems)
}

export function buildOrchestratorInsights(history) {
  const rows = [...(history ?? [])]
  if (!rows.length) {
    return {
      total_questions: 0,
      last_interaction_at: null,
      top_intent: null,
      recent_prompts: [],
      intent_mix: [],
    }
  }

  const intentCounts = {}
  const recentPrompts = []

  for (const row of rows) {
    const intent = String(row.primary_intent ?? row.primaryIntent ?? row.metadata?.primary_intent ?? 'default_priority')
    intentCounts[intent] = (intentCounts[intent] ?? 0) + 1
    const question = String(row.question ?? '').trim()
    if (question && !recentPrompts.includes(question)) recentPrompts.push(question)
  }

  const topIntent =
    Object.entries(intentCounts).sort((left, right) => Number(right[1]) - Number(left[1]) || left[0].localeCompare(right[0]))[0]?.[0] ?? null

  return {
    total_questions: rows.length,
    last_interaction_at: rows[0]?.asked_at ?? rows[0]?.askedAt ?? null,
    top_intent: topIntent,
    recent_prompts: recentPrompts.slice(0, 3),
    intent_mix: Object.entries(intentCounts)
      .sort((left, right) => Number(right[1]) - Number(left[1]) || left[0].localeCompare(right[0]))
      .map(([intent, count]) => ({ intent, count })),
  }
}

export function loadHistory(storage = globalThis?.localStorage, key = ORCHESTRATOR_HISTORY_STORAGE_KEY) {
  if (!storage?.getItem) return []
  try {
    const raw = storage.getItem(key)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveHistory(history, storage = globalThis?.localStorage, key = ORCHESTRATOR_HISTORY_STORAGE_KEY) {
  if (!storage?.setItem) return
  storage.setItem(key, JSON.stringify(history ?? []))
}

export const appendHistoryEntry = appendOrchestratorHistory
export const buildSessionInsights = buildOrchestratorInsights
