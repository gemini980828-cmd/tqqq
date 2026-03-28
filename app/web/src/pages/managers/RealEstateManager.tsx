import type { AppSnapshot } from '../../types/appSnapshot'
import ManagerActionHeader from '../../components/ManagerActionHeader'

export default function RealEstateManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const managerCard = snapshot?.manager_cards?.find((card) => card.manager_id === 'real_estate')

  return (
    <div className="space-y-6">
      <ManagerActionHeader managerId="real_estate" snapshot={snapshot} />
      <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Real Estate Manager</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">부동산 매니저</h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">관심 단지 추적, 가격/전세가 비교, 검토 상태 관리, 의사결정 메모를 위한 페이지입니다. Step 2에서는 summary cache와 상태 뼈대를 연결했고, 다음 단계에서 상세 비교/AI 브리프를 확장합니다.</p>
        <div className="mt-6 rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current focus</p>
          <p className="mt-2 text-2xl font-semibold text-white">{managerCard?.headline ?? '관심 단지 0개'}</p>
          <p className="mt-2 text-sm text-slate-400">다음 단계에서 단지별 상세, 비교 체크리스트, 총괄 AI 질의와 의사결정 로그가 추가됩니다.</p>
        </div>
      </section>
    </div>
  )
}
