# Wealth Management System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the current TQQQ dashboard into an investment-operations-centered wealth management system with Home, manager surfaces, cached manager summaries, and a real-time orchestrator chat.

**Architecture:** Keep data truth in a four-layer pipeline (raw, canonical, derived, AI summary), promote the current TQQQ dashboard into the Core Strategy Manager, add manager surfaces for stocks / real estate / cash-debt, and layer an orchestrator over cached manager summaries rather than direct raw-source chat. Start manual-truth-first and avoid brokerage API dependency in the MVP.

**Tech Stack:** Python data pipelines and ops scripts, existing app/api snapshot builders, React/Vite dashboard frontend, JSON/CSV/manual ledgers for initial source-of-truth inputs, scheduled summary generation, targeted pytest + npm lint/build verification.

---

### Task 1: Establish the wealth-system data contract and manual truth inputs

**Files:**
- Create: `src/tqqq_strategy/wealth/schema.py`
- Create: `src/tqqq_strategy/wealth/manual_inputs.py`
- Create: `tests/wealth/test_schema_contract.py`
- Modify: `docs/plans/2026-03-06-wealth-management-system-design.md`
- Modify: `tasks/todo.md`

**Step 1: Write the failing schema tests**
- Add tests that define required canonical records for:
  - assets/accounts,
  - positions,
  - transactions,
  - stock watchlist rows,
  - property watchlist rows,
  - cash/debt rows,
  - AI summary metadata (`generated_at`, `source_version`, `stale`).

**Step 2: Run tests to verify failure**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_schema_contract.py`
Expected: FAIL because wealth schema/manual input helpers do not exist yet.

**Step 3: Implement minimal schema and manual-input loaders**
- Create canonical constants / dataclasses / validation helpers for the first-release records.
- Support manual-truth-first inputs for positions, cash, debt, stock watchlists, and real-estate watchlists.
- Keep the model narrow: only fields required by approved managers and Home.

**Step 4: Run tests to verify pass**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_schema_contract.py`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/tqqq_strategy/wealth/schema.py src/tqqq_strategy/wealth/manual_inputs.py tests/wealth/test_schema_contract.py tasks/todo.md
git commit -m "feat: add wealth data contract and manual truth inputs"
```

**Acceptance criteria:**
- A developer can point to one canonical truth contract for all MVP managers.
- Manual truth inputs exist for real positions, cash/debt, stock ideas, and property watchlists.
- Tests prove missing/invalid required fields are rejected.

### Task 2: Build derived wealth snapshots and manager-summary storage

**Files:**
- Create: `src/tqqq_strategy/wealth/derived.py`
- Create: `src/tqqq_strategy/wealth/summary_store.py`
- Create: `tests/wealth/test_derived_snapshots.py`
- Create: `tests/wealth/test_summary_store.py`
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Modify: `app/api/main.py`

**Step 1: Write failing tests for derived and summary layers**
- Add tests for:
  - total net worth aggregation,
  - target-vs-actual position gaps,
  - liquidity / debt summary,
  - manager summary freshness/staleness handling,
  - Home consuming cached summaries without requiring live AI.

**Step 2: Run tests to verify failure**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_derived_snapshots.py tests/wealth/test_summary_store.py`
Expected: FAIL because the derived layer and summary store do not exist yet.

**Step 3: Implement minimal derived builders and summary store**
- Compute Home-level wealth overview and manager-card payloads from canonical inputs.
- Store manager summaries with:
  - `manager_id`,
  - `summary_text`,
  - `key_points`,
  - `warnings`,
  - `recommended_actions`,
  - `generated_at`,
  - `source_version`,
  - `stale`.
- Extend `dashboard_snapshot.py` / `app/api/main.py` to support a Home wealth snapshot contract, not just TQQQ-only cards.

**Step 4: Run tests to verify pass**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/wealth/test_derived_snapshots.py tests/wealth/test_summary_store.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_telegram_blocks.py`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/tqqq_strategy/wealth/derived.py src/tqqq_strategy/wealth/summary_store.py src/tqqq_strategy/ops/dashboard_snapshot.py app/api/main.py tests/wealth/test_derived_snapshots.py tests/wealth/test_summary_store.py
git commit -m "feat: add derived wealth snapshots and summary storage"
```

**Acceptance criteria:**
- Home-level snapshot data can be produced from manual truth inputs plus current TQQQ artifacts.
- Manager summaries are cached, versioned, and visibly stale/fresh.
- The system can render meaningful Home data without live AI execution.

