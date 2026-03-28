import type { StockResearchWorkspaceItem, StockResearchEvidence } from '../../types/appSnapshot'

interface Props {
  item: StockResearchWorkspaceItem
  evidence?: StockResearchEvidence
}

export function StockResearchEvidencePanel({ item, evidence }: Props) {
  const chart = (evidence?.chart && typeof evidence.chart === 'object') ? evidence.chart as { signal?: string; timeframe?: string } : null
  const news = Array.isArray(evidence?.news) ? evidence.news as Array<{ title?: string; summary?: string; published_at?: string }> : []
  const institutionalFlow = (evidence?.institutional_flow && typeof evidence.institutional_flow === 'object')
    ? evidence.institutional_flow as { stance?: string; confidence?: string; summary?: string }
    : null
  const evidenceRefs = item.evidence_refs ?? []

  // Use evidence data if available, otherwise fallback to static mock UI
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="p-4 rounded-xl border border-[#334155] md:col-span-2 flex flex-col justify-between" style={{ background: 'rgba(15, 23, 42, 0.7)' }}>
        <div className="flex justify-between items-center mb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest">{item.symbol} Price Trend & Key Event</h3>
            <span className="text-[10px] text-slate-500">{chart?.timeframe ?? (evidence?.chart ? 'Actual Data' : '1M View')}</span>
        </div>
        {/* Minimal Chart View */}
        <div className="h-24 w-full flex items-end justify-between gap-1 relative pt-4">
            <div className="absolute left-1/2 bottom-0 h-full w-[1px] border-l border-dashed border-emerald-500/50 z-0"></div>
            <div className="absolute left-1/2 -top-1 px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[9px] rounded z-10 -translate-x-1/2">{chart?.signal ?? '실적 서프라이즈'}</div>
            <div className="w-full bg-[#1e293b] h-[30%] rounded-t-sm z-10"></div>
            <div className="w-full bg-[#1e293b] h-[35%] rounded-t-sm z-10"></div>
            <div className="w-full bg-[#1e293b] h-[32%] rounded-t-sm z-10"></div>
            <div className="w-full bg-[#1e293b] h-[40%] rounded-t-sm z-10"></div>
            <div className="w-full bg-[#1e293b] h-[38%] rounded-t-sm z-10"></div>
            <div className="w-full bg-emerald-500/80 h-[65%] rounded-t-sm z-10"></div>
            <div className="w-full bg-emerald-400/80 h-[70%] rounded-t-sm z-10"></div>
            <div className="w-full bg-sky-500/80 h-[68%] rounded-t-sm z-10"></div>
            <div className="w-full bg-sky-400/80 h-[75%] rounded-t-sm z-10"></div>
            <div className="w-full bg-sky-400/80 h-[72%] rounded-t-sm z-10"></div>
            <div className="w-full bg-emerald-300/80 h-[85%] rounded-t-sm z-10"></div>
            <div className="w-full bg-emerald-400/80 h-[92%] rounded-t-sm z-10"></div>
        </div>
      </div>
      <div className="p-4 rounded-xl border border-[#334155] flex flex-col justify-between" style={{ background: 'rgba(15, 23, 42, 0.7)' }}>
        <div className="flex justify-between items-center mb-2">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest">기관 수급 브리프</h3>
        </div>
        <div className="mb-2">
            <div className="text-sm font-bold text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span> {institutionalFlow?.stance ?? '긍정적 (매수우위)'}
            </div>
        </div>
        <p className="text-[11px] text-slate-400 leading-relaxed border-t border-[#334155] pt-2">
            {institutionalFlow?.summary ?? news[0]?.summary ?? '최근 2주간 상위 5대 연기금/헤지펀드의 비중 확대 흐름 지속. 확신(Conviction) 점수 상승.'}
        </p>
        {evidenceRefs.length ? (
          <div className="mt-3 border-t border-[#334155] pt-3">
            <div className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">Evidence refs</div>
            <div className="space-y-2">
              {evidenceRefs.map((ref) => (
                <div key={`${ref.label}-${ref.source ?? 'ref'}`} className="rounded-lg border border-[#334155] bg-[#08101b]/40 px-3 py-2">
                  <div className="text-[11px] font-semibold text-slate-200">{ref.label}</div>
                  {ref.source ? <div className="text-[10px] text-slate-500">{ref.source}</div> : null}
                  {ref.summary ? <div className="mt-1 text-[10px] text-slate-400">{ref.summary}</div> : null}
                  {ref.url ? (
                    <a className="mt-1 inline-block text-[10px] text-sky-300 underline-offset-2 hover:underline" href={ref.url} target="_blank" rel="noreferrer">
                      원문 보기
                    </a>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
