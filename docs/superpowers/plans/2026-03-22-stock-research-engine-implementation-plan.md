# Stock Research Engine Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, replayable stock-research engine that produces `stock_research_workspace` artifacts from portfolio/watchlist inputs, with explicit state transitions, subscores, reason codes, and evidence references.

**Architecture:** Introduce a backend `src/tqqq_strategy/stock_research/` package that separates universe construction, feature building, scoring, state transitions, evidence generation, and workflow assembly. Keep the dashboard snapshot layer thin: it should call the workflow and map its output into the existing `stock_research_workspace` contract while preserving replay/backtest metadata for later validation.

**Tech Stack:** Python 3.12, existing `src/tqqq_strategy` package, pytest via `uv run --with pytest pytest`, Vite/React frontend consuming the existing snapshot contract.

---

## File Map

### New backend package
- Create: `src/tqqq_strategy/stock_research/__init__.py`
  - Package exports for the stock research engine.
- Create: `src/tqqq_strategy/stock_research/types.py`
  - Internal typed dictionaries/dataclasses for universe entries, feature snapshots, scored candidates, decision records.
- Create: `src/tqqq_strategy/stock_research/universe.py`
  - Build the research universe from manual watchlist + holdings + optional future external candidates.
- Create: `src/tqqq_strategy/stock_research/features.py`
  - Deterministic feature derivation from watchlist/positions/manual inputs.
- Create: `src/tqqq_strategy/stock_research/scoring.py`
  - Compute subscores and final score.
- Create: `src/tqqq_strategy/stock_research/state_machine.py`
  - Convert scores/features into `탐색/관찰/후보/보류/제외` and `next_action`.
- Create: `src/tqqq_strategy/stock_research/evidence.py`
  - Generate reason codes, evidence refs, and summary lines.
- Create: `src/tqqq_strategy/stock_research/workflow.py`
  - Orchestrate the full engine and return a workspace-ready artifact.
- Create: `src/tqqq_strategy/stock_research/records.py`
  - Build replay/backtest-friendly decision records.

### Backend integration
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
  - Replace inline stock research seed logic with workflow call.
- Modify: `app/api/main.py` only if normalization/defaults need to expand to carry new fields.

### Frontend contract/UI consumption
- Modify: `app/web/src/types/appSnapshot.ts`
  - Extend types to include `engine_version`, `reason_codes`, `subscores`, `confidence`, `evidence_refs` if exposed in snapshot.
- Modify: `app/web/src/lib/stockResearchDashboard.js`
  - Consume richer workspace fields without reimplementing engine logic.
- Modify: `app/web/src/components/stock-research/StockResearchDetail.tsx`
  - Surface reason codes / evidence refs / confidence when present.
- Modify: `app/web/src/components/stock-research/StockResearchEvidencePanel.tsx`
  - Display evidence refs and source-backed summaries.

### Tests
- Create: `tests/stock_research/test_universe.py`
- Create: `tests/stock_research/test_features.py`
- Create: `tests/stock_research/test_scoring.py`
- Create: `tests/stock_research/test_state_machine.py`
- Create: `tests/stock_research/test_evidence.py`
- Create: `tests/stock_research/test_workflow.py`
- Create: `tests/stock_research/test_records.py`
- Modify: `tests/contracts/test_dashboard_snapshot_v2.py`
- Modify: `tests/contracts/test_public_dashboard_snapshot_export.py`
- Modify: `app/web/src/lib/stockResearchDashboard.test.js`

---

## Chunk 1: Backend engine skeleton + typed contracts

### Task 1: Create engine package and core types

**Files:**
- Create: `src/tqqq_strategy/stock_research/__init__.py`
- Create: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_records.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.types import ResearchDecisionRecord


def test_research_decision_record_carries_required_replay_fields():
    record = ResearchDecisionRecord(
        symbol="NVDA",
        as_of="2026-01-30T00:00:00",
        engine_version="stock-research/v1",
        feature_snapshot_id="snap-1",
        final_score=68,
        status="관찰",
    )
    assert record.symbol == "NVDA"
    assert record.engine_version == "stock-research/v1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_records.py`
