import type { AppSnapshot } from '../../types/appSnapshot'

export default function StockResearchManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const managerCard = snapshot?.manager_cards?.find((card) => card.manager_id === 'stock_research')

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Stock Research Manager</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">개별주 서치 매니저</h2>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">카카오톡/캡처 기반 메모, 상태(탐색/관찰/후보/보류/제외), 관심종목 풀을 관리할 화면입니다. Step 2에서는 cached summary와 상태 카드까지 연결하고, 다음 단계에서 실시간 총괄 AI 연동을 붙입니다.</p>
      <div className="mt-6 rounded-2xl border border-white/8 bg-slate-950/40 p-5">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current focus</p>
        <p className="mt-2 text-2xl font-semibold text-white">{managerCard?.headline ?? '관심종목 0개'}</p>
        <p className="mt-2 text-sm text-slate-400">다음 단계에서 watchlist 입력 편집, 상태 변경, 메모/첨부 상세와 총괄 AI 질의 흐름이 붙습니다.</p>
      </div>
    </section>
  )
}
