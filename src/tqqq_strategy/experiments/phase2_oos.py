from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class OOSResult:
    is_score: float
    oos_score: float
    retention: float
    passed: bool


def split_is_oos(df: pd.DataFrame, oos_ratio: float = 0.3) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = len(df)
    cut = max(1, min(n - 1, int(n * (1 - oos_ratio))))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


def cagr_from_equity(eq: pd.Series) -> float:
    years = len(eq) / 252
    if years <= 0 or eq.iloc[0] <= 0:
        return 0.0
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1)


def passes_oos_retention(is_score: float, oos_score: float, threshold: float = 0.70) -> OOSResult:
    if is_score <= 0:
        return OOSResult(is_score=is_score, oos_score=oos_score, retention=0.0, passed=False)
    ratio = oos_score / is_score
    return OOSResult(is_score=is_score, oos_score=oos_score, retention=ratio, passed=ratio >= threshold)
