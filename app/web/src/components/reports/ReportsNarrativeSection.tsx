import type { AppSnapshot } from '../../types/appSnapshot';
import { useNavigate } from 'react-router-dom';
import { getManagerRoute } from '../../lib/navigation';

export default function ReportsNarrativeSection({ highlights }: { highlights?: AppSnapshot['report_highlights'] }) {
  const navigate = useNavigate();

  if (!highlights || highlights.length === 0) return null;

  return (
    <section>
      <h3 className="mb-5 flex items-center gap-2 text-lg font-semibold text-white">
        <svg className="h-5 w-5 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z"></path></svg>
        핵심 브리핑
      </h3>
      <div className="space-y-4">
        {highlights.map((item) => {
          const isWarning = item.severity.toLowerCase() === 'warning' || item.severity.toLowerCase() === 'high';
          const borderColor = isWarning ? 'border-l-amber-500' : 'border-l-sky-400';
          const badgeBg = isWarning ? 'bg-amber-500/20' : 'bg-sky-400/20';
          const badgeText = isWarning ? 'text-amber-500' : 'text-sky-400';
          const badgeBorder = isWarning ? 'border-amber-500/30' : 'border-sky-400/30';

          return (
            <div key={item.id} className={`group rounded-2xl border border-white/5 border-l-4 ${borderColor} bg-slate-900/70 p-6 shadow-sm backdrop-blur-md transition hover:-translate-y-0.5 hover:shadow-lg`}>
              <div className="mb-3 flex items-start justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <span className={`rounded border px-2 py-0.5 text-xs font-bold ${badgeBg} ${badgeText} ${badgeBorder}`}>
                      {item.severity.toUpperCase()}
                    </span>
                    {item.updated_at && (
                      <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
                        {new Date(item.updated_at).toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' })}
                      </span>
                    )}
                  </div>
                  <h4 className="text-lg font-bold text-white transition group-hover:text-sky-300">{item.title}</h4>
                </div>
                {item.manager_ids && item.manager_ids.length > 0 && (
                  <div className="flex gap-2">
                    {item.manager_ids.map(managerId => (
                      <button 
                        key={managerId}
                        onClick={() => navigate(getManagerRoute(managerId))}
                        className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-slate-700"
                      >
                        {managerId.replace('_', ' ')} <span className="text-slate-400">→</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-sm leading-relaxed text-slate-400">
                {item.summary}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  )
}
