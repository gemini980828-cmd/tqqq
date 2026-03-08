import ManagerCard from '../components/ManagerCard'
import OrchestratorPanel from '../components/OrchestratorPanel'
import type { AppSnapshot, HomeInboxItem } from '../types/appSnapshot'

type WealthOverview = NonNullable<AppSnapshot['wealth_overview']>
type ManagerCards = NonNullable<AppSnapshot['manager_cards']>

function formatKrw(value?: number) {
  if (value === undefined || Number.isNaN(value)) return 'N/A'
  return new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 }).format(value)
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-white/8 bg-white/[0.04] p-5 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-white">{value}</p>
    </div>
  )
}

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

const FALLBACK_CARDS: ManagerCards = [
  { manager_id: 'core_strategy', title: 'Core Strategy', headline: '실보유 86.63% / 목표 95.00%', summary: 'TQQQ 코어 전략 운영', status: 'active' },
  { manager_id: 'stock_research', title: 'Stock Research', headline: '관심종목 1개', summary: '후보 발굴/관찰/보류 관리', status: 'tracking' },
  { manager_id: 'real_estate', title: 'Real Estate', headline: '관심 단지 1개', summary: '관심 단지 추적 및 검토', status: 'tracking' },
  { manager_id: 'cash_debt', title: 'Cash & Debt', headline: '현금/부채 항목 1개', summary: '현금 여력과 상환일 관리', status: 'tracking' },
]

const FALLBACK_INBOX: HomeInboxItem[] = [
  {
    id: 'fallback-action',
    manager_id: 'core_strategy',
    severity: 'high',
    title: '코어전략 액션 확인',
    detail: '오늘 액션과 목표 비중을 먼저 확인하세요.',
  },
  {
    id: 'fallback-manual-source',
    manager_id: 'cash_debt',
    severity: 'low',
    title: 'Manual truth source',
    detail: 'wealth_manual.json 기준으로 manager summary cache를 갱신합니다.',
  },
]

export default function Home({ snapshot }: { snapshot?: AppSnapshot }) {
  const overview: WealthOverview = snapshot?.wealth_home?.overview ?? snapshot?.wealth_overview ?? {
    invested_krw: 9_720_000,
    investable_assets_krw: 9_720_000,
    cash_krw: 1_500_000,
    debt_krw: 0,
    net_worth_krw: 11_220_000,
  }
  const cards: ManagerCards = snapshot?.wealth_home?.manager_cards ?? snapshot?.manager_cards ?? FALLBACK_CARDS
  const action = snapshot?.action_hero?.action ?? '유지'
  const actionWeight = snapshot?.action_hero?.target_weight_pct ?? 95
  const timeline = snapshot?.event_timeline ?? []
  const inbox = snapshot?.wealth_home?.inbox_preview ?? snapshot?.home_inbox?.slice(0, 3) ?? FALLBACK_INBOX

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-white/8 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.16),_transparent_36%),linear-gradient(135deg,rgba(15,23,42,0.96),rgba(15,23,42,0.92))] p-6 shadow-[0_24px_90px_rgba(2,6,23,0.35)] md:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl space-y-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Home desk</p>
            <h2 className="text-4xl font-semibold tracking-[-0.05em] text-white md:text-5xl">전체 자산 현황과 오늘의 액션을 한 화면에서 봅니다.</h2>
            <p className="text-sm leading-7 text-slate-300 md:text-base">
              현재 단계에서는 TQQQ 코어전략을 중심축으로 유지하면서, 개별주/부동산/현금·부채 매니저로 확장할 수 있는 기본 운영데스크를 구축합니다.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:min-w-[360px]">
            <div className="rounded-2xl border border-sky-300/20 bg-sky-400/10 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Today action</p>
              <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">{action}</p>
              <p className="mt-2 text-sm text-slate-300">전략 목표 비중 {actionWeight}%</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-400">System stance</p>
              <p className="mt-2 text-base font-medium text-white">투자운영 중심 자산관리</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">실시간 AI는 나중 단계에서 붙이고, 현재는 manager shell과 truth data를 우선 안정화합니다.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryMetric label="총 순자산" value={`${formatKrw(overview.net_worth_krw)}원`} />
        <SummaryMetric label="투자 자산" value={`${formatKrw(overview.investable_assets_krw ?? overview.invested_krw)}원`} />
        <SummaryMetric label="현금" value={`${formatKrw(overview.cash_krw)}원`} />
        <SummaryMetric label="부채" value={`${formatKrw(overview.debt_krw)}원`} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
          <div className="mb-5 flex items-end justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Managers</p>
              <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">Manager hub</h3>
            </div>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-300">{cards.length || 4} surfaces</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {cards.map((card) => (
              <ManagerCard key={card.manager_id} card={card} />
            ))}
          </div>
        </div>

        <OrchestratorPanel snapshot={snapshot} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(320px,0.9fr)]">
        <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Recent activity</p>
              <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">최근 주요 변화</h3>
            </div>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-slate-300">
              {timeline.length ? `${timeline.length} events` : 'No recent events'}
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {(timeline.length
              ? timeline.slice(0, 4)
              : [{ date: '오늘', type: '유지', detail: 'Step 2에서는 Home 활동 로그와 inbox preview를 summary cache 기반으로 연결합니다.' }]
            ).map((event) => (
              <div key={`${event.date}:${event.type}:${event.detail}`} className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
                <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                  <span>{event.date}</span>
                  <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-slate-300">
                    {event.type}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-300">{event.detail}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Inbox preview</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">오늘 확인할 것</h3>
          <div className="mt-5 space-y-3 text-sm text-slate-300">
            {inbox.map((item) => (
              <div key={item.id} className={`rounded-2xl border px-4 py-3 ${getSeverityTone(item.severity)}`}>
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-white">{item.title}</p>
                  <span className="text-[11px] uppercase tracking-[0.18em] text-slate-400">{item.manager_id}</span>
                </div>
                <p className="mt-2 leading-6">{item.detail}</p>
                {item.recommended_action ? <p className="mt-2 text-xs text-slate-400">다음 액션: {item.recommended_action}</p> : null}
              </div>
            ))}
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
              Manual truth source: {snapshot?.meta?.manual_source_version ?? 'wealth_manual.json'}
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
