type RawSourceDetail =
  | string
  | {
      source_manager_id?: string
      manager_id?: string
      stale?: boolean
      summary_text?: string
      recommended_actions?: string[]
    }

type RawReply = {
  short_answer?: string
  answer?: string
  text?: string
  content?: string
  source_details?: RawSourceDetail[] | string
  source_rationale?: string
  supporting_managers?:
    | string[]
    | Array<{
        manager_id?: string
        summary_text?: string
        stale?: boolean
      }>
  manager_id?: string
  next_action?: string
  suggested_action?: string
  go_to_screen?: string
  route?: string
}

export interface StructuredOrchestratorReply {
  short_answer: string
  answer: string
  source_details: Array<{ manager_id: string; stale?: boolean }>
  supporting_managers: string[]
  next_action: string
  go_to_screen: string
}

export function normalizeOrchestratorReply(rawReply: RawReply | null | undefined): StructuredOrchestratorReply {
  if (!rawReply) {
    return {
      short_answer: '',
      answer: '응답을 파싱할 수 없습니다.',
      source_details: [],
      supporting_managers: [],
      next_action: '',
      go_to_screen: ''
    }
  }

  const sourceDetails = Array.isArray(rawReply.source_details)
    ? rawReply.source_details.reduce<Array<{ manager_id: string; stale?: boolean }>>((acc, detail) => {
        if (typeof detail === 'string') {
          acc.push({ manager_id: detail, stale: false })
          return acc
        }
        const managerId = detail.source_manager_id || detail.manager_id
        if (managerId) {
          acc.push({ manager_id: managerId, stale: detail.stale })
        }
        return acc
      }, [])
    : []

  const supportingManagers = Array.isArray(rawReply.supporting_managers)
    ? rawReply.supporting_managers.map((manager) => (typeof manager === 'string' ? manager : manager.manager_id || '')).filter(Boolean)
    : rawReply.manager_id
      ? [rawReply.manager_id]
      : []

  // Handle new expected backend format or preview format
  return {
    short_answer: rawReply.short_answer || '',
    answer: rawReply.answer || rawReply.text || rawReply.content || '',
    source_details: sourceDetails,
    supporting_managers: supportingManagers,
    next_action: rawReply.next_action || rawReply.suggested_action || '',
    go_to_screen: rawReply.go_to_screen || rawReply.route || ''
  }
}
