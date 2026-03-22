import type { EventTimelineItem } from '../../types/appSnapshot'

export default function HomeRecentActivity({ events }: { events: EventTimelineItem[] }) {
  if (!events || events.length === 0) return null

  // limit to 4-5 items as per handoff
  const recentEvents = events.slice(0, 4)

  return (
    <section className="mt-8 pt-6 border-t border-dark-700">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Recent Activity</h3>
      <div className="space-y-4">
        {recentEvents.map((evt, idx) => (
          <div key={`${evt.id ?? evt.date}-${idx}`} className="flex gap-4 items-start relative before:absolute before:inset-y-0 before:left-[11px] before:w-px before:bg-dark-600 last:before:hidden">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 z-10 ${
              evt.severity === 'high' ? 'bg-alert-danger text-white' : 
              evt.severity === 'medium' ? 'bg-alert-warning text-white' : 
              'bg-dark-600 text-gray-400'
            }`}>
              <div className="w-2 h-2 rounded-full bg-current"></div>
            </div>
            <div className="flex-1 pb-4">
              <div className="flex justify-between items-start">
                <p className="text-sm text-gray-300">
                  {evt.source_manager_id && (
                    <span className="font-semibold text-gray-400 mr-2">[{evt.source_manager_id.replace('_', ' ').toUpperCase()}]</span>
                  )}
                  {evt.title || evt.event || evt.detail}
                </p>
                <time className="text-xs text-gray-500 whitespace-nowrap ml-4">{evt.timestamp || evt.date}</time>
              </div>
              {evt.title && evt.detail ? <p className="mt-1 text-xs text-gray-400">{evt.detail}</p> : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
