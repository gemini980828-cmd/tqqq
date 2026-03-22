import type { StockResearchQueueItem } from '../../types/appSnapshot'

interface Props {
  queue: StockResearchQueueItem[]
  lastSyncAt: string
  onSelectCallback?: (symbol: string) => void
}

export function StockResearchQueue({ queue, lastSyncAt, onSelectCallback }: Props) {
  if (!queue || queue.length === 0) return null

  return (
    <div className="border-b border-slate-700/50 bg-[#08101b] px-6 py-4 shrink-0 shadow-sm z-10">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          오늘의 리서치 우선순위 큐
        </h2>
        <div className="text-xs text-slate-400 flex items-center gap-2">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          마지막 동기화: {lastSyncAt}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {queue.map((item) => {
          let styleClass = ''
          let badgeClass = ''

          if (item.severity === 'high') {
            styleClass = 'border-l-[3px] border-l-rose-500 glass-panel-hover opacity-70'
            badgeClass = 'bg-rose-500/20 text-rose-400'
          } else if (item.severity === 'medium') {
            styleClass = 'border-l-[3px] border-l-emerald-500 bg-emerald-900/10 ring-1 ring-emerald-500/50'
            badgeClass = 'bg-emerald-500/20 text-emerald-400'
          } else {
            styleClass = 'border border-slate-600 glass-panel-hover opacity-70'
            badgeClass = 'bg-slate-700 text-slate-300'
          }

          return (
            <div
              key={item.id}
              onClick={() => onSelectCallback?.(item.symbol)}
              className={`p-3 rounded-xl flex justify-between items-center cursor-pointer transition ${styleClass}`}
              style={{
                background: item.severity === 'medium' ? 'rgba(6, 78, 59, 0.1)' : 'rgba(15, 23, 42, 0.7)',
                backdropFilter: 'blur(12px)',
              }}
            >
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-widest ${badgeClass}`}>
                    {item.status}
                  </span>
                  <span className="text-[10px] text-slate-500">{item.age_label ?? item.next_action}</span>
                </div>
                <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{item.reason}</p>
              </div>
              {item.severity === 'medium' && <div className="w-2 h-2 rounded-full bg-emerald-400"></div>}
            </div>
          )
        })}
      </div>
    </div>
  )
}
