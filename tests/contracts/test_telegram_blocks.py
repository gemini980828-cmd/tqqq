import json

from app.api.main import build_dashboard_snapshot


def test_dashboard_contains_required_telegram_blocks() -> None:
    snap = build_dashboard_snapshot({})
    required = {"header", "position_change", "reason", "market_summary", "ops_log"}
    assert required.issubset(set(snap.keys()))


def test_dashboard_ops_log_contract_from_real_state_file(tmp_path) -> None:
    signal_csv = tmp_path / "signals.csv"
    data_csv = tmp_path / "data.csv"
    metrics_csv = tmp_path / "metrics.csv"
    state_json = tmp_path / "state.json"

    signal_csv.write_text(
        "time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight\n"
        "2026-03-05,2,1.0,2,1.0,2,1.0\n"
        "2026-03-06,2,1.0,2,1.0,2,1.0\n",
        encoding="utf-8",
    )
    data_csv.write_text(
        "time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,TQQQ200일 이격도\n"
        "2026-03-05,430,75,530,425,400,61,500,122.95\n"
        "2026-03-06,431,76,531,426,401,61.5,501,123.58\n",
        encoding="utf-8",
    )
    metrics_csv.write_text(
        "CAGR,MDD,AnnualVol,Sharpe,Sortino,Calmar,WinRateDaily,ProfitFactor,UlcerIndex,BetaVsQQQ,MaxDDDurationDays,AfterTaxCAGR\n"
        "0.35,-0.34,0.36,1.0,1.1,1.02,0.39,1.23,14.5,1.02,381,0.32\n",
        encoding="utf-8",
    )
    state_json.write_text(
        json.dumps(
            {
                "last_alert_key": "2026-03-06:2->2",
                "last_sent_at": "2026-03-06T15:59:00Z",
                "next_run_at": "2026-03-07T06:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    snap = build_dashboard_snapshot(
        None,
        signal_csv_path=signal_csv,
        data_csv_path=data_csv,
        metrics_csv_path=metrics_csv,
        state_path=state_json,
    )

    assert snap["ops_log"] == {
        "run_id": "daily-2026-03-06",
        "alert_key": "2026-03-06:2->2",
        "last_success_at": "2026-03-06T15:59:00Z",
        "next_run_at": "2026-03-07T06:00:00Z",
    }
