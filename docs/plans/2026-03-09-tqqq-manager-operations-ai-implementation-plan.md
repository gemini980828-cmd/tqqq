# TQQQ Manager Operations + AI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `soft_overheat_buffer`를 반영한 TQQQ 실전 운영판과 쉬운 설명형 AI Manager 패널을 Alpha Wealth Desk의 Core Strategy Manager에 추가한다.

**Architecture:** 백엔드 snapshot generator가 코어전략 전용 운영 계약(`engine_state`, `order_proposal`, `execution_checklist`, `transition_timeline`, `ai_brief`)을 생성하고, 프론트엔드는 deterministic 운영 카드와 우측 AI 패널로 이를 렌더링한다. 주문 계산과 상태 판단은 backend-owned deterministic data를 사용하고, AI/preview 레이어는 해당 데이터를 쉬운 한국어로 재구성만 한다.

**Tech Stack:** Python snapshot/export pipeline, React 19 + TypeScript + Vite frontend, node:test 기반 JS preview tests, pytest contract tests.

---

### Task 1: snapshot contract에 코어전략 운영 블록 추가

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Modify: `app/api/main.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`

**Step 1: Write the failing contract test**

`tests/contracts/test_dashboard_snapshot_v2.py`에 아래 assertions를 추가한다.

```python
assert "core_strategy_engine_state" in snap
assert "core_strategy_order_proposal" in snap
assert "core_strategy_execution_checklist" in snap
assert "core_strategy_transition_timeline" in snap
assert snap["core_strategy_engine_state"]["target_weight_pct"] == snap["action_hero"]["target_weight_pct"]
```

**Step 2: Run test to verify it fails**

Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py
```

Expected: FAIL because the new snapshot keys are absent.

**Step 3: Implement minimal snapshot defaults**

- `app/api/main.py`의 `OPTIONAL_BLOCK_DEFAULTS`에 새 블록 기본값 추가
- `src/tqqq_strategy/ops/dashboard_snapshot.py`에서 새 블록 stub 생성

Example shape:

```python
"core_strategy_engine_state": {
    "mode": "risk_on",
    "status_label": "기본 운용 상태",
    "target_weight_pct": round(target_weight * 100.0, 2),
}
```

**Step 4: Run test to verify it passes**

Run the same pytest command.

**Step 5: Commit**

```bash
git add app/api/main.py src/tqqq_strategy/ops/dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py
git commit -m "feat: add core strategy snapshot contract blocks"
```

---

### Task 2: `soft_overheat_buffer` 친화적 engine/order/checklist 계산 로직 추가

**Files:**
- Modify: `src/tqqq_strategy/ops/dashboard_snapshot.py`
- Modify: `src/tqqq_strategy/wealth/derived.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`
- Test: `tests/ai/test_manager_jobs.py`

**Step 1: Write failing tests for engine interpretation and order proposal**

Add tests for:
- 쉬운 상태 라벨 생성
- `base_target_weight_pct` vs `target_weight_pct`
- 주문 제안 수량/예상 비중 계산
- stale/freshness flag propagation

Example assertion:

```python
engine = snap["core_strategy_engine_state"]
proposal = snap["core_strategy_order_proposal"]
assert engine["target_weight_pct"] == 90.0
assert engine["buffer_active"] is True
assert "약간 보수적으로" in engine["plain_summary"]
assert proposal["action"] in {"buy", "sell", "hold"}
```

**Step 2: Run targeted tests and verify failure**

Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/ai/test_manager_jobs.py
```

Expected: FAIL on missing fields / incorrect values.

**Step 3: Implement deterministic helpers**

- `src/tqqq_strategy/ops/dashboard_snapshot.py`에 helper 추가
  - `_build_core_strategy_engine_state(...)`
  - `_build_core_strategy_order_proposal(...)`
  - `_build_core_strategy_execution_checklist(...)`
  - `_build_core_strategy_transition_timeline(...)`
- 필요 시 `src/tqqq_strategy/wealth/derived.py`에 재사용 가능한 rebalance/order math helper 추가
- 쉬운 라벨 예시:
  - `risk_on` → `기본 운용 상태`
  - `buffer_on` → `지금은 평소보다 약간 보수적으로 운영하는 상태`
  - `cash` → `현금 비중을 높여 방어하는 상태`