### Task 3: Refactor the frontend into multi-surface wealth navigation

**Files:**
- Modify: `app/web/src/App.tsx`
- Modify: `app/web/src/pages/Dashboard.tsx`
- Create: `app/web/src/pages/Home.tsx`
- Create: `app/web/src/pages/managers/CoreStrategyManager.tsx`
- Create: `app/web/src/pages/managers/StockResearchManager.tsx`
- Create: `app/web/src/pages/managers/RealEstateManager.tsx`
- Create: `app/web/src/pages/managers/CashDebtManager.tsx`
- Create: `app/web/src/pages/Research.tsx`
- Create: `app/web/src/pages/Inbox.tsx`
- Create: `app/web/src/pages/Reports.tsx`
- Create: `app/web/src/components/TopNav.tsx`
- Create: `app/web/src/components/ManagerCard.tsx`
- Create: `app/web/src/components/OrchestratorPanel.tsx`
- Modify: `app/web/src/index.css`
- Test: `app/web` build/lint commands

**Step 1: Write the failing UI contract tests or snapshot expectations**
- If UI tests exist, add failing tests for:
  - top navigation,
  - Home desk sections,
  - manager cards,
  - orchestrator panel placeholder,
  - separate manager pages.
- If no UI test harness exists yet, define component-level acceptance in TODO and verify via lint/build plus explicit mock states.

**Step 2: Run current build/lint to capture baseline**
Run:
- `npm run lint` in `app/web`
- `npm run build` in `app/web`
Expected: current single-dashboard build succeeds, but multi-surface requirements are not implemented.

**Step 3: Implement minimal navigation and page shells**
- Promote the existing TQQQ dashboard to `CoreStrategyManager`.
- Create a new `Home` page using wealth overview, inbox, manager cards, recent activity, and orchestrator entry.
- Add lightweight shells for Stocks / Real Estate / Cash & Debt / Research / Inbox / Reports.
- Keep the first pass thin; avoid styling rabbit holes until data wiring is in place.

**Step 4: Re-run lint/build and validate both mock and live snapshot states**
Run:
- `npm run lint`
- `npm run build`
Expected: PASS.

**Step 5: Commit**
```bash
git add app/web/src app/web/package.json app/web/package-lock.json
git commit -m "feat: add wealth management navigation and manager shells"
```

**Acceptance criteria:**
- A user can navigate between Home, Managers, Research, Inbox, and Reports.
- The current TQQQ board lives inside the Core Strategy Manager rather than owning the whole app.
- Home clearly reads as wealth desk + manager hub.
- Frontend lint/build remains green.

### Task 4: Add batch manager-summary jobs and Home inbox generation

**Files:**
- Create: `src/tqqq_strategy/ai/manager_jobs.py`
- Create: `src/tqqq_strategy/ai/inbox_builder.py`
- Create: `ops/scripts/run_manager_summaries.py`
- Create: `tests/ai/test_manager_jobs.py`
- Create: `tests/ai/test_inbox_builder.py`
- Modify: `.github/workflows/daily-telegram.yml`
- Modify: `ops/scripts/export_dashboard_snapshot.py`

**Step 1: Write failing tests for summary jobs and inbox output**
- Cover:
  - manager job payload assembly,
  - summary persistence metadata,
  - stale detection,
  - Home inbox items derived from TQQQ signal changes, watchlist state changes, and cash/debt warnings.

**Step 2: Run tests to verify failure**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_manager_jobs.py tests/ai/test_inbox_builder.py`
Expected: FAIL because manager-job and inbox builders do not exist yet.

**Step 3: Implement minimal batch jobs and export flow**
- Add manager-summary job entry points for:
  - Core Strategy,
  - Stocks,
  - Real Estate,
  - Cash & Debt.
- Keep implementations deterministic where possible; separate pure data assembly from later LLM calls.
- Extend the daily export pipeline to refresh summary artifacts before writing the Home dashboard snapshot.

**Step 4: Re-run tests plus pipeline smoke**
Run:
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_manager_jobs.py tests/ai/test_inbox_builder.py`
- `python3 ops/scripts/run_manager_summaries.py`
- `python3 ops/scripts/export_dashboard_snapshot.py`
Expected: tests pass and snapshot export includes inbox + manager summary fields.

