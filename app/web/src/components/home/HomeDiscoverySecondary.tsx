import type { ResearchCandidate, ReportHighlight } from '../../types/appSnapshot'

interface Props {
  candidates?: ResearchCandidate[]
  reports?: ReportHighlight[]
}

export default function HomeDiscoverySecondary({ candidates, reports }: Props) {
  if ((!candidates || candidates.length === 0) && (!reports || reports.length === 0)) return null

  return (
    <section className="mt-8 pt-6 border-t border-dark-700">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Discovery & Reports</h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {candidates && candidates.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-3">Research Candidates</h4>
            <div className="space-y-3">
              {candidates.map((c) => (
                <div key={c.idea_id} className="glass-panel p-4 rounded-xl">
                  <div className="flex justify-between items-start">
                    <div>
                      <h5 className="font-semibold text-brand-accent">{c.symbol}</h5>
                      <p className="text-xs text-gray-400 mt-1">{c.memo}</p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded bg-dark-700 border border-dark-600 text-gray-300">
                      {c.priority}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {reports && reports.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-400 mb-3">Report Highlights</h4>
            <div className="space-y-3">
              {reports.map((r) => (
                <div key={r.id} className="glass-panel p-4 rounded-xl">
                  <h5 className="font-semibold text-white text-sm">{r.title}</h5>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{r.summary}</p>
                  <div className="mt-3 flex gap-2">
                    {r.manager_ids?.map((mId) => (
                      <span key={mId} className="text-[10px] uppercase tracking-wider text-gray-500">
                        #{mId.replace('_', ' ')}
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
