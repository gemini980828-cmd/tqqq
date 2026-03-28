# Risk-on Dip-Add Overlay Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 최종 엔진 위에 risk-on 내부 dip-add overlay를 실험용으로 추가하고, OOS/MDD 게이트를 통과하는지 검증합니다.

**Architecture:** `phase2-best + soft_overheat_buffer` 최종 엔진은 유지하고, 그 위에 `risk_on_dip_add_v1`를 별도 overlay로 얹습니다. 구현은 신호 계산과 상태 노출을 분리하고, 실험 전용 비교 경로를 먼저 만든 뒤 결과가 검증 기준을 통과할 때만 런타임 승격을 검토합니다.

**Tech Stack:** Python, pandas, pytest, existing TQQQ backtest scripts, current final-engine signal pipeline

---

## File Map

### Create
- `src/tqqq_strategy/signal/dip_add_overlay.py` — dip-add overlay 규칙과 상태 관리
- `tests/signal/test_dip_add_overlay.py` — overlay 단위 테스트
- `ops/scripts/run_risk_on_dip_add_experiment.py` — 현재 최종 엔진 vs dip-add 후보 비교 실행기
- `docs/analysis/2026-03-28-risk-on-dip-add-experiment-report.md` — 실험 결과 요약

### Modify
- `src/tqqq_strategy/signal/final_engine.py` — dip-add overlay optional hook 추가, 상태 컬럼 노출
- `tests/signal/test_final_engine.py` — final_engine과 dip-add 결합 테스트 추가
- `src/tqqq_strategy/ops/daily_job.py` — 실험 단계에서는 상태 노출 훅만 준비; 기본 메시지 동작은 유지
- `tests/ops/test_daily_job.py` — dip-add 상태 노출이 켜질 때 메시지/가드 테스트
- `docs/plans/2026-03-12-main-core-strategy-engine.md` — 실험 후보 섹션만 추가; 메인 엔진 문구는 바꾸지 않음

### Reuse / Read First
- `docs/superpowers/specs/2026-03-28-risk-on-dip-add-design.md`
- `src/tqqq_strategy/signal/final_engine.py`
- `tests/signal/test_final_engine.py`
- `src/tqqq_strategy/ops/daily_job.py`
- `tests/ops/test_daily_job.py`
- `ops/scripts/user_original_reference.py`
- `src/tqqq_strategy/experiments/phase2_runner.py`

---

## Chunk 1: Overlay rule unit and state contract

### Task 1: Add pure dip-add overlay unit with hysteresis-free short hold state

**Files:**
- Create: `src/tqqq_strategy/signal/dip_add_overlay.py`
- Test: `tests/signal/test_dip_add_overlay.py`

- [ ] **Step 1: Write the failing tests**

```python
from dataclasses import replace

import pandas as pd

from tqqq_strategy.signal.dip_add_overlay import DipAddState, RiskOnDipAddOverlay, apply_risk_on_dip_add


def test_apply_risk_on_dip_add_adds_5pct_after_two_day_drop():
    overlay = RiskOnDipAddOverlay()
    close = pd.Series([100.0, 96.0, 89.0])
    base = pd.Series([0.97, 0.97, 0.97])
    result = apply_risk_on_dip_add(
        base_weight=base,
        close=close,
        spy_bull=pd.Series([True, True, True]),
        vol_lock=pd.Series([False, False, False]),
        reentry_lock=pd.Series([False, False, False]),
        buffer_active=pd.Series([False, False, False]),
        overlay=overlay,
    )
    assert result.adjusted_weight.tolist() == [0.97, 0.97, 1.0]
    assert result.dip_add_delta_pct.tolist() == [0.0, 0.0, 0.03]


def test_apply_risk_on_dip_add_blocks_when_buffer_is_on():
    ...


def test_apply_risk_on_dip_add_releases_after_two_days_or_recovery():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/signal/test_dip_add_overlay.py
```

Expected: FAIL with missing module / missing symbol errors.

- [ ] **Step 3: Write minimal implementation**

Implement these units in `src/tqqq_strategy/signal/dip_add_overlay.py`:

