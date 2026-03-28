from __future__ import annotations

import inspect

from tqqq_strategy.ai.manager_jobs import refresh_manager_summaries
from tqqq_strategy.ops.daily_job import run_daily_signal_alert
from tqqq_strategy.ops.dashboard_snapshot import generate_dashboard_snapshot


def test_runtime_defaults_point_to_final_signal_report() -> None:
    expected = "reports/signals_core_strategy_final.csv"

    assert str(inspect.signature(run_daily_signal_alert).parameters["signal_csv_path"].default) == expected
    assert str(inspect.signature(generate_dashboard_snapshot).parameters["signal_csv_path"].default) == expected
    assert str(inspect.signature(refresh_manager_summaries).parameters["signal_csv_path"].default) == expected
