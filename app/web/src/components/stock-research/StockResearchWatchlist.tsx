import type { StockResearchFilters, StockResearchWorkspaceItem } from '../../types/appSnapshot'
import { getStockResearchItemBadge, getStockResearchItemScore, getStockResearchRiskLabel } from '../../lib/stockResearchDashboard'

export type StockResearchSortType = 'score' | 'recent' | 'overlap' | 'risk'
export type StockResearchFilterType = 'all' | 'held' | 'new_focus' | 'worsened' | 'high_overlap'

interface Props {
  items: StockResearchWorkspaceItem[]
  filters: StockResearchFilters
  selectedItemId: string | null
  onSelectCallback?: (symbol: string) => void
  query: string
  onQueryChange: (q: string) => void
  activeFilter: StockResearchFilterType
  onFilterChange: (f: StockResearchFilterType) => void
  activeSort: StockResearchSortType
  onSortChange: (s: StockResearchSortType) => void
}

export function StockResearchWatchlist({ items, filters, selectedItemId, onSelectCallback, query, onQueryChange, activeFilter, onFilterChange, activeSort, onSortChange }: Props) {
  return (
    <div className="w-1/3 xl:w-96 border-r border-dark-700 bg-[#08101b] flex flex-col flex-shrink-0 z-0 h-full overflow-hidden">
      <div className="p-4 border-b border-slate-700/50 space-y-3 bg-[#08101b]/95 sticky top-0 backdrop-blur-md">
        <div className="relative">
          <input
            type="text"
            placeholder="종목, 섹터, 테마 검색..."
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            className="w-full bg-[#0f172a] border border-[#334155] rounded-lg pl-9 pr-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
          />
          <svg className="w-4 h-4 text-slate-500 absolute left-3 top-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </div>

        <div className="flex justify-between items-center">
          <div className="flex gap-2 text-xs">
            <select className="bg-[#0f172a] border border-[#334155] text-slate-300 rounded px-2 py-1 outline-none">
              <option>전체 섹터</option>
              <option>Technology</option>
              <option>Healthcare</option>
            </select>
            <select 
              value={activeSort}
              onChange={(e) => onSortChange(e.target.value as StockResearchSortType)}
              className="bg-[#0f172a] border border-[#334155] text-slate-300 rounded px-2 py-1 outline-none"
            >
              <option value="score">우선순위순 ↓</option>
              <option value="recent">최근 업데이트순 ↓</option>
              <option value="overlap">오버랩 높은순 ↓</option>
              <option value="risk">리스크 급등순 ↓</option>
            </select>
          </div>
          <button className="text-slate-400 hover:text-white transition">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path>
            </svg>
          </button>
        </div>

        {/* Advanced Filter Chips */}
        <div className="flex gap-2 overflow-x-auto custom-scrollbar pt-2 pb-1">
          <button 
            onClick={() => onFilterChange('all')}
            className={`whitespace-nowrap px-3 py-1 rounded-full text-[11px] font-medium transition ${activeFilter === 'all' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'bg-[#0f172a] text-slate-300 border border-[#334155] hover:bg-[#1e293b]'}`}
          >
            전체 ({filters.total_count})
          </button>
          <button 
            onClick={() => onFilterChange('held')}
            className={`whitespace-nowrap px-3 py-1 rounded-full text-[11px] font-medium transition ${activeFilter === 'held' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'bg-[#0f172a] text-slate-300 border border-[#334155] hover:bg-[#1e293b]'}`}
          >
            보유중 ({filters.held_count})
          </button>
          <button 
            onClick={() => onFilterChange('new_focus')}
            className={`whitespace-nowrap px-3 py-1 rounded-full text-[11px] font-medium transition ${activeFilter === 'new_focus' ? 'bg-sky-500/20 text-sky-400 border border-sky-500/30' : 'bg-[#0f172a] text-slate-300 border border-[#334155] hover:bg-[#1e293b]'}`}
          >
            신규후보 집중
          </button>
          <button 
            onClick={() => onFilterChange('worsened')}
            className={`whitespace-nowrap px-3 py-1 rounded-full text-[11px] font-medium transition flex items-center gap-1 ${activeFilter === 'worsened' ? 'bg-rose-900/30 text-rose-300 border border-rose-500/20' : 'bg-[#0f172a] text-slate-300 border border-[#334155] hover:bg-rose-900/10 hover:text-rose-300'}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${activeFilter === 'worsened' ? 'bg-rose-500' : 'bg-slate-600'}`}></span>
            최근 상태 악화
          </button>
          <button 
            onClick={() => onFilterChange('high_overlap')}
            className={`whitespace-nowrap px-3 py-1 rounded-full text-[11px] font-medium transition ${activeFilter === 'high_overlap' ? 'bg-amber-900/30 text-amber-300 border border-amber-500/20' : 'bg-[#0f172a] text-slate-300 border border-[#334155] hover:bg-amber-900/10 hover:text-amber-300'}`}
          >
            고중복(Overlap) 경계
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
        {items.map((item) => {
          const isSelected = selectedItemId === item.idea_id || selectedItemId === item.symbol
          const score = getStockResearchItemScore(item)
          const badge = getStockResearchItemBadge(item)
          const scoreTone = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-sky-300' : 'text-rose-400'
          const scoreArrow = score >= 80 ? '↑' : score >= 60 ? '→' : '↓'

          return (
            <div
              key={item.idea_id}
              onClick={() => onSelectCallback?.(item.symbol)}
              className={`p-3 rounded-lg cursor-pointer transition ml-1 relative overflow-hidden ${
                isSelected
                  ? 'bg-sky-900/30 border border-sky-500/40 shadow-[0_0_10px_rgba(56,189,248,0.05)]'
                  : 'hover:bg-[#0f172a] border border-transparent hover:border-[#334155]'
              }`}
            >
              {isSelected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-sky-500"></div>}
              <div className={`flex justify-between items-start mb-1.5 ${isSelected ? 'ml-1' : ''}`}>
                <div className="flex items-center gap-2">
                  <span className={`font-bold text-base ${isSelected ? 'text-white' : 'text-slate-300'}`}>{item.symbol}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${
                    item.is_held
                      ? 'bg-slate-700 text-slate-300 border-slate-600'
                      : item.status === '후보'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                        : 'bg-sky-500/10 text-sky-300 border-sky-500/20'
                  }`}>{badge}</span>
                  {item.priority === 'high' && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 font-medium">{item.priority_reason}</span>
                  )}
                </div>
                <span className={`text-[13px] font-bold ${scoreTone}`}>{score} <span className="text-[10px]">{scoreArrow}</span></span>
              </div>
              
              <div className={`mb-2 ${isSelected ? 'ml-1' : ''}`}>
                <div className="text-[11px] text-slate-400 truncate">{item.company_name}</div>
              </div>
              
              {isSelected && (
                <div className="flex gap-1.5 ml-1 flex-wrap mb-2">
                  <span className="text-[10px] bg-emerald-900/50 text-emerald-300 font-medium px-1.5 py-0.5 rounded flex items-center gap-1 border border-emerald-500/20">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Fit 95%
                  </span>
                  <span className="text-[10px] bg-amber-900/30 text-amber-300 font-medium px-1.5 py-0.5 rounded border border-amber-500/20">
                    Risk: {getStockResearchRiskLabel(item)}
                  </span>
                </div>
              )}
              
              <div className={`${isSelected ? 'ml-1 bg-sky-950/50 border-sky-500/20' : 'bg-[#0f172a] border-[#334155]'} border p-1.5 rounded text-[11px] ${isSelected ? 'text-sky-200' : 'text-slate-400 truncate'}`}>
                <strong>Next:</strong> {item.next_action}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