Expected: FAIL with `ModuleNotFoundError` or missing symbol

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ResearchDecisionRecord:
    symbol: str
    as_of: str
    engine_version: str
    feature_snapshot_id: str
    final_score: float
    status: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_records.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/__init__.py src/tqqq_strategy/stock_research/types.py tests/stock_research/test_records.py
git commit -m "Establish replayable stock research engine contracts\n\nStart the stock research engine as a versioned backend package so later scoring and evidence work has explicit typed boundaries and replay metadata.\n\nConstraint: Must stay compatible with existing dashboard snapshot contract during migration\nRejected: Keep implicit dict-only contracts in dashboard_snapshot.py | hard to replay and test incrementally\nConfidence: high\nScope-risk: narrow\nDirective: Add fields to decision records before wiring more logic so replayability remains first-class\nTested: uv run --with pytest pytest -q tests/stock_research/test_records.py\nNot-tested: Full snapshot integration"
```

---

## Chunk 2: Universe builder

### Task 2: Build deterministic universe from watchlist and holdings

**Files:**
- Create: `src/tqqq_strategy/stock_research/universe.py`
- Modify: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_universe.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.universe import build_research_universe


def test_build_research_universe_marks_held_symbols_and_preserves_watchlist_order():
    universe = build_research_universe(
        manual_inputs={
            "stock_watchlist": [
                {"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI 수혜 지속 모니터링"},
                {"idea_id": "stock-2", "symbol": "AAPL", "status": "후보", "memo": "대형 기술주 비교"},
            ],
            "positions": [
                {"symbol": "AAPL", "manager_id": "core_strategy"},
            ],
        },
        as_of="2026-01-30T00:00:00",
    )

    assert [item.symbol for item in universe] == ["NVDA", "AAPL"]
    assert universe[0].is_held is False
    assert universe[1].is_held is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_universe.py::test_build_research_universe_marks_held_symbols_and_preserves_watchlist_order`
Expected: FAIL because `build_research_universe` does not exist

- [ ] **Step 3: Write minimal implementation**
- Build `ResearchUniverseEntry` in `types.py`
- Implement `build_research_universe` that:
  - reads `stock_watchlist`
  - checks `positions`
  - preserves input order
  - normalizes missing symbols out

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_universe.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/types.py src/tqqq_strategy/stock_research/universe.py tests/stock_research/test_universe.py
git commit -m "Separate stock research universe construction from scoring\n\nExtract watchlist and holdings normalization into a dedicated universe builder so later feature and scoring layers do not depend on raw manual input shapes.\n\nConstraint: Universe must remain deterministic and preserve user-supplied ordering for explainability\nRejected: Fold universe logic into workflow directly | obscures test boundaries and replay inputs\nConfidence: high\nScope-risk: narrow\nDirective: Keep universe creation free of scoring assumptions and external data fetches\nTested: uv run --with pytest pytest -q tests/stock_research/test_universe.py\nNot-tested: External candidate expansion"
```

---

## Chunk 3: Feature builder

### Task 3: Derive deterministic feature snapshots

**Files:**
- Create: `src/tqqq_strategy/stock_research/features.py`
- Modify: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_features.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.features import build_feature_snapshot
from tqqq_strategy.stock_research.types import ResearchUniverseEntry


def test_build_feature_snapshot_derives_overlap_priority_inputs():
    entry = ResearchUniverseEntry(
        idea_id="stock-1",
        symbol="NVDA",
        raw_status="관찰",
        memo="AI 수혜 지속 모니터링",
        is_held=False,
        as_of="2026-01-30T00:00:00",
    )

    snapshot = build_feature_snapshot(entry)

    assert snapshot.symbol == "NVDA"
    assert snapshot.overlap_level == "low"
    assert snapshot.has_memo is True
```
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_features.py`
Expected: FAIL due to missing feature builder

- [ ] **Step 3: Write minimal implementation**
- Create `ResearchFeatureSnapshot`
- Derive:
  - normalized status
  - overlap level from `is_held`
  - memo presence
  - recency placeholder
  - catalyst placeholder flags

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_features.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/types.py src/tqqq_strategy/stock_research/features.py tests/stock_research/test_features.py
git commit -m "Introduce deterministic stock research feature snapshots\n\nAdd a stable feature-building layer so scoring and state transitions consume normalized inputs instead of raw watchlist records.\n\nConstraint: First version must avoid external data dependencies and remain fully replayable from manual inputs\nRejected: Score directly from raw universe entries | makes later backtest metadata harder to reason about\nConfidence: high\nScope-risk: narrow\nDirective: Add new features here first and keep them timestamp-aware\nTested: uv run --with pytest pytest -q tests/stock_research/test_features.py\nNot-tested: Market-data-enriched features"
```

