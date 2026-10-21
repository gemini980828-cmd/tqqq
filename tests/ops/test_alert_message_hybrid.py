from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tqqq_strategy.ops.alert_message import AlertContext
from tqqq_strategy.ops.alert_message_hybrid import (
    GAUGE_CELLS,
    build_hybrid_message,
    checklist_lines,
    marker_index,
    render_bar,
)
from tqqq_strategy.ops.alert_triggers import TriggerFacts, TriggerReport
from tqqq_strategy.ops.order_plan import plan_orders

SCRIPT = Path(__file__).resolve().parents[2] / "ops/scripts/run_daily_telegram_alert.py"
_spec = importlib.util.spec_from_file_location("run_daily_alert_hybrid_test", SCRIPT)
assert _spec is not None and _spec.loader is not None
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)

INVESTED_TRIGGERS = TriggerReport(
    "매도선까지 −7.8%",
    (),
    TriggerFacts(
        dist200=108.33,
        sell_line=99.79,
        sell_line_pct=-7.8,
        v20_pct=2.9,
        vol_limit_pct=5.9,
        overheat_enter=139.0,
        overheat_pct=28.7,
        gauge_pct=-7.8,
    ),
)


def _alloc(p: float) -> tuple[float, float, float]:
    return round(0.9 * p, 10), round(0.9 * (1.0 - p), 10), 0.1


def _ctx(
    *,
    p: float = 0.97,
    prev_p: float = 0.97,
    triggers: TriggerReport | None = None,
    contribution: bool = False,
    gold: bool = False,
) -> AlertContext:
    plan = plan_orders(
        _alloc(prev_p),
        _alloc(p),
        contribution_krw=1_670_000 if contribution else None,
        is_contribution_day=contribution,
        is_first_session_of_year=gold,
    )
    cash = p <= 1e-9
    return AlertContext(
        date_str="2026-10-20",
        strategy_name="B0_DZ 90% + GLD 10%",
        p_now=p,
        new_alloc=_alloc(p),
        plan=plan,
        triggers=triggers or INVESTED_TRIGGERS,
        tqqq_close=70.41,
        tqqq_day_pct=-0.33,
        entry_date=None if cash else "2026-07-30",
        entry_close=None if cash else 63.30,
        cash_since="2026-07-23" if cash else None,
        fx_now=1330.0,
        fx_pct=-0.26,
        prev_p=prev_p,
        prev_code="970",
        new_code="970",
    )


def test_render_bar_uses_eighth_blocks() -> None:
    assert render_bar(87.3) == "████████▋"
    assert render_bar(2.7) == "▎"
    assert render_bar(10) == "█"
    assert render_bar(100) == "█" * 10
    assert render_bar(0) == ""


def test_marker_index_is_proportional_and_clamped() -> None:
    # price space: 1/3 of the way from 0.5 to 2.0
    assert marker_index(-50.0, 100.0) == round((GAUGE_CELLS - 1) / 3)
    assert marker_index(-7.8, 28.7) == round(7.8 / 36.5 * (GAUGE_CELLS - 1))
    # already past either trigger -> pinned to the ends
    assert marker_index(5.0, 20.0) == 0
    assert marker_index(-20.0, -5.0) == GAUGE_CELLS - 1
    assert marker_index(0.0, 0.0) == GAUGE_CELLS // 2


def test_hold_message_layout() -> None:
    message = build_hybrid_message(_ctx())
    lines = message.split("\n")

    assert lines[0] == "<b>⚪ 보유 유지 · 10/20(화)</b>"
    assert lines[1] == "오늘 할 일 없음"
    assert lines[2] == ""
    assert lines[3] == "매도선까지 −7.8% · 과열 감량까지 +28.7%"
    assert lines[4].startswith("<pre>매도 ├") and lines[4].endswith("┤ 과열")
    assert "●" in lines[4]
    assert "TQQQ ████████▋   87%" in lines
    assert "SGOV ▎            3%" in lines
    assert "GLD  █           10%</pre>" in lines
    assert "📊 TQQQ $70.41 (🔴 −0.33%)" in lines
    assert "7/30 진입 후 +11.2% · 💱 1,330원 (−0.3%)" in lines
    assert "<b>기술리포트</b>" in lines
    assert "- 200일선 이격도: 108.33 (매도선 99.79, −7.8%)" in lines


