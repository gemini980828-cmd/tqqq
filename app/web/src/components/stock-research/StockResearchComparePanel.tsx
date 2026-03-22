import type { StockResearchCompareSeed, StockResearchWorkspaceItem } from '../../types/appSnapshot'
import { getStockResearchItemBadge } from '../../lib/stockResearchDashboard'

interface Props {
  item: StockResearchWorkspaceItem
  compareSeed: StockResearchCompareSeed | null
}

export function StockResearchComparePanel({ item, compareSeed }: Props) {
  return (
    <div className="p-5 rounded-xl border border-indigo-500/20 bg-indigo-900/5" style={{ background: 'rgba(15, 23, 42, 0.7)' }}>
      <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path>
        </svg>
        직접 비교 테이블 (Compare Slots)
      </h3>
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="bg-[#0f172a]/80 border border-[#334155] rounded-lg p-3 text-center cursor-pointer hover:border-slate-500 transition border-dashed">
          <span className="text-indigo-400 font-bold tracking-wide">🔍 {item.symbol}</span>
          <div className="text-[10px] text-slate-500 mt-1">{getStockResearchItemBadge(item)}</div>
        </div>
        <div className="bg-[#0f172a] border fill-indigo-500/10 border-indigo-500/30 rounded-lg p-3 text-center cursor-pointer hover:border-indigo-400 transition flex items-center justify-center group flex-col">
          <span className="text-slate-400 font-medium text-xs group-hover:text-indigo-300 transition">비교 대상 추가하기 +</span>
          <div className="text-[10px] text-slate-500 mt-1">예: {compareSeed?.candidate_symbols[0] || 'AAPL'} (신규후보)</div>
        </div>
      </div>
      <button className="w-full py-2 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-bold transition flex justify-center items-center gap-2">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
        상세 비교 뷰어 열기 (Fit & Overlap 대조)
      </button>
    </div>
  )
}
