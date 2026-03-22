import { useNavigate } from 'react-router-dom'
import type { PriorityAction } from '../../types/appSnapshot'
import { resolveScreenRoute } from '../../lib/navigation'

export default function HomePriorityActions({ actions }: { actions: PriorityAction[] }) {
  const navigate = useNavigate()

  if (!actions || actions.length === 0) return null

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-alert-danger animate-pulse"></span>
          Priority Actions
        </h3>
      </div>
      <div className="grid grid-cols-1 gap-4">
        {actions.map((action) => (
          <div key={action.id} className="glass-panel p-5 rounded-xl flex items-center justify-between hover-lift">
            <div className="flex gap-4 items-start">
              <div
                className={`mt-1 flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  action.severity === 'high'
                    ? 'bg-red-500/10 border border-red-500/20 text-red-400'
                    : action.severity === 'medium'
                    ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-500'
                    : 'bg-blue-500/10 border border-blue-500/20 text-blue-400'
                }`}
              >
                {action.severity === 'high' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                )}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-bold px-2 py-0.5 rounded border ${
                      action.severity === 'high'
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : action.severity === 'medium'
                        ? 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30'
                        : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                    }`}
                  >
                    {action.severity.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-400 bg-dark-700 px-2 py-0.5 rounded">
                    {action.manager_id.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <h4 className="text-base font-medium text-white">{action.title}</h4>
                <p className="text-sm text-gray-400 mt-1">{action.detail}</p>
              </div>
            </div>
            <button
              onClick={() => navigate(resolveScreenRoute(action.goto_screen, action.manager_id))}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition ${
                action.severity === 'high'
                  ? 'bg-brand-primary hover:bg-brand-accent text-white shadow-lg shadow-blue-500/20'
                  : 'bg-dark-600 hover:bg-dark-500 text-white border border-dark-600'
              }`}
            >
              {action.recommended_action || (action.severity === 'high' ? 'Review & Execute' : 'Go to Details')}
            </button>
          </div>
        ))}
      </div>
    </section>
  )
}
