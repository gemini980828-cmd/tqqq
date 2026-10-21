"""Hybrid Telegram alert: action checklist + monospace gauge/bars + the classic technical report (HTML parse mode)."""

from __future__ import annotations

from datetime import date

from tqqq_strategy.ops.alert_message import (
    MAX_MESSAGE_CHARS,
    TECH_SEPARATOR,
    AlertContext,
    _emoji_from_sign,
    _invested,
    _md,
    _tech_lines,
    _usd,
    esc,
)
from tqqq_strategy.ops.alert_triggers import fmt_signed_pct
from tqqq_strategy.ops.order_plan import (
    ASSETS,
    EXEC_WHEN,
    Alloc,
    format_fraction,
)

WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")
GAUGE_CELLS = 22
BAR_CELLS = 10
PARTIAL_BLOCKS = "▏▎▍▌▋▊▉"
MARKER = "●"


def _weekday_md(date_str: str) -> str:
    d = date.fromisoformat(date_str[:10])
    return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"


def marker_index(left_pct: float, right_pct: float, cells: int = GAUGE_CELLS) -> int:
    """Cell of the current price between two trigger prices, proportional in price space, clamped.

    `left_pct` / `right_pct` are the signed % moves from the current close to the left / right trigger.
    """
    left = 1.0 + left_pct / 100.0
    right = 1.0 + right_pct / 100.0
    if right == left:
        return cells // 2
    frac = (1.0 - left) / (right - left)
    return min(max(round(frac * (cells - 1)), 0), cells - 1)


def render_bar(pct: float, cells: int = BAR_CELLS) -> str:
    """`cells` cells = 100%; the remainder is drawn with eighth blocks (floored). 0% -> empty."""
    eighths = int(pct / 100.0 * cells * 8 + 1e-9)
    full, rem = divmod(eighths, 8)
    return "█" * full + (PARTIAL_BLOCKS[rem - 1] if rem else "")


def _bar_lines(alloc: Alloc) -> list[str]:
    lines = []
    for name, weight in zip(ASSETS, alloc):
        pct = weight * 100.0
        if pct < 0.05:
            continue
        lines.append(f"{name:<4} {render_bar(pct):<{BAR_CELLS}} {pct:>3.0f}%")
    return lines


def _gauge(ctx: AlertContext) -> tuple[str, str] | None:
    """(caption, gauge line) or None when there is nothing to draw (triggers unavailable).

    Hangul inside <pre> does not occupy a predictable number of monospace cells on phones, so the
    gauge is a single line with Korean words only at its two ends and the numbers go in the caption.
    """
    facts = ctx.triggers.facts
    if facts is None or facts.gauge_pct is None:
        return None
    if _invested(ctx):
        left_pct = facts.gauge_pct
        if facts.overheat_pct is not None:
            right_pct, right_label = facts.overheat_pct, "과열 감량"
        elif facts.tp_pct is not None:
            right_pct, right_label = facts.tp_pct, "익절 감량"
        else:
            right_pct, right_label = abs(left_pct), ""
        cells = ["─"] * GAUGE_CELLS
        cells[marker_index(left_pct, right_pct)] = MARKER
        line = (
            "매도 ├"
            + "".join(cells)
            + "┤"
            + (f" {right_label[:2]}" if right_label else "")
        )
        caption = f"매도선까지 {fmt_signed_pct(left_pct)}"
        if right_label:
            caption += f" · {right_label}까지 {fmt_signed_pct(right_pct)}"
        return caption, line
    track = "─" * GAUGE_CELLS
    caption = ctx.triggers.headline or f"재진입까지 {fmt_signed_pct(facts.gauge_pct)}"
    if facts.gauge_pct >= 0:
        return caption, f"현재 {MARKER}{track}┤ 재진입"
    return caption, f"재진입 ├{track}{MARKER} 현재"


def _header(ctx: AlertContext) -> str:
    when = _weekday_md(ctx.date_str)
    trade = ctx.plan.trade
    if trade is not None:
        emoji, name = {
            "buy": ("🟢", "매수일"),
            "trim": ("🟠", "일부 감량일"),
            "exit": ("🔴", "전량 매도일"),
        }[trade.kind]
    elif ctx.plan.contribution is not None:
        emoji, name = "💵", "적립일"
    elif ctx.plan.gold_rebalance is not None:
        emoji, name = "🔁", "금 리밸런싱일"
    else:
        emoji, name = "⚪", "보유 유지" if _invested(ctx) else "현금 대기"
        return f"{emoji} {name} · {when}"
    return f"{emoji} {name} — {EXEC_WHEN} · {when}"


