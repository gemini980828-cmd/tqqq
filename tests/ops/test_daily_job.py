import json

import numpy as np
import pandas as pd

from tqqq_strategy.ops.daily_job import run_daily_signal_alert
from tqqq_strategy.signal.final_engine import compute_final_signal_table

CSV_SAMPLE = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,1.0,0,0.0
2026-03-06,0,0.0,3,0.25,0,0.0
"""

DATA_SAMPLE = """time,QQQ종가,TQQQ종가,SPY종가,원달러환율
2026-03-05,100.0,50.0,600.0,1470.0
2026-03-06,102.0,51.0,605.0,1475.0
"""

CSV_SAME_WEIGHT_SAMPLE = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,2,0.95,0,0.0
2026-03-06,0,0.0,2,0.95,0,0.0
"""

SKIPPED = "조건 거리: 계산 생략"


class FakeSender:
    """Records calls; accepts any keyword arguments (e.g. parse_mode)."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        return {"sent": True, "dry_run": kwargs.get("dry_run")}


def _run(
    tmp_path, signal_text, data_text=DATA_SAMPLE, *, dry_run=True, sender=None, **kwargs
):
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    signal_csv.write_text(signal_text, encoding="utf-8")
    data_csv.write_text(data_text, encoding="utf-8")
    return run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=tmp_path / "state.json",
        bot_token=None if dry_run else "token",
        chat_id=None if dry_run else "chat",
        dry_run=dry_run,
        sender=sender or FakeSender(),
        **kwargs,
    )


def test_run_daily_signal_alert_skips_duplicate_on_second_run(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    signal_csv.write_text(CSV_SAMPLE, encoding="utf-8")
    data_csv.write_text(DATA_SAMPLE, encoding="utf-8")
    sender = FakeSender()

    def run():
        return run_daily_signal_alert(
            signal_csv_path=signal_csv,
            data_csv_path=data_csv,
            state_path=state_file,
            bot_token="token",
            chat_id="chat",
            dry_run=False,
            sender=sender,
        )

    first = run()
    second = run()

    assert first["sent"] is True
    assert first["skipped"] is False
    assert first["key"] == "2026-03-06:1->3"
    assert first["action"] == "trim"
    assert first["contribution_session"] is False

    assert second["sent"] is False
    assert second["skipped"] is True
    assert second["reason"] == "duplicate_key"
    assert second["key"] == first["key"]

    assert len(sender.calls) == 1
    assert sender.calls[0]["parse_mode"] == "HTML"
    assert sender.calls[0]["text"] == first["message"]
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    for key in (
        "last_alert_key",
        "last_sent_at",
        "date",
        "position_weight",
        "tqqq_weight",
        "sgov_weight",
        "gld_weight",
        "entry_price",
        "entry_date",
        "tp10_done",
    ):
        assert key in saved
    msg = first["message"]
    assert msg.startswith("[ 2026-03-06 ] 코어전략 운영브리프\n")
    assert "🟠 오늘 판단: 일부 감량" in msg
    assert "- TQQQ: 보유수량의 75% 매도\n- SGOV: TQQQ 매도대금 전액으로 매수" in msg
    # legacy CSV without allocation columns: falls back to 0.90*p / 0.90*(1-p) / 0.10
    assert "목표 비중: TQQQ 22.50% / SGOV 67.50% / GLD 10.00%" in msg
    assert "- signal code: 1 → 3" in msg
    assert SKIPPED in msg  # two rows of market data cannot feed the engine
    assert first["new_allocation"] == {"TQQQ": 0.225, "SGOV": 0.675, "GLD": 0.1}


def test_run_daily_signal_alert_dry_run_does_not_persist_state(tmp_path) -> None:
    sender = FakeSender()
    kwargs = {"dry_run": True, "sender": sender}

    first = _run(tmp_path, CSV_SAMPLE, **kwargs)
    second = _run(tmp_path, CSV_SAMPLE, **kwargs)

    assert first["sent"] is True
    assert second["sent"] is True
    assert second["skipped"] is False
    assert not (tmp_path / "state.json").exists()
    assert len(sender.calls) == 2
    assert all(call["dry_run"] is True for call in sender.calls)


def test_run_daily_signal_alert_derives_entry_from_csv_and_ignores_state(
    tmp_path,
) -> None:
    (tmp_path / "state.json").write_text(
        '{"last_alert_key": "old", "entry_price": 49.2, "entry_date": "2026-03-01", "position_weight": 0.95}',
        encoding="utf-8",
    )

    result = _run(tmp_path, CSV_SAME_WEIGHT_SAMPLE, dry_run=False)

    msg = result["message"]
    assert "⚪ 오늘 판단: 유지" in msg
    assert "- TQQQ 종가: $51.00 (🟢 +2.00%)" in msg
    assert "3/5 진입 후 보유 중 (평가손익 +2.0%)." in msg
    assert "- 진입: 3/5 · $50.00" in msg
    assert "$49.2" not in msg
    saved = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert saved["entry_price"] == 50.0
    assert saved["entry_date"] == "2026-03-05"
    assert result["action"] == "hold"


def test_run_daily_signal_alert_entry_is_start_of_current_invested_run(
    tmp_path,
) -> None:
    result = _run(
        tmp_path,
        "time,S2_code,S2_weight\n2026-03-03,0,0.0\n2026-03-04,2,1.0\n2026-03-05,970,0.97\n2026-03-06,970,0.97\n",
        "time,QQQ종가,TQQQ종가,SPY종가,원달러환율\n"
        "2026-03-03,98.0,48.0,590.0,1460.0\n"
        "2026-03-04,100.0,50.0,600.0,1470.0\n"
        "2026-03-05,101.0,52.0,602.0,1472.0\n"
        "2026-03-06,102.0,51.0,605.0,1475.0\n",
    )

    assert "3/4 진입 후 보유 중 (평가손익 +2.0%)." in result["message"]


def test_run_daily_signal_alert_too_short_data_skips_distances_without_failing(
    tmp_path,
) -> None:
    result = _run(
        tmp_path,
        "time,S2_code,S2_weight,base_weight,buffer_active\n"
        "2026-03-26,0,0.0,0.0,false\n"
        "2026-03-27,0,0.0,0.0,false\n",
        "time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,원달러환율\n"
        "2026-03-26,573.79,41.23,645.09,581.86,604.32,49.14,661.48,1500.97\n"
        "2026-03-27,562.58,38.78,634.09,574.73,604.29,49.15,661.63,1508.36\n",
    )

    msg = result["message"]
    assert result["sent"] is True
    assert result["action"] == "wait"
    assert "⚪ 오늘 판단: 현금 대기" in msg
    assert "- TQQQ 종가: $38.78 (🔴 −5.94%)" in msg
    assert "3/26 매도 후 SGOV 대기 중.\n" in msg
    assert f"- {SKIPPED}" in msg


def test_run_daily_signal_alert_raises_on_missing_required_columns(tmp_path) -> None:
    signal_csv = tmp_path / "signals_bad.csv"
    signal_csv.write_text(
        "time,S2_code\n2026-03-05,1\n2026-03-06,2\n", encoding="utf-8"
    )

    try:
        run_daily_signal_alert(
            signal_csv_path=signal_csv,
            state_path=tmp_path / "state.json",
            bot_token="token",
            chat_id="chat",
            dry_run=True,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "missing required columns" in str(exc)


def test_run_daily_signal_alert_raises_on_invalid_weight_value(tmp_path) -> None:
    try:
        _run(
            tmp_path,
            "time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight\n"
            "2026-03-05,0,0.0,1,abc,0,0.0\n"
            "2026-03-06,0,0.0,2,0.95,0,0.0\n",
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "invalid S2_weight value" in str(exc)


def test_run_daily_signal_alert_raises_on_single_signal_row(tmp_path) -> None:
    try:
        _run(tmp_path, "time,S2_code,S2_weight\n2026-03-06,2,1.0\n")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "at least two rows" in str(exc)


def test_run_daily_signal_alert_uses_allocation_columns(tmp_path) -> None:
    result = _run(
        tmp_path,
        "time,S2_code,S2_weight,tqqq_weight,sgov_weight,gld_weight\n"
        "2026-03-05,2,1.0,0.9,0.0,0.1\n"
        "2026-03-06,970,0.97,0.873,0.027,0.1\n",
    )

    msg = result["message"]
    assert "🟠 오늘 판단: 일부 감량" in msg
    assert "- TQQQ: 보유수량의 3% 매도\n- SGOV: TQQQ 매도대금 전액으로 매수" in msg
    assert "목표 비중: TQQQ 87.30% / SGOV 2.70% / GLD 10.00%" in msg
    assert "전략: B0_DZ 90% + GLD 10%" in msg
    alloc = result["new_allocation"]
    assert abs(sum(alloc.values()) - 1.0) < 1e-9


def test_run_daily_signal_alert_first_session_of_year_adds_gold_rebalance(
    tmp_path,
) -> None:
    result = _run(
        tmp_path,
        "time,S2_code,S2_weight\n2025-12-31,2,1.0\n2026-01-02,2,1.0\n",
        "time,QQQ종가,TQQQ종가,SPY종가,원달러환율\n2025-12-31,100.0,50.0,600.0,1470.0\n2026-01-02,102.0,51.0,605.0,1475.0\n",
    )

    assert result["action"] == "gold_rebalance"
    assert "🔁 오늘 판단: 금 리밸런싱" in result["message"]
    assert (
        "🔁 연 1회 금 리밸런싱일: GLD를 전체 자산의 10%로 맞추세요 (연초 첫 거래일)."
        in result["message"]
    )


def test_run_daily_signal_alert_mid_year_has_no_gold_rebalance(tmp_path) -> None:
    result = _run(
        tmp_path, "time,S2_code,S2_weight\n2026-03-05,2,1.0\n2026-03-06,2,1.0\n"
    )

    assert "리밸런싱" not in result["message"]
    assert result["action"] == "hold"


def test_run_daily_signal_alert_contribution_session_adds_contribution_lines(
    tmp_path,
) -> None:
    data = "time,QQQ종가,TQQQ종가,SPY종가,원달러환율\n2026-03-24,100.0,50.0,600.0,1470.0\n2026-03-26,102.0,51.0,605.0,1475.0\n"
    signal = "time,S2_code,S2_weight\n2026-03-24,2,1.0\n2026-03-26,2,1.0\n"

    result = _run(
        tmp_path, signal, data, contribution_krw=1_670_000, contribution_day=25
    )

    assert result["contribution_session"] is True
    assert result["action"] == "contribution"
    assert "💵 오늘 판단: 적립 집행" in result["message"]
    assert (
        "💵 이번 달 적립 (167만원, 오늘 밤 미국장 시가)\n- TQQQ 150만원 / GLD 17만원"
        in result["message"]
    )


def test_run_daily_signal_alert_contribution_needs_both_amount_and_day(
    tmp_path,
) -> None:
    data = "time,QQQ종가,TQQQ종가,SPY종가,원달러환율\n2026-03-24,100.0,50.0,600.0,1470.0\n2026-03-26,102.0,51.0,605.0,1475.0\n"
    signal = "time,S2_code,S2_weight\n2026-03-24,2,1.0\n2026-03-26,2,1.0\n"

    amount_only = _run(tmp_path, signal, data, contribution_krw=1_670_000)
    day_only = _run(tmp_path, signal, data, contribution_day=25)
    off_day = _run(
        tmp_path, signal, data, contribution_krw=1_670_000, contribution_day=27
    )

    for result in (amount_only, day_only, off_day):
        assert result["contribution_session"] is False
        assert "적립" not in result["message"]
        assert "⚪ 오늘 판단: 유지" in result["message"]


def test_run_daily_signal_alert_with_real_engine_computes_trigger_distances(
    tmp_path,
) -> None:
    rng = np.random.default_rng(7)
    n = 420
    market = pd.DataFrame(
        {
            "time": pd.bdate_range("2024-01-01", periods=n),
            "QQQ종가": 100.0 * np.exp(np.cumsum(rng.normal(0.0006, 0.01, n))),
            "TQQQ종가": 50.0 * np.exp(np.cumsum(3.0 * rng.normal(0.0006, 0.01, n))),
            "SPY종가": 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.008, n))),
            "원달러환율": 1400.0,
        }
    )
    signals = compute_final_signal_table(market)
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    signals.to_csv(signal_csv, index=False)
    market.to_csv(data_csv, index=False)

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=tmp_path / "state.json",
        dry_run=True,
        sender=FakeSender(),
    )

    msg = result["message"]
    assert SKIPPED not in msg
    assert "20일 변동성" in msg or "재진입" in msg
