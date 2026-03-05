"""Minimal priority decision logic for signal engine v1."""

from tqqq_strategy.signal.params import (
    CODE_CASH,
    CODE_FULL,
    CODE_REDUCE_1,
    CODE_REDUCE_2,
    CODE_REDUCE_3,
    OVERHEAT_STAGE_1,
    OVERHEAT_STAGE_2,
    OVERHEAT_STAGE_3,
    OVERHEAT_STAGE_4,
)


def decide_code(
    *,
    locked: bool,
    spy_force_cash: bool,
    reentry_blocked: bool,
    base_code: int,
    overheat_stage: int,
) -> int:
    """Return final action code with simple priority overrides."""
    if locked or spy_force_cash or reentry_blocked:
        return CODE_CASH
    if overheat_stage == OVERHEAT_STAGE_4:
        return CODE_CASH
    if overheat_stage == OVERHEAT_STAGE_3 and base_code != CODE_CASH:
        return CODE_REDUCE_3
    if overheat_stage == OVERHEAT_STAGE_2 and base_code == CODE_FULL:
        return CODE_REDUCE_2
    if overheat_stage == OVERHEAT_STAGE_1 and base_code == CODE_FULL:
        return CODE_REDUCE_1
    return base_code
