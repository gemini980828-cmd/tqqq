import type { StockResearchCompareSeed, StockResearchEvidence, StockResearchWorkspaceItem } from '../../types/appSnapshot'
import { getStockResearchDetailSummary, getStockResearchItemBadge, getStockResearchItemScore, getStockResearchRiskLabel } from '../../lib/stockResearchDashboard'
import { StockResearchEvidencePanel } from './StockResearchEvidencePanel'
import { StockResearchComparePanel } from './StockResearchComparePanel'

interface Props {
  item: StockResearchWorkspaceItem | null
  compareSeed: StockResearchCompareSeed | null
  evidence?: StockResearchEvidence
}

export function StockResearchDetail({ item, compareSeed, evidence }: Props) {
  if (!item) {
    return (
      <div className="flex-1 overflow-y-auto p-6 lg:p-10 bg-[#08101b] relative flex items-center justify-center text-slate-500">
        실데이터가 연결되면 여기에서 종목 상세를 확인할 수 있습니다.
      </div>
    )
  }

  const score = getStockResearchItemScore(item)
  const scoreTone = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-sky-300' : 'text-rose-400'
  const scoreArrowPath =
    score >= 80
      ? 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6'
      : score >= 60
        ? 'M5 12h14'
        : 'M13 17h8m0 0v-8m0 8l-8-8-4 4-6-6'

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar p-6 lg:p-10 bg-[#08101b] relative">
      <div className="max-w-4xl mx-auto space-y-8 pb-20">
        
        {/* Detail Header */}
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-3xl font-bold tracking-tight text-white">{item.company_name} ({item.symbol})</h2>
              <span className={`px-2.5 py-1 rounded font-semibold text-xs uppercase tracking-wider border ${
                item.is_held
                  ? 'bg-slate-700 text-slate-300 border-slate-600'
                  : item.status === '후보'
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : 'bg-sky-500/10 text-sky-300 border-sky-500/20'
              }`}>{getStockResearchItemBadge(item)}</span>
            </div>
            <p className="text-sm text-slate-400 flex items-center gap-3">
              <span>{item.is_held ? 'Portfolio Holding' : 'Watchlist'}</span>
              <span className="w-1 h-1 rounded-full bg-slate-600"></span>
              <span className="flex items-center gap-1">
                <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                최신 업데이트: {new Date(item.generated_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </p>
          </div>
          <div className="flex flex-col items-end">
            <div className={`text-4xl font-bold mb-1 flex items-center gap-2 ${scoreTone}`}>
              {score}
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={scoreArrowPath} />
              </svg>
            </div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold bg-[#0f172a] px-2 py-1 rounded">Quality Score</div>
          </div>
        </div>

        {/* Judgment Sentence */}
        <div className="glass-panel p-5 rounded-xl border-l-4 border-l-sky-500 bg-sky-900/10 cursor-default" style={{ background: 'rgba(12, 74, 110, 0.1)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255, 255, 255, 0.05)', borderLeftColor: '#0ea5e9' }}>
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-sm font-semibold text-white flex items-center gap-2">
              <svg className="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              현재의 평가 결론
            </h4>
            <span className="text-[11px] font-medium text-sky-200/50 bg-sky-500/10 px-2 py-0.5 rounded">판단 기준: workspace contract 기반 요약</span>
          </div>
          <p className="text-slate-200 leading-relaxed text-[15px]">{getStockResearchDetailSummary(item)}</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quality, Fit & Details (Left 2 columns) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Signals / Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-lg text-center" style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5 font-bold">기술적 시그널</div>
                <div className="text-sm font-bold text-emerald-400">강세 (Buy)</div>
              </div>
              <div className="p-3.5 rounded-lg text-center" style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5 font-bold">주요 리스크</div>
                <div className="text-sm font-bold text-amber-500">{getStockResearchRiskLabel(item)}</div>
              </div>
              <div className="p-3.5 rounded-lg text-center" style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5 font-bold">중복도 (Overlap)</div>
                <div className={`text-sm font-bold ${item.overlap_level === 'high' ? 'text-rose-400' : 'text-sky-400'}`}>
                  {item.overlap_level === 'high' ? '0.75 (주의)' : '0.25 (낮음)'}
                </div>
              </div>
              <div className="p-3.5 rounded-lg text-center border border-dashed border-slate-600 bg-slate-800/30">
                <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1.5 font-bold">최대 손실폭</div>
                <div className="text-sm font-bold text-slate-300">-12.5%</div>
              </div>
            </div>

            {/* Portfolio Fit Analysis */}
            <div className="rounded-xl overflow-hidden shadow-lg border-slate-700" style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
              <div className="bg-[#0f172a]/80 px-4 py-3 border-b border-[#1e293b]">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                  </svg>
                  포트폴리오 적합도 (Fit Analysis)
                </h3>
              </div>
              <div className="p-5 space-y-5">
                <div className="flex items-start gap-3 pb-4 border-b border-white/5">
                  <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0 mt-0.5 border border-emerald-500/30">
                    <svg className="w-3 h-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                    </svg>
                  </div>
                  <div>
                    <div className="text-[13px] font-bold text-emerald-100">거시적(Macro) 체질 보완 효과 발생</div>
                    <div className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {item.priority_reason || '실데이터 기반 요약이 연결되면 포트폴리오 적합도 설명이 여기 표시됩니다.'}
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0 mt-0.5 border border-amber-500/30">
                    <span className="text-amber-500 font-bold text-[10px]">!</span>
                  </div>
                  <div>
                    <div className="text-[13px] font-bold text-amber-100">이중 꼬리 위험 노출 주의</div>
                    <div className="text-xs text-slate-400 mt-1 leading-relaxed">{item.memo || '세부 리스크 메모가 아직 연결되지 않았습니다.'}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Supplementary Chart & Institutional Flow */}
            <StockResearchEvidencePanel item={item} evidence={evidence} />

            {/* Compare Slots */}
            <StockResearchComparePanel item={item} compareSeed={compareSeed} />

            {/* Key News */}
            <div className="pt-2">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">주요 근거 이벤트 (Key News)</h3>
              <div className="space-y-2">
                <div className="bg-[#0f172a]/50 p-3 rounded-lg border border-[#1e293b]">
                  <div className="text-[10px] text-emerald-400 mb-0.5">실적 어닝 비트 &middot; 2일 전</div>
                  <div className="text-[13px] text-white font-medium">부문별 매출 성장세 호조, 예상치 대폭 상회</div>
                  <div className="text-[11px] text-slate-400 mt-1">시장 우려가 해소되며 멀티플 팽창을 지지하는 가장 핵심적인 근거로 작용.</div>
                </div>
                <div className="bg-[#0f172a]/50 p-3 rounded-lg border border-[#1e293b]">
                  <div className="text-[10px] text-sky-400 mb-0.5">전략적 파트너십 &middot; 4일 전</div>
                  <div className="text-[13px] text-white font-medium">주요 클라우드 벤더와의 인프라 통합 서비스 제공 발표</div>
                  <div className="text-[11px] text-slate-400 mt-1">영업 레버리지 효과 극대화 가능성 증대, 상방 포텐셜 확대.</div>
                </div>
              </div>
            </div>

          </div>

          {/* Action & Memo (Right Column) */}
          <div className="space-y-6">
            
            {/* Next Action Console */}
            <div className="p-5 rounded-xl border border-sky-500/30 shadow-[0_0_20px_rgba(56,189,248,0.1)] relative" style={{ background: 'rgba(15, 23, 42, 0.7)' }}>
              <div className="absolute -top-2 -right-2 w-4 h-4 flex items-center justify-center">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-sky-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-sky-500"></span>
              </div>
              <h3 className="text-sm font-bold text-white mb-4 uppercase tracking-wider text-sky-400">넥스트 액션 결정</h3>
              
              <div className="bg-[#0f172a] rounded-lg p-3 text-sm text-slate-300 mb-4 border border-[#334155]">
                <div className="text-xs font-semibold text-slate-500 mb-1">대기 중인 계획</div>
                {item.next_action || '조건부 액션 준비중'}
              </div>
              
              <div className="space-y-2">
                <button className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-bold transition text-sm flex justify-center items-center gap-2 shadow-lg shadow-sky-900/50">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  {item.is_held ? '비중 조정(승인)' : item.status === '후보' ? '편입 확정 (승인 완료)' : '후보 승격 검토'}
                </button>
                <div className="grid grid-cols-2 gap-2">
                  <button className="py-2 bg-[#1e293b] hover:bg-[#334155] border border-[#334155] text-slate-300 rounded-lg font-medium transition text-[11px]">
                    보류 (Watch)
                  </button>
                  <button className="py-2 bg-rose-950/30 hover:bg-rose-900/50 border border-rose-500/20 text-rose-300 rounded-lg font-medium transition text-[11px]">
                    제외 (Reject)
                  </button>
                </div>
              </div>
            </div>

            {/* Notebook / Memo */}
            <div className="rounded-xl flex-1 flex flex-col overflow-hidden border border-[#334155] min-h-[250px]" style={{ background: 'rgba(15, 23, 42, 0.7)' }}>
              <div className="bg-[#0f172a]/80 px-4 py-3 border-b border-[#1e293b]">
                <h3 className="text-xs font-bold text-white tracking-wide">리서치 노트 (Memo)</h3>
              </div>
              <div className="p-4 flex-1 flex flex-col">
                <textarea 
                  className="w-full flex-1 bg-[#08101b]/50 border border-[#334155] rounded-lg p-3 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition resize-none custom-scrollbar" 
                  placeholder="종목에 대한 개인적인 메모나 투자 아이디어를 작성하세요..."
                  value={item.memo}
                  readOnly
                ></textarea>
                <div className="mt-3 flex justify-between items-center">
                  <span className="text-[10px] text-slate-500">자동 저장 활성화됨</span>
                  <button className="px-3 py-1 bg-[#1e293b] hover:bg-[#334155] text-xs font-medium text-white rounded border border-[#334155] transition">기록 저장</button>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  )
}
