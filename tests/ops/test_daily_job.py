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

MANUAL_ACTION_SAMPLE = """{
  "positions": [
    {
      "account_id": "samsung-core",
      "asset_id": "tqqq-core",
      "manager_id": "core_strategy",
      "symbol": "TQQQ",
      "name": "ProShares UltraPro QQQ",
      "quantity": 120,
      "avg_cost_krw": 76000,
      "market_price_krw": 75225,
      "market_value_krw": 9027000
    }
  ],
  "cash_debt": [
    {
      "entry_id": "cash-main",
      "kind": "cash",
      "label": "투자대기현금",
      "balance_krw": 1500000
    }
  ],
  "stock_watchlist": [],
  "property_watchlist": [],
  "transactions": []
}"""

MANUAL_HOLD_SAMPLE = """{
  "positions": [
    {
      "account_id": "samsung-core",
      "asset_id": "tqqq-core",
      "manager_id": "core_strategy",
      "symbol": "TQQQ",
      "name": "ProShares UltraPro QQQ",
      "quantity": 90,
      "avg_cost_krw": 76000,
      "market_price_krw": 75225,
      "market_value_krw": 6770250
    }
  ],
  "cash_debt": [
    {
      "entry_id": "cash-main",
      "kind": "cash",
      "label": "투자대기현금",
      "balance_krw": 1148171
    }
  ],
  "stock_watchlist": [],
  "property_watchlist": [],
  "transactions": []
}"""


def _write_csv(path: Path) -> None:
    path.write_text(CSV_SAMPLE, encoding="utf-8")


def _write_data_csv(path: Path) -> None:
    path.write_text(DATA_SAMPLE, encoding="utf-8")


def _write_same_weight_csv(path: Path) -> None:
    path.write_text(CSV_SAME_WEIGHT_SAMPLE, encoding="utf-8")


