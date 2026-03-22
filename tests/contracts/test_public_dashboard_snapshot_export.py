from __future__ import annotations

import json
from pathlib import Path


def test_public_dashboard_snapshot_includes_real_stock_research_workspace() -> None:
    snapshot = json.loads(Path("app/web/public/dashboard_snapshot.json").read_text(encoding="utf-8"))

    workspace = snapshot["stock_research_workspace"]
    assert workspace["filters"]["total_count"] >= 1
    assert workspace["items"][0]["symbol"] == "NVDA"
    assert workspace["items"][0]["status"] == "관찰"
    assert workspace["queue"][0]["symbol"] == "NVDA"
