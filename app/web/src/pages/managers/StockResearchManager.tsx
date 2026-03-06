import type { AppSnapshot } from '../../types/appSnapshot'

export default function StockResearchManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const managerCard = snapshot?.manager_cards?.find((card) => card.manager_id === 'stock_research')

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Stock Research Manager</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">개별주 서치 매니저</h2>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">카카오톡/캡처 기반 메모, 상태(탐색/관찰/후보/보류/제외), 관심종목 풀을 관리할 화면입니다. Step 1에서는 shell과 상태 카드만 먼저 고정합니다.</p>
      <div className="mt-6 rounded-2xl border border-white/8 bg-slate-950/40 p-5">
        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current focus</p>
        <p className="mt-2 text-2xl font-semibold text-white">{managerCard?.headline ?? '관심종목 0개'}</p>
        <p className="mt-2 text-sm text-slate-400">후속 단계에서 watchlist 입력, 상태 변경, 메모/첨부, AI 요약 카드가 붙습니다.</p>
      </div>
    </section>
  )
}
