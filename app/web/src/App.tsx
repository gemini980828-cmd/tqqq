import { useEffect, useState } from 'react'

import Dashboard, { type DashboardSnapshot } from './pages/Dashboard'

function App() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot | undefined>()

  useEffect(() => {
    let cancelled = false

    async function loadSnapshot() {
      try {
        const response = await fetch('/dashboard_snapshot.json', { cache: 'no-store' })
        if (!response.ok) return
        const data = (await response.json()) as DashboardSnapshot
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

  return <Dashboard snapshot={snapshot} />
}

export default App