---

## Chunk 4: Subscore-based scoring engine

### Task 4: Compute quality, fit, risk, and final score

**Files:**
- Create: `src/tqqq_strategy/stock_research/scoring.py`
- Modify: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.scoring import score_candidate
from tqqq_strategy.stock_research.types import ResearchFeatureSnapshot


def test_score_candidate_separates_quality_fit_and_risk_components():
    snapshot = ResearchFeatureSnapshot(
        idea_id="stock-1",
        symbol="NVDA",
        normalized_status="관찰",
        is_held=False,
        overlap_level="low",
        has_memo=True,
        as_of="2026-01-30T00:00:00",
    )

    scored = score_candidate(snapshot)

    assert scored.quality_score >= 0
    assert scored.fit_score >= 0
    assert scored.risk_penalty >= 0
    assert scored.final_score == scored.quality_score + scored.fit_score - scored.risk_penalty
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_scoring.py`
Expected: FAIL because scoring module is missing

- [ ] **Step 3: Write minimal implementation**
- Add `ScoredResearchCandidate`
- Use a simple deterministic scoring formula with named subscores
- Keep weights as constants in one place

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_scoring.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/types.py src/tqqq_strategy/stock_research/scoring.py tests/stock_research/test_scoring.py
git commit -m "Make stock research scoring decomposable and auditable\n\nBreak the first-pass rank into named subscores so later validation can distinguish quality, fit, and risk effects instead of hiding them inside one opaque number.\n\nConstraint: Final score must stay deterministic for replay and contract tests\nRejected: Single aggregate score only | impossible to debug and attribute later\nConfidence: high\nScope-risk: narrow\nDirective: Keep subscores explicit even if UI initially shows only final score\nTested: uv run --with pytest pytest -q tests/stock_research/test_scoring.py\nNot-tested: Historical predictive power"
```

---

## Chunk 5: State machine and next action logic

### Task 5: Convert scores into policy states

**Files:**
- Create: `src/tqqq_strategy/stock_research/state_machine.py`
- Modify: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_state_machine.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.state_machine import apply_state_policy
from tqqq_strategy.stock_research.types import ScoredResearchCandidate


def test_apply_state_policy_promotes_high_score_low_overlap_candidate_to_candidate_state():
    scored = ScoredResearchCandidate(
        symbol="NVDA",
        final_score=80,
        quality_score=50,
        fit_score=35,
        risk_penalty=5,
        overlap_level="low",
        is_held=False,
        normalized_status="관찰",
        as_of="2026-01-30T00:00:00",
    )

    decision = apply_state_policy(scored)

    assert decision.status == "후보"
    assert decision.next_action
    assert decision.recent_status_change
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_state_machine.py`
Expected: FAIL because state policy does not exist

- [ ] **Step 3: Write minimal implementation**
- Create `StateDecision`
- Implement explicit thresholds and state transitions
- Add reason codes for each transition branch

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_state_machine.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/types.py src/tqqq_strategy/stock_research/state_machine.py tests/stock_research/test_state_machine.py
git commit -m "Turn stock research statuses into explicit policy decisions\n\nPromote the UI labels into a tested state machine so candidate, observe, hold, and reject decisions are produced by clear policy branches instead of ad hoc conditionals.\n\nConstraint: Initial thresholds must be easy to inspect and tune without code archaeology\nRejected: Infer status implicitly from score buckets inside snapshot builder | too hard to trace decision changes\nConfidence: high\nScope-risk: moderate\nDirective: Keep transition reasons explicit because later backtests need to attribute status changes\nTested: uv run --with pytest pytest -q tests/stock_research/test_state_machine.py\nNot-tested: Multi-period transition stability"
```

