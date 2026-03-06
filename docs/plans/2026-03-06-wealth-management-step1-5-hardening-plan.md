# Wealth Management Step 1.5 Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the small but material gaps found in the Step 1 review so Home behaves like a real desk, Core Strategy is fully nested inside the manager surface, frontend snapshot types stop drifting, and Step 2 starts from a cleaner contract boundary.

**Architecture:** Keep the existing Step 1 structure intact and apply only four focused hardening patches: embed the legacy dashboard inside the Core Strategy manager, add the missing Home desk blocks, consolidate the frontend snapshot contract to a single shared type, and explicitly defer `transactions`/summary-store work into Step 2 documentation instead of leaving it ambiguous. Avoid broad refactors or new runtime features.

**Tech Stack:** React/Vite/TypeScript frontend, existing dashboard snapshot JSON contract, Python snapshot export, pytest, npm lint/build, markdown task tracking.

---

### Task 1: Fully embed the TQQQ dashboard inside Core Strategy Manager

**Files:**
- Modify: `app/web/src/pages/managers/CoreStrategyManager.tsx`
- Modify: `app/web/src/pages/Dashboard.tsx`
- Test/Verify: `app/web` lint/build

**Step 1: Capture the current nested-render acceptance in TODO**
- Add/update checklist note that Core Strategy must render the existing TQQQ board in `embedded` mode without a duplicate top-level app shell or competing page header.

**Step 2: Run frontend verification before changes**
Run:
```bash
cd app/web && npm run lint && npm run build
```
Expected: PASS on current Step 1 baseline.

**Step 3: Make Core Strategy explicitly use embedded mode**
- Update `CoreStrategyManager.tsx` to pass `embedded` to `Dashboard`.
- If needed, tighten `Dashboard.tsx` so embedded mode suppresses any standalone wrapper/header behavior consistently.

**Step 4: Re-run frontend verification**
Run:
```bash
cd app/web && npm run lint && npm run build
```
Expected: PASS, with no type or JSX regressions.

**Step 5: Commit**
```bash
git add app/web/src/pages/managers/CoreStrategyManager.tsx app/web/src/pages/Dashboard.tsx tasks/todo.md
git commit -m "refactor: fully embed core strategy dashboard"
```

**Acceptance criteria:**
- Core Strategy page no longer behaves like a standalone dashboard page.
- The TQQQ board renders as a manager sub-surface inside the Step 1 shell.
- Frontend lint/build remain green.

### Task 2: Promote Home from shell to true desk with activity and inbox preview

**Files:**
- Modify: `app/web/src/pages/Home.tsx`
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py` (only if extra Home-friendly fields are needed)
- Modify: `app/web/public/dashboard_snapshot.json` (via export)
- Test/Verify: `tests/contracts/test_dashboard_snapshot_v2.py`, `tests/contracts/test_wealth_home_snapshot_step1.py`, frontend lint/build

**Step 1: Define the missing Home desk blocks in TODO**
- Add checklist items for:
  - recent activity / event log block
  - inbox preview / today-check list block

**Step 2: Validate current snapshot inputs**
Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q \
  tests/contracts/test_dashboard_snapshot_v2.py \
  tests/contracts/test_wealth_home_snapshot_step1.py
```
Expected: PASS on baseline.

**Step 3: Implement the missing Home desk sections**
- Add a “recent activity” block driven by `event_timeline` with graceful fallback.
- Add an “inbox preview” block driven by existing `action_hero`, `reason_summary`, and snapshot metadata.
- Only extend the Python snapshot if the UI cannot be built cleanly from current fields.

**Step 4: Re-export and verify**
Run:
```bash
python3 ops/scripts/export_dashboard_snapshot.py
cd app/web && npm run lint && npm run build
```
Expected: snapshot export succeeds and the Home desk still builds cleanly.

**Step 5: Commit**
```bash
git add app/web/src/pages/Home.tsx src/tqqq_strategy/ops/dashboard_snapshot.py app/web/public/dashboard_snapshot.json tasks/todo.md
git commit -m "feat: harden home desk activity and inbox preview"
```

**Acceptance criteria:**
- Home contains wealth overview, manager cards, orchestrator placeholder, recent activity, and inbox preview.
- The page reads as an operations desk, not just a landing shell.
- Live snapshot export still supports the page without mock-only dependencies.

### Task 3: Consolidate frontend snapshot typing to one source of truth

