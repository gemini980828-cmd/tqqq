export const MANAGER_ROUTE_MAP: Record<string, string> = {
  core_strategy: '/managers/core-strategy',
  stock_research: '/managers/stocks',
  real_estate: '/managers/real-estate',
  cash_debt: '/managers/cash-debt',
}

export function getManagerRoute(managerId: string): string {
  return MANAGER_ROUTE_MAP[managerId] || `/managers/${managerId.replace('_', '-')}`
}

export function resolveScreenRoute(gotoScreen?: string, fallbackManagerId?: string): string {
  if (!gotoScreen) {
    return fallbackManagerId ? getManagerRoute(fallbackManagerId) : '/'
  }
  
  // If the backend passes a ready-made route (e.g. '/managers/core_strategy')
  if (gotoScreen.startsWith('/managers/')) {
    // Attempt to map the basename back to our strict route map
    const potentialId = gotoScreen.replace('/managers/', '')
    if (MANAGER_ROUTE_MAP[potentialId]) {
      return MANAGER_ROUTE_MAP[potentialId]
    }
    // Otherwise trust the route or try matching against our keys
    return gotoScreen.replace('_', '-')
  }

  // If the backend passes a pure token like 'home' or a manager id
  if (gotoScreen === 'home' || gotoScreen === '/') return '/'
  
  if (MANAGER_ROUTE_MAP[gotoScreen]) {
    return MANAGER_ROUTE_MAP[gotoScreen]
  }

  // Fallback heuristic
  return `/managers/${gotoScreen.replace('_', '-')}`
}
