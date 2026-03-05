# TQQQ 전략 고도화 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pine 기준 전략을 동치(±0.1%)로 재현하는 백테스트를 먼저 완성하고, 동일 코드베이스에서 실험 프레임과 운영 웹앱으로 단계 확장한다.

**Architecture:** 모듈형(ingest → canonical → signal → backtest → report → ops-webapp)으로 구성한다. 1차는 동치성 검증에 집중하고, 2차는 WFO/OOS 게이트를 적용한 실험, 3차는 신호/알림 자동화 + 수동 주문 운영 화면을 제공한다.

**Tech Stack:** Python 3.12, pandas/numpy, DuckDB+Parquet, pytest, FastAPI(백엔드), React/Vite(프론트엔드), APScheduler(일일 잡)

---

### Task 1: 프로젝트 골격 및 테스트 환경 부트스트랩

**Files:**
- Create: `pyproject.toml`
- Create: `src/tqqq_strategy/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

```python
# tests/test_bootstrap.py
from importlib import import_module

def test_package_importable():
    mod = import_module("tqqq_strategy")
    assert mod is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bootstrap.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tqqq_strategy'`

**Step 3: Write minimal implementation**

```toml
# pyproject.toml
[project]
name = "tqqq-strategy"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pandas", "numpy", "duckdb", "pyarrow", "yfinance", "pydantic", "fastapi", "uvicorn", "apscheduler"]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

```python
# src/tqqq_strategy/__init__.py
__all__ = ["__version__"]
__version__ = "0.1.0"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bootstrap.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add pyproject.toml src/tqqq_strategy/__init__.py tests/test_bootstrap.py && git commit -m "chore: bootstrap project skeleton" || echo "skip commit (not a git repo yet)"
```

---

### Task 2: 데이터 계약(canonical schema) 및 품질검사

**Files:**
- Create: `src/tqqq_strategy/data/schema.py`
- Create: `src/tqqq_strategy/data/quality.py`
- Test: `tests/data/test_schema_quality.py`

**Step 1: Write the failing test**

```python
# tests/data/test_schema_quality.py
import pandas as pd
from tqqq_strategy.data.quality import validate_canonical

def test_validate_canonical_rejects_duplicate_date_symbol():
    df = pd.DataFrame([
        {"date": "2024-01-02", "symbol": "TQQQ", "close": 1, "adj_close": 1, "source": "x", "tz": "America/New_York", "session_type": "RTH", "is_trading_day": True},
        {"date": "2024-01-02", "symbol": "TQQQ", "close": 2, "adj_close": 2, "source": "x", "tz": "America/New_York", "session_type": "RTH", "is_trading_day": True},
    ])
    ok, errs = validate_canonical(df)
    assert not ok
    assert any("duplicate" in e.lower() for e in errs)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_schema_quality.py::test_validate_canonical_rejects_duplicate_date_symbol -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/data/quality.py
REQUIRED = {"date","symbol","close","adj_close","source","tz","session_type","is_trading_day"}

def validate_canonical(df):
    errs = []
    missing = REQUIRED.difference(df.columns)
    if missing:
        errs.append(f"missing:{sorted(missing)}")
    if df.duplicated(subset=["date", "symbol"]).any():
        errs.append("duplicate date+symbol")
    return (len(errs) == 0), errs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_schema_quality.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/data/quality.py tests/data/test_schema_quality.py && git commit -m "feat: add canonical schema quality checks" || echo "skip commit (not a git repo yet)"
```

---

### Task 3: 원천 수집기(stooq raw / yfinance adjusted)

**Files:**
- Create: `src/tqqq_strategy/data/ingest_stooq.py`
- Create: `src/tqqq_strategy/data/ingest_yf.py`
- Test: `tests/data/test_ingest_contract.py`

**Step 1: Write the failing test**

```python
# tests/data/test_ingest_contract.py
from tqqq_strategy.data.ingest_yf import normalize_yf_row

def test_normalize_yf_row_sets_adjusted_source_fields():
    row = normalize_yf_row("TQQQ", "2024-01-02", 50.0, 49.5)
    assert row["symbol"] == "TQQQ"
    assert row["source"] == "yfinance"
    assert row["adj_close"] == 49.5
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/data/test_ingest_contract.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/data/ingest_yf.py

