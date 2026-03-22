const DEFAULT_PIPELINE = ['탐색', '관찰', '후보', '보류', '제외']

function createEmptyStatusCounts() {
  return { 전체: 0, 탐색: 0, 관찰: 0, 후보: 0, 보류: 0, 제외: 0 }
}

export function createEmptyStockResearchWorkspace(snapshot) {
  const generatedAt =
    snapshot?.stock_research_workspace?.generated_at ??
    snapshot?.manager_summaries?.stock_research?.generated_at ??
    snapshot?.wealth_home?.updated_at ??
    'stock-research:empty'
  const statusCounts = createEmptyStatusCounts()

  return {
    generated_at: generatedAt,
    filters: {
      total_count: 0,
      held_count: 0,
      candidate_count: 0,
      observe_count: 0,
      status_counts: statusCounts,
    },
    queue: [],
    items: [],
    compare_seed: {
      primary_symbol: '',
      candidate_symbols: [],
      default_mode: 'fit',
    },
    flow: {
      pipeline: DEFAULT_PIPELINE,
      active_stage: '탐색',
      stage_counts: statusCounts,
    },
    evidence: {
      news: [],
    },
  }
}

export function resolveStockResearchWorkspace(snapshot) {
  const workspace = snapshot?.stock_research_workspace
  if (!workspace || !Array.isArray(workspace.items)) {
    return createEmptyStockResearchWorkspace(snapshot)
  }

  const statusCounts = workspace.filters?.status_counts ?? createEmptyStatusCounts()

  return {
    ...createEmptyStockResearchWorkspace(snapshot),
    ...workspace,
    filters: {
      total_count: workspace.filters?.total_count ?? workspace.items.length,
      held_count: workspace.filters?.held_count ?? workspace.items.filter((item) => item?.is_held).length,
      candidate_count: workspace.filters?.candidate_count ?? statusCounts['후보'] ?? 0,
      observe_count: workspace.filters?.observe_count ?? statusCounts['관찰'] ?? 0,
      status_counts: {
        ...createEmptyStatusCounts(),
        ...statusCounts,
      },
    },
    queue: Array.isArray(workspace.queue) ? workspace.queue : [],
    items: workspace.items,
    compare_seed: {
      primary_symbol: workspace.compare_seed?.primary_symbol ?? '',
      candidate_symbols: Array.isArray(workspace.compare_seed?.candidate_symbols)
        ? workspace.compare_seed.candidate_symbols
        : [],
      default_mode: workspace.compare_seed?.default_mode ?? 'fit',
    },
    flow: workspace.flow
      ? {
          pipeline: Array.isArray(workspace.flow.pipeline) && workspace.flow.pipeline.length
            ? workspace.flow.pipeline
            : DEFAULT_PIPELINE,
          active_stage: workspace.flow.active_stage ?? workspace.items[0]?.status ?? '탐색',
          stage_counts: {
            ...createEmptyStatusCounts(),
            ...(workspace.flow.stage_counts ?? {}),
          },
        }
      : {
          pipeline: DEFAULT_PIPELINE,
          active_stage: workspace.items[0]?.status ?? '탐색',
          stage_counts: {
            ...createEmptyStatusCounts(),
            ...statusCounts,
          },
        },
  }
}

export function getStockResearchItemBadge(item) {
  if (item?.is_held) return '보유 종목'
  if (item?.status === '후보') return '신규 편입 후보'
  if (item?.status === '관찰') return '관찰 종목'
  if (item?.status === '보류') return '보류 종목'
  if (item?.status === '제외') return '제외 종목'
  return '탐색 종목'
}

export function getStockResearchItemScore(item) {
  if (Number.isFinite(item?.score)) return item.score
  if (item?.priority === 'high') return 88
  if (item?.priority === 'medium') return 65
  return 45
}

export function getStockResearchRiskLabel(item) {
  if (item?.risk_level === 'high') return '높음'
  if (item?.risk_level === 'medium') return '중간'
  if (item?.risk_level === 'low') return '낮음'
  if (item?.overlap_level === 'high') return '중복도 높음'
  if (item?.overlap_level === 'medium') return '중복도 중간'
  return '관찰 필요'
}

export function getStockResearchDetailSummary(item) {
  const parts = [
    `${item?.symbol ?? '종목'}는 현재 ${item?.status ?? '탐색'} 상태입니다.`,
    item?.priority_reason ? `${item.priority_reason}.` : null,
    item?.recent_status_change ? `최근 상태 변화: ${item.recent_status_change}.` : null,
    item?.memo ? `메모: ${item.memo}` : null,
  ].filter(Boolean)

  return parts.join(' ')
}
