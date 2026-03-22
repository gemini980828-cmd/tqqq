import type { AppSnapshot } from '../../types/appSnapshot';

export default function ReportsComparisonSection({ compareData }: { compareData?: AppSnapshot['compare_data'] }) {
  if (!compareData) return null;

  const managerPairs = compareData.manager_pairs || [];
  const conflicts = compareData.conflicting_recommendations || [];
  const overlaps = compareData.holding_overlap || [];

  if (managerPairs.length === 0 && conflicts.length === 0 && overlaps.length === 0) return null;

  return (
    <section>
      <h3 className="mb-5 flex items-center gap-2 text-lg font-semibold text-white">
        <svg className="h-5 w-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
        매니저 비교 인텔리전스
      </h3>

      {managerPairs.length > 0 && (
        <div className="mb-6 rounded-xl border border-slate-700 bg-slate-900/70 p-5 shadow-sm backdrop-blur-md">
          <h4 className="mb-4 text-sm font-semibold text-white">우선 비교 대상</h4>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {managerPairs.map((pair, i) => (
              <div key={pair.pair_id || i} className="rounded-lg border border-slate-800 bg-slate-950/60 p-4">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-400">
                  <span>{pair.manager_ids[0].replace('_', ' ')}</span>
                  <span className="text-slate-600">&times;</span>
                  <span>{pair.manager_ids[1].replace('_', ' ')}</span>
                </div>
                {pair.headlines && (
                  <div className="mt-3 space-y-2 text-xs text-slate-300">
                    {pair.manager_ids.map((managerId) => (
                      <div key={managerId}>
                        <span className="font-medium text-white">{managerId.replace('_', ' ')}</span>
                        <p className="mt-1 text-slate-400">{pair.headlines?.[managerId] || '요약 없음'}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        
        {/* Conflicting Recommendations */}
        {conflicts.length > 0 && (
          <div className="rounded-xl border border-rose-500/20 bg-slate-900/70 p-5 shadow-sm backdrop-blur-md">
            <h4 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <span className="h-2 w-2 rounded-full bg-rose-500"></span>
              충돌 신호
            </h4>
            <div className="space-y-4">
              {conflicts.map((conflict, i) => (
                <div key={conflict.conflict_id || i} className="border-b border-slate-800 pb-4 last:border-0 last:pb-0">
                  <p className="mb-2 text-sm leading-relaxed text-slate-300">{conflict.detail}</p>
                  <div className="flex flex-wrap gap-2">
                    {conflict.manager_ids.map(mid => (
                      <span key={mid} className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-[11px] font-medium text-slate-300">
                        {mid.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Holding Overlaps */}
        {overlaps.length > 0 && (
          <div className="rounded-xl border border-indigo-400/20 bg-slate-900/70 p-5 shadow-sm backdrop-blur-md">
            <h4 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
              <span className="h-2 w-2 rounded-full bg-indigo-400"></span>
              공통 노출
            </h4>
            <div className="space-y-4">
              {overlaps.map((overlap, i) => (
                <div key={overlap.overlap_id || i} className="border-b border-slate-800 pb-4 last:border-0 last:pb-0">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-400">{overlap.left_manager_id.replace('_', ' ')}</span>
                    <span className="text-xs text-slate-600">&times;</span>
                    <span className="text-xs font-semibold text-slate-400">{overlap.right_manager_id.replace('_', ' ')}</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {overlap.shared_symbols.map(sym => (
                      <span key={sym} className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-bold text-emerald-400">
                        {sym}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
      </div>
    </section>
  )
}
