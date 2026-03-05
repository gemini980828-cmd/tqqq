from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
from typing import Iterable


@dataclass(frozen=True)
class Phase2Params:
    vol_threshold: float
    dist200_enter: float
    dist200_exit: float
    slope_thr: float
    tp10_trigger: float
    tp10_cap: float
    overheat1_enter: float
    overheat2_enter: float
    overheat3_enter: float
    overheat4_enter: float


def validate_candidate(p: Phase2Params) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not (p.dist200_enter > p.dist200_exit):
        errs.append("dist200_enter must be > dist200_exit")
    if not (p.overheat1_enter < p.overheat2_enter < p.overheat3_enter < p.overheat4_enter):
        errs.append("overheat enters must be strictly increasing")
    if not (0.01 <= p.tp10_trigger <= 0.25):
        errs.append("tp10_trigger out of range")
    if not (0.80 <= p.tp10_cap <= 1.0):
        errs.append("tp10_cap out of range")
    if not (0.03 <= p.vol_threshold <= 0.10):
        errs.append("vol_threshold out of range")
    return len(errs) == 0, errs


def coarse_grid() -> list[Phase2Params]:
    out: list[Phase2Params] = []
    for vals in product(
        [0.058, 0.060],
        [100.8, 101.2],
        [99.8, 100.0],
        [0.10, 0.12],
        [0.09, 0.11],
        [0.94, 0.96],
        [139.0],
        [146.0],
        [149.0],
        [151.0],
    ):
        p = Phase2Params(*vals)
        ok, _ = validate_candidate(p)
        if ok:
            out.append(p)
    return out


def fine_grid(seeds: Iterable[Phase2Params]) -> list[Phase2Params]:
    out: list[Phase2Params] = []
    for s in seeds:
        for dv in [-0.001, 0.0, 0.001]:
            for ds in [-0.01, 0.0, 0.01]:
                p = Phase2Params(
                    vol_threshold=round(s.vol_threshold + dv, 4),
                    dist200_enter=round(s.dist200_enter + ds, 3),
                    dist200_exit=round(s.dist200_exit + ds, 3),
                    slope_thr=round(s.slope_thr + ds, 4),
                    tp10_trigger=round(s.tp10_trigger + ds, 3),
                    tp10_cap=round(s.tp10_cap - ds, 3),
                    overheat1_enter=s.overheat1_enter,
                    overheat2_enter=s.overheat2_enter,
                    overheat3_enter=s.overheat3_enter,
                    overheat4_enter=s.overheat4_enter,
                )
                ok, _ = validate_candidate(p)
                if ok:
                    out.append(p)
    uniq = {tuple(asdict(x).items()): x for x in out}
    return list(uniq.values())
