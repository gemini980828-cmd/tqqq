# Step 5 Implementation Plan - Orchestrator Quality Deepening

## Work Objectives
Strengthen the orchestrator only in three areas: question classification, prioritization policy, and answer quality. Keep sector managers as scaffold-only surfaces.

## Guardrails
### Must Have
- One deterministic intent-routing source of truth.
- Stronger handling for generic portfolio/priority questions.
- Stable prioritization/composition for mixed prompts.
- Verification covering backend + preview + snapshot/export behavior.

### Must NOT Have
- No deep sector-manager agent UX.
- No live AI/provider dependency.
- No page-load auto invocation.
- No authority-data mutations from orchestrator features.

## Task Flow

### Task 1 — Intent policy contract first
Create failing tests for orchestrator routing and response policy.

**Acceptance criteria**
- Tests cover generic prompts, mixed prompts, and domain-specific prompts.
- Tests assert brief key order, fallback behavior, and manager source de-duplication.
- Tests encode consistent metadata naming between backend and preview paths.

### Task 2 — Shared routing/policy implementation
Move routing/prioritization logic into a shared backend-owned policy surface and make preview consume the same semantics.

**Acceptance criteria**
- Backend and preview no longer maintain divergent intent tables.
- Generic prompts can intentionally select `default_priority` / portfolio-wide guidance.
- Mixed prompts produce deterministic ordering.

### Task 3 — Response quality improvement
Refine backend-owned reply assembly so answers start with a primary recommendation and then add concise supporting briefs.

**Acceptance criteria**
- Replies contain a clear primary priority statement.
- Generic questions are no longer action-only unless the policy says so.
- Highlight/source metadata remains coherent and deduplicated.

### Task 4 — Verification and review hardening
Run focused/full verification and document Step 5 review in `tasks/todo.md`.

**Acceptance criteria**
- Targeted orchestrator tests pass.
- Full pytest passes.
- Preview helper test passes.
- Frontend lint/build passes.
- Snapshot export still includes the required orchestrator fields.

## Verification Checklist
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_orchestrator_*.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_dashboard_snapshot_export_freshness.py`
- `cd app/web && node --test src/lib/orchestratorPreview.test.js`
- `cd app/web && npm run lint && npm run build`
- `PYTHONPATH=.:'src' python3 ops/scripts/run_manager_summaries.py`
- `PYTHONPATH=.:'src' python3 ops/scripts/export_dashboard_snapshot.py`