def checklist_lines(ctx: AlertContext) -> list[str]:
    """`☐` items, sells first. Empty when nothing is to be done today."""
    plan = ctx.plan
    trade = plan.trade
    legs = dict(plan.contribution.legs) if plan.contribution is not None else {}
    lines: list[str] = []
    if trade is not None:
        if trade.full:
            lines.append(f"☐ {trade.sell_asset} 전량 매도")
        else:
            lines.append(
                f"☐ {trade.sell_asset} 보유수량의 {format_fraction(trade.sell_fraction)}% 매도"
            )
    for asset in ASSETS:
        amount = legs.get(asset)
        parts: list[str] = []
        if trade is not None and trade.proceeds_to == asset:
            parts.append(f"{trade.sell_asset} 매도대금" + ("" if amount else " 전액"))
        if amount:
            parts.append(f"적립 {amount}만원")
        if not parts:
            continue
        if trade is None:
            lines.append(f"☐ {asset} 매수 {amount}만원")
        else:
            lines.append(f"☐ {asset} 매수 ({' + '.join(parts)})")
    if plan.gold_rebalance is not None:
        lines.append(
            f"☐ GLD 전체 자산의 {format_fraction(plan.gold_rebalance.target)}%로 리밸런싱"
        )
    return lines


def _status_lines(ctx: AlertContext) -> list[str]:
    # two short lines: one long line wraps on a phone-width bubble
    lines = [
        f"📊 TQQQ {_usd(ctx.tqqq_close)} ({_emoji_from_sign(ctx.tqqq_day_pct)} {fmt_signed_pct(ctx.tqqq_day_pct, 2)})"
    ]
    second = ""
    if _invested(ctx):
        if ctx.entry_date and ctx.entry_close:
            if ctx.entry_date[:10] == ctx.date_str[:10]:
                second = "오늘 진입"
            else:
                pnl = (ctx.tqqq_close / ctx.entry_close - 1.0) * 100.0
                second = f"{_md(ctx.entry_date)} 진입 후 {fmt_signed_pct(pnl)}"
    elif ctx.cash_since:
        second = f"{_md(ctx.cash_since)} 매도 후 SGOV 대기"
    if ctx.fx_now is not None:
        fx = f"💱 {ctx.fx_now:,.0f}원"
        if ctx.fx_pct is not None:
            fx += f" ({fmt_signed_pct(ctx.fx_pct, 1)})"
        second = f"{second} · {fx}" if second else fx
    if second:
        lines.append(second)
    return lines


def build_hybrid_message(ctx: AlertContext) -> str:
    items = checklist_lines(ctx)
    head = [
        f"<b>{esc(_header(ctx))}</b>",
        *(esc(line) for line in items or ["오늘 할 일 없음"]),
        "",
    ]

    facts = ctx.triggers.facts
    gauge = _gauge(ctx)
    block: list[str] = []
    if gauge is not None:
        caption, line = gauge
        head.append(esc(caption))
        block += [line, ""]
    elif facts is not None and not _invested(ctx) and facts.reentry_condition:
        head.append(esc(f"재진입 조건: {facts.reentry_condition}"))
    block += _bar_lines(ctx.new_alloc)
    pre = "<pre>" + esc("\n".join(block)) + "</pre>"

    # <pre> renders as its own block, so no blank lines around it
    body = [*head, pre, *(esc(line) for line in _status_lines(ctx))]
    tech = _tech_lines(ctx)
    tech_html = [
        "",
        esc(TECH_SEPARATOR),
        f"<b>{esc(tech[0])}</b>",
        *(esc(line) for line in tech[1:]),
    ]
    full = "\n".join([*body, *tech_html])
    if len(full) > MAX_MESSAGE_CHARS:
        full = "\n".join(
            body
        )  # drop the technical report rather than exceed Telegram's 4096 limit
    return full
