from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "ops/scripts/run_daily_telegram_alert.py"
_spec = importlib.util.spec_from_file_location(
    "run_daily_telegram_alert_under_test", SCRIPT
)
assert _spec is not None and _spec.loader is not None
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(
    script
)  # defines functions only; main() is guarded by __name__


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "1670000", "CORE_CONTRIBUTION_DAY": "25"},
            (1_670_000, 25),
        ),
        (
            {
                "CORE_MONTHLY_CONTRIBUTION_KRW": "1,670,000",
                "CORE_CONTRIBUTION_DAY": " 5 ",
            },
            (1_670_000, 5),
        ),
        ({}, (None, None)),
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "", "CORE_CONTRIBUTION_DAY": ""},
            (None, None),
        ),
        ({"CORE_MONTHLY_CONTRIBUTION_KRW": "1670000"}, (1_670_000, None)),
        ({"CORE_CONTRIBUTION_DAY": "31"}, (None, 31)),
    ],
)
def test_parse_contribution_env_valid_and_missing(env, expected, capsys) -> None:
    assert script._parse_contribution_env(env) == expected
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "abc", "CORE_CONTRIBUTION_DAY": "25"},
            (None, 25),
        ),
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "-5", "CORE_CONTRIBUTION_DAY": "25"},
            (None, 25),
        ),
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "1670000", "CORE_CONTRIBUTION_DAY": "0"},
            (1_670_000, None),
        ),
        (
            {"CORE_MONTHLY_CONTRIBUTION_KRW": "1670000", "CORE_CONTRIBUTION_DAY": "32"},
            (1_670_000, None),
        ),
        (
            {
                "CORE_MONTHLY_CONTRIBUTION_KRW": "1670000",
                "CORE_CONTRIBUTION_DAY": "25th",
            },
            (1_670_000, None),
        ),
    ],
)
def test_parse_contribution_env_invalid_values_warn_and_become_none(
    env, expected, capsys
) -> None:
    assert script._parse_contribution_env(env) == expected
    assert "warning" in capsys.readouterr().err
