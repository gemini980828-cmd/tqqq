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
}

export function buildPreviewReply(snapshot: AppSnapshot | undefined, question: string): PreviewReply | null
