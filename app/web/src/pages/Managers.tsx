import ManagerCard from '../components/ManagerCard'
import type { AppSnapshot } from '../types/appSnapshot'

const FALLBACK_CARDS = [
  { manager_id: 'core_strategy', title: 'Core Strategy', headline: '전략 목표 vs 실제 포지션 비교', summary: '기존 TQQQ 운영판을 매니저 표면으로 승격했습니다.', status: 'active' },
  { manager_id: 'stock_research', title: 'Stock Research', headline: '관심종목 보드 준비', summary: '후보/관찰/보류 상태와 리서치 메모 구조를 준비했습니다.', status: 'tracking' },
  { manager_id: 'real_estate', title: 'Real Estate', headline: '관심 단지 팔로잉 준비', summary: '단지 상태와 비교 메모를 담을 shell을 제공합니다.', status: 'tracking' },
  { manager_id: 'cash_debt', title: 'Cash & Debt', headline: '현금 여력 점검', summary: '투자 가능 현금과 부채 상태를 자산관리 관점에서 보여줍니다.', status: 'tracking' },
]

export default function Managers({ snapshot }: { snapshot?: AppSnapshot }) {
  const cards = snapshot?.wealth_home?.manager_cards ?? snapshot?.manager_cards ?? FALLBACK_CARDS

  return (
    <div className="space-y-6">
      <section>
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Managers</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.05em] text-white">자산군별 Manager 작업실</h2>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300 md:text-base">
          Step 1에서는 Core Strategy를 실전 운영판으로 유지하고, 나머지 매니저는 shell과 기본 데이터 연결 상태로 시작합니다.
        </p>
      </section>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <ManagerCard key={card.manager_id} card={card} />
        ))}
      </section>
    </div>
  )
}
