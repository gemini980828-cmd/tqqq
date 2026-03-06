import { useMemo, useState } from 'react';
import type { AppSnapshot, RiskGaugeValue, RiskStatus } from '../types/appSnapshot';

type MockState = 'action-needed' | 'no-action';

export type DashboardSnapshot = AppSnapshot;

const MOCK_SNAPSHOTS: Record<MockState, DashboardSnapshot> = {
  'action-needed': {
    action_hero: {
      action: '매수',
      target_weight_pct: 100,
      reason_summary: '추세 조건 5/6 충족, 과열 해제 확인, 오늘 장마감 기준 비중 확대 검토가 필요합니다.',
      updated_at: '2026-03-06T06:00:00Z',
    },
    kpi_cards: {
      cagr_pct: 35.07,
      mdd_pct: -34.22,
      month_1_return_pct: 1.25,
      condition_pass_rate: '5/6',
    },
    risk_gauges: {
      vol20: { value: 3.24, threshold: 5.9, status: 'green' },
      spy200_dist: { value: 103.85, threshold: 97.75, status: 'green' },
      tqqq_dist200: { value: 101.72, threshold: 101.0, status: 'amber' },
    },
    event_timeline: [
      { date: '2026-03-06', type: '비중 변경', detail: '보유 비중 0% → 100% 전환 조건 충족' },
      { date: '2026-03-05', type: '재진입', detail: '현금 → 10% 선진입 허용 구간 복귀' },
      { date: '2026-02-21', type: 'TP10', detail: '100% → 95% 감량, +10% 이익 일부 확정' },
      { date: '2026-01-28', type: '강제청산', detail: '변동성 락 발동으로 100% → 0% 전환' },
    ],
    ops_log: {
      run_id: 'daily-2026-03-06',
      alert_key: '2026-03-06:0->2',
      last_success_at: '2026-03-06T06:00:03Z',
      next_run_at: '2026-03-07T06:00:00Z',
    },
  },
  'no-action': {
    action_hero: {
      action: '유지',
      target_weight_pct: 95,
      reason_summary: '주요 조건이 안정적으로 유지되어 추가 체결 없이 현재 포지션만 모니터링하면 됩니다.',
      updated_at: '2026-03-06T06:00:00Z',
    },
    kpi_cards: {
      cagr_pct: 34.81,
      mdd_pct: -33.94,
      month_1_return_pct: 2.14,
      condition_pass_rate: '6/6',
    },
    risk_gauges: {
      vol20: { value: 2.88, threshold: 5.9, status: 'green' },
      spy200_dist: { value: 105.12, threshold: 97.75, status: 'green' },
      tqqq_dist200: { value: 104.4, threshold: 101.0, status: 'green' },
    },
    event_timeline: [
      { date: '2026-03-06', type: '유지', detail: '오늘도 TQQQ 95% 유지, 신규 액션 없음' },
      { date: '2026-03-04', type: '리스크 점검', detail: 'Vol20·SPY200·Dist200 모두 안정 구간 유지' },
      { date: '2026-03-03', type: '운영 상태', detail: '텔레그램/대시보드 스냅샷 갱신 완료' },
      { date: '2026-02-21', type: 'TP10', detail: '100% → 95% 감량 이후 상태 유지' },
    ],
    ops_log: {
      run_id: 'daily-2026-03-06',
      alert_key: '2026-03-06:2->2',
      last_success_at: '2026-03-06T06:00:02Z',
      next_run_at: '2026-03-07T06:00:00Z',
    },
  },
};

function formatPct(val?: number, fractionDigits = 2) {
  if (val === undefined || Number.isNaN(val)) return 'N/A';
  return `${val > 0 ? '+' : ''}${val.toFixed(fractionDigits)}%`;
}

