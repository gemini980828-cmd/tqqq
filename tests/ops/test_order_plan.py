from __future__ import annotations

import pytest

from tqqq_strategy.ops.order_plan import (
    is_contribution_day,
    is_first_session_of_year,
    plan_orders,
    render_action,
    split_contribution_manwon,
)

CONTRIBUTION_KRW = 1_670_000


def alloc(p: float) -> tuple[float, float, float]:
    return round(0.9 * p, 10), round(0.9 * (1.0 - p), 10), 0.1


EXEC = "오늘 밤 미국장 시가"
# (id, prev p, new p, trade lines w/o contribution, contribution legs at the new target)
CASES = [
    ("hold", 0.97, 0.97, None, "TQQQ 146만원 / SGOV 4만원 / GLD 17만원"),
    ("cash", 0.0, 0.0, None, "SGOV 150만원 / GLD 17만원"),
    (
        "buy_full",
        0.0,
        1.0,
        ["- SGOV: 전량 매도", "- TQQQ: SGOV 매도대금 전액으로 매수"],
        "TQQQ 150만원 / GLD 17만원",
    ),
    (
        "buy_tenth",
        0.0,
        0.1,
        ["- SGOV: 보유수량의 10% 매도", "- TQQQ: SGOV 매도대금 전액으로 매수"],
        "TQQQ 15만원 / SGOV 135만원 / GLD 17만원",
    ),
    (
        "buy_partial",
        0.05,
        0.9,
        ["- SGOV: 보유수량의 89.5% 매도", "- TQQQ: SGOV 매도대금 전액으로 매수"],
        "TQQQ 135만원 / SGOV 15만원 / GLD 17만원",
    ),
    (
        "trim",
        1.0,
        0.97,
        ["- TQQQ: 보유수량의 3% 매도", "- SGOV: TQQQ 매도대금 전액으로 매수"],
        "TQQQ 146만원 / SGOV 4만원 / GLD 17만원",
    ),
    (
        "exit",
        0.97,
        0.0,
        ["- TQQQ: 전량 매도", "- SGOV: TQQQ 매도대금 전액으로 매수"],
        "SGOV 150만원 / GLD 17만원",
    ),
]
GOLD_LINE = (
    "🔁 연 1회 금 리밸런싱일: GLD를 전체 자산의 10%로 맞추세요 (연초 첫 거래일)."
)


def _expected(trade_lines, legs, *, contribution: bool, gold: bool):
    """Full action lines per the message spec, or None when nothing is to be done."""
    if trade_lines is not None:
        lines = [f"🛒 실행 액션 ({EXEC})", *trade_lines, "- GLD: 유지"]
    elif contribution or gold:
        lines = ["🛒 실행 액션: 기존 보유분 매매 없음"]
    else:
        return None
    if contribution:
        lines += ["", f"💵 이번 달 적립 (167만원, {EXEC})", f"- {legs}"]
    if gold:
        lines += ["", GOLD_LINE]
    return lines


@pytest.mark.parametrize("gold", [False, True], ids=["nogold", "gold"])
@pytest.mark.parametrize("contribution", [False, True], ids=["nocontrib", "contrib"])
@pytest.mark.parametrize(
    ("case_id", "prev_p", "new_p", "trade_lines", "legs"),
    CASES,
    ids=[c[0] for c in CASES],
)
def test_plan_orders_renders_expected_lines(
    case_id, prev_p, new_p, trade_lines, legs, contribution, gold
) -> None:
    plan = plan_orders(
        alloc(prev_p),
        alloc(new_p),
        contribution_krw=CONTRIBUTION_KRW if contribution else None,
        is_contribution_day=contribution,
        is_first_session_of_year=gold,
    )

    assert render_action(plan) == _expected(
        trade_lines, legs, contribution=contribution, gold=gold
    )


def test_contribution_amount_without_session_day_has_no_line() -> None:
    plan = plan_orders(
        alloc(0.97),
        alloc(0.97),
        contribution_krw=CONTRIBUTION_KRW,
        is_contribution_day=False,
        is_first_session_of_year=False,
    )
    assert plan.contribution is None
    assert render_action(plan) is None


def test_contribution_day_without_amount_has_no_line() -> None:
    plan = plan_orders(
        alloc(0.97),
        alloc(0.97),
        contribution_krw=None,
        is_contribution_day=True,
        is_first_session_of_year=False,
    )
    assert plan.contribution is None
    assert render_action(plan) is None


