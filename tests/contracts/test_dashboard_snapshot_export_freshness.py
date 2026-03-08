from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SIGNALS = """time,S1_code,S1_weight,S2_code,S2_weight,S3_code,S3_weight
2026-03-05,0,0.0,1,0.1,1,0.1
2026-03-06,0,0.0,2,1.0,2,1.0
"""

DATA = """time,QQQ종가,TQQQ종가,SPY종가,QQQ3일선,QQQ161일선,TQQQ200일선,SPY200일선,TQQQ200일 이격도
2026-02-10,103,43,504,101,99,39,490,110.26
2026-02-11,104,44,505,101,99,39,490,112.82
2026-02-12,105,45,506,101,99,39,490,115.38
2026-02-13,106,46,507,101,99,39,490,117.95
2026-02-14,107,47,508,101,99,39,490,120.51
2026-02-17,108,48,509,101,99,39,490,123.08
2026-02-18,109,49,510,101,99,39,490,125.64
2026-02-19,110,50,511,101,99,39,490,128.21
2026-02-20,111,51,512,101,99,39,490,130.77
2026-02-21,112,52,513,101,99,39,490,133.33
2026-02-24,113,53,514,101,99,39,490,135.90
2026-02-25,114,54,515,101,99,39,490,138.46
2026-02-26,115,55,516,101,99,39,490,141.03
2026-02-27,116,56,517,101,99,39,490,143.59
2026-02-28,117,57,518,101,99,39,490,146.15
2026-03-03,118,58,519,101,99,39,490,148.72
2026-03-04,119,59,520,120,100,39,490,151.28
2026-03-05,120,60,521,121,100,39,490,153.85
2026-03-06,121,61,522,122,100,39,490,156.41
2026-03-07,122,62,523,123,100,39,490,158.97
2026-03-08,123,63,524,124,100,39,490,161.54
2026-03-09,124,64,525,125,100,39,490,164.10
"""

METRICS = """CAGR,MDD,AnnualVol,Sharpe,Sortino,Calmar,WinRateDaily,ProfitFactor,UlcerIndex,BetaVsQQQ,MaxDDDurationDays,AfterTaxCAGR
0.3506,-0.3421,0.36,1.0,1.09,1.02,0.39,1.23,14.58,1.01,381,0.3216
"""

EQUITY = "date,weight,equity,taxed_equity\n" + "\n".join(
    f"2026-02-{day:02d},1.0,{100 + idx},{100 + idx}" for idx, day in enumerate(range(1, 23), start=0)
) + "\n2026-03-05,1.0,124,124\n2026-03-06,1.0,126,126\n"

STATE = '{"last_alert_key":"2026-03-06:1->2","last_sent_at":"2026-03-06T22:30:00+00:00","next_run_at":"2099-12-31T00:00:00+00:00"}'

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
  ],
  "transactions": []
}
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_refresh_and_export_keep_summary_cache_fresh(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    signals = _write(tmp_path / "signals.csv", SIGNALS)
    data = _write(tmp_path / "data.csv", DATA)
    metrics = _write(tmp_path / "metrics.csv", METRICS)
    equity = _write(tmp_path / "equity.csv", EQUITY)
    state = _write(tmp_path / "state.json", STATE)
    manual = _write(tmp_path / "wealth_manual.json", MANUAL)
    summary_store = tmp_path / "wealth_manager_summaries.json"
    out = tmp_path / "dashboard_snapshot.json"

    common_args = [
        "--signals",
        str(signals),
        "--data",
        str(data),
        "--metrics",
        str(metrics),
        "--state",
        str(state),
        "--equity",
        str(equity),
        "--manual-truth",
        str(manual),
        "--summary-store",
        str(summary_store),
    ]
    subprocess.run(
        [sys.executable, "ops/scripts/run_manager_summaries.py", *common_args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "ops/scripts/export_dashboard_snapshot.py", *common_args, "--out", str(out)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    summary_payload = json.loads(summary_store.read_text(encoding="utf-8"))
    snapshot = json.loads(out.read_text(encoding="utf-8"))

    source_versions = {record["source_version"] for record in summary_payload.values()}
    assert len(source_versions) == 1
    assert snapshot["meta"]["summary_source_version"] == next(iter(source_versions))
    assert all(record["stale"] is False for record in summary_payload.values())
    assert all(record["stale"] is False for record in snapshot["manager_summaries"].values())
    assert snapshot["ops_log"]["next_run_at"] == "2099-12-31T00:00:00+00:00"
