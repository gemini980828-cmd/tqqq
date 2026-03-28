# Core Strategy Final Promotion Review

## Scope

Review target: adopted core strategy candidate = `phase2-best` modified TQQQ core plus `soft_overheat_buffer`, using repo-local evidence only.

Primary evidence reviewed:
- `experiments/best_config.json`
- `experiments/stress_test_summary.json`
- `experiments/stress_test_windows.csv`
- `experiments/pre2011_stress_test_summary.json`
- `experiments/pre2011_stress_test_windows.csv`
- `experiments/ext2000_stress_test_summary.json`
- `experiments/ext2000_stress_test_windows.csv`
- `experiments/overlay_improvement_summary.json`
- `experiments/overlay_improvement_trials.csv`
- `experiments/overlay_improvement_winners.csv`
- `experiments/upgrade/upgrade_summary.json`
- `ops/scripts/run_overlay_improvement_experiments.py`
- `src/tqqq_strategy/experiments/overlay_candidates.py`
- `tests/experiments/test_overlay_candidates.py`
- `tests/experiments/test_phase2_constraints.py`

## Executive verdict

**Recommendation: tune slightly before final promotion.**

More specifically:
1. **Keep the `phase2-best` core unchanged** as the promotion baseline.
2. **Do not promote the currently selected `soft_overheat_buffer` overlay as-is.**
3. Re-rank overlay candidates against **`phase2-best`**, not against the original baseline, and only keep an overlay if the risk trade-off is explicitly desired.

This is not a full rejection because the `phase2-best` core has solid robustness evidence. It is also not a keep-as-is because the adopted overlay selection logic is misaligned with the actual production baseline.

## 1) Robustness and evidence audit

### Phase2 core looks promotion-worthy on its own

From `experiments/best_config.json`:
- `phase2-best` after-tax CAGR: **0.3981**
- original after-tax CAGR baseline in `experiments/overlay_improvement_summary.json`: **0.3860**
- full-period OOS retention: **0.7044** (`oos_pass: true`)
- pretax MDD: **-0.4088**

Interpretation:
- The core improves full-period after-tax CAGR by about **+1.22 percentage points** versus original.
- It clears the repo’s explicit OOS retention bar (`>= 0.70`).
- The price paid is a slightly worse drawdown and higher tax bill than original.

### Stress artifacts support the phase2 core more than the original baseline

From `experiments/stress_test_summary.json` / `stress_test_windows.csv`:
- post-2011 windows improved: **5 / 5**
- average delta after-tax CAGR: **+0.0080**
- full window delta after-tax CAGR: **+0.0122**
- full-window OOS flips from **fail (0.6814)** to **pass (0.7044)**

From `experiments/pre2011_stress_test_summary.json` / `pre2011_stress_test_windows.csv`:
- improved windows: **5 / 6**
- only non-improved window: **PRE2011**, delta after-tax CAGR **-0.0019**

From `experiments/ext2000_stress_test_summary.json` / `ext2000_stress_test_windows.csv`:
- improved windows: **6 / 8**
- the two non-improved windows are **DOTCOM** and **GFC**, both effectively flat/equal in the artifact

Interpretation:
- The phase2 core’s advantage is not coming from one lucky subperiod.
- The edge is strongest in the live-relevant modern sample and remains directionally positive in broader stress artifacts.
- However, the core does **not** improve drawdown in those stress windows; drawdown is consistently a little worse.

### Test coverage exists, but it mostly protects invariants instead of promotion logic

Covered today:
- overlay hysteresis and cap behavior: `tests/experiments/test_overlay_candidates.py`
- candidate parameter invariants: `tests/experiments/test_phase2_constraints.py`

Not covered by dedicated tests:
- the final promotion rule for choosing an adopted overlay on top of `phase2-best`
- a guard asserting that an adopted overlay must beat or intentionally trade off against `phase2-best`

## 2) Overfitting-risk review and challenge

### Main challenge: the overlay is evaluated on `phase2-best` but selected against the wrong comparator

`ops/scripts/run_overlay_improvement_experiments.py` builds each overlay by applying `apply_soft_overheat_buffer(...)` to `phase2_weight`.

But the winner filter is:
- `delta_aftertax_cagr_vs_orig >= 0.0`
- `delta_pretax_mdd_vs_orig > 0.0`
- `oos_pass`

So the overlay is **applied to `phase2-best`** but is **selected against the original baseline**.

That is the key evidence gap.

### The currently selected overlay materially hurts the actual production baseline

