import Dashboard, { type DashboardSnapshot } from '../Dashboard'

function formatKrw(value?: number) {
  if (value === undefined || Number.isNaN(value)) return 'N/A'
  return `${new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 }).format(value)}원`
}

export default function CoreStrategyManager({ snapshot }: { snapshot?: DashboardSnapshot }) {
  const position = snapshot?.core_strategy_position ?? snapshot?.core_strategy_actuals

  return (
    <div className="space-y-6">
      <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Core Strategy Manager</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">TQQQ 코어전략 운영판</h2>
        <p className="mt-3 text-sm leading-7 text-slate-400">기존 TQQQ 대시보드를 그대로 유지하면서, 실제 포지션과 전략 목표 비중의 괴리를 함께 확인하는 Manager 형태로 승격합니다.</p>

        {position && (
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">실제 비중</p>
              <p className="mt-2 text-2xl font-semibold text-white">{position.actual_weight_pct?.toFixed?.(2) ?? position.actual_weight_pct}%</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">목표 비중</p>
              <p className="mt-2 text-2xl font-semibold text-white">{position.target_weight_pct?.toFixed?.(2) ?? position.target_weight_pct}%</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">리밸런싱 차이</p>
              <p className={`mt-2 text-2xl font-semibold ${Number(position.gap_pct ?? 0) < 0 ? 'text-amber-200' : 'text-emerald-200'}`}>
                {(position.gap_pct ?? 0) > 0 ? '+' : ''}{position.gap_pct?.toFixed?.(2) ?? position.gap_pct}%
              </p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">평가금액</p>
              <p className="mt-2 text-2xl font-semibold text-white">{formatKrw(position.market_value_krw ?? position.actual_value_krw)}</p>
            </div>
          </div>
        )}
      </section>

      <Dashboard snapshot={snapshot} />
    </div>
  )
}
