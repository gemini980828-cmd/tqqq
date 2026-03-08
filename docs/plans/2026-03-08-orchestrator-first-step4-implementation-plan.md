# Step 4 Implementation Plan — Orchestrator First

## Task 1 — Lock scope
- Keep manager surfaces unchanged except for contracts/summaries already present.
- Implement only orchestrator-facing improvements in this step.

## Task 2 — Add backend-owned briefs
- Create `src/tqqq_strategy/ai/orchestrator_brief.py`
- Export `orchestrator_briefs` from snapshot generation
- Add/extend contract tests proving snapshot contains the brief set

## Task 3 — Unify reply path
- Refactor `run_orchestrator(...)` to compose replies from brief keys
- Refactor frontend preview to consume exported `orchestrator_briefs`
- Avoid duplicating detailed phrasing in the client

## Task 4 — Telemetry / audit trail
- Create `src/tqqq_strategy/ai/orchestrator_audit.py`
- Make `build_orchestrator_reply(...)` append JSONL audit rows when enabled
- Add tests for audit logging and no-authoritative-data mutation

## Task 5 — Preview logic verification
- Add frontend preview helper logic test using Node built-in test runner
- Verify explicit submit path remains manual-only in browser smoke

## Task 6 — Verify and document
- Run targeted pytest + node test + frontend lint/build + export smoke
- Update `tasks/todo.md` review notes
