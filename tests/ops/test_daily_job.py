from pathlib import Path

from tqqq_strategy.ops.daily_job import run_daily_signal_alert


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


def _write_csv(path: Path) -> None:
    path.write_text(CSV_SAMPLE, encoding="utf-8")


def _write_data_csv(path: Path) -> None:
    path.write_text(DATA_SAMPLE, encoding="utf-8")


def _write_same_weight_csv(path: Path) -> None:
    path.write_text(CSV_SAME_WEIGHT_SAMPLE, encoding="utf-8")


def test_run_daily_signal_alert_skips_duplicate_on_second_run(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    _write_csv(signal_csv)
    _write_data_csv(data_csv)

    calls: list[dict] = []

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        calls.append(
            {
                "bot_token": bot_token,
                "chat_id": chat_id,
                "text": text,
                "dry_run": dry_run,
            }
        )
        return {"sent": True, "dry_run": dry_run}

    first = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    assert first["sent"] is True
    assert first["skipped"] is False
    assert first["key"] == "2026-03-06:1->3"

    assert second["sent"] is False
    assert second["skipped"] is True
    assert second["reason"] == "duplicate_key"
    assert second["key"] == first["key"]

    assert len(calls) == 1
    assert state_file.exists()
    saved = state_file.read_text(encoding="utf-8")
    assert "entry_price" in saved
    assert "position_weight" in saved
    assert "tp10_done" in saved
    assert "📢 [매매 필요]" in first["message"]
    assert "신호:" in first["message"]
    assert "일간 수익:" in first["message"]
    assert "진입가 대비:" in first["message"]
    assert "로스컷:" in first["message"]
    assert "🧩 체크" in first["message"]
    assert "20일 변동성 < 5.9%" in first["message"]
    assert "비중 변경:" in first["message"]
    assert "📈 시장 요약" in first["message"]
    assert "SPY200 이격도" in first["message"]
    assert "QQQ RSI(14)" in first["message"]


def test_run_daily_signal_alert_dry_run_does_not_persist_state(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    _write_csv(signal_csv)
    _write_data_csv(data_csv)

    calls: list[dict] = []

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        calls.append({"text": text, "dry_run": dry_run})
        return {"sent": True, "dry_run": dry_run}

    first = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=True,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=True,
        sender=fake_sender,
    )

    assert first["sent"] is True
    assert second["sent"] is True
    assert second["skipped"] is False
    assert not state_file.exists()
    assert len(calls) == 2


def test_run_daily_signal_alert_uses_existing_entry_price_when_weight_not_increased(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    _write_csv(signal_csv)
    _write_data_csv(data_csv)
    state_file.write_text(
        '{"last_alert_key": "old", "entry_price": 49.2, "entry_date": "2026-03-01", "position_weight": 1.0}',
        encoding="utf-8",
    )

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    assert "진입가 $49.20" in result["message"]


def test_run_daily_signal_alert_compact_template_for_no_action_day(tmp_path) -> None:
    signal_csv = tmp_path / "signals_same.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    _write_same_weight_csv(signal_csv)
    _write_data_csv(data_csv)
    state_file.write_text('{"last_alert_key":"old","entry_price":49.2}', encoding="utf-8")

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    msg = result["message"]
    assert "📢 [액션 없음]" in msg
    assert "조건 " in msg and "/3 충족" in msg
    assert "run_id: daily-2026-03-06" in msg


def test_run_daily_signal_alert_raises_on_missing_required_columns(tmp_path) -> None:
    signal_csv = tmp_path / "signals_bad.csv"
    state_file = tmp_path / "state.json"
    signal_csv.write_text("time,S2_code\n2026-03-05,1\n2026-03-06,2\n", encoding="utf-8")

    try:
        run_daily_signal_alert(
            signal_csv_path=signal_csv,
            state_path=state_file,
            bot_token="token",
            chat_id="chat",
            dry_run=True,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "missing required columns" in str(exc)


def test_run_daily_signal_alert_raises_on_invalid_weight_value(tmp_path) -> None:
    signal_csv = tmp_path / "signals_bad_weight.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    _write_data_csv(data_csv)
    signal_csv.write_text(
        "time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight\n"
        "2026-03-05,0,0.0,1,abc,0,0.0\n"
        "2026-03-06,0,0.0,2,0.95,0,0.0\n",
        encoding="utf-8",
    )

    try:
        run_daily_signal_alert(
            signal_csv_path=signal_csv,
            data_csv_path=data_csv,
            state_path=state_file,
            bot_token="token",
            chat_id="chat",
            dry_run=True,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "invalid S2_weight value" in str(exc)
