"""Turn a target-allocation change into a human order plan (pure functions; no I/O).

The plan is expressed as FRACTIONS, not share counts, because the repo has no holdings source:
- `Trade.sell_fraction`: share of the SOURCE position to sell (SGOV when buying TQQQ, TQQQ when trimming/exiting),
  proceeds go to `Trade.proceeds_to`.
- `ContributionPlan.raw_krw`: the configured monthly new money, untouched; `legs` is its 만원 split at the NEW target.
- `GoldRebalance.target`: yearly GLD rebalance target weight.

Contract for a future holdings source (e.g. a broker balance API): multiply `sell_fraction` by the held share
count of the source asset, and `raw_krw` by the FX rate, to get exact order sizes. Nothing in here fetches or
assumes holdings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from tqqq_strategy.signal.final_engine import CORE_SHARE, GLD_FIXED_WEIGHT

Alloc = tuple[float, float, float]  # (TQQQ, SGOV, GLD) portfolio weights
ASSETS = ("TQQQ", "SGOV", "GLD")
FULL_FRACTION = 0.9995  # sell_fraction at/above this is shown as "전량"
EXEC_WHEN = "오늘 밤 미국장 시가"  # alert arrives after the US close; orders go in at the next US open
MANWON = 10_000


@dataclass(frozen=True)
class Trade:
    kind: Literal["buy", "trim", "exit"]
    sell_asset: Literal["SGOV", "TQQQ"]
    proceeds_to: Literal["TQQQ", "SGOV"]
    sell_fraction: float
    prev_p: float
    new_p: float

    @property
    def full(self) -> bool:
        return self.sell_fraction >= FULL_FRACTION


@dataclass(frozen=True)
class ContributionPlan:
    raw_krw: int  # configured amount, as given
    total_manwon: int  # raw_krw rounded to 만원
    legs: tuple[
        tuple[str, int], ...
    ]  # (asset, 만원) at the new target; zero legs dropped

    @property
    def new_money_krw(self) -> int:
        return self.raw_krw


@dataclass(frozen=True)
class GoldRebalance:
    target: float = GLD_FIXED_WEIGHT


@dataclass(frozen=True)
class OrderPlan:
    trade: Trade | None
    contribution: ContributionPlan | None
    gold_rebalance: GoldRebalance | None

    @property
    def has_action(self) -> bool:
        return (
            self.trade is not None
            or self.contribution is not None
            or self.gold_rebalance is not None
        )


def signal_p(alloc: Alloc) -> float:
    """Raw signal weight p from the TQQQ allocation (TQQQ = 0.90 * p)."""
    return min(max(alloc[0] / CORE_SHARE, 0.0), 1.0)


def split_contribution_manwon(amount_krw: int, weights: Alloc) -> tuple[int, ...]:
    """Split `amount_krw` (rounded to 만원) across `weights` with largest-remainder rounding."""
    total = round(amount_krw / MANWON)
    raw = [total * w for w in weights]
    floors = [int(x // 1) for x in raw]
    remainders = [(-(x - f), idx) for idx, (x, f) in enumerate(zip(raw, floors))]
    missing = total - sum(floors)
    result = list(floors)
    for _neg_rem, idx in sorted(remainders)[: max(missing, 0)]:
        result[idx] += 1
    return tuple(result)


def _as_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _month_target(year: int, month: int, day: int) -> date:
    if month == 12:
        dim = 31
    else:
        dim = (date(year, month + 1, 1) - date(year, month, 1)).days
    return date(year, month, min(day, dim))


def is_contribution_day(prev_date: str | date, today: str | date, day: int) -> bool:
    """True if the contribution day-of-month fell in (prev_date, today] (this or previous month)."""
    prev_d = _as_date(prev_date)
    today_d = _as_date(today)
    prev_month = (
        (today_d.year, today_d.month - 1)
        if today_d.month > 1
        else (today_d.year - 1, 12)
    )
    for year, month in (prev_month, (today_d.year, today_d.month)):
        target = _month_target(year, month, day)
        if prev_d < target <= today_d:
            return True
    return False


def is_first_session_of_year(prev_date: str | date, today: str | date) -> bool:
    return _as_date(prev_date).year != _as_date(today).year


def _plan_trade(prev_alloc: Alloc, new_alloc: Alloc) -> Trade | None:
    p_prev = signal_p(prev_alloc)
    p_new = signal_p(new_alloc)
    if abs(p_new - p_prev) < 1e-6:
        return None
    if p_new > p_prev:
        fraction = 1.0 - (1.0 - p_new) / (1.0 - p_prev) if p_prev < 1.0 else 0.0
        return Trade("buy", "SGOV", "TQQQ", fraction, p_prev, p_new)
    fraction = 1.0 - p_new / p_prev
    kind: Literal["trim", "exit"] = "exit" if fraction >= FULL_FRACTION else "trim"
    return Trade(kind, "TQQQ", "SGOV", fraction, p_prev, p_new)


def plan_orders(
    prev_alloc: Alloc,
    new_alloc: Alloc,
    *,
    contribution_krw: int | None,
    is_contribution_day: bool,
    is_first_session_of_year: bool,
) -> OrderPlan:
    trade = _plan_trade(prev_alloc, new_alloc)

    contribution: ContributionPlan | None = None
    if contribution_krw is not None and contribution_krw > 0 and is_contribution_day:
        manwon = split_contribution_manwon(contribution_krw, new_alloc)
        legs = tuple(
            (asset, amount) for asset, amount in zip(ASSETS, manwon) if amount > 0
        )
        contribution = ContributionPlan(int(contribution_krw), sum(manwon), legs)

    gold = GoldRebalance() if is_first_session_of_year else None
    return OrderPlan(trade=trade, contribution=contribution, gold_rebalance=gold)


# ---------------------------------------------------------------- rendering (all wording lives here)


def format_fraction(fraction: float) -> str:
    """Percent with one decimal, '.0' stripped: 0.03 -> '3', 0.8947 -> '89.5'."""
    text = f"{fraction * 100:.1f}"
    return text.removesuffix(".0")


def render_trade_lines(trade: Trade) -> list[str]:
    """Per-asset order bullets, sells first."""
    sold = (
        "전량 매도"
        if trade.full
        else f"보유수량의 {format_fraction(trade.sell_fraction)}% 매도"
    )
    bought = f"{trade.sell_asset} 매도대금 전액으로 매수"
    return [
        f"- {trade.sell_asset}: {sold}",
        f"- {trade.proceeds_to}: {bought}",
        "- GLD: 유지",
    ]


def render_contribution_lines(contribution: ContributionPlan) -> list[str]:
    legs = " / ".join(f"{asset} {amount}만원" for asset, amount in contribution.legs)
    return [
        f"💵 이번 달 적립 ({contribution.total_manwon}만원, {EXEC_WHEN})",
        f"- {legs}",
    ]


def render_gold_line(gold: GoldRebalance) -> str:
    return f"🔁 연 1회 금 리밸런싱일: GLD를 전체 자산의 {format_fraction(gold.target)}%로 맞추세요 (연초 첫 거래일)."


def render_action(plan: OrderPlan) -> list[str] | None:
    """Lines of the action sections (blank lines between sections), or None when there is nothing to do."""
    if not plan.has_action:
        return None
    lines: list[str] = []
    if plan.trade is not None:
        lines += [f"🛒 실행 액션 ({EXEC_WHEN})", *render_trade_lines(plan.trade)]
    else:
        lines.append("🛒 실행 액션: 기존 보유분 매매 없음")
    if plan.contribution is not None:
        lines += ["", *render_contribution_lines(plan.contribution)]
    if plan.gold_rebalance is not None:
        lines += ["", render_gold_line(plan.gold_rebalance)]
    return lines
