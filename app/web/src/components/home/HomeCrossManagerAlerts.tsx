import { useNavigate } from 'react-router-dom'
import type { CrossManagerAlert } from '../../types/appSnapshot'
import { resolveScreenRoute } from '../../lib/navigation'

export default function HomeCrossManagerAlerts({ alerts }: { alerts: CrossManagerAlert[] }) {
  const navigate = useNavigate()

  if (!alerts || alerts.length === 0) return null

  return (
    <section>
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Cross-Manager Alerts</h3>
      <div className="space-y-3">
        {alerts.map((alert) => (
          <div key={alert.id} className="glass-panel p-4 rounded-xl border-l-4 border-l-brand-primary">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-white">{alert.title}</h4>
                <p className="text-xs text-gray-400 mt-1">{alert.detail}</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-end items-center">
                {alert.manager_ids.map((mId) => (
                  <span key={mId} className="text-xs px-2 py-1 rounded-md bg-dark-700 text-gray-300 border border-dark-600">
                    {mId.replace('_', ' ').toUpperCase()}
                  </span>
                ))}
                <button
                  onClick={() => navigate(resolveScreenRoute(alert.goto_screen, alert.manager_ids[0]))}
                  className="text-xs text-brand-accent hover:text-white px-2 py-1 rounded-md bg-brand-primary/10 ml-2"
                >
                  Analyze Conflict &rarr;
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
