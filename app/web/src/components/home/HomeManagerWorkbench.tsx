import { Link } from 'react-router-dom'
import type { ManagerCardSummary, PriorityAction, CrossManagerAlert } from '../../types/appSnapshot'
import ManagerCard from '../ManagerCard'

export default function HomeManagerWorkbench({ managers, priorityActions = [], crossAlerts = [] }: { managers: ManagerCardSummary[], priorityActions?: PriorityAction[], crossAlerts?: CrossManagerAlert[] }) {
  if (!managers || managers.length === 0) return null

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Manager Workbench</h3>
        <Link to="/managers" className="text-xs text-brand-primary hover:underline">View All</Link>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {managers.map((manager) => {
          const hasPriorityAction = priorityActions.some(a => a.manager_id === manager.manager_id);
          const hasCrossAlert = crossAlerts.some(a => a.manager_ids.includes(manager.manager_id));
          return <ManagerCard key={manager.manager_id} card={manager} hasPriorityAction={hasPriorityAction} hasCrossAlert={hasCrossAlert} />
        })}
      </div>
    </section>
  )
}
