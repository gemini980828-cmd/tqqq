from __future__ import annotations

import json
from pathlib import Path

import pytest

from tqqq_strategy.wealth.summary_store import (
    DEFAULT_SUMMARY_STORE_PATH,
    load_manager_summary,
    load_summary_store,
    save_manager_summary,
)


SUMMARY_RECORD = {
    "manager_id": "core_strategy",
    "summary_text": "목표 비중 대비 실보유가 부족하여 증액이 필요합니다.",
    "key_points": ["실보유 31.59%", "목표 95.00%"],
    "warnings": ["리밸런싱 gap이 큽니다."],
    "recommended_actions": ["장마감 기준 추가 매수 검토"],
    "generated_at": "2026-03-06T10:30:00+00:00",
    "source_version": "wealth_manual.json:2026-03-06",
    "stale": False,
}


def test_default_summary_store_path_points_to_reports_cache() -> None:
    assert DEFAULT_SUMMARY_STORE_PATH == Path("reports/wealth_manager_summaries.json")


def test_save_and_load_manager_summary_round_trips_metadata(tmp_path: Path) -> None:
    store_path = tmp_path / "manager_summaries.json"

    saved = save_manager_summary(SUMMARY_RECORD, path=store_path)
    loaded = load_manager_summary("core_strategy", path=store_path)
    raw_store = json.loads(store_path.read_text(encoding="utf-8"))

    assert saved == SUMMARY_RECORD
    assert loaded == SUMMARY_RECORD
    assert raw_store["core_strategy"]["summary_text"] == SUMMARY_RECORD["summary_text"]
    assert raw_store["core_strategy"]["key_points"] == SUMMARY_RECORD["key_points"]
    assert raw_store["core_strategy"]["recommended_actions"] == SUMMARY_RECORD["recommended_actions"]


def test_load_manager_summary_marks_summary_stale_when_source_version_changes(tmp_path: Path) -> None:
    store_path = tmp_path / "manager_summaries.json"
    save_manager_summary(SUMMARY_RECORD, path=store_path)

    stale_record = load_manager_summary(
        "core_strategy",
        path=store_path,
        expected_source_version="wealth_manual.json:2026-03-07",
    )
    store = load_summary_store(store_path)

    assert stale_record is not None
    assert stale_record["stale"] is True
    assert store["core_strategy"]["stale"] is True
    assert store["core_strategy"]["source_version"] == SUMMARY_RECORD["source_version"]


def test_load_manager_summary_clears_stale_flag_when_expected_source_matches(tmp_path: Path) -> None:
    store_path = tmp_path / "manager_summaries.json"
    stale_seed = {**SUMMARY_RECORD, "stale": True}
    save_manager_summary(stale_seed, path=store_path)

    fresh_record = load_manager_summary(
        "core_strategy",
        path=store_path,
        expected_source_version=SUMMARY_RECORD["source_version"],
    )

    assert fresh_record is not None
    assert fresh_record["stale"] is False


def test_save_manager_summary_rejects_missing_cache_metadata_lists(tmp_path: Path) -> None:
    store_path = tmp_path / "manager_summaries.json"

    with pytest.raises(ValueError, match="key_points"):
        save_manager_summary(
            {
                "manager_id": "core_strategy",
                "summary_text": "invalid",
                "warnings": [],
                "recommended_actions": [],
                "generated_at": "2026-03-06T10:30:00+00:00",
                "source_version": "v1",
                "stale": False,
            },
            path=store_path,
        )
