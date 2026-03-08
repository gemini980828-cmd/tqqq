# Step 5 Design - Orchestrator Quality Deepening

## Goal
Deepen only the cross-domain orchestrator while keeping all sector managers as scaffold surfaces backed by cached summaries.

## Scope
- Improve orchestrator question classification quality.
- Introduce a deterministic prioritization policy for generic / mixed / conflicting questions.
- Improve response quality using backend-owned structure rather than ad-hoc frontend phrasing.
- Preserve explicit-only, cache-first, manager-scaffolds-only constraints.

## Out of Scope
- Deepening stock / real estate / cash manager workflows.
- Adding live model calls on page load.
- Turning sector managers into conversational agents.
- Replacing manual truth or summary store contracts.

## Design Principles
1. **Single routing source of truth**
   Intent classification rules should live in one place and be reused by backend and preview paths.
2. **Generic questions need first-class handling**
   Questions like "전체적으로", "요약", "포트폴리오", "지금 뭐가 우선" should not accidentally collapse to `action` only.
3. **Priority policy beats keyword dumping**
   Mixed prompts should return ordered, de-duplicated guidance with an explicit primary recommendation.
4. **Backend owns semantics**
   Frontend should consume backend-owned policy/brief outputs rather than rebuild business wording.
5. **Guardrails stay intact**
   Explicit submit only, cache-first, no live provider, no manager deepening.

## Acceptance Targets
- Generic cross-domain prompts map to an intentional default/portfolio priority path.
- Mixed prompts (e.g. risk + cash + action) return stable ordering and deduplicated manager sources.
- Frontend preview and backend reply use the same routing semantics.
- Metadata naming is consistent enough for audit/debugging.
- Existing Step 4 behavior remains green.
