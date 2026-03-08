export default function OrchestratorPanel() {
  return (
    <section className="rounded-[24px] border border-white/10 bg-white/[0.04] p-5 shadow-[0_12px_32px_rgba(15,23,42,0.18)]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">Orchestrator AI</p>
          <h3 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-white">총괄 AI 대화 준비</h3>
        </div>
        <span className="rounded-full border border-amber-300/20 bg-amber-500/10 px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-amber-100">
          Step 2 Ready
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-300">
        총괄 AI 실시간 대화는 다음 단계에서 연결됩니다. 현재는 Home inbox, manager summary cache, manual truth가 모두 연결된 준비 상태입니다.
      </p>
      <div className="mt-5 rounded-2xl border border-white/8 bg-slate-950/40 p-4 text-sm text-slate-400">
        예시 질문: 오늘 가장 중요한 액션은? / 현금 여력이 충분한가? / TQQQ와 개별주 중 어디가 우선인가?
      </div>
    </section>
  );
}