def test_checklists_per_action() -> None:
    assert checklist_lines(_ctx(p=1.0, prev_p=0.0, contribution=True)) == [
        "☐ SGOV 전량 매도",
        "☐ TQQQ 매수 (SGOV 매도대금 + 적립 150만원)",
        "☐ GLD 매수 (적립 17만원)",
    ]
    assert checklist_lines(_ctx(p=1.0, prev_p=0.0)) == [
        "☐ SGOV 전량 매도",
        "☐ TQQQ 매수 (SGOV 매도대금 전액)",
    ]
    assert checklist_lines(_ctx(p=0.97, prev_p=1.0, contribution=True)) == [
        "☐ TQQQ 보유수량의 3% 매도",
        "☐ TQQQ 매수 (적립 146만원)",
        "☐ SGOV 매수 (TQQQ 매도대금 + 적립 4만원)",
        "☐ GLD 매수 (적립 17만원)",
    ]
    assert checklist_lines(_ctx(p=0.97, prev_p=1.0)) == [
        "☐ TQQQ 보유수량의 3% 매도",
        "☐ SGOV 매수 (TQQQ 매도대금 전액)",
    ]
    assert checklist_lines(_ctx(p=0.0, prev_p=0.97)) == [
        "☐ TQQQ 전량 매도",
        "☐ SGOV 매수 (TQQQ 매도대금 전액)",
    ]
    assert checklist_lines(_ctx(contribution=True)) == [
        "☐ TQQQ 매수 146만원",
        "☐ SGOV 매수 4만원",
        "☐ GLD 매수 17만원",
    ]
    assert checklist_lines(_ctx(gold=True)) == ["☐ GLD 전체 자산의 10%로 리밸런싱"]
    assert checklist_lines(_ctx()) == []


def test_headers_per_action() -> None:
    first = lambda **kw: (
        build_hybrid_message(_ctx(**kw))
        .split("\n", 1)[0]
        .removeprefix("<b>")
        .removesuffix("</b>")
    )
    assert first(p=1.0, prev_p=0.0) == "🟢 매수일 — 오늘 밤 미국장 시가 · 10/20(화)"
    assert (
        first(p=0.97, prev_p=1.0) == "🟠 일부 감량일 — 오늘 밤 미국장 시가 · 10/20(화)"
    )
    assert (
        first(p=0.0, prev_p=0.97) == "🔴 전량 매도일 — 오늘 밤 미국장 시가 · 10/20(화)"
    )
    assert first(contribution=True) == "💵 적립일 — 오늘 밤 미국장 시가 · 10/20(화)"
    assert first(gold=True) == "🔁 금 리밸런싱일 — 오늘 밤 미국장 시가 · 10/20(화)"


def test_cash_price_gauge_and_non_price_condition() -> None:
    up = TriggerReport(
        "재진입까지 TQQQ +5.2%",
        ("✗ 조건",),
        TriggerFacts(gauge_pct=5.2, summary_clause="s"),
    )
    message = build_hybrid_message(_ctx(p=0.0, prev_p=0.0, triggers=up))
    assert "재진입까지 TQQQ +5.2%\n<pre>현재 ●" in message
    assert "┤ 재진입" in message
    assert "SGOV █████████   90%" in message
    assert "TQQQ" not in message.split("<pre>")[1].split("</pre>")[0]

    lock = TriggerReport(
        "x",
        ("✗ 조건",),
        TriggerFacts(reentry_condition="QQQ RSI 43 이상 (현재 39.3)"),
    )
    message = build_hybrid_message(_ctx(p=0.0, prev_p=0.0, triggers=lock))
    assert "재진입 조건: QQQ RSI 43 이상 (현재 39.3)" in message
    assert "●" not in message
    assert "매수까지 남은 조건" in message


def test_triggers_unavailable_omits_gauge_but_keeps_bars() -> None:
    skipped = TriggerReport(None, ("조건 거리: 계산 생략",))
    message = build_hybrid_message(_ctx(triggers=skipped))

    assert "●" not in message and "├" not in message
    assert "TQQQ ████████▋   87%" in message
    assert "- 조건 거리: 계산 생략" in message


def test_length_cap_and_escaping() -> None:
    huge = TriggerReport("x", tuple("조건 " * 40 for _ in range(60)), TriggerFacts())
    message = build_hybrid_message(_ctx(p=0.0, prev_p=0.0, triggers=huge))
    assert "기술리포트" not in message
    assert len(message) < 4096

    nasty = TriggerReport("x", ("값 <5 & >3",), TriggerFacts(reentry_condition="a<b&c"))
    message = build_hybrid_message(_ctx(p=0.0, prev_p=0.0, triggers=nasty))
    assert "재진입 조건: a&lt;b&amp;c" in message
    assert "- 값 &lt;5 &amp; &gt;3" in message
    stripped = message
    for tag in ("<pre>", "</pre>", "<b>", "</b>", "&lt;"):
        stripped = stripped.replace(tag, "")
    assert "<" not in stripped.replace("&gt;", "").replace("&amp;", "")


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, "classic"),
        ({"ALERT_STYLE": ""}, "classic"),
        ({"ALERT_STYLE": "classic"}, "classic"),
        ({"ALERT_STYLE": " Hybrid "}, "hybrid"),
    ],
)
def test_parse_alert_style(env, expected) -> None:
    assert script._parse_alert_style(env) == expected


def test_parse_alert_style_invalid_warns_and_falls_back(capsys) -> None:
    assert script._parse_alert_style({"ALERT_STYLE": "fancy"}) == "classic"
    assert "ALERT_STYLE" in capsys.readouterr().err