```python
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RiskOnDipAddOverlay:
    trigger_2d_pct: float = -10.0
    stronger_trigger_2d_pct: float = -14.0
    add_pct: float = 0.05
    stronger_add_pct: float = 0.10
    min_base_weight: float = 0.90
    max_weight: float = 1.00
    max_hold_days: int = 2
    release_2d_pct: float = 0.0


@dataclass
class DipAddResult:
    adjusted_weight: pd.Series
    dip_add_active: pd.Series
    dip_add_delta_pct: pd.Series
    hold_days_left: pd.Series
```

Implementation rules:
- 2일 누적 수익률 계산
- `spy_bull`, `vol_lock`, `reentry_lock`, `buffer_active`, `base_weight >= 0.90` 모두 만족 시만 발동
- `<= -10%`면 `+0.05`, `<= -14%`면 `+0.10`
- `min(base + add, 1.0)` 상단 제한
- recovery (`2일 수익률 >= 0`) 또는 max hold days 시 해제
- 내부 상태는 시계열 순회로 관리하고, 외부 IO 없이 순수 함수 유지

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/signal/test_dip_add_overlay.py
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/signal/dip_add_overlay.py tests/signal/test_dip_add_overlay.py
git commit -m "Add a bounded risk-on dip-add overlay for experiments"
```

---

## Chunk 2: Final engine integration without changing runtime default

### Task 2: Wire dip-add as an optional final-engine experiment path

**Files:**
- Modify: `src/tqqq_strategy/signal/final_engine.py`
- Modify: `tests/signal/test_final_engine.py`

- [ ] **Step 1: Write the failing integration tests**

Add tests like:

```python
def test_compute_final_signal_table_can_emit_dip_add_columns_when_enabled():
    frame = compute_final_signal_table(sample_df, dip_add_overlay=RiskOnDipAddOverlay())
    assert "dip_add_active" in frame.columns
    assert "dip_add_delta_pct" in frame.columns


def test_compute_final_signal_table_keeps_current_output_when_dip_add_disabled():
    frame = compute_final_signal_table(sample_df)
    assert "dip_add_active" in frame.columns
    assert frame["dip_add_active"].eq(False).all()
```

- [ ] **Step 2: Run the focused tests to confirm failure**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/signal/test_final_engine.py
```

Expected: FAIL on missing columns / new parameter.

- [ ] **Step 3: Implement the minimal integration**

Modify `src/tqqq_strategy/signal/final_engine.py` to:
- import `RiskOnDipAddOverlay`, `apply_risk_on_dip_add`
- add optional parameter:

```python
dip_add_overlay: RiskOnDipAddOverlay | None = None
```

- compute supporting series:
  - `spy_dist200`
  - `vol20`
  - `reentry_lock` equivalent state if available; if not directly available, derive a conservative placeholder and document the limitation
- after `soft_overheat_buffer`, run dip-add only when `dip_add_overlay is not None`
- always emit columns:
  - `dip_add_active`
  - `dip_add_delta_pct`
  - `dip_add_hold_days_left`
- keep current runtime default unchanged by passing `dip_add_overlay=None` everywhere outside experiments

- [ ] **Step 4: Re-run the focused tests**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/signal/test_final_engine.py tests/signal/test_dip_add_overlay.py
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/signal/final_engine.py tests/signal/test_final_engine.py
git commit -m "Expose dip-add experiment state from the final signal engine"
```

---

## Chunk 3: Experiment runner and acceptance report

### Task 3: Add experiment runner that compares current final engine vs dip-add candidate

**Files:**
- Create: `ops/scripts/run_risk_on_dip_add_experiment.py`
- Create: `docs/analysis/2026-03-28-risk-on-dip-add-experiment-report.md`

- [ ] **Step 1: Write the failing script-level test or smoke contract**

If there is no good pytest home for script smoke, add a minimal test file:

```python
def test_risk_on_dip_add_experiment_outputs_required_summary_fields(tmp_path):
    ...
    assert "aftertax_cagr_delta" in summary
    assert "pretax_mdd_delta" in summary
    assert "oos_retention" in summary
    assert "dip_add_active_days" in summary
```

Prefer `tests/experiments/test_risk_on_dip_add_experiment.py` if needed.

- [ ] **Step 2: Run the focused test/smoke and confirm failure**

Run one of:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/experiments/test_risk_on_dip_add_experiment.py
```

or, if no test file is added:

