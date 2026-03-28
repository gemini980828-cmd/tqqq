from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from tqqq_strategy.experiments.phase2_config import Phase2Params

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PHASE2_BEST_CONFIG_PATH = PROJECT_ROOT / "experiments/best_config.json"
FINAL_RUNTIME_SIGNAL_PATH = Path("reports/signals_core_strategy_final.csv")


@dataclass(frozen=True)
class SoftOverheatOverlay:
    enter_dist: float
    exit_dist: float
    cap_weight: float
    min_risk_weight: float = 0.95

    def validate(self) -> None:
        if self.enter_dist <= self.exit_dist:
            raise ValueError("enter_dist must be > exit_dist")
        if not (0.0 <= self.cap_weight <= 1.0):
            raise ValueError("cap_weight must be within [0, 1]")
        if self.cap_weight > self.min_risk_weight:
            raise ValueError("cap_weight must be <= min_risk_weight")


def apply_soft_overheat_buffer(
    base_weight: pd.Series,
    dist200: pd.Series,
    overlay: SoftOverheatOverlay,
) -> pd.Series:
    overlay.validate()

    adjusted = base_weight.astype(float).copy()
    hot = False

    for i in range(len(adjusted)):
        dist = dist200.iloc[i]
        current = float(adjusted.iloc[i])
        base = float(base_weight.iloc[i])

        if pd.isna(dist):
            continue

        if (not hot) and base >= overlay.min_risk_weight and dist >= overlay.enter_dist:
            hot = True
        elif hot and dist <= overlay.exit_dist:
            hot = False

        if hot and current > overlay.cap_weight:
            adjusted.iloc[i] = overlay.cap_weight

    return adjusted


DEFAULT_FINAL_OVERLAY = SoftOverheatOverlay(
    enter_dist=129.0,
    exit_dist=123.0,
    cap_weight=0.90,
    min_risk_weight=0.95,
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_phase2_best_params(best_config_path: Path | str = DEFAULT_PHASE2_BEST_CONFIG_PATH) -> Phase2Params:
    best = json.loads(Path(best_config_path).read_text(encoding="utf-8"))
    return Phase2Params(**json.loads(best["params_json"]))


def build_final_signal_frame(
    *,
    time: pd.Series | pd.Index,
    base_weight: pd.Series,
    dist200: pd.Series,
    overlay: SoftOverheatOverlay = DEFAULT_FINAL_OVERLAY,
) -> pd.DataFrame:
    adjusted = apply_soft_overheat_buffer(base_weight, dist200, overlay)
    reference_mod = _load_module(PROJECT_ROOT / "ops/scripts/user_original_reference.py", "user_original_reference_final_frame")
    codes = adjusted.map(reference_mod.weight_to_code).astype(int)
    buffer_active = (adjusted < base_weight).astype(bool)

    return pd.DataFrame(
        {
            "time": pd.to_datetime(pd.Series(time)),
            "S2_code": codes,
            "S2_weight": adjusted.astype(float),
            "base_weight": base_weight.astype(float),
            "buffer_active": buffer_active,
            "dist200": dist200.astype(float),
        }
    )


def compute_final_signal_table(
    data: pd.DataFrame,
    *,
    best_config_path: Path | str = DEFAULT_PHASE2_BEST_CONFIG_PATH,
    overlay: SoftOverheatOverlay = DEFAULT_FINAL_OVERLAY,
) -> pd.DataFrame:
    reference_mod = _load_module(PROJECT_ROOT / "ops/scripts/user_original_reference.py", "user_original_reference_final_signal")
    params = load_phase2_best_params(best_config_path)
    basic_params = reference_mod.BasicParams(
        vol_threshold=params.vol_threshold,
        dist200_enter=params.dist200_enter,
        dist200_exit=params.dist200_exit,
        slope_thr=params.slope_thr,
        tp10_trigger=params.tp10_trigger,
        tp10_cap=params.tp10_cap,
        overheat1_enter=params.overheat1_enter,
        overheat2_enter=params.overheat2_enter,
        overheat3_enter=params.overheat3_enter,
        overheat4_enter=params.overheat4_enter,
        spy_bear_cap=0.0,
    )

    working = data.copy()
    reference_mod.ensure_sma(working, "QQQ종가", 3, "QQQ3일선")
    reference_mod.ensure_sma(working, "QQQ종가", 161, "QQQ161일선")
    reference_mod.ensure_sma(working, "TQQQ종가", 200, "TQQQ200일선")
    if "SPY200일선" not in working.columns:
        reference_mod.ensure_sma(working, "SPY종가", 200, "SPY200일선")

    time = working["time"].to_numpy()
    q_close = working["QQQ종가"].to_numpy()
    q_ma3 = working["QQQ3일선"].to_numpy()
    q_ma161 = working["QQQ161일선"].to_numpy()
    t_close = working["TQQQ종가"].to_numpy()
    t_ma200 = working["TQQQ200일선"].to_numpy()
    spy_close = working["SPY종가"].to_numpy()
    spy_ma200 = working["SPY200일선"].to_numpy()

    _codes, weights = reference_mod.compute_basic_strategy(
        time,
        q_close,
        q_ma3,
        q_ma161,
        t_close,
        t_ma200,
        spy_close,
        spy_ma200,
        basic_params,
    )

    base_weight = pd.Series(weights, index=working.index, dtype=float)
    dist200 = (pd.Series(t_close, index=working.index, dtype=float) / pd.Series(t_ma200, index=working.index, dtype=float)) * 100.0
    result = build_final_signal_frame(
        time=working["time"],
        base_weight=base_weight,
        dist200=dist200,
        overlay=overlay,
    )
    result["engine_version"] = "core-strategy/final-v1"
    result["phase2_params_json"] = json.dumps(params.__dict__, ensure_ascii=False, sort_keys=True)
    result["overlay_json"] = json.dumps(
        {
            "enter_dist": overlay.enter_dist,
            "exit_dist": overlay.exit_dist,
            "cap_weight": overlay.cap_weight,
            "min_risk_weight": overlay.min_risk_weight,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return result
