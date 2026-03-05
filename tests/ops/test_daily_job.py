from pathlib import Path

from tqqq_strategy.ops.daily_job import run_daily_signal_alert


CSV_SAMPLE = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,1.0,0,0.0
2026-03-06,0,0.0,3,0.25,0,0.0
"""


def _write_csv(path: Path) -> None:
    path.write_text(CSV_SAMPLE, encoding="utf-8")


def test_run_daily_signal_alert_skips_duplicate_on_second_run(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    state_file = tmp_path / "state.json"
    _write_csv(signal_csv)

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
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
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


def test_run_daily_signal_alert_dry_run_does_not_persist_state(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    state_file = tmp_path / "state.json"
    _write_csv(signal_csv)

    calls: list[dict] = []

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        calls.append({"text": text, "dry_run": dry_run})
        return {"sent": True, "dry_run": dry_run}

    first = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        state_path=state_file,
        bot_token="token",
        chat_id="chat",
        dry_run=True,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
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
    state_file = tmp_path / "state.json"
    signal_csv.write_text(
        "time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight\n"
        "2026-03-05,0,0.0,1,abc,0,0.0\n"
        "2026-03-06,0,0.0,2,0.95,0,0.0\n",
        encoding="utf-8",
    )

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
        assert "invalid S2_weight value" in str(exc)
