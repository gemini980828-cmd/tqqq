export type StockResearchStatus = '탐색' | '관찰' | '후보' | '보류' | '제외'
export type StockResearchJudgment = '매수 후보' | '추가매수 후보' | '보유 유지' | '축소 검토' | '제외'
export type StockChartPoint = { date: string; close: number; ma20?: number; ma50?: number }
export type StockChartMarker = { kind: 'earnings' | 'risk' | 'memo'; date: string; label: string }
export type StockPriceZone = { label: string; value: number }
export type StockCaptureThumb = { id: string; label: string; image_url: string }
export type StockOverlapDetail = {
  type: 'sector' | 'theme' | 'holding'
  label: string
  matched_symbol?: string
  impact: 'low' | 'medium' | 'high'
  reason: string
}
export type StockResearchHoldAction = '추가매수 후보' | '보유 유지' | '축소 검토'
export type StockResearchScoringBreakdown = {
  stock_quality_raw: number
  portfolio_fit_raw: number
  concentration_penalty: number
}
export type StockResearchFixtureItem = {
  id: string
  symbol: string
  company_name: string
  status: string
  primary_reason: string
  score_drivers: string[]
  is_held: boolean
  hold_action: StockResearchHoldAction | null
  display_judgment: StockResearchJudgment
  risk_flags: string[]
  sector_overlap_flags: string[]
  overlap_details: StockOverlapDetail[]
  scoring_breakdown: StockResearchScoringBreakdown
  chart_series: StockChartPoint[]
  chart_markers: StockChartMarker[]
  price_zones: StockPriceZone[]
  chart_notes: string[]
  macro_summary: string
  options_summary: string
  memo: string
  next_action: string
  captures: StockCaptureThumb[]
}
export type StockResearchItemViewModel = {
  id: string
  symbol: string
  company_name: string
  status: StockResearchStatus
  buy_priority_score: number
  primary_reason: string
  score_drivers: string[]
  is_held: boolean
  hold_action: StockResearchHoldAction | null
  display_judgment: StockResearchJudgment
  risk_flags: string[]
  sector_overlap_flags: string[]
  overlap_details: StockOverlapDetail[]
  scoring_breakdown: StockResearchScoringBreakdown
  chart_series: StockChartPoint[]
  chart_markers: StockChartMarker[]
  price_zones: StockPriceZone[]
  chart_notes: string[]
  macro_summary: string
  options_summary: string
  memo: string
  next_action: string
  captures: StockCaptureThumb[]
}
export type StockResearchStatusCounts = Record<StockResearchStatus, number>
export type StockResearchViewModel = {
  generated_at: string
  items: StockResearchItemViewModel[]
  selected_item_id: string | null
  status_counts: StockResearchStatusCounts
  top_candidates: string[]
  summary_line: string
  warning_line: string | null
}
export type StockResearchHeaderState = {
  top_candidates: string[]
  summary_line: string
  warning_line: string | null
  is_stale: boolean
}
