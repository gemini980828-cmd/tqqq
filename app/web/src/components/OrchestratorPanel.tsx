import { useMemo, useState } from 'react'

import type { AppSnapshot } from '../types/appSnapshot'
import { buildPreviewReply } from '../lib/orchestratorPreview.js'

type OrchestratorReply = {
  answer: string
  highlights: string[]
  sourceManagers: string[]
  primaryIntent: string
  briefKeysUsed: string[]
  metadata: {
    mode: string
    question_chars: number
    source_manager_count: number
    primary_intent: string
  }
}

const FALLBACK_QUICK_PROMPTS = ['오늘 가장 중요한 액션은?', '지금 우선순위를 요약해줘', '현금 여력이 충분한가?', '지금 리스크 상태는 어때?']

export default function OrchestratorPanel({ snapshot }: { snapshot?: AppSnapshot }) {
  const [question, setQuestion] = useState('')
  const [reply, setReply] = useState<OrchestratorReply | null>(null)
  const lastUpdated = useMemo(() => snapshot?.action_hero?.updated_at ?? snapshot?.wealth_home?.updated_at ?? 'N/A', [snapshot])
  const quickPrompts = useMemo(() => snapshot?.orchestrator_policy?.quick_prompts ?? FALLBACK_QUICK_PROMPTS, [snapshot])

  function submitQuestion(nextQuestion: string) {
    const prompt = nextQuestion.trim()
    if (!prompt) return
    setQuestion(prompt)
    setReply(buildPreviewReply(snapshot, prompt) as OrchestratorReply | null)
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
        <p>기준 데이터: exported orchestrator briefs + cached manager summaries + wealth snapshot</p>
        <p className="mt-2">마지막 업데이트: {lastUpdated}</p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {quickPrompts.map((item) => (
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
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-200">{reply.answer}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {reply.highlights.map((item) => (
              <span key={item} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-slate-300">
                {item}
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">Sources: {reply.sourceManagers.join(', ') || 'core_strategy'}</p>
          <p className="mt-1 text-xs text-slate-500">
            Mode: {reply.metadata.mode} · intent: {reply.primaryIntent} · chars: {reply.metadata.question_chars} · source managers:{' '}
            {reply.metadata.source_manager_count}
          </p>
        </div>
      ) : null}
    </section>
  )
}
