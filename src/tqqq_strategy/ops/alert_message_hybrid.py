"""Hybrid Telegram alert: action checklist + monospace gauge/bars + the classic technical report (HTML parse mode)."""

from __future__ import annotations

import unicodedata
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
GAUGE_CELLS = 30
BAR_CELLS = 10
PARTIAL_BLOCKS = "▏▎▍▌▋▊▉"
MARKER = "●"


def _weekday_md(date_str: str) -> str:
    d = date.fromisoformat(date_str[:10])
    return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"


def _width(text: str) -> int:
    return sum(
        2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text
    )


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


def _place(width: int, items: list[tuple[int, str]]) -> str:
    """Put each text at its display column (left to right, assumed not overlapping)."""
    out = ""
    for col, text in sorted(items):
        out += " " * max(col - _width(out), 0) + text
    return out.ljust(width)


def _pct_line(width: int, left: str, right: str) -> str:
    gap = max(width - _width(left) - _width(right), 1)
    return left + " " * gap + right


def _gauge_lines(ctx: AlertContext) -> list[str]:
    """Gauge block lines, or [] when there is nothing to draw (triggers unavailable)."""
    facts = ctx.triggers.facts
    if facts is None:
        return []
    width = GAUGE_CELLS + 2
    if _invested(ctx):
        if facts.gauge_pct is None:
            return []
        left_pct = facts.gauge_pct
        if facts.overheat_pct is not None:
            right_pct, right_label = facts.overheat_pct, "과열 감량"
        elif facts.tp_pct is not None:
            right_pct, right_label = facts.tp_pct, "익절 감량"
        else:
            right_pct, right_label = abs(left_pct), ""
        idx = marker_index(left_pct, right_pct)
        cells = ["─"] * GAUGE_CELLS
        cells[idx] = MARKER
        bar = "├" + "".join(cells) + "┤"
        left_label, now = "매도선", "현재"
        label_items = [(0, left_label)]
        if right_label:
            label_items.append((width - _width(right_label), right_label))
        # "현재" sits over the marker, shifted sideways just enough to keep a gap to both end labels
        lowest = _width(left_label) + 1
        highest = (width - _width(right_label) - 1 if right_label else width) - _width(
            now
        )
        now_col = min(max(idx, lowest), highest)
        if lowest <= highest:
            label_items.append((now_col, now))
        return [
            _place(width, label_items).rstrip(),
            bar,
            _pct_line(width, fmt_signed_pct(left_pct), fmt_signed_pct(right_pct)),
        ]
    if facts.gauge_pct is not None:
        pct = facts.gauge_pct
        track = "─" * GAUGE_CELLS
        if pct >= 0:
            return [
                _pct_line(width, "현재", "재진입"),
                f"{MARKER}{track}┤",
                _pct_line(width, "", fmt_signed_pct(pct)),
            ]
        return [
            _pct_line(width, "재진입", "현재"),
            f"├{track}{MARKER}",
            _pct_line(width, fmt_signed_pct(pct), ""),
        ]
    return []


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
    market = f"📊 TQQQ {_usd(ctx.tqqq_close)} ({_emoji_from_sign(ctx.tqqq_day_pct)} {fmt_signed_pct(ctx.tqqq_day_pct, 2)})"
    if ctx.fx_now is not None:
        market += f" · 원/달러 {ctx.fx_now:,.2f}"
        if ctx.fx_pct is not None:
            market += f" ({fmt_signed_pct(ctx.fx_pct, 2)})"
    lines = [market]
    if _invested(ctx):
        if ctx.entry_date and ctx.entry_close:
            pnl = (ctx.tqqq_close / ctx.entry_close - 1.0) * 100.0
            lines.append(f"{_md(ctx.entry_date)} 진입 후 {fmt_signed_pct(pnl)}")
    elif ctx.cash_since:
        lines.append(f"{_md(ctx.cash_since)} 매도 후 SGOV 대기 중")
    return lines


def build_hybrid_message(ctx: AlertContext) -> str:
    items = checklist_lines(ctx)
    head = [esc(_header(ctx)), *(esc(line) for line in items or ["오늘 할 일 없음"])]

    facts = ctx.triggers.facts
    gauge = _gauge_lines(ctx)
    block: list[str] = []
    if gauge:
        block += [*gauge, ""]
    elif facts is not None and not _invested(ctx) and facts.reentry_condition:
        block_text = f"재진입 조건: {facts.reentry_condition}"
        head.append(esc(block_text))
    block += _bar_lines(ctx.new_alloc)
    pre = "<pre>" + esc("\n".join(block)) + "</pre>"

    body = [*head, "", pre, "", *(esc(line) for line in _status_lines(ctx))]
    tech = ["", TECH_SEPARATOR, *_tech_lines(ctx)]
    full = "\n".join([*body, *(esc(line) for line in tech)])
    if len(full) > MAX_MESSAGE_CHARS:
        full = "\n".join(
            body
        )  # drop the technical report rather than exceed Telegram's 4096 limit
    return full
