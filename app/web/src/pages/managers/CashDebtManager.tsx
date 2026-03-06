import type { DashboardSnapshot } from '../Dashboard'

function formatKrw(value?: number) {
  if (value === undefined || Number.isNaN(value)) return 'N/A'
  return `${new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 }).format(value)}원`
}

export default function CashDebtManager({ snapshot }: { snapshot?: DashboardSnapshot }) {
  const overview = snapshot?.wealth_overview

  return (
    <section className="space-y-6">
      <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Cash & Debt Manager</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">현금 · 부채 매니저</h2>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">투자 여력과 부채 상태를 투자운영 관점에서 빠르게 확인하기 위한 화면입니다. Step 1에서는 summary 기반 카드만 우선 노출합니다.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">현금</p>
          <p className="mt-2 text-2xl font-semibold text-white">{formatKrw(overview?.cash_krw)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">부채</p>
          <p className="mt-2 text-2xl font-semibold text-white">{formatKrw(overview?.debt_krw)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">투자 자산</p>
          <p className="mt-2 text-2xl font-semibold text-white">{formatKrw(overview?.investable_assets_krw ?? overview?.invested_krw)}</p>
        </div>
      </div>
    </section>
  )
}
