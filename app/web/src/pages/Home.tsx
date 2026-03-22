import type { AppSnapshot } from '../types/appSnapshot'
import OrchestratorPanel from '../components/OrchestratorPanel'

import HomeHeroCompact from '../components/home/HomeHeroCompact'
import HomePriorityActions from '../components/home/HomePriorityActions'
import HomeCrossManagerAlerts from '../components/home/HomeCrossManagerAlerts'
import HomeManagerWorkbench from '../components/home/HomeManagerWorkbench'
import HomeRecentActivity from '../components/home/HomeRecentActivity'
import HomeDiscoverySecondary from '../components/home/HomeDiscoverySecondary'

const FALLBACK_CARDS = [
  { manager_id: 'core_strategy', title: 'Core Strategy', headline: '실보유 86.63% / 목표 95.00%', summary: 'TQQQ 코어 전략 운영', status: 'active' },
  { manager_id: 'stock_research', title: 'Stock Research', headline: '관심종목 1개', summary: '후보 발굴/관찰/보류 관리', status: 'tracking' },
  { manager_id: 'real_estate', title: 'Real Estate', headline: '관심 단지 1개', summary: '관심 단지 추적 및 검토', status: 'tracking' },
  { manager_id: 'cash_debt', title: 'Cash & Debt', headline: '현금/부채 항목 1개', summary: '현금 여력과 상환일 관리', status: 'tracking' },
]

export default function Home({ snapshot }: { snapshot?: AppSnapshot }) {
  const priorityActions = snapshot?.priority_actions ?? []
  const crossAlerts = snapshot?.cross_manager_alerts ?? []
  const managers = snapshot?.manager_cards ?? FALLBACK_CARDS
  const timeline = snapshot?.event_timeline ?? []
  const candidates = snapshot?.research_candidates ?? []
  const reports = snapshot?.report_highlights ?? []

  // Re-sort priority_actions based on home_discovery ordered IDs if available
  const sortedPriorityActions = [...priorityActions]
  if (snapshot?.home_discovery?.priority_action_ids) {
    const idMap = new Map(snapshot.home_discovery.priority_action_ids.map((id, index) => [id, index]))
    sortedPriorityActions.sort((a, b) => {
      const idxA = idMap.get(a.id) ?? 999
      const idxB = idMap.get(b.id) ?? 999
      return idxA - idxB
    })
  }

  // Same for cross_manager_alerts
  const sortedCrossAlerts = [...crossAlerts]
  if (snapshot?.home_discovery?.cross_manager_alert_ids) {
    const crossMap = new Map(snapshot.home_discovery.cross_manager_alert_ids.map((id, index) => [id, index]))
    sortedCrossAlerts.sort((a, b) => {
      const idxA = crossMap.get(a.id) ?? 999
      const idxB = crossMap.get(b.id) ?? 999
      return idxA - idxB
    })
  }

  return (
    <div className="flex h-[calc(100vh-[var(--header-height,64px)])] w-full max-w-none overflow-hidden mx-auto">
      
      {/* Left Content Area (Hub) */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 custom-scrollbar relative border-r border-dark-700 bg-dark-900">
        <div className="max-w-4xl mx-auto space-y-8 pb-12">
          <HomeHeroCompact actionHero={snapshot?.action_hero} />
          <HomePriorityActions actions={sortedPriorityActions} />
          <HomeCrossManagerAlerts alerts={sortedCrossAlerts} />
          <HomeManagerWorkbench managers={managers} priorityActions={sortedPriorityActions} crossAlerts={sortedCrossAlerts} />
          <HomeRecentActivity events={timeline} />
          <HomeDiscoverySecondary candidates={candidates} reports={reports} />
        </div>
      </div>

      {/* Right Side Orchestrator Panel */}
      <div className="hidden lg:flex flex-col shrink-0 w-[420px] bg-dark-800 shadow-2xl z-20 overflow-hidden">
        <OrchestratorPanel snapshot={snapshot} />
      </div>

    </div>
  )
}