**Files:**
- Modify: `app/web/src/types/appSnapshot.ts`
- Modify: `app/web/src/pages/Dashboard.tsx`
- Modify: `app/web/src/App.tsx`
- Modify: `app/web/src/pages/Home.tsx`
- Modify: `app/web/src/pages/Managers.tsx`
- Modify: any manager pages still depending on duplicated snapshot shapes
- Test/Verify: `app/web` lint/build

**Step 1: Identify all snapshot type definitions/usages**
Run:
```bash
rg -n "AppSnapshot|DashboardSnapshot|RiskGaugeValue|RiskStatus" app/web/src
```
Expected: find duplicated typing between `Dashboard.tsx` and `src/types/appSnapshot.ts`.

**Step 2: Make one canonical frontend snapshot type**
- Keep `app/web/src/types/appSnapshot.ts` as the only source of truth.
- Convert `Dashboard.tsx` to import and re-export the shared type if needed.
- Remove duplicate local shape definitions that can drift.

**Step 3: Re-run frontend verification**
Run:
```bash
cd app/web && npm run lint && npm run build
```
Expected: PASS with no duplicate-type regressions.

**Step 4: Commit**
```bash
git add app/web/src/types/appSnapshot.ts app/web/src/pages/Dashboard.tsx app/web/src/App.tsx app/web/src/pages/Home.tsx app/web/src/pages/Managers.tsx app/web/src/pages/managers
git commit -m "refactor: unify frontend dashboard snapshot types"
```

**Acceptance criteria:**
- Frontend snapshot typing lives in one place.
- Adding Step 2 fields requires changing one shared contract, not parallel type copies.
- Frontend lint/build remain green.

### Task 4: Resolve Step 2 contract ambiguity in docs and TODO

**Files:**
- Modify: `docs/plans/2026-03-06-wealth-management-system-implementation-plan.md`
- Modify: `tasks/todo.md`
- Optional Modify: `docs/plans/2026-03-06-wealth-management-system-design.md`

**Step 1: Document the explicit defer decision**
- Update the implementation plan so `transactions`, `assets/accounts`, `summary_store`, stale/fresh cache signaling, and manager batch summaries are explicitly marked as **Step 2 scope**.
- Remove ambiguity that Step 1 should already have completed them.

**Step 2: Align TODO wording**
- Add a short “Step 2 preconditions” subsection noting:
  - `transactions` truth contract to be introduced in Step 2
  - summary/cache layer to be introduced first in Step 2

**Step 3: Review for consistency**
Run:
```bash
rg -n "transactions|summary_store|stale|fresh|Step 2" docs/plans/2026-03-06-wealth-management-system-implementation-plan.md tasks/todo.md
```
Expected: docs clearly separate Step 1 hardening from Step 2 foundation work.

**Step 4: Commit**
```bash
git add docs/plans/2026-03-06-wealth-management-system-implementation-plan.md docs/plans/2026-03-06-wealth-management-system-design.md tasks/todo.md
git commit -m "docs: clarify step2 data and summary scope"
```

**Acceptance criteria:**
- No reviewer could mistake `transactions` or `summary_store` as unfinished Step 1 bugs.
- Step 2 starts with an explicit dependency list.
- TODO and plan documents agree on what is deferred.

### Task 5: Final hardening verification and handoff

**Files:**
- Modify: `tasks/todo.md`
- Verify: backend/frontend commands only

**Step 1: Run the focused suite**
Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q \
  tests/wealth/test_schema_contract.py \
  tests/wealth/test_derived_foundation.py \
  tests/wealth/test_step1_dashboard_snapshot.py \
  tests/contracts/test_dashboard_snapshot_v2.py \
  tests/contracts/test_wealth_home_snapshot_step1.py
```
Expected: PASS.

**Step 2: Run the full suite and snapshot export**
Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q
python3 ops/scripts/export_dashboard_snapshot.py
cd app/web && npm run lint && npm run build
```
Expected: all PASS.

**Step 3: Update review notes**
- Record exact verification outputs in `tasks/todo.md` under a new Step 1.5 review section.
- Explicitly state that Step 2 can start on top of the hardened Step 1 base.

**Step 4: Commit**
```bash
git add tasks/todo.md app/web/public/dashboard_snapshot.json
git commit -m "chore: verify step1.5 hardening readiness"
```

**Acceptance criteria:**
- Step 1 review findings are resolved or explicitly deferred.
- Home, Core Strategy, and the frontend contract are stable enough for Step 2.
- A future executor can start Step 2 without re-litigating Step 1 gaps.
