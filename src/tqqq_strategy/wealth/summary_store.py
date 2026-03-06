from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from tqqq_strategy.wealth.schema import validate_summary_record

DEFAULT_SUMMARY_STORE_PATH = Path("reports/wealth_manager_summaries.json")
SUMMARY_LIST_FIELDS = ("key_points", "warnings", "recommended_actions")


class SummaryStoreError(ValueError):
    pass


def _coerce_string_list(field: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise SummaryStoreError(f"summary {field} must be a list")
    return [str(item) for item in value]


def _normalize_summary_record(record: Mapping[str, object]) -> dict[str, Any]:
    normalized = validate_summary_record(record)
    for field in SUMMARY_LIST_FIELDS:
        if field not in record:
            raise SummaryStoreError(f"summary missing required fields: {field}")
        normalized[field] = _coerce_string_list(field, record[field])

    normalized["manager_id"] = str(normalized["manager_id"])
    normalized["summary_text"] = str(normalized["summary_text"])
    normalized["generated_at"] = str(normalized["generated_at"])
    normalized["source_version"] = str(normalized["source_version"])
    normalized["stale"] = bool(normalized["stale"])
    return normalized


def _read_store(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SummaryStoreError("summary store root must be an object")

    return {
        manager_id: _normalize_summary_record(record)
        for manager_id, record in payload.items()
        if isinstance(record, Mapping)
    }


def _write_store(path: Path, payload: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_summary_store(path: str | Path = DEFAULT_SUMMARY_STORE_PATH) -> dict[str, dict[str, Any]]:
    return _read_store(Path(path))


def save_manager_summary(
    record: Mapping[str, object],
    *,
    path: str | Path = DEFAULT_SUMMARY_STORE_PATH,
) -> dict[str, Any]:
    summary_path = Path(path)
    store = _read_store(summary_path)
    normalized = _normalize_summary_record(record)
    store[normalized["manager_id"]] = normalized
    _write_store(summary_path, store)
    return dict(normalized)


def load_manager_summary(
    manager_id: str,
    *,
    path: str | Path = DEFAULT_SUMMARY_STORE_PATH,
    expected_source_version: str | None = None,
) -> dict[str, Any] | None:
    summary_path = Path(path)
    store = _read_store(summary_path)
    record = store.get(manager_id)
    if record is None:
        return None

    if expected_source_version is not None:
        expected = str(expected_source_version)
        stale = record["source_version"] != expected
        if bool(record["stale"]) != stale:
            record = {**record, "stale": stale}
            store[manager_id] = record
            _write_store(summary_path, store)
        else:
            record = {**record, "stale": stale}

    return dict(record)