```bash
PYTHONPATH=src python3 ops/scripts/run_risk_on_dip_add_experiment.py --help
```

Expected: FAIL / missing file.

- [ ] **Step 3: Implement the experiment runner**

`ops/scripts/run_risk_on_dip_add_experiment.py` should:
- load `data/user_input.csv`
- compute baseline final engine table (`dip_add_overlay=None`)
- compute dip-add candidate table (`dip_add_overlay=RiskOnDipAddOverlay()`)
- simulate both paths using existing backtest helpers, reusing current cost/tax assumptions
- write a compact markdown summary with:
  - after-tax CAGR
  - pretax MDD
  - OOS retention
  - dip-add active days
  - turnover delta if available
  - pass/fail verdict vs spec gates

Suggested summary keys:

```python
summary = {
    "baseline_aftertax_cagr": ...,
    "candidate_aftertax_cagr": ...,
    "aftertax_cagr_delta": ...,
    "baseline_pretax_mdd": ...,
    "candidate_pretax_mdd": ...,
    "pretax_mdd_delta": ...,
    "candidate_oos_retention": ...,
    "dip_add_active_days": ...,
    "verdict": "pass" or "reject",
}
```

- [ ] **Step 4: Run the experiment and capture results**

Run:

```bash
PYTHONPATH=src python3 ops/scripts/run_risk_on_dip_add_experiment.py
```

Expected:
- markdown report written
- summary contains all required fields

- [ ] **Step 5: Write the acceptance note**

Update `docs/analysis/2026-03-28-risk-on-dip-add-experiment-report.md` with:
- exact baseline vs candidate numbers
- pass/reject decision
- whether runtime promotion is recommended

- [ ] **Step 6: Commit**

```bash
git add ops/scripts/run_risk_on_dip_add_experiment.py docs/analysis/2026-03-28-risk-on-dip-add-experiment-report.md tests/experiments/test_risk_on_dip_add_experiment.py
git commit -m "Add a reproducible experiment lane for dip-add evaluation"
```

---

## Chunk 4: Optional ops exposure only if experiment passes

### Task 4: Add non-default ops visibility for dip-add state

**Files:**
- Modify: `src/tqqq_strategy/ops/daily_job.py`
- Modify: `tests/ops/test_daily_job.py`
- Modify: `docs/plans/2026-03-12-main-core-strategy-engine.md`

- [ ] **Step 1: Write the failing ops-facing tests**

Add a focused test:

```python
def test_run_daily_signal_alert_mentions_dip_add_when_state_is_active(tmp_path):
    ...
    assert "dip-add" in result["message"]
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/ops/test_daily_job.py
```

Expected: FAIL on missing dip-add messaging.

- [ ] **Step 3: Implement minimal visibility**

Only if Task 3 verdict is pass:
- add compact state line in Telegram/summary:
  - `dip-add: ON (+5%)`
  - or `dip-add: OFF`
- do **not** switch runtime defaults automatically
- update engine doc with a small “experimental overlay candidate” subsection, not a promotion

- [ ] **Step 4: Re-run focused ops tests**

Run:

```bash
PYTHONPATH=src UV_CACHE_DIR=/tmp/.uv-cache uv run --with pytest pytest -q tests/ops/test_daily_job.py
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/tqqq_strategy/ops/daily_job.py tests/ops/test_daily_job.py docs/plans/2026-03-12-main-core-strategy-engine.md
git commit -m "Expose dip-add experiment state without changing runtime defaults"
```

---

## Plan review notes

- This plan intentionally stops short of runtime promotion.
- Promotion requires Task 3 to produce a passing verdict against the spec gates.
- If reentry-lock state cannot be reconstructed cleanly from current final-engine inputs, prefer **conservative disablement** over inferred behavior.

## Execution order

1. Chunk 1
2. Chunk 2
3. Chunk 3
4. Chunk 4 only if Chunk 3 verdict passes

## Done definition

- overlay unit tests pass
- final-engine integration tests pass
- experiment runner produces a reproducible report
- report includes pass/reject verdict against CAGR/MDD/OOS gates
- runtime defaults remain unchanged unless a separate promotion decision is made

---

Plan complete and saved to `docs/superpowers/plans/2026-03-28-risk-on-dip-add-experiment.md`. Ready to execute?
