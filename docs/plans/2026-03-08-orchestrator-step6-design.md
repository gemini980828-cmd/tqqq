# Step 6 Design - Orchestrator 상담 UX / History / Operational Insights

## Goal
Deepen only the user-facing orchestrator experience by making the panel feel like an actual 상담 surface: recent questions, reusable follow-ups, and lightweight operational insights.

## Scope
- Improve the Home orchestrator panel UX without changing sector manager depth.
- Add local question/reply history for replay and continuity.
- Surface lightweight operational insights from orchestrator usage.
- Keep explicit-only, cache-first, no-live-provider guardrails.

## Out of Scope
- Deep sector manager analysis workflows.
- Always-on chat backends or streaming providers.
- Authority-data mutations or writeback into manual truth.
- Multi-user auth/session systems.

## Design Principles
1. **상담 UX는 총괄 AI에만 집중**
   History, replay, follow-up UX는 orchestrator에만 붙인다.
2. **질문 기록은 가볍고 되돌릴 수 있어야 함**
   Browser-local history + optional audit summary 정도로 충분하다.
3. **운영 인사이트는 해설용**
   사용량/intent/source manager 집계는 참고 정보이며 source of truth가 아니다.
4. **정적 배포와 호환**
   Static snapshot만 있어도 작동하고, backend audit summary가 있으면 더 좋아지는 구조로 간다.

## Acceptance Targets
- 사용자가 Home에서 최근 질문/답변을 다시 볼 수 있다.
- 질문 히스토리에서 한 번에 재질문(replay)할 수 있다.
- orchestrator panel에 최소 3개의 운영 인사이트가 보인다.
- snapshot export는 audit log가 있으면 요약 인사이트를 포함하고, 없으면 비어 있어도 깨지지 않는다.
- Step 5의 explicit-only / cache-first 동작은 유지된다.
