import { useEffect, useMemo, useState } from 'react'

import type { AppSnapshot } from '../types/appSnapshot'
import {
  appendHistoryEntry,
  buildSessionInsights,
  createHistoryEntry,
  loadHistory,
  ORCHESTRATOR_HISTORY_STORAGE_KEY,
  saveHistory,
  type OrchestratorHistoryEntry,
} from '../lib/orchestratorSession.js'
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
  const [history, setHistory] = useState<OrchestratorHistoryEntry[]>(() => {
    if (typeof window === 'undefined') return []
    try {
      return loadHistory(window.localStorage, ORCHESTRATOR_HISTORY_STORAGE_KEY)
    } catch {
      return []
    }
  })
  const lastUpdated = useMemo(() => snapshot?.action_hero?.updated_at ?? snapshot?.wealth_home?.updated_at ?? 'N/A', [snapshot])
  const quickPrompts = useMemo(() => snapshot?.orchestrator_policy?.quick_prompts ?? FALLBACK_QUICK_PROMPTS, [snapshot])
  const sessionInsights = useMemo(() => buildSessionInsights(history), [history])
  const auditInsights = snapshot?.orchestrator_insights
  const promptButtons = useMemo(() => {
    const prompts = [...(sessionInsights.recent_prompts ?? [])]
    for (const item of quickPrompts) {
      if (prompts.length >= 6) break
      if (!prompts.includes(item)) prompts.push(item)
    }
    return prompts
  }, [quickPrompts, sessionInsights.recent_prompts])

  useEffect(() => {
    if (typeof window === 'undefined') return
    saveHistory(history, window.localStorage, ORCHESTRATOR_HISTORY_STORAGE_KEY)
  }, [history])

  function submitQuestion(nextQuestion: string) {
    const prompt = nextQuestion.trim()
    if (!prompt) return
    setQuestion(prompt)
    const nextReply = buildPreviewReply(snapshot, prompt) as OrchestratorReply | null
    setReply(nextReply)
    if (nextReply) {
      setHistory((current) => appendHistoryEntry(current, createHistoryEntry(prompt, nextReply, new Date().toISOString())))
    }
  }

  function clearHistory() {
    setHistory([])
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(ORCHESTRATOR_HISTORY_STORAGE_KEY)
    }
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
        {promptButtons.map((item) => (
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

      {history.length ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Session 질문 수</p>
              <p className="mt-2 text-xl font-semibold text-white">{sessionInsights.total_questions}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">주된 intent</p>
              <p className="mt-2 text-sm font-medium text-white">{sessionInsights.top_intent ?? 'N/A'}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-slate-950/40 px-4 py-3">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">누적 audit 질문 수</p>
              <p className="mt-2 text-xl font-semibold text-white">{auditInsights?.total_questions ?? 0}</p>
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-white/8 bg-slate-950/40 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Question history</p>
                <p className="mt-1 text-sm text-slate-300">최근 질문을 다시 보거나 replay 할 수 있습니다.</p>
              </div>
              <button
                type="button"
                onClick={clearHistory}
                disabled={!history.length}
                className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-slate-300 transition enabled:hover:border-rose-300/30 enabled:hover:bg-rose-400/10 disabled:opacity-40"
              >
                history clear
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {history.slice(0, 4).map((item) => (
                <div key={`${item.asked_at}:${item.question}`} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-white">{item.question}</p>
                      <p className="mt-2 line-clamp-3 whitespace-pre-line text-sm leading-6 text-slate-300">{item.answer}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        intent: {item.primary_intent} · sources: {item.source_managers.join(', ') || 'core_strategy'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => submitQuestion(item.question)}
                      className="rounded-full border border-sky-300/20 bg-sky-400/10 px-3 py-1.5 text-[11px] text-sky-100 transition hover:bg-sky-400/20"
                    >
                      replay
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-white/8 bg-slate-950/40 p-4">
            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Operational insights</p>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">마지막 explicit 질문</p>
                <p className="mt-2 text-sm font-medium text-white">{sessionInsights.last_interaction_at ?? 'N/A'}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Session intent mix</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {sessionInsights.intent_mix.map((item) => (
                    <span key={item.intent} className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[11px] text-slate-300">
                      {item.intent} × {item.count}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              {(auditInsights?.recent_questions ?? []).slice(0, 3).map((item) => (
                <div key={`${item.timestamp}:${item.question}`} className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
                  <p className="text-sm font-medium text-white">{item.question}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    intent: {item.primary_intent} · sources: {(item.source_manager_ids ?? []).join(', ') || 'core_strategy'}
                  </p>
                </div>
              ))}
              {!auditInsights?.recent_questions?.length ? (
                <p className="text-sm text-slate-500">아직 backend audit summary가 없습니다. 현재는 session history 기준으로 상담 UX를 제공합니다.</p>
              ) : null}
            </div>
          </div>
        </>
      ) : (
        <div className="mt-5 rounded-2xl border border-dashed border-white/10 bg-slate-950/30 px-4 py-4 text-sm text-slate-400">
          아직 질문 기록이 없습니다. quick prompt나 직접 질문으로 첫 상담 기록을 만들어보세요.
        </div>
      )}
    </section>
  )
}
