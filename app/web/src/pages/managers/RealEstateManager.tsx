import type { AppSnapshot } from '../../types/appSnapshot'

export default function RealEstateManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const managerCard = snapshot?.manager_cards?.find((card) => card.manager_id === 'real_estate')

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Real Estate Manager</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">부동산 매니저</h2>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">관심 단지 추적, 가격/전세가 비교, 검토 상태 관리, 의사결정 메모를 위한 페이지입니다. Step 1에서는 구조와 상태 뼈대를 먼저 잡습니다.</p>
      <div className="mt-6 rounded-2xl border border-white/8 bg-slate-950/40 p-5">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current focus</p>
        <p className="mt-2 text-2xl font-semibold text-white">{managerCard?.headline ?? '관심 단지 0개'}</p>
        <p className="mt-2 text-sm text-slate-400">후속 단계에서 단지별 상세, 비교 체크리스트, AI 요약 브리프가 추가됩니다.</p>
      </div>
    </section>
  )
}