def _write_manual(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_run_daily_signal_alert_skips_duplicate_on_second_run(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    _write_csv(signal_csv)
    _write_data_csv(data_csv)
    _write_manual(manual_file, MANUAL_ACTION_SAMPLE)

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
        manual_truth_path=manual_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
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
    assert "🟠 오늘 판단: 감량" in first["message"]
    assert "🛒 실행 액션" in first["message"]
    assert "기준가: 오늘 종가 $51.00" in first["message"]
    assert "예상 주문금액:" in first["message"]
    assert "📊 오늘 시장 / 내 자산" in first["message"]
    assert "TQQQ 종가: $51.00" in first["message"]
    assert "내 TQQQ 자산 변화:" in first["message"]
    assert "현재 평가금액:" in first["message"]
    assert "기술리포트" in first["message"]
    assert "전략: B0_DZ 90% + GLD 10%" in first["message"]
    # legacy CSV without allocation columns: falls back to 0.90*p / 0.90*(1-p) / 0.10
    assert "목표 비중: TQQQ 22.50% / SGOV 67.50% / GLD 10.00%" in first["message"]
    assert "- TQQQ: 90.00% → 22.50% (매도 67.50%p)" in first["message"]
    assert "- SGOV: 0.00% → 67.50% (매수 67.50%p)" in first["message"]
    assert "- GLD: 유지 (목표 10%)" in first["message"]
    assert "금 10% 고정(연 1회 리밸런싱)" in first["message"]
    assert "연 1회 금 리밸런싱일" not in first["message"]
    assert first["new_allocation"] == {"TQQQ": 0.225, "SGOV": 0.675, "GLD": 0.1}


def test_run_daily_signal_alert_dry_run_does_not_persist_state(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    _write_csv(signal_csv)
    _write_data_csv(data_csv)
    _write_manual(manual_file, MANUAL_ACTION_SAMPLE)

    calls: list[dict] = []

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        calls.append({"text": text, "dry_run": dry_run})
        return {"sent": True, "dry_run": dry_run}

    first = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
        bot_token="token",
        chat_id="chat",
        dry_run=True,
        sender=fake_sender,
    )
    second = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
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
    signal_csv = tmp_path / "signals_same.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    _write_same_weight_csv(signal_csv)
    _write_data_csv(data_csv)
    _write_manual(manual_file, MANUAL_HOLD_SAMPLE)
    state_file.write_text(
        '{"last_alert_key": "old", "entry_price": 49.2, "entry_date": "2026-03-01", "position_weight": 0.95}',
        encoding="utf-8",
    )

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    assert "로스컷 감시:" in result["message"]
    assert "$46.30" in result["message"]


def test_run_daily_signal_alert_compact_template_for_no_action_day(tmp_path) -> None:
    signal_csv = tmp_path / "signals_same.csv"
    data_csv = tmp_path / "data.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    _write_same_weight_csv(signal_csv)
    _write_data_csv(data_csv)
    _write_manual(manual_file, MANUAL_HOLD_SAMPLE)
    state_file.write_text('{"last_alert_key":"old","entry_price":49.2}', encoding="utf-8")

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    msg = result["message"]
    assert "🟢 오늘 판단: 유지" in msg
    assert "실행 액션: 오늘은 주문 없음" in msg
    assert "TQQQ 종가: $51.00" in msg
    assert "내 TQQQ 자산 변화:" in msg
    assert "기술리포트" in msg


def test_run_daily_signal_alert_shows_distance_to_next_buy_when_target_is_zero(tmp_path) -> None:
    signal_csv = tmp_path / "signals_zero.csv"
    data_csv = tmp_path / "data_zero.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    signal_csv.write_text(
        "time,S2_code,S2_weight,base_weight,buffer_active\n"
        "2026-03-26,0,0.0,0.0,false\n"
        "2026-03-27,0,0.0,0.0,false\n",
        encoding="utf-8",
    )
    data_csv.write_text(
        "time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,원달러환율\n"
        "2026-03-26,573.79,41.23,645.09,581.86,604.32,49.14,661.48,1500.97\n"
        "2026-03-27,562.58,38.78,634.09,574.73,604.29,49.15,661.63,1508.36\n",
        encoding="utf-8",
    )
    _write_manual(manual_file, '{"positions":[],"cash_debt":[{"entry_id":"cash-main","kind":"cash","label":"투자예수금","balance_krw":11220000}],"stock_watchlist":[],"property_watchlist":[],"transactions":[]}')

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    result = run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=state_file,
        manual_truth_path=manual_file,
        bot_token="token",
        chat_id="chat",
        dry_run=False,
        sender=fake_sender,
    )

    msg = result["message"]
    assert "매수까지 남은 조건" in msg
    assert "SPY bull 회복까지" in msg
    assert "TQQQ risk-on 회복까지" in msg
    assert "QQQ 단기 추세" in msg


def test_run_daily_signal_alert_raises_on_missing_required_columns(tmp_path) -> None:
    signal_csv = tmp_path / "signals_bad.csv"
    state_file = tmp_path / "state.json"
    manual_file = tmp_path / "manual.json"
    signal_csv.write_text("time,S2_code\n2026-03-05,1\n2026-03-06,2\n", encoding="utf-8")
    _write_manual(manual_file, MANUAL_ACTION_SAMPLE)

    try:
        run_daily_signal_alert(
            signal_csv_path=signal_csv,
            state_path=state_file,
            manual_truth_path=manual_file,
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
    manual_file = tmp_path / "manual.json"
    _write_data_csv(data_csv)
    _write_manual(manual_file, MANUAL_ACTION_SAMPLE)
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
            manual_truth_path=manual_file,
            bot_token="token",
            chat_id="chat",
            dry_run=True,
        )
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "invalid S2_weight value" in str(exc)


