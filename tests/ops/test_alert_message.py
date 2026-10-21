from __future__ import annotations

import re

from tqqq_strategy.ops.alert_message import (
    MAX_MESSAGE_CHARS,
    AlertContext,
    build_alert_message,
)
from tqqq_strategy.ops.alert_triggers import TriggerReport
from tqqq_strategy.ops.order_plan import plan_orders

FORBIDDEN_VISIBLE = ("%p", "비중", "S2", "신호")
TAG_RE = re.compile(r"</?b>|<blockquote expandable>|</blockquote>")


def _alloc(p: float) -> tuple[float, float, float]:
    return round(0.9 * p, 10), round(0.9 * (1.0 - p), 10), 0.1


def _ctx(
    *,
    p: float = 0.97,
    prev_p: float = 0.97,
    strategy: str = "B0_DZ 90% + GLD 10%",
    triggers: TriggerReport | None = None,
    contribution: bool = False,
) -> AlertContext:
    plan = plan_orders(
        _alloc(prev_p),
        _alloc(p),
        contribution_krw=1_670_000 if contribution else None,
        is_contribution_day=contribution,
        is_first_session_of_year=False,
    )
    return AlertContext(
        date_str="2026-10-20",
        strategy_name=strategy,
        p_now=p,
        new_alloc=_alloc(p),
        plan=plan,
        triggers=triggers
        or TriggerReport(
            "매도선까지 −7.8%",
            ("TQQQ/200일선 108.3% (99.79% 미만 → 10%로 축소, −7.8%)",),
        ),
        tqqq_close=70.41,
        tqqq_day_pct=-0.3,
        entry_date="2026-07-30",
        entry_close=63.30,
        fx_now=1330.0,
        fx_pct=-0.3,
    )


def _visible(message: str) -> str:
    return message.split("<blockquote", 1)[0]


def test_hold_message_matches_spec() -> None:
    message = build_alert_message(_ctx())

    lines = message.split("\n")
    assert lines[0] == "<b>⚪ 보유 유지</b>"
    assert lines[1] == "TQQQ $70.41 (−0.3%) · 매도선까지 −7.8%"
    assert lines[2] == "10/20(화) 미국장 마감 기준"
    assert lines[3] == "<blockquote expandable><b>상세</b>"
    assert "목표  TQQQ 87.3% · SGOV 2.7% · GLD 10%" in lines
    assert "진입  7/30 · $63.30 · 평가손익 +11.2%" in lines
    assert "환율 1,330.0원 (−0.3%)" in lines
    assert lines[-1] == "B0_DZ 90% + GLD 10%</blockquote>"


def test_cash_wait_message_uses_headline_as_second_line() -> None:
    triggers = TriggerReport("재진입: QQQ RSI 43 이상 (현재 41.8)", ())
    message = build_alert_message(_ctx(p=0.0, prev_p=0.0, triggers=triggers))

    lines = message.split("\n")
    assert lines[0] == "<b>⚪ 현금 대기 (SGOV)</b>"
    assert lines[1] == "재진입: QQQ RSI 43 이상 (현재 41.8)"


def test_trade_message_has_header_move_line_and_contribution() -> None:
    message = build_alert_message(_ctx(p=0.97, prev_p=1.0, contribution=True))

    lines = message.split("\n")
    assert lines[0] == "<b>🟠 TQQQ 3% 매도 · 오늘 밤 시가</b>"
    assert lines[1] == "TQQQ 3% → SGOV"
    assert lines[2] == "적립 167만원: TQQQ 146 · SGOV 4 · GLD 17"


def test_visible_part_has_no_jargon_and_first_line_is_bold() -> None:
    for kwargs in (
        {},
        {"p": 0.0, "prev_p": 0.0},
        {"p": 1.0, "prev_p": 0.0},
        {"p": 0.97, "prev_p": 1.0, "contribution": True},
    ):
        message = build_alert_message(_ctx(**kwargs))
        first = message.split("\n", 1)[0]
        assert first.startswith("<b>") and first.endswith("</b>")
        visible = _visible(message)
        for word in FORBIDDEN_VISIBLE:
            assert word not in visible


def test_dynamic_text_is_html_escaped() -> None:
    message = build_alert_message(
        _ctx(
            strategy="a<b&c", triggers=TriggerReport("매도선까지 <x>&", ("값 <5 & >3",))
        )
    )

    assert "a&lt;b&amp;c" in message
    assert "매도선까지 &lt;x&gt;&amp;" in message
    assert "값 &lt;5 &amp; &gt;3" in message
    assert "<" not in TAG_RE.sub("", message)


def test_details_dropped_when_message_too_long() -> None:
    huge = TriggerReport("매도선까지 −7.8%", tuple("조건 " * 40 for _ in range(60)))
    message = build_alert_message(_ctx(triggers=huge))

    assert "<blockquote" not in message
    assert len(message) <= MAX_MESSAGE_CHARS
    assert message.startswith("<b>⚪ 보유 유지</b>")
    assert message.endswith("미국장 마감 기준")