**Step 4: Re-run tests**

Run the same targeted pytest command.

**Step 5: Commit**

```bash
git add src/tqqq_strategy/ops/dashboard_snapshot.py src/tqqq_strategy/wealth/derived.py tests/contracts/test_dashboard_snapshot_v2.py tests/ai/test_manager_jobs.py
git commit -m "feat: add deterministic core strategy engine and order proposal"
```

---

### Task 3: manager summary / AI brief용 코어전략 요약 확장

**Files:**
- Modify: `src/tqqq_strategy/ai/manager_jobs.py`
- Test: `tests/ai/test_manager_jobs.py`

**Step 1: Write failing tests for easy-language brief**

Add assertions that manager summary / AI brief:
- 쉬운 한국어 요약을 제공한다
- 내부 용어를 전면에 내세우지 않는다
- 주문안과 경고를 함께 담는다

Example:

```python
core = records["core_strategy"]
assert "약간 보수적으로" in core["summary_text"] or "목표보다" in core["summary_text"]
assert "buffer" not in core["summary_text"].lower()
```

**Step 2: Run the test to verify it fails**

Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/ai/test_manager_jobs.py
```

**Step 3: Implement minimal summary enrichment**

- `core_strategy_engine_state` / `core_strategy_order_proposal`를 읽어 core manager summary 개선
- snapshot export용 `core_strategy_ai_brief`를 추가하거나 summary에서 파생 가능하도록 정리
- quick prompts와 order memo 문구를 backend-owned data로 제공

**Step 4: Re-run test**

Run the same pytest command.

**Step 5: Commit**

```bash
git add src/tqqq_strategy/ai/manager_jobs.py tests/ai/test_manager_jobs.py
git commit -m "feat: add core strategy ai brief content"
```

---

### Task 4: 프론트 타입과 TQQQ AI preview helper 추가

**Files:**
- Modify: `app/web/src/types/appSnapshot.ts`
- Create: `app/web/src/lib/tqqqManagerBrief.js`
- Create: `app/web/src/lib/tqqqManagerBrief.test.js`

**Step 1: Write the failing preview tests**

Create `app/web/src/lib/tqqqManagerBrief.test.js`.

Test cases:
- blank input이면 기본 브리프 반환 또는 null 처리
- engine state + proposal 기반 쉬운 한국어 요약 생성
- stale=true면 주문 권고보다 입력 갱신 경고가 먼저 나온다

Example:

```js
const brief = buildTqqqManagerBrief(snapshot)
assert.match(brief.summary, /약간 보수적으로 운영/)
assert.match(brief.orderMemo, /삼성증권/)
```

**Step 2: Run test to verify it fails**

Run:
```bash
node --test app/web/src/lib/tqqqManagerBrief.test.js
```

**Step 3: Implement minimal preview helper + types**

- `AppSnapshot`에 새 core strategy fields 추가
- `tqqqManagerBrief.js`에서 deterministic data를 쉬운 문장으로 변환
- stale 우선 경고 규칙 반영

**Step 4: Run test to verify it passes**

Run the same node test command.

**Step 5: Commit**

```bash
git add app/web/src/types/appSnapshot.ts app/web/src/lib/tqqqManagerBrief.js app/web/src/lib/tqqqManagerBrief.test.js
git commit -m "feat: add tqqq manager brief preview helper"
```

---

### Task 5: Core Strategy Manager UI를 운영판 + AI 패널로 재구성

**Files:**
- Modify: `app/web/src/pages/managers/CoreStrategyManager.tsx`
- Create: `app/web/src/components/coreStrategy/EngineStateHero.tsx`
- Create: `app/web/src/components/coreStrategy/StateMachineMonitor.tsx`
- Create: `app/web/src/components/coreStrategy/OrderProposalCard.tsx`
- Create: `app/web/src/components/coreStrategy/ExecutionChecklist.tsx`
- Create: `app/web/src/components/coreStrategy/TransitionTimeline.tsx`
- Create: `app/web/src/components/coreStrategy/TqqqAiManagerPanel.tsx`
- Optionally modify: `app/web/src/pages/Dashboard.tsx` (only if a shared subcomponent extraction reduces duplication)

**Step 1: Write the failing UI smoke checklist**

Document acceptance criteria in code comments or test notes:
- 상단 hero에 쉬운 상태 문구 노출
- 주문안 카드에 수량/금액/예상 비중 노출
- 우측 AI 패널에 brief + quick prompts + order memo 노출
- stale 시 경고 배지 노출

If adding UI tests is too heavy for this repo, use build/lint as the executable proof and keep logic in tested helper modules.

**Step 2: Run build/lint before changes to establish baseline**

Run:
```bash
cd app/web && npm run build && npm run lint
```

Expected: PASS before refactor.

**Step 3: Implement the UI**

- `CoreStrategyManager.tsx`에서 기존 embedded dashboard 의존도를 낮추고 새 2열 레이아웃 구성
- 좌측 deterministic blocks / 우측 AI panel 배치
- quick prompts는 `core_strategy_ai_brief.quick_prompts` 우선, 없으면 fallback 사용
- AI 패널 문구는 `tqqqManagerBrief.js` 또는 snapshot brief data를 사용

**Step 4: Re-run frontend verification**

Run:
```bash
cd app/web && npm run build && npm run lint && node --test src/lib/tqqqManagerBrief.test.js src/lib/orchestratorPreview.test.js
```

**Step 5: Commit**

```bash
git add app/web/src/pages/managers/CoreStrategyManager.tsx app/web/src/components/coreStrategy app/web/src/types/appSnapshot.ts app/web/src/lib/tqqqManagerBrief.js app/web/src/lib/tqqqManagerBrief.test.js
git commit -m "feat: redesign core strategy manager as operations board"
```

---

### Task 6: snapshot export/fixtures refresh 및 회귀 검증

**Files:**
- Modify: `app/web/public/dashboard_snapshot.json`
- Modify if needed: `ops/scripts/export_dashboard_snapshot.py`
- Test: `tests/contracts/test_dashboard_snapshot_v2.py`
- Test: `tests/ai/test_manager_jobs.py`

**Step 1: Refresh fixture/export path**

Run:
```bash
PYTHONPATH=src python3 ops/scripts/export_dashboard_snapshot.py
```

Expected: `Saved dashboard snapshot to app/web/public/dashboard_snapshot.json`

**Step 2: Run targeted Python tests**

Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q tests/contracts/test_dashboard_snapshot_v2.py tests/ai/test_manager_jobs.py
```

