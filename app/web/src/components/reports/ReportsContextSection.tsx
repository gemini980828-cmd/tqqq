import type { AppSnapshot } from '../../types/appSnapshot';
import { useNavigate } from 'react-router-dom';
import { resolveScreenRoute } from '../../lib/navigation';

export default function ReportsContextSection({
  priorityActions = [],
  events = [],
  meta,
}: {
  priorityActions?: AppSnapshot['priority_actions'];
  events?: AppSnapshot['event_timeline'];
  meta?: AppSnapshot['meta'];
}) {
  const navigate = useNavigate();

  const activeAction = priorityActions[0];
  const recentEvent = events[0];
  const hasMeta = Boolean(meta?.signal_updated_at || meta?.market_updated_at || meta?.summary_source_version);

  if (!activeAction && !recentEvent && !hasMeta) return null;

  return (
    <section>
      <div className="mb-5 flex items-center justify-between">
        <h3 className="text-sm font-semibold tracking-wider text-slate-500 uppercase">연결된 컨텍스트</h3>
      </div>
      
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {activeAction && (
          <div className="flex items-center justify-between rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 backdrop-blur-md">
            <div>
              <h4 className="text-sm font-semibold text-white">우선 액션 {priorityActions.length}건 대기 중</h4>
              <p className="mt-0.5 text-xs text-slate-400">{activeAction.title}</p>
            </div>
            {activeAction.goto_screen && (
              <button 
                onClick={() => navigate(resolveScreenRoute(activeAction.goto_screen, activeAction.manager_id))}
                className="rounded bg-rose-500/20 px-4 py-1.5 text-xs font-medium text-rose-400 transition hover:bg-rose-500/30"
              >
                액션 보기
              </button>
            )}
          </div>
        )}

        {recentEvent && (
          <div className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-900/70 p-4 backdrop-blur-md">
            <div>
              <h4 className="text-sm font-semibold text-white">최근 이벤트</h4>
              <p className="mt-0.5 text-xs text-slate-400">{recentEvent.title || recentEvent.detail}</p>
            </div>
            {recentEvent.date && (
              <span className="text-xs text-slate-500">
                {new Date(recentEvent.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
              </span>
            )}
          </div>
        )}

        {hasMeta && (
          <div className="rounded-xl border border-slate-700 bg-slate-900/70 p-4 backdrop-blur-md">
            <h4 className="text-sm font-semibold text-white">기준 시점</h4>
            <div className="mt-2 space-y-1 text-xs text-slate-400">
              {meta?.signal_updated_at ? <p>신호 기준: {new Date(meta.signal_updated_at).toLocaleString('ko-KR')}</p> : null}
              {meta?.market_updated_at ? <p>시장 기준: {new Date(meta.market_updated_at).toLocaleString('ko-KR')}</p> : null}
              {meta?.summary_source_version ? <p>요약 버전: {meta.summary_source_version}</p> : null}
              {typeof meta?.audit_available === 'boolean' ? <p>감사 로그: {meta.audit_available ? '사용 가능' : '없음'}</p> : null}
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
