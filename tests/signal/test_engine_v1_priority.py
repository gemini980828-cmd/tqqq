from tqqq_strategy.signal.engine_v1 import decide_code
from tqqq_strategy.signal.params import CODE_CASH, CODE_FULL, OVERHEAT_NONE


def test_vol_lock_has_highest_priority() -> None:
    code = decide_code(
        locked=True,
        spy_force_cash=False,
        reentry_blocked=False,
        base_code=CODE_FULL,
        overheat_stage=OVERHEAT_NONE,
    )
    assert code == CODE_CASH
