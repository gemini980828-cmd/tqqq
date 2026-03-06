from pathlib import Path

from app.api.main import build_dashboard_snapshot
from tqqq_strategy.ops.dashboard_snapshot import generate_dashboard_snapshot


SIGNALS = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-04,0,0.0,0,0.0,0,0.0
2026-03-05,0,0.0,1,0.1,1,0.1
2026-03-06,0,0.0,2,1.0,2,1.0
"""

DATA = """time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,TQQQ200일 이격도
2026-02-05,100,40,500,101,99,39,490,102.56
2026-02-06,101,41,501,101,99,39,490,105.13
2026-02-09,102,42,503,101,99,39,490,107.69
2026-02-10,103,43,504,101,99,39,490,110.26
2026-02-11,104,44,505,101,99,39,490,112.82
2026-02-12,105,45,506,101,99,39,490,115.38
2026-02-13,106,46,507,101,99,39,490,117.95
2026-02-16,107,47,508,101,99,39,490,120.51
2026-02-17,108,48,509,101,99,39,490,123.08
2026-02-18,109,49,510,101,99,39,490,125.64
2026-02-19,110,50,511,101,99,39,490,128.21
2026-02-20,111,51,512,101,99,39,490,130.77
2026-02-23,112,52,513,101,99,39,490,133.33
2026-02-24,113,53,514,101,99,39,490,135.90
2026-02-25,114,54,515,101,99,39,490,138.46
2026-02-26,115,55,516,101,99,39,490,141.03
2026-02-27,116,56,517,101,99,39,490,143.59
2026-03-02,117,57,518,101,99,39,490,146.15
2026-03-03,118,58,519,101,99,39,490,148.72
2026-03-04,119,59,520,120,100,39,490,151.28
2026-03-05,120,60,521,121,100,39,490,153.85
2026-03-06,121,61,522,122,100,39,490,156.41
"""

METRICS = """CAGR,MDD,AnnualVol,Sharpe,Sortino,Calmar,WinRateDaily,ProfitFactor,UlcerIndex,BetaVsQQQ,MaxDDDurationDays,AfterTaxCAGR
0.3506,-0.3421,0.36,1.0,1.09,1.02,0.39,1.23,14.58,1.01,381,0.3216
"""

EQUITY = "date,weight,equity,taxed_equity\n" + "\n".join(
    f"2026-02-{day:02d},1.0,{100 + idx},{100 + idx}" for idx, day in enumerate(range(1, 23), start=0)
) + "\n2026-03-05,1.0,124,124\n2026-03-06,1.0,126,126\n"

STATE = '{"last_alert_key":"2026-03-06:1->2","last_sent_at":"2026-03-06T22:30:00+00:00"}'

MANUAL = """{
  "positions": [
    {
      "account_id": "samsung-core",
      "asset_id": "tqqq-core",
      "manager_id": "core_strategy",
      "symbol": "TQQQ",
      "name": "ProShares UltraPro QQQ",
      "quantity": 120.0,
      "avg_cost_krw": 76000,
      "market_price_krw": 81000,
      "market_value_krw": 9720000
    }
  ],
  "cash_debt": [
    {
      "entry_id": "cash-main",
      "kind": "cash",
      "label": "투자대기현금",
      "balance_krw": 15000000
    },
    {
      "entry_id": "loan-margin",
      "kind": "debt",
      "label": "마이너스통장",
      "balance_krw": 2000000
    }
  ],
  "stock_watchlist": [
    {
      "idea_id": "stock-1",
      "symbol": "NVDA",
      "status": "관찰",
      "memo": "AI 인프라 핵심 수혜"
    }
  ],
  "property_watchlist": [
    {
      "property_id": "apt-1",
      "name": "마포래미안푸르지오",
      "region": "서울 마포구",
      "status": "관심"
    }
  ]
}"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_dashboard_snapshot_v2_keys() -> None:
    snap = build_dashboard_snapshot({})
    required = {"action_hero", "kpi_cards", "risk_gauges", "event_timeline", "ops_log"}
    assert required.issubset(set(snap.keys()))


def test_generate_dashboard_snapshot_uses_real_files(tmp_path: Path) -> None:
    snap = generate_dashboard_snapshot(
        signal_csv_path=_write(tmp_path / "signals.csv", SIGNALS),
        data_csv_path=_write(tmp_path / "data.csv", DATA),
        metrics_csv_path=_write(tmp_path / "metrics.csv", METRICS),
        equity_csv_path=_write(tmp_path / "equity.csv", EQUITY),
        state_path=_write(tmp_path / "state.json", STATE),
        manual_truth_path=_write(tmp_path / "wealth_manual.json", MANUAL),
    )

    assert snap["action_hero"]["action"] == "매수"
    assert snap["action_hero"]["target_weight_pct"] == 100.0
    assert snap["kpi_cards"]["cagr_pct"] == 32.16
    assert snap["kpi_cards"]["mdd_pct"] == -34.21
    assert snap["risk_gauges"]["vol20"]["status"] in {"green", "amber", "red"}
    assert snap["event_timeline"], "expected at least one event"
    assert any(
        item["date"] == "2026-03-06" and item["type"] == "비중 변경" and "10.00% → 100.00%" in item["detail"]
        for item in snap["event_timeline"]
    )
    assert snap["ops_log"]["alert_key"] == "2026-03-06:1->2"
    assert snap["wealth_overview"]["net_worth_krw"] == 22720000
    assert snap["core_strategy_actuals"]["symbol"] == "TQQQ"
    assert snap["manager_cards"][0]["manager_id"] == "core_strategy"
