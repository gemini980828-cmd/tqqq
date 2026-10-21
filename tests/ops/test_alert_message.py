from __future__ import annotations

from tqqq_strategy.ops.alert_message import (
    MAX_MESSAGE_CHARS,
    AlertContext,
    build_alert_message,
)
from tqqq_strategy.ops.alert_triggers import TriggerFacts, TriggerReport
from tqqq_strategy.ops.order_plan import plan_orders

INVESTED_FACTS = TriggerFacts(
    dist200=108.33,
    sell_line=99.79,
    sell_line_pct=-7.8,
    spy_dist=105.95,
    spy_sell_line=97.75,
    spy_sell_pct=-7.7,
    v20_pct=2.9,
    vol_limit_pct=5.9,
    stop_price=59.57,
    stop_pct=-15.4,
    overheat_enter=139.0,
    overheat_pct=28.7,
    summary_clause="TQQQ가 약 7.8% 더 내리면 10%로 축소됩니다.",
)
INVESTED_TRIGGERS = TriggerReport(
    "매도선까지 −7.8%",
    ("TQQQ/200일선 108.3% (99.79% 미만 → 10%로 축소, −7.8%)",),
    INVESTED_FACTS,
)
CASH_TRIGGERS = TriggerReport(
    "재진입: QQQ RSI 43 이상 (현재 39.3)",
    (
        "✗ 손절 후 재진입 잠금: QQQ RSI 39.3 (43 이상 필요)",
        "✓ 20일 변동성 4.4% (5.9% 미만 필요)",
    ),
    TriggerFacts(summary_clause="재진입 조건: QQQ RSI 43 이상 (현재 39.3)."),
)


def _alloc(p: float) -> tuple[float, float, float]:
    return round(0.9 * p, 10), round(0.9 * (1.0 - p), 10), 0.1


