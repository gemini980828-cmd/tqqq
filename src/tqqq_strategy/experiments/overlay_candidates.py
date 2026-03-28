from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


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


def slice_aligned_weight(weight: pd.Series, mask: pd.Series) -> pd.Series:
    return weight[mask.to_numpy()].reset_index(drop=True)
