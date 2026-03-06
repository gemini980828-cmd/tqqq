import type { AppSnapshot, HomeInboxItem } from '../types/appSnapshot'

function getSeverityTone(severity?: HomeInboxItem['severity']) {
  switch (severity) {
    case 'high':
      return 'border-rose-300/15 bg-rose-500/8 text-rose-100'
    case 'medium':
      return 'border-amber-300/15 bg-amber-500/8 text-amber-100'
    default:
      return 'border-white/8 bg-slate-950/40 text-slate-300'
  }
}

const FALLBACK_ITEMS: HomeInboxItem[] = [
  {
    id: 'fallback-action',
    manager_id: 'core_strategy',
    severity: 'high',
    title: '오늘 액션 확인',
    detail: 'manager summary cache가 없으면 action_hero 기준 기본 액션만 표시합니다.',
  },
]

export default function Inbox({ snapshot }: { snapshot?: AppSnapshot }) {
  const items = snapshot?.home_inbox ?? FALLBACK_ITEMS

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Inbox</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">실행 인박스</h2>
      <div className="mt-5 space-y-3">
        {items.map((item) => (
          <div key={item.id} className={`rounded-2xl border px-4 py-3 ${getSeverityTone(item.severity)}`}>
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium text-white">{item.title}</p>
              <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400">{item.manager_id}</span>
            </div>
            <p className="mt-2 text-sm leading-6">{item.detail}</p>
            {item.recommended_action ? <p className="mt-2 text-xs text-slate-400">다음 액션: {item.recommended_action}</p> : null}
          </div>
        ))}
      </div>
    </section>
  )
}