**Step 5: Commit**
```bash
git add src/tqqq_strategy/ai/manager_jobs.py src/tqqq_strategy/ai/inbox_builder.py ops/scripts/run_manager_summaries.py ops/scripts/export_dashboard_snapshot.py .github/workflows/daily-telegram.yml tests/ai/test_manager_jobs.py tests/ai/test_inbox_builder.py
git commit -m "feat: add manager summary jobs and home inbox generation"
```

**Acceptance criteria:**
- Manager summaries can be refreshed in batch without rendering the UI.
- Home inbox items exist even without a live orchestrator session.
- The snapshot export pipeline now reflects the approved cost model (batch first, cached by default).

### Task 5: Introduce real-time orchestrator chat with strict cost guardrails

**Files:**
- Create: `src/tqqq_strategy/ai/orchestrator_context.py`
- Create: `src/tqqq_strategy/ai/orchestrator_service.py`
- Create: `tests/ai/test_orchestrator_context.py`
- Create: `tests/ai/test_orchestrator_guardrails.py`
- Modify: `app/web/src/components/OrchestratorPanel.tsx`
- Modify: `app/api/main.py` or add a dedicated orchestrator route module
- Modify: `docs/runbooks/github-actions-telegram.md`
- Modify: `tasks/todo.md`

**Step 1: Write failing tests for orchestrator context assembly and guardrails**
- Verify that the orchestrator consumes:
  - canonical/derived state,
  - cached manager summaries,
  - inbox items,
  and does **not** require raw long-form sources for normal prompts.
- Verify guardrails that prevent automatic invocation during page load.

**Step 2: Run tests to verify failure**
Run: `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_orchestrator_context.py tests/ai/test_orchestrator_guardrails.py`
Expected: FAIL because orchestrator service does not yet exist.

**Step 3: Implement minimal orchestrator service and UI panel**
- Build a context packer that loads the latest summaries and derived wealth data.
- Add a UI panel that allows explicit user-triggered prompts only.
- Keep provider integration thin and swappable; do not hardwire every domain to live chat.
- Log prompt/result metadata for cost visibility and debugging.

**Step 4: Verify end-to-end behavior**
Run:
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_orchestrator_context.py tests/ai/test_orchestrator_guardrails.py`
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q`
- `npm run lint`
- `npm run build`
Expected: PASS.

**Step 5: Commit**
```bash
git add src/tqqq_strategy/ai/orchestrator_context.py src/tqqq_strategy/ai/orchestrator_service.py app/web/src/components/OrchestratorPanel.tsx app/api/main.py tests/ai/test_orchestrator_context.py tests/ai/test_orchestrator_guardrails.py tasks/todo.md
git commit -m "feat: add guarded real-time orchestrator chat"
```

**Acceptance criteria:**
- The user can open Home and inspect wealth state with zero live AI calls.
- The user can explicitly ask the orchestrator cross-domain questions in real time.
- Guardrails ensure the orchestrator is opt-in and consistent with Policy B.
- Full pytest + frontend lint/build remain green.

## Cross-cutting guardrails
- Keep Home summary-oriented; do not move full manager detail into Home.
- Avoid introducing brokerage API dependencies in this plan.
- Keep manual-truth-first inputs valid until a later dedicated automation phase.
- Do not let AI write back authoritative balances or status values.
- Add freshness / source-version metadata to every cached summary artifact.
- Prefer deterministic builders around LLM boundaries so failures are easy to debug and test.

## Suggested verification checklist
- `UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q`
- `python3 ops/scripts/run_manager_summaries.py`
- `python3 ops/scripts/export_dashboard_snapshot.py`
- `npm run lint` in `app/web`
- `npm run build` in `app/web`
- manual UI verification for:
  - Home overview,
  - TQQQ manager,
  - Stocks manager shell,
  - Real Estate manager shell,
  - Cash & Debt manager shell,
  - Inbox,
  - Reports,
  - orchestrator chat panel,
  - stale summary indicators.

## MVP acceptance criteria
1. Home acts as a real wealth desk rather than a single-strategy dashboard.
2. TQQQ remains the deepest and most operational manager surface.
3. Stocks, Real Estate, and Cash/Debt have usable stateful manager pages.
4. Manager summaries are batch-generated and cached with freshness metadata.
5. Real-time orchestrator chat is available only on explicit user request.
6. Manual truth inputs drive balances and positions across the system.
7. The platform can operate meaningfully even when the AI layer is unavailable.
