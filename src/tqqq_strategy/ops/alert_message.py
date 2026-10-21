"""Render the daily Telegram alert (classic layout, HTML parse mode). Pure; wording lives here and in order_plan.render_*."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date

from tqqq_strategy.ops.alert_triggers import TriggerReport, fmt_num, fmt_signed_pct
from tqqq_strategy.ops.order_plan import (
    Alloc,
    OrderPlan,
    Trade,
    format_fraction,
    render_action,
)

MAX_MESSAGE_CHARS = 3500
TECH_SEPARATOR = "──────────"


@dataclass(frozen=True)
class AlertContext:
    date_str: str  # signal date, YYYY-MM-DD (US session that just closed)
    strategy_name: str
    p_now: float  # raw signal weight today
    new_alloc: Alloc  # (TQQQ, SGOV, GLD)
    plan: OrderPlan
    triggers: TriggerReport
    tqqq_close: float
    tqqq_day_pct: float
    entry_date: str | None = None  # start of the current p>0 run
    entry_close: float | None = None
    cash_since: str | None = None  # start of the current p=0 run
    fx_now: float | None = None
    fx_pct: float | None = None
    prev_p: float | None = None  # raw signal weight on the previous session
    prev_code: str | None = None
    new_code: str | None = None


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def _md(date_str: str) -> str:
    d = date.fromisoformat(date_str[:10])
    return f"{d.month}/{d.day}"


def _usd(value: float) -> str:
    return f"${value:,.2f}"


def _emoji_from_sign(value: float) -> str:
    if value > 0:
        return "🟢"
    if value < 0:
        return "🔴"
    return "⚪"


def _alloc_text(alloc: Alloc) -> str:
    tqqq, sgov, gld = alloc
    return f"TQQQ {tqqq * 100:.2f}% / SGOV {sgov * 100:.2f}% / GLD {gld * 100:.2f}%"


def _invested(ctx: AlertContext) -> bool:
    return ctx.p_now > 1e-9


def _judgment(ctx: AlertContext) -> tuple[str, str]:
    trade = ctx.plan.trade
    if trade is not None:
        if trade.kind == "buy":
            return "🟢", "매수"
        if trade.kind == "exit":
            return "🔴", "전량 매도"
        return "🟠", "일부 감량"
    if ctx.plan.contribution is not None:
        return "💵", "적립 집행"
    if ctx.plan.gold_rebalance is not None:
        return "🔁", "금 리밸런싱"
    if _invested(ctx):
        return "⚪", "유지"
    return "⚪", "현금 대기"


def _trade_summary(trade: Trade) -> str:
    move = f"신호 비중이 {format_fraction(trade.prev_p)}% → {format_fraction(trade.new_p)}%로 바뀌어 "
    if trade.kind == "buy":
        source = "SGOV 전량을" if trade.full else "SGOV 일부를"
        return move + f"{source} TQQQ로 옮깁니다."
    if trade.kind == "exit":
        return move + "TQQQ를 전량 매도하고 SGOV로 옮깁니다."
    return move + "TQQQ 일부를 SGOV로 옮깁니다."


def _summary(ctx: AlertContext) -> str:
    if ctx.plan.trade is not None:
        return _trade_summary(ctx.plan.trade)
    facts = ctx.triggers.facts
    clause = facts.summary_clause if facts is not None else None
    if _invested(ctx):
        if ctx.entry_date and ctx.entry_close:
            pnl = (ctx.tqqq_close / ctx.entry_close - 1.0) * 100.0
            text = f"{_md(ctx.entry_date)} 진입 후 보유 중 (평가손익 {fmt_signed_pct(pnl)})."
        else:
            text = "보유 중."
    else:
        text = (
            f"{_md(ctx.cash_since)} 매도 후 SGOV 대기 중."
            if ctx.cash_since
            else "SGOV 대기 중."
        )
    return f"{text} {clause}" if clause else text


def _market_lines(ctx: AlertContext) -> list[str]:
    lines = [
        "📊 오늘 시장",
        f"- TQQQ 종가: {_usd(ctx.tqqq_close)} ({_emoji_from_sign(ctx.tqqq_day_pct)} {fmt_signed_pct(ctx.tqqq_day_pct, 2)})",
    ]
    if ctx.fx_now is not None:
        fx = f"- 원/달러 환율: {ctx.fx_now:,.2f}"
        if ctx.fx_pct is not None:
            fx += f" ({fmt_signed_pct(ctx.fx_pct, 2)})"
        lines.append(fx)
    return lines


def _entry_line(ctx: AlertContext) -> str | None:
    if not (ctx.entry_date and ctx.entry_close):
        return None
    text = f"- 진입: {_md(ctx.entry_date)} · {_usd(ctx.entry_close)}"
    facts = ctx.triggers.facts
    if (
        facts is not None
        and facts.stop_price is not None
        and facts.stop_pct is not None
    ):
        text += f" · 손절선 {_usd(facts.stop_price)} ({fmt_signed_pct(facts.stop_pct)})"
    return text


def _invested_tech_lines(ctx: AlertContext) -> list[str]:
    facts = ctx.triggers.facts
    lines: list[str] = []
    entry = _entry_line(ctx)
    if entry:
        lines.append(entry)
    if facts is None:
        return [*lines, *[f"- {line}" for line in ctx.triggers.detail_lines]]
    if (
        facts.dist200 is not None
        and facts.sell_line is not None
        and facts.sell_line_pct is not None
    ):
        label = "100% 진입선" if facts.qqq_cross_pct is not None else "매도선"
        lines.append(
            f"- 200일선 이격도: {facts.dist200:.2f} ({label} {fmt_num(facts.sell_line)}, {fmt_signed_pct(facts.sell_line_pct)})"
        )
    if facts.qqq_cross_pct is not None:
        lines.append(
            f"- QQQ 3일선/161일선: 3일선이 아래로 내려가면 전량 매도 (QQQ {fmt_signed_pct(facts.qqq_cross_pct)})"
        )
    if facts.spy_dist is not None:
        spy = f"- SPY 200일선: {facts.spy_dist:.2f}"
        if facts.spy_sell_line is not None and facts.spy_sell_pct is not None:
            spy += f" (매도선 {fmt_num(facts.spy_sell_line)}, {fmt_signed_pct(facts.spy_sell_pct)})"
        lines.append(spy)
    if facts.v20_pct is not None and facts.vol_limit_pct is not None:
        lines.append(
            f"- 20일 변동성: {facts.v20_pct:.2f}% (한도 {facts.vol_limit_pct:.2f}%)"
        )
    if facts.overheat_enter is not None and facts.overheat_pct is not None:
        lines.append(
            f"- 과열 감량 시작: {fmt_num(facts.overheat_enter)} ({fmt_signed_pct(facts.overheat_pct)})"
        )
    if facts.tp_price is not None and facts.tp_pct is not None:
        lines.append(
            f"- 익절 감량: {_usd(facts.tp_price)} ({fmt_signed_pct(facts.tp_pct)})"
        )
    return lines


def _cash_tech_lines(ctx: AlertContext) -> list[str]:
    # ✓/✗ condition lines already carry a marker; a "- " bullet in front would double it
    detail = [
        line if line[:1] in "✓✗" else f"- {line}" for line in ctx.triggers.detail_lines
    ]
    if ctx.triggers.facts is None or not detail:
        return detail
    return ["매수까지 남은 조건", *detail]


def _tech_lines(ctx: AlertContext) -> list[str]:
    prev_p = ctx.prev_p
    if prev_p is None:
        prev_p = ctx.plan.trade.prev_p if ctx.plan.trade is not None else ctx.p_now
    lines = [
        "기술리포트",
        f"- 신호 비중 p: {prev_p * 100:.2f}% → {ctx.p_now * 100:.2f}%",
    ]
    lines += _invested_tech_lines(ctx) if _invested(ctx) else _cash_tech_lines(ctx)
    if ctx.prev_code is not None and ctx.new_code is not None:
        lines.append(f"- signal code: {ctx.prev_code} → {ctx.new_code}")
    return lines


def build_alert_message(ctx: AlertContext) -> str:
    emoji, judgment = _judgment(ctx)
    action = render_action(ctx.plan) or ["🛒 실행 액션: 오늘은 주문 없음"]
    head = [
        f"[ {ctx.date_str[:10]} ] 코어전략 운영브리프",
        "",
        f"전략: {ctx.strategy_name}",
        "",
        f"{emoji} 오늘 판단: {judgment}",
        f"목표 비중: {_alloc_text(ctx.new_alloc)}",
        "",
        *action,
        "",
        "요약:",
        _summary(ctx),
        "",
        *_market_lines(ctx),
    ]
    full = "\n".join([*head, "", TECH_SEPARATOR, *_tech_lines(ctx)])
    if len(full) > MAX_MESSAGE_CHARS:
        full = "\n".join(
            head
        )  # drop the technical report rather than exceed Telegram's 4096 limit
    return esc(full)
