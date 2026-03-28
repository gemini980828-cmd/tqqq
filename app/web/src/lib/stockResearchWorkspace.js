export const FALLBACK_STOCK_RESEARCH_GENERATED_AT = 'fixture:stock-research'

const EMPTY_STATUS_COUNTS = {
  탐색: 0,
  관찰: 0,
  후보: 0,
  보류: 0,
  제외: 0,
}

const STATUS_PRIORITY = {
  후보: 3,
  관찰: 2,
  탐색: 1,
  보류: 0,
  제외: -1,
}

function createEmptyStatusCounts() {
  return { ...EMPTY_STATUS_COUNTS }
}

function toFiniteNumber(value) {
  return Number.isFinite(value) ? value : 0
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function pickStockResearchCard(snapshot) {
  const wealthHomeCard = snapshot?.wealth_home?.manager_cards?.find((card) => card?.manager_id === 'stock_research')
  const topLevelCard = snapshot?.manager_cards?.find((card) => card?.manager_id === 'stock_research')

  return { wealthHomeCard, topLevelCard }
}

function deriveWarningLine(items) {
  for (const item of items) {
    const overlapWarning = item.overlap_details?.find((detail) => detail?.impact === 'high')?.reason
    if (overlapWarning) return overlapWarning
  }

  for (const item of items) {
    const riskWarning = item.risk_flags?.[0]
    if (riskWarning) return riskWarning
  }

  return null
}

function deriveDisplayJudgment(item, status) {
  if (status === '제외') return '제외'
  if (item.is_held) {
    if (item.hold_action) return item.hold_action
    return item.display_judgment === '제외' ? '보유 유지' : item.display_judgment
  }
  return '매수 후보'
}

function deriveItemViewModel(item) {
  const status = normalizeResearchStatus(item?.status)
  const holdAction = item?.hold_action ?? null
  const displayJudgment = deriveDisplayJudgment(item, status)
  const scoreBreakdown = item?.scoring_breakdown ?? {
    stock_quality_raw: 0,
    portfolio_fit_raw: 0,
    concentration_penalty: 0,
  }
  const baseScore = calculateBuyPriorityScore(scoreBreakdown, item?.is_held, holdAction)
  const statusOffset = STATUS_PRIORITY[status] ?? 0
  const buyPriorityScore = clamp(baseScore + statusOffset * 6, 0, 100)

  return {
    ...item,
    status,
    hold_action: holdAction,
    display_judgment: displayJudgment,
    buy_priority_score: buyPriorityScore,
  }
}

function sortItems(items) {
  return [...items].sort(
    (left, right) => right.buy_priority_score - left.buy_priority_score || left.symbol.localeCompare(right.symbol),
  )
}

function buildViewModelFromItems(snapshot, items, selectedItemId) {
  const sortedItems = sortItems(items)
  const statusCounts = createEmptyStatusCounts()
  for (const item of sortedItems) {
    statusCounts[item.status] += 1
  }

  const headerState = deriveStockResearchHeaderState(snapshot, sortedItems)
  const generatedAt =
    snapshot?.wealth_home?.updated_at ??
    snapshot?.manager_summaries?.stock_research?.generated_at ??
    FALLBACK_STOCK_RESEARCH_GENERATED_AT
  const nextSelectedId = sortedItems.some((item) => item.id === selectedItemId)
    ? selectedItemId
    : (sortedItems[0]?.id ?? null)

  return {
    generated_at: generatedAt,
    items: sortedItems,
    selected_item_id: nextSelectedId,
    status_counts: statusCounts,
    top_candidates: headerState.top_candidates,
    summary_line: headerState.summary_line,
    warning_line: headerState.warning_line,
  }
}

export function normalizeResearchStatus(raw) {
  const key = String(raw ?? '').trim()
  if (key === '매수후보' || key === '검토') return '후보'
  if (key === '관찰' || key === '후보' || key === '보류' || key === '제외') return key
  return '탐색'
}

export function calculateBuyPriorityScore(breakdown, isHeld, holdAction) {
  const stockQuality = toFiniteNumber(breakdown?.stock_quality_raw)
  const portfolioFit = toFiniteNumber(breakdown?.portfolio_fit_raw)
  const penalty = toFiniteNumber(breakdown?.concentration_penalty)
  const base = Math.floor(clamp(stockQuality * 0.6 + portfolioFit * 0.4 - penalty, 0, 100))

  if (!isHeld) return base
  if (holdAction === '추가매수 후보') return base
  if (holdAction === '보유 유지') return clamp(base, 50, 69)
  if (holdAction === '축소 검토') return clamp(base, 0, 29)
  return base
}

export function deriveStockResearchHeaderState(snapshot, items) {
  const sortedItems = sortItems(items ?? [])
  const topCandidates = sortedItems
    .filter((item) => item.status === '후보' || (item.is_held && item.display_judgment === '추가매수 후보'))
    .slice(0, 3)
    .map((item) => item.symbol)
  const warningLine = deriveWarningLine(sortedItems)
  const summaryLine = topCandidates.length
    ? `상위 후보 ${topCandidates.length}개 추적 중${warningLine ? `, ${warningLine}` : ''}`
    : '후보 없음, 관찰 종목 중심으로 관리 중'
  const { wealthHomeCard, topLevelCard } = pickStockResearchCard(snapshot)
  const isStale = Boolean(wealthHomeCard?.stale || topLevelCard?.stale || snapshot?.manager_summaries?.stock_research?.stale)

  return {
    top_candidates: topCandidates,
    summary_line: summaryLine,
    warning_line: warningLine,
    is_stale: isStale,
  }
}

export function buildStockResearchViewModel({ snapshot, fixtureBySymbol }) {
  const items = Object.values(fixtureBySymbol ?? {}).map((item) => deriveItemViewModel(item))
  return buildViewModelFromItems(snapshot, items, null)
}

export function filterStockResearchItems(items, filters) {
  const query = String(filters?.query ?? '').trim().toLowerCase()
  const status = String(filters?.status ?? '전체')
  const holding = String(filters?.holding ?? 'all')

  return [...(items ?? [])].filter((item) => {
    const matchesQuery =
      !query ||
      item.symbol.toLowerCase().includes(query) ||
      item.company_name.toLowerCase().includes(query) ||
      item.primary_reason.toLowerCase().includes(query)

    const matchesStatus = status === '전체' || item.status === status
    const matchesHolding =
      holding === 'all' ||
      (holding === 'held' && item.is_held) ||
      (holding === 'unheld' && !item.is_held)

    return matchesQuery && matchesStatus && matchesHolding
  })
}

export function rederiveStockResearchViewModel({ snapshot, previousModel, updater }) {
  const currentItems = previousModel?.items ?? []
  const updatedItems = updater(currentItems.map((item) => ({ ...item })))
  const rederivedItems = updatedItems.map((item) => deriveItemViewModel(item))
  return buildViewModelFromItems(snapshot, rederivedItems, previousModel?.selected_item_id ?? null)
}