function formatTime(value?: string) {
  if (!value) return '';
  return new Date(value).toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusMeta(status?: RiskStatus) {
  switch (status) {
    case 'green':
      return {
        label: 'SAFE',
        text: 'text-emerald-200',
        badge: 'bg-emerald-500/12 text-emerald-100 border-emerald-300/35',
        track: 'bg-emerald-950/80',
        fill: 'from-emerald-500 via-emerald-400 to-emerald-300',
        glow: 'shadow-[0_0_30px_rgba(16,185,129,0.24)]',
        dot: 'bg-emerald-300',
        border: 'border-emerald-400/20',
      };
    case 'amber':
      return {
        label: 'WATCH',
        text: 'text-amber-100',
        badge: 'bg-amber-500/12 text-amber-50 border-amber-300/35',
        track: 'bg-amber-950/80',
        fill: 'from-amber-500 via-amber-400 to-amber-200',
        glow: 'shadow-[0_0_30px_rgba(251,191,36,0.24)]',
        dot: 'bg-amber-300',
        border: 'border-amber-400/20',
      };
    case 'red':
      return {
        label: 'RISK',
        text: 'text-rose-100',
        badge: 'bg-rose-500/12 text-rose-50 border-rose-300/35',
        track: 'bg-rose-950/80',
        fill: 'from-rose-500 via-rose-400 to-rose-200',
        glow: 'shadow-[0_0_30px_rgba(244,63,94,0.24)]',
        dot: 'bg-rose-300',
        border: 'border-rose-400/20',
      };
    default:
      return {
        label: 'UNKNOWN',
        text: 'text-slate-300',
        badge: 'bg-slate-500/10 text-slate-200 border-slate-400/20',
        track: 'bg-slate-900/80',
        fill: 'from-slate-500 via-slate-400 to-slate-300',
        glow: '',
        dot: 'bg-slate-400',
        border: 'border-white/10',
      };
  }
}

function getMockState(): MockState {
  if (typeof window === 'undefined') return 'action-needed';
  const state = new URLSearchParams(window.location.search).get('mock');
  return state === 'no-action' ? 'no-action' : 'action-needed';
}

function classifyEvent(type: string) {
  switch (type) {
    case '강제청산':
      return 'border-rose-300/20 bg-rose-500/10 text-rose-100';
    case 'TP10':
      return 'border-amber-300/20 bg-amber-500/10 text-amber-50';
    case '재진입':
    case '비중 변경':
      return 'border-sky-300/20 bg-sky-500/10 text-sky-100';
    default:
      return 'border-white/10 bg-white/5 text-slate-200';
  }
}

function calcGaugeFill(item: RiskGaugeValue, higherIsBetter: boolean) {
  if (Number.isNaN(item.value)) return 0;
  const ratio = item.threshold === 0 ? 0 : item.value / item.threshold;
  const normalized = higherIsBetter ? ratio * 72 : (2 - ratio) * 55;
  return Math.max(8, Math.min(100, normalized));
}

const ActionHero = ({ data, showingMock }: { data?: DashboardSnapshot['action_hero']; showingMock: boolean }) => {
  if (!data) {
    return <div className="rounded-3xl border border-rose-500/30 bg-rose-500/8 p-6 text-rose-200">Action Data N/A</div>;
  }

  const isActionNeeded = data.action !== '유지';
  const heroTone = isActionNeeded
    ? 'border-amber-400/30 bg-[radial-gradient(circle_at_top_left,_rgba(251,191,36,0.18),_transparent_42%),linear-gradient(135deg,rgba(15,23,42,0.98),rgba(17,24,39,0.94))]'
    : 'border-emerald-400/25 bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.16),_transparent_44%),linear-gradient(135deg,rgba(15,23,42,0.98),rgba(17,24,39,0.94))]';
  const badgeTone = isActionNeeded
    ? 'border-amber-300/30 bg-amber-400/12 text-amber-100'
    : 'border-emerald-300/30 bg-emerald-400/12 text-emerald-100';
  const directive = isActionNeeded
    ? `오늘 장마감 기준 TQQQ ${data.target_weight_pct}% ${data.action}`
    : `현재 포지션 ${data.target_weight_pct}% 유지`;

  return (
    <section className={`overflow-hidden rounded-[28px] border px-6 py-6 shadow-[0_24px_90px_rgba(2,6,23,0.42)] md:px-8 md:py-8 ${heroTone}`}>
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${badgeTone}`}>
              {isActionNeeded ? 'Action Needed' : 'No Action'}
            </span>
            <span className="text-sm text-slate-400">{formatTime(data.updated_at)} 업데이트</span>
            {showingMock && (
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
                Demo snapshot
              </span>
            )}
          </div>

          <div className="space-y-3">
            <p className="text-sm font-medium tracking-[0.24em] text-slate-400 uppercase">Today&apos;s directive</p>
            <h1 className="text-4xl font-semibold leading-tight tracking-[-0.04em] text-white md:text-5xl">{directive}</h1>
            <p className="max-w-2xl text-[15px] leading-7 text-slate-300 md:text-base">{data.reason_summary}</p>
          </div>
        </div>

        <div className="grid min-w-full gap-3 sm:grid-cols-2 lg:min-w-[380px] lg:max-w-[420px]">
          <div className="rounded-2xl border border-white/10 bg-white/6 p-4 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Current action</p>
            <p className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white">{data.action}</p>
            <p className="mt-2 text-sm text-slate-300">목표 비중 {data.target_weight_pct}%</p>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4 backdrop-blur-sm">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-400">Execution guide</p>
            <p className="mt-2 text-base font-medium text-white">{isActionNeeded ? '정규장 종가 체결 가이드 확인' : '추가 주문 없음'}</p>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {isActionNeeded ? '주문 직전 Vol20 / SPY200 / Dist200 상태를 한 번 더 확인하세요.' : '리스크 게이지만 모니터링하고 다음 장 마감 업데이트를 기다립니다.'}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

const KpiRow = ({ data }: { data?: DashboardSnapshot['kpi_cards'] }) => {
  const cards = [
    {
      label: '세후 CAGR',
      value: formatPct(data?.cagr_pct),
      tone: 'border-l-4 border-l-emerald-400/90 bg-emerald-500/[0.05]',
      valueTone: (data?.cagr_pct ?? 0) > 0 ? 'text-white' : 'text-rose-200',
    },
    {
      label: 'MDD',
      value: formatPct(data?.mdd_pct),
      tone: 'border-l-4 border-l-rose-400/90 bg-rose-500/[0.05]',
      valueTone: 'text-rose-100',
    },
    {
      label: '1M 수익률',
      value: formatPct(data?.month_1_return_pct),
      tone: 'border-l-4 border-l-violet-400/90 bg-violet-500/[0.05]',
      valueTone: (data?.month_1_return_pct ?? 0) > 0 ? 'text-white' : 'text-rose-200',
    },
    {
      label: '조건 충족률',
      value: data?.condition_pass_rate || 'N/A',
      tone: 'border-l-4 border-l-sky-400/90 bg-sky-500/[0.05]',
      valueTone: 'text-white',
    },
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => (
        <div key={card.label} className={`rounded-[22px] border border-white/8 px-5 py-5 shadow-[0_12px_32px_rgba(15,23,42,0.22)] ${card.tone}`}>
          <p className="text-[12px] font-semibold uppercase tracking-[0.2em] text-slate-400">{card.label}</p>
          <p className={`mt-3 text-[32px] font-semibold tracking-[-0.05em] ${card.valueTone}`}>{card.value}</p>
        </div>
      ))}
    </section>
  );
};

const RiskGaugeRow = ({ data }: { data?: DashboardSnapshot['risk_gauges'] }) => {
  const gauges: Array<{
    label: string;
    key: 'vol20' | 'spy200_dist' | 'tqqq_dist200';
    helper: string;
    unit?: string;
    higherIsBetter: boolean;
  }> = [
    { label: 'Vol20', key: 'vol20', helper: '낮을수록 안전', unit: '%', higherIsBetter: false },
    { label: 'SPY200', key: 'spy200_dist', helper: '97.75 초과 유지', unit: '', higherIsBetter: true },
    { label: 'Dist200', key: 'tqqq_dist200', helper: '101.0 이상 추세', unit: '', higherIsBetter: true },
  ];

  return (
    <section className="grid gap-4 xl:grid-cols-3">
      {gauges.map((gauge) => {
        const item = data?.[gauge.key];
        if (!item) {
          return (
            <div key={gauge.key} className="rounded-[22px] border border-white/8 bg-white/[0.04] p-5 text-slate-400">
              <p className="text-sm font-medium text-slate-300">{gauge.label}</p>
              <p className="mt-3 text-sm">N/A</p>
            </div>
          );
        }

        const meta = getStatusMeta(item.status);
        const fill = calcGaugeFill(item, gauge.higherIsBetter);
        const formattedValue = `${item.value.toFixed(2)}${gauge.unit ?? ''}`;
        const formattedThreshold = `${item.threshold.toFixed(2)}${gauge.unit ?? ''}`;
        const thresholdOp = gauge.higherIsBetter ? '>' : '<';

        return (
          <div key={gauge.key} className={`rounded-[22px] border bg-white/[0.04] p-5 shadow-[0_12px_32px_rgba(15,23,42,0.18)] ${meta.border} ${meta.glow}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">{gauge.label}</p>
                <p className="mt-1 text-xs tracking-[0.16em] text-slate-400 uppercase">{gauge.helper}</p>
              </div>
              <span className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] ${meta.badge}`}>
                <span className={`h-2.5 w-2.5 rounded-full ${meta.dot}`} />
                {meta.label}
              </span>
            </div>

            <div className="mt-5 space-y-3">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className={`text-3xl font-semibold tracking-[-0.04em] ${meta.text}`}>{formattedValue}</p>
                  <p className="mt-1 text-sm text-slate-400">{thresholdOp} {formattedThreshold}</p>
                </div>
                <p className="text-sm font-medium text-slate-300">{fill.toFixed(0)}%</p>
              </div>

              <div className={`h-3 overflow-hidden rounded-full ${meta.track}`}>
                <div className={`h-full rounded-full bg-gradient-to-r ${meta.fill}`} style={{ width: `${fill}%` }} />
              </div>
            </div>
          </div>
        );
      })}
    </section>
  );
};

const EventTimeline = ({ data }: { data?: DashboardSnapshot['event_timeline'] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 text-center text-sm text-slate-400">
        최근 30일 내 주요 이벤트가 없습니다.
      </div>
    );
  }

  return (
    <section className="rounded-[24px] border border-white/8 bg-white/[0.04] p-6 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-400">Decision timeline</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-white">최근 이벤트 흐름</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">{data.length} items</span>
      </div>

      <div className="space-y-5">
        {data.map((event, index) => (
          <div key={`${event.date}-${event.type}-${index}`} className="flex gap-4">
            <div className="flex flex-col items-center">
              <div className="mt-1 h-3 w-3 rounded-full border border-sky-300/40 bg-sky-300/80 shadow-[0_0_20px_rgba(125,211,252,0.35)]" />
              {index !== data.length - 1 && <div className="mt-2 h-full min-h-10 w-px bg-gradient-to-b from-sky-300/40 to-transparent" />}
            </div>
            <div className="flex-1 rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.18em] ${classifyEvent(event.type)}`}>{event.type}</span>
                <span className="text-xs text-slate-500">{event.date}</span>
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-300">{event.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const OpsLogAccordion = ({ data }: { data?: DashboardSnapshot['ops_log'] }) => {
  const [open, setOpen] = useState(false);

  if (!data) return null;

  return (
    <div className="overflow-hidden rounded-[24px] border border-white/8 bg-white/[0.04] text-sm shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <div className="grid gap-3 border-b border-white/8 bg-slate-950/35 px-4 py-4 text-xs text-slate-300">
        <div className="flex items-center justify-between gap-3"><span className="text-slate-500">last_success</span><span className="font-mono">{data.last_success_at}</span></div>
        {data.next_run_at && <div className="flex items-center justify-between gap-3"><span className="text-slate-500">next_run</span><span className="font-mono">{data.next_run_at}</span></div>}
      </div>
      <button onClick={() => setOpen(!open)} className="flex min-h-11 w-full items-center justify-between px-4 py-4 text-left transition hover:bg-white/[0.03]">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">System status</p>
          <p className="mt-1 text-sm font-medium text-white">운영 로그 추적</p>
        </div>
        <span className="text-slate-400">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <div className="grid gap-3 bg-slate-950/40 px-4 py-4 text-xs text-slate-300">
          <div className="flex items-center justify-between gap-4"><span className="text-slate-500">run_id</span><span className="font-mono">{data.run_id}</span></div>
          <div className="flex items-center justify-between gap-4"><span className="text-slate-500">alert_key</span><span className="font-mono">{data.alert_key}</span></div>
        </div>
      )}
    </div>
  );
};

