import { Link } from 'react-router-dom'
import { getManagerRoute } from '../lib/navigation'
import type { ManagerCardSummary } from '../types/appSnapshot'

export default function ManagerCard({ card, hasPriorityAction, hasCrossAlert }: { card: ManagerCardSummary, hasPriorityAction?: boolean, hasCrossAlert?: boolean }) {
  const route = getManagerRoute(card.manager_id)

  let borderStyle = 'border-dark-700 hover:border-gray-500'
  let topNavColor = 'bg-green-500'
  let dotColor = 'bg-green-500'
  let textColor = 'text-green-400'
  let statusText = 'Monitoring Normal'

  if (hasPriorityAction) {
    borderStyle = 'border-brand-primary/30 hover:border-brand-primary/60'
    topNavColor = 'bg-gradient-to-r from-red-500 to-yellow-500'
    dotColor = 'bg-red-500'
    textColor = 'text-red-400'
    statusText = 'Priority Action required'
  } else if (hasCrossAlert) {
    borderStyle = 'border-yellow-500/30 hover:border-yellow-500/60'
    topNavColor = 'bg-yellow-500'
    dotColor = 'bg-yellow-500'
    textColor = 'text-yellow-500'
    statusText = 'Alerted'
  }

  return (
    <Link
      to={route}
      className={`glass-panel p-5 rounded-xl border ${borderStyle} relative overflow-hidden group transition cursor-pointer`}
      title={card.summary}
    >
        <div className={`absolute top-0 left-0 w-full h-1 ${topNavColor}`}></div>
        
        <h4 className="font-semibold text-white">{card.title || card.manager_id.replace('_', ' ').toUpperCase()}</h4>
        
        <div className="flex items-center gap-2 mt-2">
            <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
            <span className={`text-xs ${textColor} font-medium`}>{statusText}</span>
        </div>
        
        <div className="mt-4 pt-4 border-t border-dark-700 flex justify-between items-center text-sm text-gray-400">
            <span>{card.headline || 'Status: Active'}</span>
            <span className="group-hover:text-white transition">Enter &rarr;</span>
        </div>
    </Link>
  )
}
