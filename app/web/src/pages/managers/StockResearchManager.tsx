import { useMemo, useState } from 'react'
import type { AppSnapshot } from '../../types/appSnapshot'
import ManagerActionHeader from '../../components/ManagerActionHeader'
import { StockResearchHeader } from '../../components/stock-research/StockResearchHeader'
import { StockResearchQueue } from '../../components/stock-research/StockResearchQueue'
import { StockResearchWatchlist, type StockResearchFilterType, type StockResearchSortType } from '../../components/stock-research/StockResearchWatchlist'
import { StockResearchDetail } from '../../components/stock-research/StockResearchDetail'
import { resolveStockResearchWorkspace } from '../../lib/stockResearchDashboard'

export default function StockResearchManager({ snapshot }: { snapshot?: AppSnapshot }) {
  const workspace = useMemo(() => resolveStockResearchWorkspace(snapshot), [snapshot])
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(workspace.items[0]?.symbol ?? null)
  const [query, setQuery] = useState('')
  const [activeFilter, setActiveFilter] = useState<StockResearchFilterType>('all')
  const [activeSort, setActiveSort] = useState<StockResearchSortType>('score')

  const visibleItems = useMemo(() => {
    let result = [...workspace.items]

    if (query.trim()) {
      const q = query.toLowerCase()
      result = result.filter(item => 
        item.symbol.toLowerCase().includes(q) || 
        item.company_name.toLowerCase().includes(q)
      )
    }

    switch (activeFilter) {
      case 'held':
        result = result.filter(item => item.is_held)
        break
      case 'new_focus':
        result = result.filter(item => !item.is_held && item.priority === 'high')
        break
      case 'worsened':
        result = result.filter(item => item.priority === 'high' && item.is_held)
        break
      case 'high_overlap':
        result = result.filter(item => item.overlap_level === 'high')
        break
    }

    result.sort((a, b) => {
      if (activeSort === 'score') {
        const priorityOrder = { high: 3, medium: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      }
      if (activeSort === 'recent') {
        return new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime()
      }
      if (activeSort === 'overlap') {
        const overlapOrder = { high: 3, medium: 2, low: 1 }
        return overlapOrder[b.overlap_level] - overlapOrder[a.overlap_level]
      }
      if (activeSort === 'risk') {
        return (b.priority === 'high' ? 1 : 0) - (a.priority === 'high' ? 1 : 0)
      }
      return 0
    })

    return result
  }, [workspace.items, query, activeFilter, activeSort])

  const selectedItem = useMemo(() => {
    return workspace.items.find(item => item.symbol === selectedSymbol) ?? visibleItems[0] ?? null
  }, [workspace.items, selectedSymbol, visibleItems])

  return (
    <div className="flex flex-col">
      <ManagerActionHeader managerId="stock_research" snapshot={snapshot} />
      <StockResearchHeader workspace={workspace} />
      
      <div className="mb-6">
        <StockResearchQueue 
          queue={workspace.queue} 
          lastSyncAt={new Date(workspace.generated_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
          onSelectCallback={setSelectedSymbol}
        />
      </div>

      <div className="workspace h-[calc(100vh-350px)] min-h-[600px] flex overflow-hidden rounded-2xl border border-white/5 bg-[#0b1423]">
        <StockResearchWatchlist 
          items={visibleItems} 
          filters={workspace.filters} 
          selectedItemId={selectedItem?.symbol ?? null}
          onSelectCallback={setSelectedSymbol}
          query={query}
          onQueryChange={setQuery}
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          activeSort={activeSort}
          onSortChange={setActiveSort}
        />
        <StockResearchDetail 
          item={selectedItem} 
          compareSeed={workspace.compare_seed} 
          evidence={workspace.evidence}
        />
      </div>
    </div>
  )
}
