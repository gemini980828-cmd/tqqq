# Wealth Management Step 4 Design — Orchestrator First

## Goal
Strengthen the orchestrator as the primary cross-domain assistant while intentionally keeping sector managers as lightweight shells with cached summaries only.

## Scope
### In scope
- Backend-owned orchestrator briefs derived from cached snapshot/context
- Audit/telemetry for orchestrator replies
- Frontend preview path consuming exported orchestrator briefs instead of duplicating business phrasing
- Explicit-only guardrail verification and preview logic tests

### Out of scope
- Deep stock/real-estate/cash manager agent workflows
- Per-manager conversational UX
- New brokerage/real-estate live integrations

## Design
1. **Orchestrator briefs**
   - Build concise backend-owned brief strings for action, cash, risk, stock research, real estate, and default priority.
   - Export them into dashboard snapshot so Home UI can reuse the same wording.
2. **Reply path unification**
   - Python orchestrator service composes answers from briefs.
   - Frontend preview helper selects/joins those briefs, keeping only question-intent routing in the client.
3. **Telemetry / audit**
   - Backend helper appends JSONL audit rows with question, trigger, used brief keys, source managers, and context source versions.
   - This is for future API-backed orchestrator paths; preview-only frontend mode remains read-only.
4. **Verification**
   - Contract tests for briefs/audit
   - Existing orchestrator tests extended where needed
   - Frontend preview helper test + lint/build
   - Export smoke to ensure briefs land in snapshot

## Acceptance Criteria
- Snapshot includes backend-generated orchestrator briefs.
- Backend orchestrator replies are built from shared brief records, not duplicated ad-hoc strings.
- Frontend preview consumes exported briefs and no longer reconstructs detailed domain wording from raw snapshot fields.
- Orchestrator audit log records explicit requests without mutating authoritative wealth data.
- Full pytest + frontend lint/build remain green.
