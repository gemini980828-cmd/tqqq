from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tqqq_strategy.wealth import build_core_strategy_position, build_manager_cards, build_wealth_overview, load_manual_inputs


DEFAULT_MANUAL_INPUTS_PATH = Path("data/manual/wealth_manual.json")


def _status_lower_better(value: float, threshold: float, amber_ratio: float = 0.85) -> str:
    if pd.isna(value):
        return "red"
    if value >= threshold:
        return "red"
    if value >= threshold * amber_ratio:
        return "amber"
    return "green"


def _status_higher_better(value: float, threshold: float, amber_ratio: float = 1.03) -> str:
    if pd.isna(value):
        return "red"
    if value <= threshold:
        return "red"
    if value <= threshold * amber_ratio:
        return "amber"
    return "green"


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _build_reason_summary(action: str, target_weight_pct: float, dist200: float, vol20: float, spy200: float) -> str:
    if action == "매수":
        return f"추세 강화로 비중 확대 (Dist200 {dist200:.2f}, Vol20 {vol20:.2f}%)"
    if action == "매도":
        if target_weight_pct <= 0:
            return f"리스크 조건으로 현금 전환 (Vol20 {vol20:.2f}% / SPY200 {spy200:.2f})"
        return f"리스크 관리 차원 감량 (목표 비중 {target_weight_pct:.0f}%)"
    return f"추세 조건 유지 (Dist200 {dist200:.2f} / SPY200 {spy200:.2f})"


def _build_condition_pass_rate(row: pd.Series, vol20: float, dist200: float, spy200: float) -> str:
    checks = [
        vol20 < 5.9 if pd.notna(vol20) else False,
        spy200 > 97.75 if pd.notna(spy200) else False,
        dist200 >= 101.0 if pd.notna(dist200) else False,
        (
            float(row.get("QQQ3일선", float("nan"))) > float(row.get("QQQ161일선", float("nan")))
            if pd.notna(row.get("QQQ3일선")) and pd.notna(row.get("QQQ161일선"))
            else False
        ),
        dist200 < 139.0 if pd.notna(dist200) else False,
        vol20 < 6.0 if pd.notna(vol20) else False,
    ]
    return f"{sum(1 for x in checks if x)}/{len(checks)}"


def _build_event_timeline(signals: pd.DataFrame, limit: int = 5) -> list[dict[str, str]]:
    timeline: list[dict[str, str]] = []
    recent = signals.tail(90).reset_index(drop=True)
    for i in range(1, len(recent)):
        prev = float(recent.iloc[i - 1]["S2_weight"])
        cur = float(recent.iloc[i]["S2_weight"])
        if abs(prev - cur) < 1e-12:
            continue
        date = recent.iloc[i]["time"].strftime("%Y-%m-%d")
        if prev <= 1e-9 and cur > 1e-9:
            event_type = "재진입"
            detail = f"{prev * 100:.2f}% → {cur * 100:.2f}% 진입"
        elif prev > 1e-9 and cur <= 1e-9:
            event_type = "강제청산"
            detail = f"{prev * 100:.2f}% → 0.00% 전환"
        elif abs(prev - 1.0) < 1e-9 and abs(cur - 0.95) < 1e-9:
            event_type = "TP10"
            detail = "100% → 95% 감량"
        else:
            event_type = "비중 변경"
            detail = f"{prev * 100:.2f}% → {cur * 100:.2f}% 조정"
        timeline.append({"date": date, "type": event_type, "detail": detail})
    return list(reversed(timeline[-limit:]))


