import type { AppSnapshot } from '../types/appSnapshot'
import ReportsSummaryBar from '../components/reports/ReportsSummaryBar'
import ReportsNarrativeSection from '../components/reports/ReportsNarrativeSection'
import ReportsComparisonSection from '../components/reports/ReportsComparisonSection'
import ReportsContextSection from '../components/reports/ReportsContextSection'

const MOCK_REPORTS_DATA = {
  kpi_cards: {
    cagr_pct: 41.2,
    mdd_pct: -14.5,
    month_1_return_pct: 5.4,
    condition_pass_rate: "92%",
  },
  report_highlights: [
    {
      id: "rh_1",
      severity: "info",
      title: "기술 섹터 순환 조짐 감지",
      summary: "최근 모멘텀 지표는 하드웨어 중심 기술주에서 소프트웨어·서비스 영역으로의 완만한 순환 가능성을 시사합니다. 코어 전략은 유지 가능하지만, 단기 변동성 확대 신호를 함께 점검해야 합니다.",
      manager_ids: ["core_strategy"],
      updated_at: new Date().toISOString()
    },
    {
      id: "rh_2",
      severity: "warning",
      title: "현금 버퍼가 최소 구간에 접근 중",
      summary: "최근 분할매수 집행과 예정된 부채 상환으로 인해 가용 현금 버퍼가 최소 기준선에 가까워지고 있습니다. 비핵심 정기 매수는 잠시 속도를 조절할 필요가 있습니다.",
      manager_ids: ["cash_debt"],
    }
  ],
  compare_data: {
    manager_pairs: [
      {
        pair_id: "core_strategy-vs-cash_debt",
        manager_ids: ["core_strategy", "cash_debt"],
        headlines: {
          core_strategy: "하락 구간 분할 매수 기조 유지",
          cash_debt: "현금 버퍼 최소 기준 접근"
        }
      }
    ],
    conflicting_recommendations: [
      {
        conflict_id: "cr_1",
        manager_ids: ["cash_debt", "core_strategy"],
        detail: "코어 전략은 적극적 저가 매수를 시사하지만, 현금/부채 관점에서는 방어 여력을 먼저 점검해야 합니다."
      }
    ],
    holding_overlap: [
      {
        overlap_id: "ho_1",
        left_manager_id: "stock_research",
        right_manager_id: "core_strategy",
        shared_symbols: ["NVDA", "MSFT"]
      }
    ]
  },
  priority_actions: [
    {
      id: "pa_1",
      severity: "high",
      manager_id: "core_strategy",
      title: "코어 전략 리밸런싱 점검 필요",
      detail: "목표 비중과 실제 비중의 괴리가 커져 장마감 전 재확인이 필요합니다.",
      recommended_action: "코어 전략 보기",
      goto_screen: "managers/core_strategy"
    }
  ],
  event_timeline: [
    {
      date: new Date().toISOString(),
      type: "상태 변경",
      detail: "거시 판단이 중립 구간으로 이동했습니다.",
      title: "거시 상태가 중립으로 전환"
    }
  ],
  meta: {
    signal_updated_at: new Date().toISOString(),
    market_updated_at: new Date().toISOString(),
    audit_available: true,
  }
} as Partial<AppSnapshot>;

export default function Reports({ snapshot }: { snapshot?: AppSnapshot }) {
  const isMissingReportsData = !snapshot?.report_highlights || snapshot.report_highlights.length === 0;
  const activeData = isMissingReportsData ? MOCK_REPORTS_DATA : snapshot;

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8 custom-scrollbar relative border-r border-slate-800 bg-slate-950">
      <div className="mx-auto max-w-4xl space-y-10 pb-12">
        <header>
          <h2 className="mb-2 text-3xl font-bold tracking-tight text-white">운영 브리핑</h2>
          <p className="text-[15px] text-slate-400">최근 변화, 매니저 간 비교 포인트, 그리고 다시 봐야 할 운영 서사를 한 화면에서 정리합니다. {isMissingReportsData && <span className="text-amber-500 text-xs ml-2 border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 rounded">목업 데이터</span>}</p>
        </header>

        <ReportsSummaryBar kpiCards={activeData.kpi_cards} />
        <ReportsNarrativeSection highlights={activeData.report_highlights} />
        <ReportsComparisonSection compareData={activeData.compare_data} />
        <ReportsContextSection 
          priorityActions={activeData.priority_actions} 
          events={activeData.event_timeline} 
          meta={activeData.meta}
        />
      </div>
    </div>
  )
}
