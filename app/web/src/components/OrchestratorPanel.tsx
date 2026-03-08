import { useMemo, useState } from 'react'

import type { AppSnapshot } from '../types/appSnapshot'

type OrchestratorReply = {
  answer: string
  highlights: string[]
  sourceManagers: string[]
  metadata: {
    mode: string
    questionChars: number
    sourceManagerCount: number
  }
}

function formatKrw(value?: number) {
  if (value === undefined || Number.isNaN(value)) return 'N/A'
  return `${new Intl.NumberFormat('ko-KR', { maximumFractionDigits: 0 }).format(value)}원`
}

function buildLocalReply(snapshot: AppSnapshot | undefined, question: string): OrchestratorReply {
  const prompt = question.trim()
  const action = snapshot?.action_hero?.action ?? '유지'
  const targetWeight = snapshot?.action_hero?.target_weight_pct
  const reason = snapshot?.action_hero?.reason_summary ?? ''
  const inbox = snapshot?.home_inbox ?? []
  const liquidity = snapshot?.liquidity_summary
  const risk = snapshot?.risk_gauges
  const summaries = snapshot?.manager_summaries

  const parts: string[] = []
  const highlights: string[] = []
  const sourceManagers = new Set<string>()

  const wantsAction = ['액션', '해야', '우선', '중요'].some((token) => prompt.includes(token))
  const wantsCash = ['현금', '유동성', '여력'].some((token) => prompt.includes(token))
  const wantsRisk = ['리스크', '위험', '안전'].some((token) => prompt.includes(token))

  if (wantsAction || (!wantsCash && !wantsRisk)) {
    parts.push(`현재 가장 중요한 액션은 ${action}이며 전략 목표 비중은 ${targetWeight ?? 'N/A'}%입니다.`)
    if (reason) parts.push(`근거는 ${reason} 입니다.`)
    if (inbox[0]) {
      parts.push(`가장 앞선 inbox는 '${inbox[0].title}'이며 ${inbox[0].detail}`)
    }
    highlights.push(`Action ${action}`)
    sourceManagers.add('core_strategy')
  }

  if (wantsCash) {
    parts.push(
      `현금 여력은 현금 ${formatKrw(liquidity?.cash_krw)}, 부채 ${formatKrw(liquidity?.debt_krw)}, 유동성 비중 ${liquidity?.liquidity_ratio_pct ?? 'N/A'}% 기준으로 보시면 됩니다.`,
    )
    highlights.push(`Cash ${formatKrw(liquidity?.cash_krw)}`)
    sourceManagers.add('cash_debt')
  }

  if (wantsRisk) {
    const riskNotes = [
      risk?.vol20 ? `Vol20 ${risk.vol20.value} (${risk.vol20.status})` : null,
      risk?.spy200_dist ? `SPY200 ${risk.spy200_dist.value} (${risk.spy200_dist.status})` : null,
      risk?.tqqq_dist200 ? `Dist200 ${risk.tqqq_dist200.value} (${risk.tqqq_dist200.status})` : null,
    ].filter(Boolean)

    if (riskNotes.length) {
      parts.push(`현재 리스크 계기판은 ${riskNotes.join(', ')} 상태입니다.`)
      highlights.push(riskNotes[0]!)
      sourceManagers.add('core_strategy')
    }
  }

  if (prompt.includes('개별주') || prompt.includes('주식')) {
    const stockSummary = summaries?.stock_research?.summary_text
    if (stockSummary) {
      parts.push(`개별주 매니저 기준으로는 ${stockSummary}`)
      highlights.push(stockSummary)
    }
    sourceManagers.add('stock_research')
  }

  if (prompt.includes('부동산')) {
    const realEstateSummary = summaries?.real_estate?.summary_text
    if (realEstateSummary) {
      parts.push(`부동산 매니저 기준으로는 ${realEstateSummary}`)
      highlights.push(realEstateSummary)
    }
    sourceManagers.add('real_estate')
  }

  if (!parts.length) {
    parts.push('현재 cache-first summary 기준으로는 코어전략 점검 → 현금 여력 확인 순서가 가장 중요합니다.')
    highlights.push('Cache-first summary')
    sourceManagers.add('core_strategy')
  }

  return {
    answer: parts.join(' '),
    highlights,
    sourceManagers: Array.from(sourceManagers),
    metadata: {
      mode: 'cache_first',
      questionChars: prompt.length,
      sourceManagerCount: sourceManagers.size,
    },
  }
}

const QUICK_PROMPTS = ['오늘 가장 중요한 액션은?', '현금 여력이 충분한가?', 'TQQQ와 개별주 중 어디가 우선인가?', '지금 리스크 상태는 어때?']

export default function OrchestratorPanel({ snapshot }: { snapshot?: AppSnapshot }) {
  const [question, setQuestion] = useState('')
  const [reply, setReply] = useState<OrchestratorReply | null>(null)
  const lastUpdated = useMemo(() => snapshot?.action_hero?.updated_at ?? snapshot?.wealth_home?.updated_at ?? 'N/A', [snapshot])

  function submitQuestion(nextQuestion: string) {
    const prompt = nextQuestion.trim()
    if (!prompt) return
    setQuestion(prompt)
    setReply(buildLocalReply(snapshot, prompt))
  }

  return (
    <section className="rounded-[24px] border border-white/10 bg-white/[0.04] p-5 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Orchestrator AI</p>
          <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-white">총괄 AI 대화</h3>
        </div>
        <span className="rounded-full border border-amber-300/20 bg-amber-500/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-amber-100">
          Explicit only
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">
        페이지 로드시 자동 호출은 하지 않고, 현재 snapshot / manager summary cache 기준으로 질문을 보낼 때만 즉시 답변합니다.
      </p>
      <div className="mt-5 rounded-2xl border border-white/8 bg-slate-950/40 p-4 text-sm text-slate-400">
        <p>기준 데이터: Home inbox + cached manager summaries + wealth snapshot</p>
        <p className="mt-2">마지막 업데이트: {lastUpdated}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {QUICK_PROMPTS.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => submitQuestion(item)}
            className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-200 transition hover:border-sky-300/30 hover:bg-sky-400/10"
          >
            {item}
          </button>
        ))}
      </div>

      <div className="mt-4 space-y-3">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
          placeholder="예: 지금 가장 중요한 액션과 현금 여력을 같이 알려줘"
          className="w-full rounded-2xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm text-white outline-none ring-0 placeholder:text-slate-500"
        />
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-slate-500">Live AI 호출 없음 · explicit submit only · cache-first</p>
          <button
            type="button"
            onClick={() => submitQuestion(question)}
            disabled={!question.trim()}
            className="rounded-full border border-sky-300/25 bg-sky-400/10 px-4 py-2 text-sm font-medium text-sky-100 transition enabled:hover:bg-sky-400/20 disabled:cursor-not-allowed disabled:opacity-40"
          >
            질문 실행
          </button>
        </div>
      </div>

      {reply ? (
        <div className="mt-5 rounded-2xl border border-white/8 bg-slate-950/40 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Orchestrator reply</p>
          <p className="mt-3 text-sm leading-7 text-slate-200">{reply.answer}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {reply.highlights.map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-slate-300">
                {item}
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">Sources: {reply.sourceManagers.join(', ') || 'core_strategy'}</p>
          <p className="mt-1 text-xs text-slate-500">
            Mode: {reply.metadata.mode} · chars: {reply.metadata.questionChars} · source managers: {reply.metadata.sourceManagerCount}
          </p>
        </div>
      ) : null}
    </section>
  )
}
