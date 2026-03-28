import type { AppSnapshot } from '../types/appSnapshot'

type PreviewReply = {
  answer: string
  highlights: string[]
  sourceManagers: string[]
  briefKeysUsed: string[]
  primaryIntent: string
  metadata: {
    mode: string
    question_chars: number
    source_manager_count: number
    primary_intent: string
  }
  short_answer: string
  source_details: Array<{ manager_id: string; stale?: boolean }>
  supporting_managers: string[]
  next_action?: string
  go_to_screen?: string
}

export function buildPreviewReply(snapshot: AppSnapshot | undefined, question: string): PreviewReply | null
