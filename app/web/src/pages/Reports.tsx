import type { DashboardSnapshot } from './Dashboard'

function formatPct(val?: number) {
  if (val === undefined || Number.isNaN(val)) return 'N/A'
  return `${val > 0 ? '+' : ''}${val.toFixed(2)}%`
}

export default function Reports({ snapshot }: { snapshot?: DashboardSnapshot }) {
  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Reports</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">리포트</h2>
      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">세후 CAGR</p>
          <p className="mt-2 text-2xl font-semibold text-white">{formatPct(snapshot?.kpi_cards?.cagr_pct)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">MDD</p>
          <p className="mt-2 text-2xl font-semibold text-rose-100">{formatPct(snapshot?.kpi_cards?.mdd_pct)}</p>
        </div>
        <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-5">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">1M 수익률</p>
          <p className="mt-2 text-2xl font-semibold text-white">{formatPct(snapshot?.kpi_cards?.month_1_return_pct)}</p>
        </div>
      </div>
    </section>
  )
}