---

## Chunk 6: Evidence and reason-code generation

### Task 6: Generate explanation artifacts without LLM dependency

**Files:**
- Create: `src/tqqq_strategy/stock_research/evidence.py`
- Modify: `src/tqqq_strategy/stock_research/types.py`
- Test: `tests/stock_research/test_evidence.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.evidence import build_evidence_artifact
from tqqq_strategy.stock_research.types import StateDecision


def test_build_evidence_artifact_emits_reason_codes_and_refs():
    decision = StateDecision(
        symbol="NVDA",
        status="관찰",
        next_action="NVDA 후속 리서치 업데이트",
        recent_status_change="관찰 유지",
        reason_codes=["status.observe", "fit.low_overlap"],
        as_of="2026-01-30T00:00:00",
    )

    evidence = build_evidence_artifact(decision)

    assert evidence.reason_codes == ["status.observe", "fit.low_overlap"]
    assert evidence.evidence_refs
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_evidence.py`
Expected: FAIL because evidence builder is missing

- [ ] **Step 3: Write minimal implementation**
- Create `EvidenceArtifact`
- Build deterministic `evidence_refs` and summary strings from reason codes
- No LLM calls in this task

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_evidence.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/types.py src/tqqq_strategy/stock_research/evidence.py tests/stock_research/test_evidence.py
git commit -m "Add deterministic evidence artifacts for stock research decisions\n\nGenerate reason codes and evidence references in a separate layer so explanations stay replayable and later LLM assistance remains optional.\n\nConstraint: Evidence generation must not alter scores or statuses\nRejected: Embed freeform narrative strings directly in state policy | mixes explanation with decision logic\nConfidence: high\nScope-risk: narrow\nDirective: Keep evidence refs stable because the frontend will depend on them for auditability\nTested: uv run --with pytest pytest -q tests/stock_research/test_evidence.py\nNot-tested: External citation retrieval"
```

---

## Chunk 7: Workflow assembly and snapshot integration

### Task 7: Assemble the engine workflow

**Files:**
- Create: `src/tqqq_strategy/stock_research/workflow.py`
- Modify: `src/tqqq_strategy/stock_research/__init__.py`
- Test: `tests/stock_research/test_workflow.py`

- [ ] **Step 1: Write the failing test**

```python
from tqqq_strategy.stock_research.workflow import build_stock_research_workspace


def test_build_stock_research_workspace_returns_workspace_contract_fields():
    workspace = build_stock_research_workspace(
        manual_inputs={
            "stock_watchlist": [{"idea_id": "stock-1", "symbol": "NVDA", "status": "관찰", "memo": "AI 수혜 지속 모니터링"}],
            "positions": [],
        },
        generated_at="2026-01-30T00:00:00",
    )

    assert set(workspace) >= {"generated_at", "filters", "queue", "items", "compare_seed", "flow", "evidence"}
    assert workspace["items"][0]["symbol"] == "NVDA"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_workflow.py`
Expected: FAIL because workflow is missing

- [ ] **Step 3: Write minimal implementation**
- Orchestrate universe → features → scoring → state policy → evidence
- Build current snapshot contract from internal typed objects
- Include `engine_version` in the workspace or items

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_workflow.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/__init__.py src/tqqq_strategy/stock_research/workflow.py tests/stock_research/test_workflow.py
git commit -m "Assemble a deterministic stock research workflow artifact\n\nConnect universe, feature, scoring, state, and evidence layers into one backend workflow that emits the dashboard workspace contract.\n\nConstraint: Workflow must remain pure for replay and backtest support\nRejected: Perform snapshot-specific formatting inside each module | duplicates contract mapping logic\nConfidence: high\nScope-risk: moderate\nDirective: Keep internal typed objects richer than the UI contract and map at the workflow boundary\nTested: uv run --with pytest pytest -q tests/stock_research/test_workflow.py\nNot-tested: Frontend rendering"
```