def test_sell_fraction_full_boundary_at_0_9995() -> None:
    # p 1.0 -> 0.00049 : fraction 0.99951 -> exit ("전량"); 0.00051 -> 0.99949 -> trim "99.9%"
    exit_plan = plan_orders(
        alloc(1.0),
        alloc(0.00049),
        contribution_krw=None,
        is_contribution_day=False,
        is_first_session_of_year=False,
    )
    trim_plan = plan_orders(
        alloc(1.0),
        alloc(0.00051),
        contribution_krw=None,
        is_contribution_day=False,
        is_first_session_of_year=False,
    )

    assert (
        exit_plan.trade is not None
        and exit_plan.trade.full
        and exit_plan.trade.kind == "exit"
    )
    assert (
        trim_plan.trade is not None
        and not trim_plan.trade.full
        and trim_plan.trade.kind == "trim"
    )
    assert render_action(exit_plan) == [
        f"🛒 실행 액션 ({EXEC})",
        "- TQQQ: 전량 매도",
        "- SGOV: TQQQ 매도대금 전액으로 매수",
        "- GLD: 유지",
    ]
    assert render_action(trim_plan) == [
        f"🛒 실행 액션 ({EXEC})",
        "- TQQQ: 보유수량의 99.9% 매도",
        "- SGOV: TQQQ 매도대금 전액으로 매수",
        "- GLD: 유지",
    ]


def test_trade_keeps_sell_fraction_and_proceeds_source() -> None:
    buy = plan_orders(
        alloc(0.05),
        alloc(0.9),
        contribution_krw=None,
        is_contribution_day=False,
        is_first_session_of_year=False,
    ).trade
    sell = plan_orders(
        alloc(1.0),
        alloc(0.97),
        contribution_krw=None,
        is_contribution_day=False,
        is_first_session_of_year=False,
    ).trade

    assert buy is not None and (buy.sell_asset, buy.proceeds_to) == ("SGOV", "TQQQ")
    assert buy.sell_fraction == pytest.approx(1 - 0.1 / 0.95)
    assert sell is not None and (sell.sell_asset, sell.proceeds_to) == ("TQQQ", "SGOV")
    assert sell.sell_fraction == pytest.approx(0.03)


def test_contribution_keeps_raw_amount_and_gold_target() -> None:
    plan = plan_orders(
        alloc(0.97),
        alloc(0.97),
        contribution_krw=1_674_321,
        is_contribution_day=True,
        is_first_session_of_year=True,
    )

    assert plan.contribution is not None
    assert plan.contribution.raw_krw == 1_674_321
    assert plan.contribution.new_money_krw == 1_674_321
    assert plan.contribution.total_manwon == 167
    assert plan.gold_rebalance is not None and plan.gold_rebalance.target == 0.10


@pytest.mark.parametrize(
    ("weights", "expected"),
    [
        ((0.873, 0.027, 0.1), (146, 4, 17)),
        ((0.0, 0.9, 0.1), (0, 150, 17)),
        ((0.09, 0.81, 0.1), (15, 135, 17)),
    ],
)
def test_split_contribution_manwon_largest_remainder(weights, expected) -> None:
    result = split_contribution_manwon(1_670_000, weights)

    assert result == expected
    assert sum(result) == 167


@pytest.mark.parametrize("amount", [500_000, 1_234_567, 3_000_000, 10_000])
@pytest.mark.parametrize("p", [0.0, 0.05, 0.1, 0.8, 0.9, 0.97, 1.0])
def test_split_contribution_manwon_always_sums_to_total(amount, p) -> None:
    result = split_contribution_manwon(amount, alloc(p))

    assert sum(result) == round(amount / 10_000)
    assert all(v >= 0 for v in result)


@pytest.mark.parametrize(
    ("prev", "today", "day", "expected"),
    [
        (
            "2026-07-24",
            "2026-07-27",
            25,
            True,
        ),  # 25th fell on a weekend: first session after it
        ("2026-07-27", "2026-07-28", 25, False),
        ("2026-08-24", "2026-08-25", 25, True),
        ("2026-08-25", "2026-08-26", 25, False),
        (
            "2026-02-26",
            "2026-03-02",
            31,
            True,
        ),  # day clamps to Feb 28 / then Mar 31 not yet
        ("2026-03-02", "2026-03-03", 31, False),
        ("2026-04-29", "2026-04-30", 31, True),  # April has 30 days -> 30th
        (
            "2026-01-02",
            "2026-01-05",
            1,
            False,
        ),  # Jan 1 holiday was already covered by the Jan 2 session
        ("2025-12-31", "2026-01-02", 1, True),
    ],
)
def test_is_contribution_day(prev, today, day, expected) -> None:
    assert is_contribution_day(prev, today, day) is expected


def test_is_first_session_of_year() -> None:
    assert is_first_session_of_year("2025-12-31", "2026-01-02") is True
    assert is_first_session_of_year("2026-03-05", "2026-03-06") is False
