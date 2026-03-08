export type OrchestratorHistoryEntry = {
  id: string
  question: string
  asked_at: string
  answer: string
  primary_intent: string
  source_managers: string[]
  brief_keys_used: string[]
  metadata: {
    mode: string
    question_chars: number
    source_manager_count: number
    primary_intent: string
  }
}

export type OrchestratorInsights = {
  total_questions: number
  last_interaction_at: string | null
  top_intent: string | null
  recent_prompts: string[]
  intent_mix: Array<{ intent: string; count: number }>
}

export const ORCHESTRATOR_HISTORY_STORAGE_KEY: string
export const MAX_ORCHESTRATOR_HISTORY: number

export type OrchestratorReplyLike = {
  answer: string
  primaryIntent?: string
  sourceManagers?: string[]
  briefKeysUsed?: string[]
  metadata?: {
    mode?: string
    question_chars?: number
    source_manager_count?: number
    primary_intent?: string
  }
}

export const ORCHESTRATOR_HISTORY_STORAGE_KEY: string
export function createHistoryEntry(question: string, reply: OrchestratorReplyLike | null, askedAt?: string): OrchestratorHistoryEntry | null
export function appendOrchestratorHistory(
  history: OrchestratorHistoryEntry[] | undefined,
  entry: OrchestratorHistoryEntry | null,
  maxItems?: number,
): OrchestratorHistoryEntry[]
export function buildOrchestratorInsights(history: OrchestratorHistoryEntry[] | undefined): OrchestratorInsights
export function loadHistory(
  storage?: { getItem?: (key: string) => string | null },
  key?: string,
): OrchestratorHistoryEntry[]
export function saveHistory(
  history: OrchestratorHistoryEntry[] | undefined,
  storage?: { setItem?: (key: string, value: string) => void },
  key?: string,
): void
export function loadHistory(storage?: Storage | undefined, key?: string): OrchestratorHistoryEntry[]
export function saveHistory(history: OrchestratorHistoryEntry[] | undefined, storage?: Storage | undefined, key?: string): void
export const appendHistoryEntry: typeof appendOrchestratorHistory
export const buildSessionInsights: typeof buildOrchestratorInsights
