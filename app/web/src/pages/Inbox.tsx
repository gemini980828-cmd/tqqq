import type { AppSnapshot } from '../types/appSnapshot'

export default function Inbox({ snapshot }: { snapshot?: AppSnapshot }) {
  const items = [
    `오늘 액션: ${snapshot?.action_hero?.action ?? '유지'} / 목표 ${snapshot?.action_hero?.target_weight_pct ?? 95}%`,
    'Manager summary cache 연결 예정',
    '리스크 경보/수동 follow-up 항목은 후속 단계에서 자동 생성',
  ]

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Inbox</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">실행 인박스</h2>
      <div className="mt-5 space-y-3">
        {items.map((item) => (
          <div key={item} className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3 text-sm text-slate-300">
            {item}
          </div>
        ))}
      </div>
    </section>
  )
}