### Task 8: Replace inline snapshot builder logic with workflow call

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Modify: `tests/contracts/test_dashboard_snapshot_v2.py`
- Modify: `tests/contracts/test_public_dashboard_snapshot_export.py`

- [ ] **Step 1: Write the failing integration test**

Add assertions that snapshot items now contain:
- `engine_version`
- `reason_codes` or `evidence_refs`
- stable deterministic queue ordering

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_public_dashboard_snapshot_export.py`
Expected: FAIL because inline builder does not emit the new fields

- [ ] **Step 3: Write minimal integration code**
- Import `build_stock_research_workspace`
- Remove or slim `_build_stock_research_workspace`
- Keep contract defaults intact

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_public_dashboard_snapshot_export.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/ops/dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_public_dashboard_snapshot_export.py
git commit -m "Move stock research snapshot generation behind a dedicated workflow\n\nReplace the inline stock research seed builder with the new workflow so snapshot generation stays thin and engine logic lives in one domain package.\n\nConstraint: Existing dashboard consumers must keep working during the migration\nRejected: Leave duplicate logic in snapshot builder and workflow | guarantees divergence\nConfidence: high\nScope-risk: moderate\nDirective: Snapshot code should compose artifacts, not own research policy logic\nTested: uv run --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_public_dashboard_snapshot_export.py\nNot-tested: Live production snapshot generation"
```

---

## Chunk 8: Frontend exposure of richer engine artifacts

### Task 9: Extend frontend types and consumers for engine metadata

**Files:**
- Modify: `app/web/src/types/appSnapshot.ts`
- Modify: `app/web/src/lib/stockResearchDashboard.js`
- Modify: `app/web/src/lib/stockResearchDashboard.test.js`
- Modify: `app/web/src/components/stock-research/StockResearchDetail.tsx`
- Modify: `app/web/src/components/stock-research/StockResearchEvidencePanel.tsx`

- [ ] **Step 1: Write the failing frontend test**

Add a test ensuring the dashboard helper preserves `engine_version`, `reason_codes`, and `evidence_refs` when present in snapshot items.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd app/web && node --test src/lib/stockResearchDashboard.test.js`
Expected: FAIL because helper drops the fields

- [ ] **Step 3: Write minimal implementation**
- Extend TS types
- Preserve richer fields in `resolveStockResearchWorkspace`
- Render evidence refs / reason codes in detail panel

- [ ] **Step 4: Run test to verify it passes**

Run: `cd app/web && node --test src/lib/stockResearchDashboard.test.js && npm run build`
Expected: PASS and successful build

- [ ] **Step 5: Commit**

```bash
git add app/web/src/types/appSnapshot.ts app/web/src/lib/stockResearchDashboard.js app/web/src/lib/stockResearchDashboard.test.js app/web/src/components/stock-research/StockResearchDetail.tsx app/web/src/components/stock-research/StockResearchEvidencePanel.tsx
git commit -m "Expose stock research engine metadata in the dashboard UI\n\nCarry engine versioning and evidence metadata through the frontend so the UI can explain decisions without re-creating backend logic.\n\nConstraint: UI must remain a consumer of engine artifacts rather than a second scoring engine\nRejected: Derive reason codes in React components | duplicates policy logic and breaks replayability\nConfidence: high\nScope-risk: moderate\nDirective: Only render backend-produced explanation fields; do not invent them on the client\nTested: cd app/web && node --test src/lib/stockResearchDashboard.test.js && npm run build\nNot-tested: Browser interaction flow"
```

---

## Chunk 9: Decision records and validation harness hooks

### Task 10: Persist replay/backtest-friendly decision records

**Files:**
- Create: `src/tqqq_strategy/stock_research/records.py`
- Modify: `src/tqqq_strategy/stock_research/workflow.py`
- Test: `tests/stock_research/test_records.py`

- [ ] **Step 1: Write the failing test**

Add a test that workflow output can emit decision records containing:
- `decision_time`
- `engine_version`
- `feature_snapshot_id`
- `subscores`
- `status`
- `evidence_refs`

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest -q tests/stock_research/test_records.py`
Expected: FAIL because workflow does not emit records

