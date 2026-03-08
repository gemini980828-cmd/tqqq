import type { AppSnapshot } from '../types/appSnapshot'

type PreviewReply = {
  answer: string
  highlights: string[]
  sourceManagers: string[]
  metadata: {
    mode: string
    questionChars: number
    sourceManagerCount: number
  }
}

export function buildPreviewReply(snapshot: AppSnapshot | undefined, question: string): PreviewReply | null
