import type { StockResearchWorkspace } from '../types/appSnapshot';

export const MOCK_STOCK_RESEARCH_WORKSPACE: StockResearchWorkspace = {
  generated_at: new Date().toISOString(),
  filters: {
    total_count: 42,
    held_count: 12,
    candidate_count: 5,
    observe_count: 8,
    status_counts: {
      전체: 42,
      탐색: 20,
      관찰: 8,
      후보: 5,
      보류: 7,
      제외: 2,
    },
  },
  queue: [
    {
      id: "q_1",
      symbol: "NVDA",
      title: "NVDA 점수 하락 경고",
      reason: "최근 1주일간 모멘텀 지표 이탈, 비중 축소 요망",
      severity: "high",
      status: "매각 리뷰",
      is_held: true,
      next_action: "2시간 전"
    },
    {
      id: "q_2",
      symbol: "PLTR",
      title: "PLTR 편입 검토",
      reason: "S-Curve 초기 진입 시그널 감지. 상세 분석 중",
      severity: "medium",
      status: "투자의견 상향",
      is_held: false,
      next_action: "방금 전"
    },
    {
      id: "q_3",
      symbol: "AAPL",
      title: "AAPL 배당 삭감 리스크",
      reason: "현금 흐름 악화 우려 (다음 주 추적 예정)",
      severity: "low",
      status: "루틴 점검",
      is_held: true,
      next_action: "어제"
    }
  ],
  items: [
    {
      idea_id: "idx_pltr",
      symbol: "PLTR",
      company_name: "Palantir Technologies",
      status: "신규후보",
      memo: "지난 달 분석 시 밸류에이션 부담으로 보류했으나, 최신 FCF 마진 상승으로 인해 프리미엄 정당성이 입증됨. 포트폴리오 편입 준비 완료.",
      is_held: false,
      overlap_level: "low",
      priority: "high",
      priority_reason: "신규후보 집중",
      next_action: "편입 논리 점검 완료 대기",
      generated_at: new Date().toISOString()
    },
    {
      idea_id: "idx_nvda",
      symbol: "NVDA",
      company_name: "NVIDIA Corporation",
      status: "보유중 (15%)",
      memo: "AI 가속기 독점 지위 유지, 그러나 단기 과매수 시그널 발생.",
      is_held: true,
      overlap_level: "high",
      priority: "medium",
      priority_reason: "축소 검토",
      next_action: "비율 -5% 조정안 실행 여부",
      generated_at: new Date().toISOString()
    }
  ],
  compare_seed: {
    primary_symbol: "PLTR",
    candidate_symbols: ["NVDA", "AAPL", "MSFT"]
  }
};