def generate_dashboard_snapshot(
    signal_csv_path: Path | str = Path("reports/signals_s1_s2_s3_user_original.csv"),
    data_csv_path: Path | str = Path("data/user_input.csv"),
    metrics_csv_path: Path | str = Path("reports/backtest_metrics_primary.csv"),
    state_path: Path | str = Path("reports/daily_telegram_alert_state.json"),
    equity_csv_path: Path | str = Path("reports/backtest_equity_primary.csv"),
    manual_inputs_path: Path | str | None = None,
    manual_truth_path: Path | str | None = None,
) -> dict[str, Any]:
    """Generate the action-first dashboard snapshot plus wealth-foundation fields."""
    signal_csv = Path(signal_csv_path)
    data_csv = Path(data_csv_path)
    metrics_csv = Path(metrics_csv_path)
    state_file = Path(state_path)
    equity_csv = Path(equity_csv_path)

    signals = pd.read_csv(signal_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    market = pd.read_csv(data_csv, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    metrics = pd.read_csv(metrics_csv)
    equity = (
        pd.read_csv(equity_csv, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
        if equity_csv.exists()
        else pd.DataFrame()
    )
    state = _read_optional_json(state_file)
    resolved_manual_path = manual_truth_path or manual_inputs_path or DEFAULT_MANUAL_INPUTS_PATH
    manual_inputs = load_manual_inputs(resolved_manual_path)

    latest_signal = signals.iloc[-1]
    prev_signal = signals.iloc[-2] if len(signals) >= 2 else latest_signal
    latest_date = latest_signal["time"]
    market_row = market.loc[market["time"] == latest_date]
    market_latest = market_row.iloc[-1] if not market_row.empty else market.iloc[-1]

    target_weight = float(latest_signal["S2_weight"])
    prev_weight = float(prev_signal["S2_weight"])
    action = "유지"
    if target_weight > prev_weight + 1e-9:
        action = "매수"
    elif target_weight < prev_weight - 1e-9:
        action = "매도"

    tqqq_close = float(market_latest["TQQQ종가"])
    spy_close = float(market_latest["SPY종가"])
    spy_ma200 = float(market_latest["SPY200일선"])
    tqqq_ma200 = float(market_latest["TQQQ200일선"])
    vol20_series = market["TQQQ종가"].pct_change().rolling(20, min_periods=20).std(ddof=1) * 100.0
    vol20 = float(vol20_series.iloc[int(market_latest.name)]) if pd.notna(vol20_series.iloc[int(market_latest.name)]) else float("nan")
    spy200_dist = (spy_close / spy_ma200) * 100.0 if spy_ma200 else float("nan")
    tqqq_dist200 = (tqqq_close / tqqq_ma200) * 100.0 if tqqq_ma200 else float("nan")

    month_1_return_pct = float("nan")
    if not equity.empty and "taxed_equity" in equity.columns and len(equity) >= 22:
        month_1_return_pct = (float(equity["taxed_equity"].iloc[-1]) / float(equity["taxed_equity"].iloc[-22]) - 1.0) * 100.0

    metrics_row = metrics.iloc[0] if not metrics.empty else pd.Series(dtype=float)
    condition_pass_rate = _build_condition_pass_rate(market_latest, vol20, tqqq_dist200, spy200_dist)
    default_next_run = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=22, minute=30, second=0, microsecond=0)

    wealth_overview = build_wealth_overview(manual_inputs)
    home_overview = {
        "invested_krw": wealth_overview["invested_krw"],
        "cash_krw": wealth_overview["cash_krw"],
        "debt_krw": wealth_overview["debt_krw"],
        "net_worth_krw": wealth_overview["net_worth_krw"],
    }
    core_strategy_position = build_core_strategy_position(manual_inputs, target_weight_pct=round(target_weight * 100.0, 2))
    manager_cards = build_manager_cards(manual_inputs, target_weight_pct=round(target_weight * 100.0, 2))

    return {
        "action_hero": {
            "action": action,
            "target_weight_pct": round(target_weight * 100.0, 2),
            "reason_summary": _build_reason_summary(action, target_weight * 100.0, tqqq_dist200, vol20, spy200_dist),
            "updated_at": latest_date.isoformat(),
        },
        "kpi_cards": {
            "cagr_pct": round(float(metrics_row.get("AfterTaxCAGR", float("nan"))) * 100.0, 2),
            "mdd_pct": round(float(metrics_row.get("MDD", float("nan"))) * 100.0, 2),
            "month_1_return_pct": round(month_1_return_pct, 2) if pd.notna(month_1_return_pct) else float("nan"),
            "condition_pass_rate": condition_pass_rate,
        },
        "risk_gauges": {
            "vol20": {"value": round(vol20, 2), "threshold": 5.9, "status": _status_lower_better(vol20, 5.9)},
            "spy200_dist": {"value": round(spy200_dist, 2), "threshold": 97.75, "status": _status_higher_better(spy200_dist, 97.75)},
            "tqqq_dist200": {"value": round(tqqq_dist200, 2), "threshold": 101.0, "status": _status_higher_better(tqqq_dist200, 101.0)},
        },
        "event_timeline": _build_event_timeline(signals),
        "ops_log": {
            "run_id": f"daily-{latest_date.strftime('%Y-%m-%d')}",
            "alert_key": str(state.get("last_alert_key") or f"{latest_date.strftime('%Y-%m-%d')}:{prev_weight}->{target_weight}"),
            "last_success_at": str(state.get("last_sent_at") or latest_date.isoformat()),
            "next_run_at": str(state.get("next_run_at") or default_next_run.isoformat()),
        },
        "wealth_home": {
            "overview": home_overview,
            "manager_cards": manager_cards,
            "updated_at": latest_date.isoformat(),
        },
        "wealth_overview": wealth_overview,
        "manager_cards": manager_cards,
        "core_strategy_position": core_strategy_position,
        "core_strategy_actuals": core_strategy_position,
        "meta": {"manual_source_version": str(Path(resolved_manual_path).name)},
    }