**Step 3: Run full verification slice**

Run:
```bash
UV_CACHE_DIR=/tmp/.uv-cache uv run --offline --with pytest pytest -q
cd app/web && npm run build && npm run lint && node --test src/lib/tqqqManagerBrief.test.js src/lib/orchestratorPreview.test.js
```

Expected: all pass.

**Step 4: Review generated snapshot manually**

Check:
- `core_strategy_engine_state.status_label`
- `core_strategy_order_proposal`
- `core_strategy_ai_brief`
- `wealth_home.manager_cards[0]`

**Step 5: Commit**

```bash
git add app/web/public/dashboard_snapshot.json ops/scripts/export_dashboard_snapshot.py tests/contracts/test_dashboard_snapshot_v2.py tests/ai/test_manager_jobs.py
git commit -m "test: refresh dashboard snapshot for tqqq manager operations board"
```

---

### Task 7: Documentation and rollout notes

**Files:**
- Modify: `docs/plans/2026-03-09-tqqq-manager-operations-ai-design.md`
- Modify: `tasks/todo.md`
- Modify: `tasks/lessons.md` (only if new feedback appears during implementation)

**Step 1: Add review notes to task tracker**

Document:
- 구현 범위
- 검증 명령
- 남은 리스크

**Step 2: Re-read design vs implementation**

Confirm shipped behavior matches:
- 쉬운 말 우선
- deterministic engine ownership
- 삼성증권 수동 주문 보조

**Step 3: Final verification note**

Add exact passing commands and snapshot refresh timestamp.

**Step 4: Commit**

```bash
git add docs/plans/2026-03-09-tqqq-manager-operations-ai-design.md tasks/todo.md
git commit -m "docs: record tqqq manager operations board rollout notes"
```