export default function Dashboard({ snapshot, embedded = false }: { snapshot?: DashboardSnapshot; embedded?: boolean }) {
  const mockState = useMemo(() => getMockState(), []);
  const usingMock = !snapshot;
  const effSnapshot = snapshot ?? MOCK_SNAPSHOTS[mockState];

  return (
    <div className={`${embedded ? "" : "min-h-screen bg-[#08101b] px-4 py-6 md:px-8 md:py-8"} text-slate-100`}>
      <div className={`${embedded ? "space-y-6" : "mx-auto max-w-6xl space-y-6"}`}>
        {!embedded && <header className="flex flex-col gap-3 border-b border-white/8 pb-6 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.32em] text-slate-500">Institutional platform</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-[-0.06em] text-white md:text-5xl">
              Alpha <span className="text-sky-300">200TQ</span>
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">실행 우선순위가 가장 높은 액션과 리스크 상태를 한 화면에서 확인하는 운영형 대시보드.</p>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300">
            {usingMock ? '`?mock=action-needed` / `?mock=no-action`' : 'live snapshot'}
          </div>
        </header>}

        <ActionHero data={effSnapshot.action_hero} showingMock={usingMock} />
        <KpiRow data={effSnapshot.kpi_cards} />
        <RiskGaugeRow data={effSnapshot.risk_gauges} />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
          <EventTimeline data={effSnapshot.event_timeline} />
          <OpsLogAccordion data={effSnapshot.ops_log} />
        </div>
      </div>
    </div>
  );
}
