import { useEffect, useState } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'

import TopNav from './components/TopNav'
import type { AppSnapshot } from './types/appSnapshot'
import Dashboard from './pages/Dashboard'
import Home from './pages/Home'
import Inbox from './pages/Inbox'
import Managers from './pages/Managers'
import Research from './pages/Research'
import Reports from './pages/Reports'
import CashDebtManager from './pages/managers/CashDebtManager'
import CoreStrategyManager from './pages/managers/CoreStrategyManager'
import ManagersLayout from './pages/managers/ManagersLayout'
import RealEstateManager from './pages/managers/RealEstateManager'
import StockResearchManager from './pages/managers/StockResearchManager'

function AppShell({ snapshot }: { snapshot?: AppSnapshot }) {
  return (
    <HashRouter>
      <div className="h-screen w-screen overflow-hidden bg-[#08101b] text-slate-100 flex flex-col">
        <TopNav />
        <main className="flex-1 overflow-y-auto mx-auto w-full max-w-7xl px-4 py-6 md:px-8 md:py-8">
          <Routes>
            <Route path="/" element={<Home snapshot={snapshot} />} />
            <Route path="/managers" element={<ManagersLayout />}>
              <Route index element={<Managers snapshot={snapshot} />} />
              <Route path="core-strategy" element={<CoreStrategyManager snapshot={snapshot} />} />
              <Route path="stocks" element={<StockResearchManager snapshot={snapshot} />} />
              <Route path="real-estate" element={<RealEstateManager snapshot={snapshot} />} />
              <Route path="cash-debt" element={<CashDebtManager snapshot={snapshot} />} />
            </Route>
            <Route path="/research" element={<Research />} />
            <Route path="/inbox" element={<Inbox snapshot={snapshot} />} />
            <Route path="/reports" element={<Reports snapshot={snapshot} />} />
            <Route path="/legacy-dashboard" element={<Dashboard snapshot={snapshot} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}

export default function App() {
  const [snapshot, setSnapshot] = useState<AppSnapshot | undefined>()

  useEffect(() => {
    let cancelled = false

    async function loadSnapshot() {
      try {
        const response = await fetch('/dashboard_snapshot.json', { cache: 'no-store' })
        if (!response.ok) return
        const data = (await response.json()) as AppSnapshot
        if (!cancelled) {
          setSnapshot(data)
        }
      } catch {
        // Fallback to in-component mock snapshot when static export is unavailable.
      }
    }

    void loadSnapshot()
    return () => {
      cancelled = true
    }
  }, [])

  return <AppShell snapshot={snapshot} />
}
