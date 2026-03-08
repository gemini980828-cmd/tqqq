# Step 6 Implementation Plan - Orchestrator 상담 UX / History / Operational Insights

## Work Objectives
Strengthen the orchestrator only at the user-facing layer: session history, replay UX, and lightweight operational insight summaries.

## Guardrails
### Must Have
- History/replay only for orchestrator.
- Static dashboard compatibility.
- Explicit-only / cache-first behavior preserved.
- Verification across backend audit summary + frontend history UX.

### Must NOT Have
- No sector-manager deepening.
- No live provider integration.
- No mutations to manual truth / summary store.
- No page-load auto invocation.

## Task Flow

### Task 1 — Audit/insight contract first
Add failing tests for audit summary and history insight helpers.

**Acceptance criteria**
- Audit summary builder can aggregate count, last question time, top intents, and recent questions.
- Frontend helper can derive stable session insights from local history entries.

### Task 2 — Backend operational insight summary
Extend orchestrator audit module + snapshot export to include optional `orchestrator_insights`.

**Acceptance criteria**
- Missing audit file does not fail snapshot export.
- Existing audit file yields deterministic summary fields.
- Contract/type tests cover the new block.

### Task 3 — Home 상담 UX deepening
Add local question history, replay action, clear-history control, and operational insight cards to `OrchestratorPanel`.

**Acceptance criteria**
- Submitting a question appends a history item.
- Replay reuses a previous question without manual copy-paste.
- Session insights render even without backend audit summary.

### Task 4 — Verification and review hardening
Run focused/full verification and document Step 6 review in `tasks/todo.md`.

**Acceptance criteria**
- Targeted orchestrator tests pass.
- Full pytest passes.
- New frontend helper tests pass.
- Frontend lint/build passes.

## Verification Checklist
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_orchestrator_audit.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_dashboard_snapshot_export_freshness.py`
- `cd app/web && node --test src/lib/orchestratorPreview.test.js src/lib/orchestratorHistory.test.js`
- `cd app/web && npm run lint && npm run build`
- `PYTHONPATH=.:'src' python3 ops/scripts/run_manager_summaries.py`
- `PYTHONPATH=.:'src' python3 ops/scripts/export_dashboard_snapshot.py`
