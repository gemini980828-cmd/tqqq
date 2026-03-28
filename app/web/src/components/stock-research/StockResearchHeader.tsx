import type { StockResearchWorkspace } from '../../types/appSnapshot'

interface Props {
  workspace: StockResearchWorkspace
}

export function StockResearchHeader({ workspace }: Props) {
  const topPick = workspace.queue[0]
  const activeStage = workspace.flow?.active_stage
  const pipeline = workspace.flow?.pipeline ?? []
  
  return (
    <div className="mb-6 rounded-2xl border border-white/10 bg-white/[0.02] p-6 shadow-xl backdrop-blur-md flex flex-col lg:flex-row gap-6 justify-between lg:items-center">
      <div className="space-y-1 flex-1">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-xl font-semibold tracking-tight text-white">Stock Research</h1>
          <span className="px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 text-xs font-medium border border-sky-500/20">
            Workbench
          </span>
        </div>
        <p className="text-sm text-slate-400 leading-relaxed max-w-2xl">
          주식 자산군의 후보 탐색, 우선순위 큐 관리, 리스크 및 핏 검증을 수행하는 메인 작업 공간입니다.
        </p>
      </div>

      {pipeline.length > 0 && (
        <div className="flex items-center gap-2 shrink-0 bg-slate-900/50 p-2.5 rounded-xl border border-white/5">
          {pipeline.map((stage, i) => {
            const isActive = stage === activeStage
            return (
              <div key={stage} className="flex items-center">
                <div className={`px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-colors ${
                  isActive ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]' : 'text-slate-500'
                }`}>
                  {stage}
                </div>
                {i < pipeline.length - 1 && (
                  <div className="w-4 h-[1px] bg-slate-700 mx-1" />
                )}
              </div>
            )
          })}
        </div>
      )}

      {topPick && (
        <div className="shrink-0 flex items-center gap-4 bg-sky-950/30 p-4 rounded-xl border border-sky-500/20 shadow-inner min-w-[280px]">
          <div className="w-10 h-10 rounded-full bg-sky-500/20 flex items-center justify-center border border-sky-500/30 text-sky-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m12 14 4-4" />
              <path d="M3.34 19a10 10 0 1 1 17.32 0" />
            </svg>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-sky-400/80 font-semibold mb-0.5">Top Priority Queue</p>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-bold text-white">{topPick.symbol}</span>
              <span className="text-sm text-slate-300 truncate max-w-[120px]">{topPick.title}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
