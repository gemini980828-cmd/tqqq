from __future__ import annotations

from pathlib import Path

from tqqq_strategy.ops.signal_preflight import verify_signal_ready


SIGNALS = """time,S2_code,S2_weight
2026-03-05,2,1.0
2026-03-06,3,0.9
"""

DATA = """time,QQQ종가,TQQQ종가,SPY종가,원달러환율
2026-03-05,100,50,500,1470
2026-03-06,101,51,501,1475
"""


def test_verify_signal_ready_accepts_matching_latest_dates(tmp_path: Path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    signal_csv.write_text(SIGNALS, encoding="utf-8")
    data_csv.write_text(DATA, encoding="utf-8")

    result = verify_signal_ready(signal_csv_path=signal_csv, data_csv_path=data_csv)

    assert result["ok"] is True
    assert result["signal_date"] == "2026-03-06"
    assert result["market_date"] == "2026-03-06"
    assert result["row_count"] == 2


def test_verify_signal_ready_rejects_stale_signal_date(tmp_path: Path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    signal_csv.write_text("time,S2_code,S2_weight\n2026-03-04,2,1.0\n2026-03-05,3,0.9\n", encoding="utf-8")
    data_csv.write_text(DATA, encoding="utf-8")

    try:
        verify_signal_ready(signal_csv_path=signal_csv, data_csv_path=data_csv)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "signal date" in str(exc)


def test_verify_signal_ready_rejects_missing_required_columns(tmp_path: Path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    signal_csv.write_text("time,S2_code\n2026-03-05,2\n2026-03-06,3\n", encoding="utf-8")
    data_csv.write_text(DATA, encoding="utf-8")

    try:
        verify_signal_ready(signal_csv_path=signal_csv, data_csv_path=data_csv)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "missing required columns" in str(exc)