def _ctx(
    *,
    p: float = 0.97,
    prev_p: float = 0.97,
    strategy: str = "B0_DZ 90% + GLD 10%",
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
        strategy_name=strategy,
        p_now=p,
        new_alloc=_alloc(p),
        plan=plan,
        triggers=triggers or (CASH_TRIGGERS if cash else INVESTED_TRIGGERS),
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


def test_hold_message_matches_classic_layout() -> None:
    message = build_alert_message(_ctx())

    expected = [
        "[ 2026-10-20 ] 코어전략 운영브리프",
        "",
        "전략: B0_DZ 90% + GLD 10%",
        "",
        "⚪ 오늘 판단: 유지",
        "목표 비중: TQQQ 87.30% / SGOV 2.70% / GLD 10.00%",
        "",
        "🛒 실행 액션: 오늘은 주문 없음",
        "",
        "요약:",
        "7/30 진입 후 보유 중 (평가손익 +11.2%). TQQQ가 약 7.8% 더 내리면 10%로 축소됩니다.",
        "",
        "📊 오늘 시장",
        "- TQQQ 종가: $70.41 (🔴 −0.33%)",
        "- 원/달러 환율: 1,330.00 (−0.26%)",
        "",
        "──────────",
        "기술리포트",
        "- 신호 비중 p: 97.00% → 97.00%",
        "- 진입: 7/30 · $63.30 · 손절선 $59.57 (−15.4%)",
        "- 200일선 이격도: 108.33 (매도선 99.79, −7.8%)",
        "- SPY 200일선: 105.95 (매도선 97.75, −7.7%)",
        "- 20일 변동성: 2.90% (한도 5.90%)",
        "- 과열 감량 시작: 139 (+28.7%)",
        "- signal code: 970 → 970",
    ]
    assert message == "\n".join(expected)


def test_cash_wait_message_lists_conditions() -> None:
    message = build_alert_message(_ctx(p=0.0, prev_p=0.0))

    assert "⚪ 오늘 판단: 현금 대기" in message
    assert (
        "7/23 매도 후 SGOV 대기 중. 재진입 조건: QQQ RSI 43 이상 (현재 39.3)."
        in message
    )
    tech = message.split("기술리포트\n", 1)[1].split("\n")
    assert tech[0] == "- 신호 비중 p: 0.00% → 0.00%"
    assert tech[1] == "매수까지 남은 조건"
    assert tech[2] == "✗ 손절 후 재진입 잠금: QQQ RSI 39.3 (43 이상 필요)"


def test_trade_message_has_action_section_and_contribution() -> None:
    message = build_alert_message(_ctx(p=0.97, prev_p=1.0, contribution=True))

    assert "🟠 오늘 판단: 일부 감량" in message
    assert (
        "🛒 실행 액션 (오늘 밤 미국장 시가)\n"
        "- TQQQ: 보유수량의 3% 매도\n"
        "- SGOV: TQQQ 매도대금 전액으로 매수\n"
        "- GLD: 유지\n"
        "\n"
        "💵 이번 달 적립 (167만원, 오늘 밤 미국장 시가)\n"
        "- TQQQ 146만원 / SGOV 4만원 / GLD 17만원\n"
    ) in message
    assert "신호 비중이 100% → 97%로 바뀌어 TQQQ 일부를 SGOV로 옮깁니다." in message


def test_buy_and_exit_action_lines() -> None:
    buy = build_alert_message(_ctx(p=1.0, prev_p=0.0))
    assert "🟢 오늘 판단: 매수" in buy
    assert "- SGOV: 전량 매도\n- TQQQ: SGOV 매도대금 전액으로 매수\n- GLD: 유지" in buy

    partial = build_alert_message(_ctx(p=0.9, prev_p=0.05))
    assert "- SGOV: 보유수량의 89.5% 매도" in partial

    exit_ = build_alert_message(_ctx(p=0.0, prev_p=0.97))
    assert "🔴 오늘 판단: 전량 매도" in exit_
    assert "- TQQQ: 전량 매도\n- SGOV: TQQQ 매도대금 전액으로 매수" in exit_


def test_contribution_only_and_gold_only_judgment() -> None:
    contribution = build_alert_message(_ctx(contribution=True))
    assert "💵 오늘 판단: 적립 집행" in contribution
    assert "- TQQQ 146만원 / SGOV 4만원 / GLD 17만원" in contribution

    cash = build_alert_message(_ctx(p=0.0, prev_p=0.0, contribution=True))
    assert "- SGOV 150만원 / GLD 17만원" in cash

    gold = build_alert_message(_ctx(gold=True))
    assert "🔁 오늘 판단: 금 리밸런싱" in gold
    assert (
        "🔁 연 1회 금 리밸런싱일: GLD를 전체 자산의 10%로 맞추세요 (연초 첫 거래일)."
        in gold
    )
    assert "💵" not in gold


def test_triggers_unavailable_omits_distance_clause() -> None:
    skipped = TriggerReport(None, ("조건 거리: 계산 생략",))

    invested = build_alert_message(_ctx(triggers=skipped))
    assert "7/30 진입 후 보유 중 (평가손익 +11.2%).\n" in invested
    assert "- 조건 거리: 계산 생략" in invested

    cash = build_alert_message(_ctx(p=0.0, prev_p=0.0, triggers=skipped))
    assert "7/23 매도 후 SGOV 대기 중.\n" in cash
    assert "- 조건 거리: 계산 생략" in cash
    assert "매수까지 남은 조건" not in cash


def test_no_blockquote_or_bold_markup() -> None:
    for kwargs in (
        {},
        {"p": 0.0, "prev_p": 0.0},
        {"p": 1.0, "prev_p": 0.0},
        {"p": 0.97, "prev_p": 1.0, "contribution": True},
    ):
        message = build_alert_message(_ctx(**kwargs))
        assert "<b>" not in message and "<blockquote" not in message


def test_dynamic_text_is_html_escaped() -> None:
    message = build_alert_message(
        _ctx(
            strategy="a<b&c",
            triggers=TriggerReport(
                "x", ("값 <5 & >3",), TriggerFacts(summary_clause="가 <x>&")
            ),
        )
    )

    assert "전략: a&lt;b&amp;c" in message
    assert "가 &lt;x&gt;&amp;" in message
    assert (
        "- 값 &lt;5 &amp; &gt;3" not in message
    )  # facts present -> detail lines not shown
    cash = build_alert_message(
        _ctx(
            p=0.0,
            prev_p=0.0,
            triggers=TriggerReport("x", ("값 <5 & >3",), TriggerFacts()),
        )
    )
    assert "- 값 &lt;5 &amp; &gt;3" in cash
    assert "<" not in message.replace("&lt;", "")


def test_tech_report_dropped_when_message_too_long() -> None:
    huge = TriggerReport("x", tuple("조건 " * 40 for _ in range(60)), TriggerFacts())
    message = build_alert_message(_ctx(p=0.0, prev_p=0.0, triggers=huge))

    assert "기술리포트" not in message
    assert len(message) <= MAX_MESSAGE_CHARS < 4096
    assert message.startswith("[ 2026-10-20 ] 코어전략 운영브리프")
