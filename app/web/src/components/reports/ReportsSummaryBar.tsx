import type { AppSnapshot } from '../../types/appSnapshot'

function formatPct(val?: number) {
  if (val === undefined || Number.isNaN(val)) return 'N/A'
  return `${val > 0 ? '+' : ''}${val.toFixed(2)}%`
}

export default function ReportsSummaryBar({ kpiCards }: { kpiCards?: AppSnapshot['kpi_cards'] }) {
  if (!kpiCards) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="rounded-xl border border-white/5 bg-slate-900/70 p-4 shadow-sm backdrop-blur-md">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">세후 CAGR</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">{formatPct(kpiCards.cagr_pct)}</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/5 bg-slate-900/70 p-4 shadow-sm backdrop-blur-md">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">MDD</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">{formatPct(kpiCards.mdd_pct)}</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/5 bg-slate-900/70 p-4 shadow-sm backdrop-blur-md">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">1개월 수익률</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">{formatPct(kpiCards.month_1_return_pct)}</span>
        </div>
      </div>
      <div className="rounded-xl border border-white/5 bg-slate-900/70 p-4 shadow-sm backdrop-blur-md">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">조건 충족률</h3>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">{kpiCards.condition_pass_rate || 'N/A'}</span>
          <span className="text-xs font-medium text-slate-400">현재 기준</span>
        </div>
      </div>
    </div>
  )
}