def _run_alloc_preview(tmp_path, signal_text, data_text=DATA_SAMPLE):
    signal_csv = tmp_path / "signals_alloc.csv"
    data_csv = tmp_path / "data.csv"
    manual_file = tmp_path / "manual.json"
    signal_csv.write_text(signal_text, encoding="utf-8")
    data_csv.write_text(data_text, encoding="utf-8")
    _write_manual(manual_file, MANUAL_ACTION_SAMPLE)

    def fake_sender(*, bot_token, chat_id, text, dry_run):
        return {"sent": True, "dry_run": dry_run}

    return run_daily_signal_alert(
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        state_path=tmp_path / "state.json",
        manual_truth_path=manual_file,
        bot_token=None,
        chat_id=None,
        dry_run=True,
        sender=fake_sender,
    )


def test_run_daily_signal_alert_uses_allocation_columns_and_lists_all_three_assets(tmp_path) -> None:
    result = _run_alloc_preview(
        tmp_path,
        "time,S2_code,S2_weight,tqqq_weight,sgov_weight,gld_weight\n"
        "2026-03-05,2,1.0,0.9,0.0,0.1\n"
        "2026-03-06,970,0.97,0.873,0.027,0.1\n",
    )

    msg = result["message"]
    assert "전략: B0_DZ 90% + GLD 10%" in msg
    assert "목표 비중: TQQQ 87.30% / SGOV 2.70% / GLD 10.00%" in msg
    assert "- TQQQ: 90.00% → 87.30% (매도 2.70%p)" in msg
    assert "- SGOV: 0.00% → 2.70% (매수 2.70%p)" in msg
    assert "- GLD: 유지 (목표 10%)" in msg
    assert "금 10% 고정(연 1회 리밸런싱)" in msg
    assert "연 1회 금 리밸런싱일" not in msg
    assert "완충" not in msg
    alloc = result["new_allocation"]
    assert abs(sum(alloc.values()) - 1.0) < 1e-9


def test_run_daily_signal_alert_order_quantity_uses_tqqq_target_not_raw_signal(tmp_path) -> None:
    # investable total = 9,027,000 + 1,500,000; target TQQQ = 0.9 * p (p = 1.0 -> 90%)
    result = _run_alloc_preview(
        tmp_path,
        "time,S2_code,S2_weight\n2026-03-05,2,1.0\n2026-03-06,2,1.0\n",
    )
    msg = result["message"]
    close_krw = 51.0 * 1475.0
    total = 9_027_000 + 1_500_000
    # actual TQQQ value is revalued at today's close inside the job; quantity 120
    gap = total * 0.90 - 120 * close_krw
    expected_qty = int(round(abs(gap) / close_krw))
    verb = "매수" if gap > 0 else "매도"
    if expected_qty > 0:
        assert f"- TQQQ {expected_qty}주 {verb}" in msg
    else:
        assert "오늘은 주문 없음" in msg


def test_run_daily_signal_alert_first_session_of_year_adds_gold_rebalance_reminder(tmp_path) -> None:
    result = _run_alloc_preview(
        tmp_path,
        "time,S2_code,S2_weight\n2025-12-31,2,1.0\n2026-01-02,2,1.0\n",
        "time,QQQ종가,TQQQ종가,SPY종가,원달러환율\n2025-12-31,100.0,50.0,600.0,1470.0\n2026-01-02,102.0,51.0,605.0,1475.0\n",
    )
    assert "🔁 연 1회 금 리밸런싱일: GLD를 전체 자산의 10%로 맞추세요" in result["message"]


def test_run_daily_signal_alert_mid_year_has_no_gold_rebalance_reminder(tmp_path) -> None:
    result = _run_alloc_preview(
        tmp_path,
        "time,S2_code,S2_weight\n2026-03-05,2,1.0\n2026-03-06,2,1.0\n",
    )
    assert "연 1회 금 리밸런싱일" not in result["message"]
    assert "- GLD: 유지 (목표 10%)" in result["message"] or "오늘은 주문 없음" in result["message"]