From `experiments/overlay_improvement_summary.json`:
- selected overlay: `cap_weight=0.9, enter=126, exit=123`
- delta after-tax CAGR vs `phase2-best`: **-0.0073**
- delta pretax MDD vs `phase2-best`: **+0.0164**

Interpretation:
- The chosen overlay is a real risk-off trade.
- It is **not** a free improvement over the core.
- The repo currently justifies it because it beats the **original** baseline, not because it is the best final production choice over `phase2-best`.

### No overlay in the reviewed grid strictly dominates `phase2-best`

Review of `experiments/overlay_improvement_trials.csv` shows:
- the strongest MDD-improving overlays all lose meaningful after-tax CAGR vs `phase2-best`
- the closest “near-flat” overlays use `cap_weight=0.95`, not `0.90`

Examples with smaller drag vs `phase2-best`:
- `0.95 / 130 / 123`: CAGR delta **-0.0011**, MDD delta **+0.0029**, OOS retention **0.7059**
- `0.95 / 129 / 123`: CAGR delta **-0.0014**, MDD delta **+0.0040**, OOS retention **0.7047**
- `0.95 / 127 / 123`: CAGR delta **-0.0019**, MDD delta **+0.0042**, OOS retention **0.7062**

Interpretation:
- If an overlay must exist, the repo-local evidence favors a **lighter `0.95` cap family** as the safer final discussion set.
- The currently selected `0.90` cap family is tuned for maximum drawdown relief, not for preserving the core’s edge.

### Separate upgrade search already warns that tiny gains disappear under OOS scrutiny

From `experiments/upgrade/upgrade_summary.json`:
- strict candidates: **2**
- strict OOS candidates: **0**
- best strict candidate improves after-tax CAGR by only **+0.00036** and pretax MDD by only **+0.000005**, but still fails OOS

Interpretation:
- The repo’s own broader search already says “small apparent improvements are fragile.”
- That makes the overlay comparator mismatch even more important.

## 3) Safe final-improvement opportunities that preserve anti-overfit constraints

These are safe because they do **not** widen the parameter search or add new knobs.

### Opportunity A — change the overlay promotion gate

When judging overlays added to `phase2-best`, require comparison against `phase2-best`, not the original baseline.

Recommended gate:
- compare `delta_aftertax_cagr_vs_phase2`
- compare `delta_pretax_mdd_vs_phase2`
- keep `oos_pass`
- explicitly label results as either:
  - **strict improve**, or
  - **intentional risk trade-off**

### Opportunity B — if an overlay is mandatory, prefer the lighter 0.95-cap candidates

Repo-local evidence suggests the current selected `0.90` cap is too heavy if the goal is “final promotion” rather than “maximum risk trim.”

Best discussion set from current artifacts:
- `0.95 / 129 / 123`
- `0.95 / 130 / 123`
- `0.95 / 127 / 123`

These are still not strict winners over `phase2-best`, but they preserve far more of the core’s CAGR while still improving MDD modestly.

### Opportunity C — simplest anti-overfit choice: promote the core alone

The most conservative final move is:
- promote `phase2-best`
- keep `soft_overheat_buffer` disabled until a phase2-relative selection rule exists

This is the cleanest option if the team wants to minimize last-mile optimization risk.

## Final recommendation

**Decision category: tune slightly.**

### Recommended final action

- **Promote `phase2-best` core readiness now**.
- **Do not ship the currently selected `soft_overheat_buffer` unchanged**.
- Before final combo promotion, either:
  1. **disable the overlay** and ship the core alone, or
  2. **reselect the overlay with a `vs_phase2` gate**, using the lighter `0.95` family only if the team explicitly wants a small CAGR-for-drawdown trade.

### Why this is the right category

- **Not keep as-is:** current adopted overlay choice is justified against the wrong comparator.
- **Not reject entirely:** the core itself has strong repo-local robustness evidence and clears the OOS bar.
- **Tune slightly:** the needed correction is narrow, local, and anti-overfit-aligned.

## Decision taken after review

The follow-up decision is to proceed with the tuned overlay variant:

- `phase2-best` core
- `soft_overheat_buffer(enter=129, exit=123, cap=0.90, min_risk_weight=0.95)`

Why this was chosen:
- keeps the same overlay structure and hysteresis
- reduces active intervention days versus `126 / 123 / 0.90`
- preserves the repo-local OOS pass
- gives back part of the CAGR drag while still keeping a drawdown-softening role
