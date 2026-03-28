import type { AppSnapshot } from '../../types/appSnapshot'

export default function HomeHeroCompact({ actionHero }: { actionHero?: AppSnapshot['action_hero'] }) {
  if (!actionHero) {
    return (
      <header className="mb-6">
        <h2 className="text-2xl font-bold text-white tracking-tight">System Operational</h2>
        <p className="text-gray-400 text-sm mt-1">Monitoring portfolio indicators and active positions.</p>
      </header>
    )
  }

  const isActionNeeded = actionHero.action !== '유지'
  const actionText = isActionNeeded 
    ? `오늘은 ${actionHero.action} 검토가 필요합니다.`
    : `현재 비중 유지가 기본 전략입니다.`
  const headlineColor = isActionNeeded ? 'text-amber-400' : 'text-emerald-400'

  return (
    <header className="mb-8 space-y-3 bg-dark-800/20 px-6 py-5 rounded-2xl border border-dark-700/50">
      <h2 className={`text-3xl font-bold tracking-tight ${headlineColor}`}>{actionText}</h2>
      <p className="text-gray-200 font-medium text-[15px]">
        {isActionNeeded ? '정규장 종가 체결 목표' : '안정적 상태 유지 중'}, 전략 목표 비중 {actionHero.target_weight_pct}% 기준.
      </p>
      {actionHero.reason_summary && (
        <p className="text-gray-400 text-sm mt-2 line-clamp-2 md:line-clamp-none pl-3 border-l-2 border-dark-600 max-w-3xl">
          {actionHero.reason_summary}
        </p>
      )}
    </header>
  )
}
