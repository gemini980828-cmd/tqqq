"""Render the daily Telegram alert (HTML parse mode). Pure; all wording lives here and in order_plan.render_*."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date

from tqqq_strategy.ops.alert_triggers import TriggerReport, fmt_num, fmt_signed_pct
from tqqq_strategy.ops.order_plan import Alloc, OrderPlan, render_action

MAX_MESSAGE_CHARS = 3500
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")


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


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def _md(date_str: str) -> str:
    d = date.fromisoformat(date_str[:10])
    return f"{d.month}/{d.day}"


def _date_line(date_str: str) -> str:
    d = date.fromisoformat(date_str[:10])
    return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]}) 미국장 마감 기준"


def _usd(value: float) -> str:
    return f"${value:,.2f}"


def _price_line(ctx: AlertContext) -> str:
    text = f"TQQQ {_usd(ctx.tqqq_close)} ({fmt_signed_pct(ctx.tqqq_day_pct)})"
    if ctx.triggers.headline:
        text += f" · {ctx.triggers.headline}"
    return text


def _visible_lines(ctx: AlertContext) -> list[str]:
    action = render_action(ctx.plan)
    if action is not None:
        header, body = action
        return [f"<b>{esc(header)}</b>", *[esc(line) for line in body]]
    if ctx.p_now > 1e-9:
        return ["<b>⚪ 보유 유지</b>", esc(_price_line(ctx))]
    second = ctx.triggers.headline or _price_line(ctx)
    return ["<b>⚪ 현금 대기 (SGOV)</b>", esc(second)]


def _alloc_text(alloc: Alloc) -> str:
    tqqq, sgov, gld = alloc
    return f"TQQQ {fmt_num(tqqq * 100, 1)}% · SGOV {fmt_num(sgov * 100, 1)}% · GLD {fmt_num(gld * 100, 1)}%"


def _detail_lines(ctx: AlertContext) -> list[str]:
    lines = [f"목표  {_alloc_text(ctx.new_alloc)}"]
    if ctx.p_now > 1e-9 and ctx.entry_date and ctx.entry_close:
        pnl = (ctx.tqqq_close / ctx.entry_close - 1.0) * 100.0
        lines.append(
            f"진입  {_md(ctx.entry_date)} · {_usd(ctx.entry_close)} · 평가손익 {fmt_signed_pct(pnl)}"
        )
    elif ctx.p_now <= 1e-9 and ctx.cash_since:
        lines.append(f"현금  {_md(ctx.cash_since)}부터")
    lines.extend(ctx.triggers.detail_lines)
    if ctx.fx_now is not None:
        fx = f"환율 {ctx.fx_now:,.1f}원"
        if ctx.fx_pct is not None:
            fx += f" ({fmt_signed_pct(ctx.fx_pct)})"
        lines.append(fx)
    lines.append(ctx.strategy_name)
    return lines


def build_alert_message(ctx: AlertContext) -> str:
    visible = [*_visible_lines(ctx), esc(_date_line(ctx.date_str))]
    details = "\n".join(["<b>상세</b>", *[esc(line) for line in _detail_lines(ctx)]])
    full = "\n".join(visible) + "\n<blockquote expandable>" + details + "</blockquote>"
    if len(full) > MAX_MESSAGE_CHARS:
        return "\n".join(visible)
    return full