def normalize_yf_row(symbol, date, close, adj_close):
    return {
        "date": date,
        "symbol": symbol,
        "close": float(close),
        "adj_close": float(adj_close),
        "source": "yfinance",
        "tz": "America/New_York",
        "session_type": "RTH",
        "is_trading_day": True,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/data/test_ingest_contract.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/data/ingest_yf.py tests/data/test_ingest_contract.py && git commit -m "feat: add source normalizers for stooq/yfinance" || echo "skip commit (not a git repo yet)"
```

---

### Task 4: Pine 동치 신호엔진 v1 구현

**Files:**
- Create: `src/tqqq_strategy/signal/engine_v1.py`
- Create: `src/tqqq_strategy/signal/params.py`
- Test: `tests/signal/test_engine_v1_priority.py`

**Step 1: Write the failing test**

```python
# tests/signal/test_engine_v1_priority.py
from tqqq_strategy.signal.engine_v1 import decide_code

def test_vol_lock_has_highest_priority():
    code = decide_code(locked=True, spy_force_cash=False, reentry_blocked=False, base_code=2, overheat_stage=0)
    assert code == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/signal/test_engine_v1_priority.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/signal/engine_v1.py

def decide_code(*, locked, spy_force_cash, reentry_blocked, base_code, overheat_stage):
    if locked or spy_force_cash or reentry_blocked:
        return 0
    if overheat_stage == 4:
        return 0
    if overheat_stage == 3 and base_code != 0:
        return 5
    if overheat_stage == 2 and base_code == 2:
        return 4
    if overheat_stage == 1 and base_code == 2:
        return 3
    return base_code
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/signal/test_engine_v1_priority.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/signal/engine_v1.py tests/signal/test_engine_v1_priority.py && git commit -m "feat: implement v1 priority decision logic" || echo "skip commit (not a git repo yet)"
```

---

### Task 5: 백테스트 엔진(체결/비용/세후) 및 벤치마크

**Files:**
- Create: `src/tqqq_strategy/backtest/runner.py`
- Create: `src/tqqq_strategy/backtest/tax_kr.py`
- Test: `tests/backtest/test_cost_tax.py`

**Step 1: Write the failing test**

```python
# tests/backtest/test_cost_tax.py
from tqqq_strategy.backtest.tax_kr import apply_korean_overseas_tax

def test_tax_applies_after_2_5m_deduction():
    tax = apply_korean_overseas_tax(realized_profit_krw=10_000_000)
    assert tax == (10_000_000 - 2_500_000) * 0.22
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/backtest/test_cost_tax.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/backtest/tax_kr.py

def apply_korean_overseas_tax(realized_profit_krw: float) -> float:
    taxable = max(realized_profit_krw - 2_500_000, 0.0)
    return taxable * 0.22
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/backtest/test_cost_tax.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/backtest/tax_kr.py tests/backtest/test_cost_tax.py && git commit -m "feat: add KR overseas stock tax model" || echo "skip commit (not a git repo yet)"
```

---

### Task 6: 동치성 검증 하네스(TradingView vs Python)

**Files:**
- Create: `src/tqqq_strategy/validation/golden_diff.py`
- Test: `tests/validation/test_weight_tolerance.py`
- Create: `reports/.gitkeep`

**Step 1: Write the failing test**

```python
# tests/validation/test_weight_tolerance.py
from tqqq_strategy.validation.golden_diff import within_tolerance

def test_within_tolerance_uses_point_one_percent_rule():
    assert within_tolerance(0.9500, 0.9491, tol=0.001)
    assert not within_tolerance(0.9500, 0.9488, tol=0.001)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/validation/test_weight_tolerance.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/validation/golden_diff.py

def within_tolerance(expected: float, actual: float, tol: float = 0.001) -> bool:
    return abs(expected - actual) <= tol
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/validation/test_weight_tolerance.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/validation/golden_diff.py tests/validation/test_weight_tolerance.py && git commit -m "feat: add golden diff tolerance checker" || echo "skip commit (not a git repo yet)"
```

---

### Task 7: 2차 실험 프레임(WFO/OOS 70% 게이트)

**Files:**
- Create: `src/tqqq_strategy/experiments/wfo.py`
- Test: `tests/experiments/test_oos_gate.py`

**Step 1: Write the failing test**

```python
# tests/experiments/test_oos_gate.py
from tqqq_strategy.experiments.wfo import passes_oos_gate

def test_oos_gate_requires_70_percent_retention():
    assert passes_oos_gate(is_score=1.0, oos_score=0.7)
    assert not passes_oos_gate(is_score=1.0, oos_score=0.69)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/experiments/test_oos_gate.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/experiments/wfo.py

def passes_oos_gate(is_score: float, oos_score: float, min_ratio: float = 0.70) -> bool:
    if is_score <= 0:
        return False
    return (oos_score / is_score) >= min_ratio
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/experiments/test_oos_gate.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/experiments/wfo.py tests/experiments/test_oos_gate.py && git commit -m "feat: add OOS retention gate" || echo "skip commit (not a git repo yet)"
```

---

### Task 8: 운영 웹앱 MVP(텔레그램 UI 매핑)

**Files:**
- Create: `app/api/main.py`
- Create: `app/web/src/pages/Dashboard.tsx`
- Create: `app/contracts/telegram_snapshot.schema.json`
- Test: `tests/contracts/test_telegram_blocks.py`

**Step 1: Write the failing test**

```python
# tests/contracts/test_telegram_blocks.py
from app.api.main import build_dashboard_snapshot

def test_dashboard_contains_required_telegram_blocks():
    snap = build_dashboard_snapshot({})
    required = {"header", "position_change", "reason", "market_summary", "ops_log"}
    assert required.issubset(set(snap.keys()))
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/contracts/test_telegram_blocks.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# app/api/main.py

def build_dashboard_snapshot(payload: dict) -> dict:
    return {
        "header": {},
        "position_change": {},
        "reason": {},
        "market_summary": {},
        "ops_log": {},
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/contracts/test_telegram_blocks.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add app/api/main.py tests/contracts/test_telegram_blocks.py && git commit -m "feat: add dashboard telegram block contract" || echo "skip commit (not a git repo yet)"
```

---

### Task 9: 일일 운영 잡(수집→신호→알림) + 멱등성

**Files:**
- Create: `src/tqqq_strategy/ops/daily_job.py`
- Create: `src/tqqq_strategy/ops/idempotency.py`
- Test: `tests/ops/test_idempotency.py`

**Step 1: Write the failing test**

```python
# tests/ops/test_idempotency.py
from tqqq_strategy.ops.idempotency import build_alert_key

def test_alert_key_is_stable_per_day_signal():
    k1 = build_alert_key("2026-03-05", 1, 2)
    k2 = build_alert_key("2026-03-05", 1, 2)
    assert k1 == k2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/ops/test_idempotency.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# src/tqqq_strategy/ops/idempotency.py

def build_alert_key(date_str: str, prev_code: int, new_code: int) -> str:
    return f"{date_str}:{prev_code}->{new_code}"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/ops/test_idempotency.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add src/tqqq_strategy/ops/idempotency.py tests/ops/test_idempotency.py && git commit -m "feat: add alert idempotency key" || echo "skip commit (not a git repo yet)"
```

---

### Task 10: 통합 검증 및 릴리즈 체크

**Files:**
- Create: `docs/runbooks/backtest-and-ops-checklist.md`
- Modify: `README.md` (if exists)

**Step 1: Write the failing test/check command**

```bash
pytest -q
```

**Step 2: Run check to observe current failures**

Run: `pytest -q`
Expected: initial 일부 FAIL/ERROR 가능

**Step 3: Implement missing glue code and docs**

```markdown
# docs/runbooks/backtest-and-ops-checklist.md
- 데이터 수집 성공 여부
- 동치 검증 통과 여부(±0.1%)
- 공식/보조 리포트 분리 확인
- 운영 알림 멱등성 확인
```

**Step 4: Run full verification**

Run:
- `pytest -q`
- `python -m tqqq_strategy.validation.golden_diff` (CLI가 구현되면)
Expected: 테스트 통과 + 동치 리포트 생성

**Step 5: Commit**

```bash
git rev-parse --is-inside-work-tree && git add . && git commit -m "chore: finalize validation and runbooks" || echo "skip commit (not a git repo yet)"
```

