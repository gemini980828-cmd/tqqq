import type { AppSnapshot } from '../types/appSnapshot'
import type {
  StockResearchFixtureItem,
  StockResearchHeaderState,
  StockResearchHoldAction,
  StockResearchItemViewModel,
  StockResearchScoringBreakdown,
  StockResearchStatus,
  StockResearchViewModel,
} from '../types/stockResearch'

export const FALLBACK_STOCK_RESEARCH_GENERATED_AT: string

export function normalizeResearchStatus(raw: string | null | undefined): StockResearchStatus
export function calculateBuyPriorityScore(
  breakdown: StockResearchScoringBreakdown,
  isHeld: boolean,
  holdAction: StockResearchHoldAction | null,
): number
export function deriveStockResearchHeaderState(
  snapshot: AppSnapshot | undefined,
  items: StockResearchViewModel['items'],
): StockResearchHeaderState
export function buildStockResearchViewModel(args: {
  snapshot?: AppSnapshot
  fixtureBySymbol?: Record<string, StockResearchFixtureItem>
}): StockResearchViewModel
export function filterStockResearchItems(
  items: StockResearchItemViewModel[],
  filters: {
    query?: string
    status?: '전체' | StockResearchStatus
    holding?: 'all' | 'held' | 'unheld'
  },
): StockResearchItemViewModel[]
export function rederiveStockResearchViewModel(args: {
  snapshot?: AppSnapshot
  previousModel: StockResearchViewModel
  updater: (items: StockResearchItemViewModel[]) => StockResearchItemViewModel[]
}): StockResearchViewModel
