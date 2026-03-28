import { useEffect, useMemo, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import type { AppSnapshot, OrchestratorPromptStarter } from '../types/appSnapshot'
import { createHistoryEntry, loadHistory, ORCHESTRATOR_HISTORY_STORAGE_KEY, saveHistory, type OrchestratorHistoryEntry } from '../lib/orchestratorSession'
import { buildPreviewReply } from '../lib/orchestratorPreview'
import { normalizeOrchestratorReply, type StructuredOrchestratorReply } from '../lib/orchestratorReplyAdapter'
import { resolveScreenRoute } from '../lib/navigation'

type HistoryEntryWithNormalized = OrchestratorHistoryEntry & { normalized?: StructuredOrchestratorReply }

export default function OrchestratorPanel({ snapshot }: { snapshot?: AppSnapshot }) {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [history, setHistory] = useState<OrchestratorHistoryEntry[]>(() => {
    if (typeof window === 'undefined') return []
    try {
      return loadHistory(window.localStorage, ORCHESTRATOR_HISTORY_STORAGE_KEY)
    } catch {
      return []
    }
  })
  
  const scrollRef = useRef<HTMLDivElement>(null)

  const promptStarters: OrchestratorPromptStarter[] = useMemo(() => {
    return snapshot?.orchestrator_prompt_starters ?? [
      { id: '1', label: 'Compare AAPL with MSFT', prompt: 'Compare AAPL with MSFT', source_manager_ids: [], intent: 'research' },
      { id: '2', label: "What's the macro outlook?", prompt: "What is the macro outlook today?", source_manager_ids: [], intent: 'macro' }
    ]
  }, [snapshot])

  useEffect(() => {
    if (typeof window === 'undefined') return
    saveHistory(history, window.localStorage, ORCHESTRATOR_HISTORY_STORAGE_KEY)
  }, [history])

  // scroll to bottom on new message
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [history, isTyping])

  function submitQuestion(nextQuestion: string) {
    const prompt = nextQuestion.trim()
    if (!prompt) return
    setQuestion('')
    
    // Optimistically add user message
    const tempEntry = createHistoryEntry(prompt, { answer: '...', sourceManagers: [], primaryIntent: '', briefKeysUsed: [], metadata: { mode: '', question_chars: 0, source_manager_count: 0, primary_intent: '' } }, new Date().toISOString())
    if (tempEntry) {
      setHistory((current) => [...current, tempEntry].slice(-5))
    }
    setIsTyping(true)

    // Simulate network delay for effect
    setTimeout(() => {
      const rawReply = buildPreviewReply(snapshot, prompt)
      const nextReply = normalizeOrchestratorReply(rawReply)
      
      setHistory((current) => {
        // Find and replace the optimistic entry
        const idx = current.findIndex(e => e.question === prompt && e.answer === '...')
        if (idx >= 0) {
          const newHistory = [...current] as HistoryEntryWithNormalized[]
          const replaced = createHistoryEntry(prompt, { answer: nextReply.answer || '', sourceManagers: nextReply.supporting_managers || [], primaryIntent: '', briefKeysUsed: [], metadata: { mode: '', question_chars: 0, source_manager_count: 0, primary_intent: '' } }, new Date().toISOString())
          if (replaced) {
            newHistory[idx] = { ...replaced, normalized: nextReply }
          }
          return newHistory
        }
        const finalEntry = createHistoryEntry(prompt, { answer: nextReply.answer || '', sourceManagers: nextReply.supporting_managers || [], primaryIntent: '', briefKeysUsed: [], metadata: { mode: '', question_chars: 0, source_manager_count: 0, primary_intent: '' } }, new Date().toISOString())
        if (!finalEntry) return current
        return [...current, { ...finalEntry, normalized: nextReply }].slice(-5)
      })
      setIsTyping(false)
    }, 600)
  }

  function renderBotReply(reply: HistoryEntryWithNormalized) {
    const sr: StructuredOrchestratorReply = reply.normalized || normalizeOrchestratorReply(reply)
    
    return (
      <div className="max-w-[95%]">
        {/* Orchestrator Badge */}
        <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded bg-brand-primary flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <span className="text-xs font-semibold text-brand-accent uppercase">Analysis Completed</span>
        </div>
        
        <div className="glass-panel rounded-xl overflow-hidden border border-brand-primary/20">
            {/* Short Answer (요약) */}
            {sr.short_answer && (
              <div className="p-4 bg-brand-primary/5 border-b border-dark-700">
                  <p className="text-sm font-semibold text-white">
                      {sr.short_answer}
                  </p>
              </div>
            )}
            
            {/* Details (근거) */}
            {(sr.answer || sr.source_details) && (
              <div className="p-4 text-sm text-gray-300">
                  {sr.answer}
              </div>
            )}

            {/* Source Details (투명성) */}
            {(sr.source_details.length > 0 || sr.supporting_managers.length > 0) && (
              <div className="px-4 py-3 bg-dark-800/80 border-t border-dark-700 flex items-center justify-between">
                  <div className="flex items-center flex-wrap gap-2">
                      <span className="text-xs text-gray-500 uppercase font-semibold">Sources:</span>
                      {(sr.source_details.length > 0
                        ? sr.source_details
                        : sr.supporting_managers.map((manager_id) => ({ manager_id, stale: false }))).map(sm => (
                        <span key={sm.manager_id} className="text-xs px-1.5 py-0.5 rounded bg-dark-700 text-gray-300 border border-dark-600">
                          {sm.manager_id}{sm.stale ? ' (Stale)' : ''}
                        </span>
                      ))}
                  </div>
              </div>
            )}

            {/* Next Action (다음 행동) */}
            {sr.next_action && (
              <div className="p-4 border-t border-brand-primary/20 bg-dark-900 flex justify-between items-center">
                  <div>
                      <h5 className="text-xs font-semibold text-brand-accent uppercase mb-1">Recommended Action</h5>
                      <p className="text-sm text-white font-medium">{sr.next_action}</p>
                  </div>
                  <button
                    onClick={() => navigate(resolveScreenRoute(sr.go_to_screen))}
                    className="px-3 py-1.5 bg-brand-primary hover:bg-brand-accent text-white rounded text-xs font-medium transition shadow-lg shadow-blue-500/10"
                  >
                      View
                  </button>
              </div>
            )}
        </div>
      </div>
    )
  }

  return (
    <aside className="h-full bg-dark-800 flex flex-col z-20">
        <div className="p-4 border-b border-dark-700 flex justify-between items-center bg-dark-900/50">
            <div className="flex items-center gap-2">
                <span className="animate-pulse w-2 h-2 bg-brand-accent rounded-full"></span>
                <h2 className="font-semibold text-white">Orchestrator</h2>
            </div>
            <button 
              onClick={() => {
                setHistory([])
                if (typeof window !== 'undefined') window.localStorage.removeItem(ORCHESTRATOR_HISTORY_STORAGE_KEY)
              }}
              className="text-gray-400 hover:text-white" title="Clear History">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8h16M4 16h16"></path></svg>
            </button>
        </div>
        
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6 flex flex-col custom-scrollbar">
            {history.length === 0 ? (
              <div className="flex-1 flex items-center justify-center text-center px-4">
                <p className="text-sm text-gray-500 leading-relaxed">
                  How can I assist you with your portfolio today?<br/>Select a prompt below or type your question.
                </p>
              </div>
            ) : (
              history.map((entry, idx) => (
                <div key={idx} className="flex flex-col space-y-4">
                  {/* User Msg */}
                  <div className="self-end max-w-[85%] bg-dark-700 rounded-2xl rounded-tr-sm px-4 py-3 text-sm text-white">
                      {entry.question}
                  </div>

                  {/* Orchestrator AI Response Structured */}
                  {entry.answer === '...' ? (
                    <div className="text-sm text-gray-500 animate-pulse ml-2">Orchestrator is analyzing...</div>
                  ) : renderBotReply(entry)}
                </div>
              ))
            )}
        </div>

        {/* Input & Prompts */}
        <div className="p-4 bg-dark-900 border-t border-dark-700">
            {/* Prompt Starters */}
            <div className="flex gap-2 mb-3 overflow-x-auto pb-1 custom-scrollbar">
                {promptStarters.map(starter => (
                  <button 
                    key={starter.id}
                    onClick={() => submitQuestion(starter.prompt)}
                    className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full bg-dark-700 border border-dark-600 text-gray-300 hover:text-white hover:border-gray-500 transition whitespace-nowrap"
                  >
                      {starter.label}
                  </button>
                ))}
            </div>
            {/* Input Box */}
            <form 
              onSubmit={(e) => { e.preventDefault(); submitQuestion(question); }}
              className="relative flex items-center"
            >
                <input 
                  type="text" 
                  value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder="Ask Orchestrator for insights..." 
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg py-3 px-4 pr-12 text-sm text-white focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary transition" 
                />
                <button 
                  type="submit"
                  disabled={!question.trim()}
                  className="absolute right-2 p-1.5 bg-brand-primary rounded-md text-white hover:bg-brand-accent transition disabled:opacity-50 disabled:hover:bg-brand-primary"
                >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                </button>
            </form>
        </div>
    </aside>
  )
}
