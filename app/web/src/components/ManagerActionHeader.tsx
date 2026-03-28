import { Link, useNavigate } from 'react-router-dom';
import type { AppSnapshot } from '../types/appSnapshot';
import { getManagerRoute, resolveScreenRoute } from '../lib/navigation';

function getSeverityTone(severity?: 'high' | 'medium' | 'low') {
  switch (severity) {
    case 'high':
      return 'border-rose-300/15 bg-rose-500/8 text-rose-100'
    case 'medium':
      return 'border-amber-300/15 bg-amber-500/8 text-amber-100'
    default:
      return 'border-white/8 bg-slate-950/40 text-slate-300'
  }
}

export default function ManagerActionHeader({ managerId, snapshot }: { managerId: string; snapshot?: AppSnapshot }) {
  const navigate = useNavigate()
  const priorityActions = snapshot?.priority_actions?.filter(a => a.manager_id === managerId) ?? [];
  const crossAlerts = snapshot?.cross_manager_alerts?.filter(a => a.manager_ids.includes(managerId)) ?? [];
  const managerEvents = snapshot?.manager_events?.[managerId] ?? [];

  if (priorityActions.length === 0 && crossAlerts.length === 0 && managerEvents.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4 mb-6">
      {/* 2. Priority Action 소비 */}
      {priorityActions.length > 0 && (
        <section className="rounded-[24px] border border-rose-500/30 bg-rose-500/5 p-5 shadow-lg">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-rose-400">Priority Actions</p>
          <div className="mt-3 space-y-3">
            {priorityActions.map(action => (
              <div key={action.id} className={`rounded-xl border px-4 py-3 ${getSeverityTone(action.severity)} flex flex-col md:flex-row md:items-center justify-between gap-4`}>
                <div>
                  <p className="font-semibold text-white">{action.title}</p>
                  <p className="mt-1 text-sm text-slate-300 leading-6">{action.detail}</p>
                </div>
                {action.recommended_action && (
                  <button
                    onClick={() => navigate(resolveScreenRoute(action.goto_screen, action.manager_id))}
                    className="whitespace-nowrap px-4 py-2 bg-rose-500/20 hover:bg-rose-500/40 text-rose-100 rounded-lg text-sm font-medium transition-colors border border-rose-500/30"
                  >
                    {action.recommended_action}
                  </button>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 3. Cross-Manager 관련성 힌트 */}
      {crossAlerts.length > 0 && (
        <section className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-amber-500">Cross-Manager Alert</p>
            <p className="text-sm text-slate-200 mt-1">이 매니저와 관련된 복합 이슈가 있습니다. 연관된 매니저를 함께 확인하세요.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {crossAlerts.flatMap(a => a.manager_ids).filter((v, i, a) => a.indexOf(v) === i).filter(id => id !== managerId).map(relatedId => (
               <Link key={relatedId} to={getManagerRoute(relatedId)} className="text-xs bg-dark-700 hover:bg-dark-600 text-amber-200 px-3 py-1.5 rounded-lg border border-amber-500/30 transition-colors">
                  {relatedId} 확인하기 &rarr;
               </Link>
            ))}
          </div>
        </section>
      )}

      {/* 1. Manager별 Event 연결 */}
      {managerEvents.length > 0 && (
        <section className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400 mb-4">최근 이벤트 / 판단 변화</p>
          <div className="space-y-3">
            {managerEvents.slice(0, 3).map((ev, idx) => (
              <div key={ev.id || idx} className="flex gap-3 text-sm">
                <span className="text-slate-500 font-mono text-xs mt-0.5 whitespace-nowrap">{ev.date}</span>
                <div>
                   {ev.title && <p className="font-medium text-slate-200">{ev.title}</p>}
                   <p className="text-slate-400 leading-6">{ev.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