- [ ] **Step 3: Write minimal implementation**
- Implement record builder from scored/state/evidence objects
- Expose a helper used by later validation code

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest -q tests/stock_research/test_records.py tests/stock_research/test_workflow.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/stock_research/records.py src/tqqq_strategy/stock_research/workflow.py tests/stock_research/test_records.py tests/stock_research/test_workflow.py
git commit -m "Emit replayable stock research decision records from the workflow\n\nCapture the workflow outputs in a stable record format so later backtests and failure analysis can compare decisions across engine versions honestly.\n\nConstraint: Record emission must not mutate the workspace contract\nRejected: Delay decision-record support until validation phase | loses ground-truth history during early engine tuning\nConfidence: high\nScope-risk: narrow\nDirective: Keep record shape stable and additive because validation code will build on it soon\nTested: uv run --with pytest pytest -q tests/stock_research/test_records.py tests/stock_research/test_workflow.py\nNot-tested: Long-horizon historical replay"
```

---

## Chunk 10: Final verification and export refresh

### Task 11: Run full affected verification suite

**Files:**
- Modify: `app/web/public/dashboard_snapshot.json` via export script

- [ ] **Step 1: Refresh the snapshot export**

Run: `python3 ops/scripts/export_dashboard_snapshot.py`
Expected: `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`

- [ ] **Step 2: Run backend engine and contract tests**

Run:
```bash
uv run --with pytest pytest -q tests/stock_research/test_universe.py tests/stock_research/test_features.py tests/stock_research/test_scoring.py tests/stock_research/test_state_machine.py tests/stock_research/test_evidence.py tests/stock_research/test_workflow.py tests/stock_research/test_records.py tests/contracts/test_dashboard_snapshot_v2.py tests/contracts/test_public_dashboard_snapshot_export.py
```
Expected: all PASS

- [ ] **Step 3: Run frontend verification**

Run:
```bash
cd app/web && node --test src/lib/stockResearchDashboard.test.js && npm run lint && npm run build
```
Expected: all PASS

- [ ] **Step 4: Perform a quick browser smoke test**

Run the dev server and verify:
- `/#/managers/stocks` loads
- queue/items/detail align
- reason/evidence metadata render without crashing

- [ ] **Step 5: Final commit**

```bash
git add src/tqqq_strategy/stock_research src/tqqq_strategy/ops/dashboard_snapshot.py tests/stock_research tests/contracts app/web/src app/web/public/dashboard_snapshot.json
git commit -m "Make stock research decisions replayable before model sophistication\n\nDeliver the first deterministic stock research engine as a replayable backend workflow with explicit subscores, policy states, and evidence artifacts so later validation and model upgrades have a trustworthy base.\n\nConstraint: Must improve engine structure without breaking the existing stock research dashboard contract\nRejected: Jump straight to ML or LLM scoring | would create untestable complexity before replay and validation foundations exist\nConfidence: medium\nScope-risk: moderate\nDirective: Do not add ML or LLM-driven ranking until the replay records and baseline validation loop are in active use\nTested: python3 ops/scripts/export_dashboard_snapshot.py; uv run --with pytest pytest -q tests/stock_research/... tests/contracts/...; cd app/web && node --test src/lib/stockResearchDashboard.test.js && npm run lint && npm run build\nNot-tested: Multi-year out-of-sample alpha validation"
```

---

## Acceptance Criteria

- Backend engine logic no longer lives inline in `dashboard_snapshot.py`
- `stock_research_workspace` is produced by a dedicated workflow package
- Scores are decomposed into named subscores, not a single opaque formula
- Status transitions are explicit and tested
- Evidence artifacts are deterministic and separate from score logic
- Decision records are replayable for later backtests
- Frontend consumes engine metadata without implementing engine policy
- Snapshot export, contract tests, frontend tests, lint, and build all pass

---

## Suggested Implementation Order

1. Chunk 1–3 (types, universe, features)
2. Chunk 4–6 (scoring, state machine, evidence)
3. Chunk 7 (workflow + snapshot integration)
4. Chunk 8 (frontend metadata rendering)
5. Chunk 9–10 (records + verification)
