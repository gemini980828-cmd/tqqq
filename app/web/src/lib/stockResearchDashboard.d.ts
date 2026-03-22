import type { AppSnapshot, StockResearchWorkspace, StockResearchWorkspaceItem } from '../types/appSnapshot'

export function createEmptyStockResearchWorkspace(snapshot?: AppSnapshot): StockResearchWorkspace
export function resolveStockResearchWorkspace(snapshot?: AppSnapshot): StockResearchWorkspace
export function getStockResearchItemBadge(item: Partial<StockResearchWorkspaceItem>): string
export function getStockResearchItemScore(item: Partial<StockResearchWorkspaceItem>): number
export function getStockResearchRiskLabel(item: Partial<StockResearchWorkspaceItem>): string
export function getStockResearchDetailSummary(item: Partial<StockResearchWorkspaceItem>): string
