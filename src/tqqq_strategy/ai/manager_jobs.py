from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from tqqq_strategy.ai.stock_research_status import normalize_stock_status

from tqqq_strategy.wealth import (
    DEFAULT_MANUAL_TRUTH_PATH,
    DEFAULT_SUMMARY_STORE_PATH,
    build_core_strategy_position,
    build_liquidity_summary,
    build_summary_source_version,
    load_manual_truth,
    save_manager_summary,
)

MANAGER_IDS = (
    "core_strategy",
    "stock_research",
    "real_estate",
    "cash_debt",
)


def _ensure_generated_at(value: str | None = None) -> str:
    return str(value) if value else datetime.now(timezone.utc).isoformat()


def _count_status(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        key = str(record.get("status") or "미분류").strip()
        counts[key] = counts.get(key, 0) + 1
    return counts


def _format_krw(value: float | int) -> str:
    return f"{int(round(float(value))):,}원"


def _build_core_strategy_summary(snapshot: Mapping[str, Any], source_version: str, generated_at: str) -> dict[str, Any]:
    actuals = dict(snapshot.get("core_strategy_actuals") or snapshot.get("core_strategy_position") or {})
    action_hero = dict(snapshot.get("action_hero") or {})
    actual_weight = float(actuals.get("actual_weight_pct") or 0.0)
    target_weight = float(actuals.get("target_weight_pct") or action_hero.get("target_weight_pct") or 0.0)
    gap_weight = float(actuals.get("gap_weight_pct") or 0.0)
    gap_value = abs(int(round(float(actuals.get("rebalance_gap_krw") or 0.0))))
    action = str(action_hero.get("action") or "유지")
    reason = str(action_hero.get("reason_summary") or "전략 요약 없음")

    warnings: list[str] = []
    if abs(gap_weight) >= 5.0:
        warnings.append(f"목표 대비 괴리 {gap_weight:.2f}%p가 커서 리밸런싱 우선순위가 높습니다.")

    if action == "매수":
        recommended_actions = ["장마감 기준 추가 매수 검토"]
    elif action == "매도":
        recommended_actions = ["장마감 기준 감량/정리 검토"]
    else:
        recommended_actions = ["현재 전략 비중 유지"]

    return {
        "manager_id": "core_strategy",
        "summary_text": f"실보유 {actual_weight:.2f}% / 목표 {target_weight:.2f}% · {reason}",
        "key_points": [
            f"실보유 {actual_weight:.2f}%",
            f"목표 {target_weight:.2f}%",
            f"리밸런싱 gap {_format_krw(gap_value)}",
        ],
        "warnings": warnings,
        "recommended_actions": recommended_actions,
        "generated_at": generated_at,
        "source_version": source_version,
        "stale": False,
    }


def _build_stock_research_summary(manual_inputs: Mapping[str, list[dict[str, Any]]], source_version: str, generated_at: str) -> dict[str, Any]:
    watchlist = list(manual_inputs.get("stock_watchlist", []))
    normalized_statuses = [normalize_stock_status(row.get("status")) for row in watchlist]
    candidate_count = sum(1 for status in normalized_statuses if status == "후보")
    observe_count = sum(1 for status in normalized_statuses if status == "관찰")
    first_candidate = next(
        (str(row.get("symbol")) for row in watchlist if normalize_stock_status(row.get("status")) == "후보"),
        None,
    )
    recommended_action = f"{first_candidate} 후속 리서치 정리" if first_candidate else "관심종목 신규 발굴"

    return {
        "manager_id": "stock_research",
        "summary_text": f"관심종목 {len(watchlist)}개를 추적 중입니다.",
        "key_points": [
            f"관심종목 {len(watchlist)}개",
            f"후보 {candidate_count}개",
            f"관찰 {observe_count}개",
        ],
        "warnings": [] if watchlist else ["관심종목이 비어 있습니다."],
        "recommended_actions": [recommended_action],
        "generated_at": generated_at,
        "source_version": source_version,
        "stale": False,
    }


def _build_real_estate_summary(manual_inputs: Mapping[str, list[dict[str, Any]]], source_version: str, generated_at: str) -> dict[str, Any]:
    watchlist = list(manual_inputs.get("property_watchlist", []))
    counts = _count_status(watchlist)
    review_count = counts.get("검토", 0)
    interest_count = counts.get("관심", 0)
    recommended_action = "검토 단지 체크리스트 업데이트" if review_count else "관심 단지 신규 후보 보강"

    return {
        "manager_id": "real_estate",
        "summary_text": f"관심 단지 {len(watchlist)}개를 팔로잉 중입니다.",
        "key_points": [
            f"관심 단지 {len(watchlist)}개",
            f"검토 {review_count}개",
            f"관심 {interest_count}개",
        ],
        "warnings": [] if review_count else ["즉시 검토 중인 단지가 없습니다."],
        "recommended_actions": [recommended_action],
        "generated_at": generated_at,
        "source_version": source_version,
        "stale": False,
    }


def _build_cash_debt_summary(manual_inputs: Mapping[str, list[dict[str, Any]]], source_version: str, generated_at: str) -> dict[str, Any]:
    liquidity = build_liquidity_summary(dict(manual_inputs))
    warnings: list[str] = []
    if int(liquidity["debt_krw"]) > 0:
        warnings.append(f"부채 {_format_krw(liquidity['debt_krw'])}이 있어 상환 우선순위를 함께 점검해야 합니다.")
    if int(liquidity["net_liquidity_krw"]) < 0:
        warnings.append("순유동성이 음수입니다.")

    recommended_action = "현금 방어 여력 점검" if warnings else "현금/부채 현황 유지"
    return {
        "manager_id": "cash_debt",
        "summary_text": f"현금 {_format_krw(liquidity['cash_krw'])} / 부채 {_format_krw(liquidity['debt_krw'])}",
        "key_points": [
            f"현금 {_format_krw(liquidity['cash_krw'])}",
            f"부채 {_format_krw(liquidity['debt_krw'])}",
            f"유동성 비중 {float(liquidity['liquidity_ratio_pct']):.2f}%",
        ],
        "warnings": warnings,
        "recommended_actions": [recommended_action],
        "generated_at": generated_at,
        "source_version": source_version,
        "stale": False,
    }


def build_manager_summary_records(
    snapshot: Mapping[str, Any],
    manual_inputs: Mapping[str, list[dict[str, Any]]],
    *,
    source_version: str,
    generated_at: str,
) -> dict[str, dict[str, Any]]:
    return {
        "core_strategy": _build_core_strategy_summary(snapshot, source_version, generated_at),
        "stock_research": _build_stock_research_summary(manual_inputs, source_version, generated_at),
        "real_estate": _build_real_estate_summary(manual_inputs, source_version, generated_at),
        "cash_debt": _build_cash_debt_summary(manual_inputs, source_version, generated_at),
    }


def _build_refresh_snapshot(signal_csv_path: str | Path, manual_inputs: Mapping[str, list[dict[str, Any]]]) -> dict[str, Any]:
    signals = pd.read_csv(signal_csv_path, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
    latest = signals.iloc[-1]
    previous = signals.iloc[-2] if len(signals) >= 2 else latest
    target_weight_pct = round(float(latest["S2_weight"]) * 100.0, 2)
    prev_weight_pct = round(float(previous["S2_weight"]) * 100.0, 2)
    action = "유지"
    if target_weight_pct > prev_weight_pct + 1e-9:
        action = "매수"
    elif target_weight_pct < prev_weight_pct - 1e-9:
        action = "매도"

    core_actuals = build_core_strategy_position(dict(manual_inputs), target_weight_pct=target_weight_pct)
    return {
        "action_hero": {
            "action": action,
            "target_weight_pct": target_weight_pct,
            "reason_summary": f"코어전략 목표 비중 {target_weight_pct:.2f}% 기준 요약",
            "updated_at": latest["time"].isoformat(),
        },
        "core_strategy_actuals": core_actuals,
        "core_strategy_position": core_actuals,
    }


def refresh_manager_summaries(
    *,
    signal_csv_path: str | Path = Path("reports/signals_s1_s2_s3_user_original.csv"),
    data_csv_path: str | Path = Path("data/user_input.csv"),
    metrics_csv_path: str | Path = Path("reports/backtest_metrics_primary.csv"),
    state_path: str | Path = Path("reports/daily_telegram_alert_state.json"),
    equity_csv_path: str | Path = Path("reports/backtest_equity_primary.csv"),
    manual_truth_path: str | Path = DEFAULT_MANUAL_TRUTH_PATH,
    summary_store_path: str | Path = DEFAULT_SUMMARY_STORE_PATH,
    generated_at: str | None = None,
) -> dict[str, dict[str, Any]]:
    _ = (data_csv_path, metrics_csv_path, state_path, equity_csv_path)
    manual_path = Path(manual_truth_path)
    manual_inputs = load_manual_truth(manual_path)
    snapshot = _build_refresh_snapshot(signal_csv_path, manual_inputs)
    snapshot_updated_at = str((snapshot.get("action_hero") or {}).get("updated_at") or "")
    resolved_generated_at = generated_at or snapshot_updated_at or _ensure_generated_at()
    source_version = build_summary_source_version(
        manual_inputs,
        snapshot_updated_at or resolved_generated_at,
        source_label=manual_path.name,
    )
    records = build_manager_summary_records(
        snapshot,
        manual_inputs,
        source_version=source_version,
        generated_at=resolved_generated_at,
    )
    for record in records.values():
        save_manager_summary(record, path=summary_store_path)
    return records
