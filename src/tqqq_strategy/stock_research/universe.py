from __future__ import annotations

from typing import Any

from tqqq_strategy.stock_research.types import ResearchUniverseEntry


def build_research_universe(
    manual_inputs: dict[str, list[dict[str, Any]]],
    *,
    as_of: str,
) -> list[ResearchUniverseEntry]:
    held_symbols = {
        str(position.get("symbol") or "").strip()
        for position in manual_inputs.get("positions", [])
        if str(position.get("symbol") or "").strip()
    }

    universe: list[ResearchUniverseEntry] = []
    for record in manual_inputs.get("stock_watchlist", []):
        symbol = str(record.get("symbol") or "").strip()
        if not symbol:
            continue
        universe.append(
            ResearchUniverseEntry(
                idea_id=str(record.get("idea_id") or symbol.lower()),
                symbol=symbol,
                raw_status=str(record.get("status") or ""),
                memo=str(record.get("memo") or ""),
                is_held=symbol in held_symbols,
                as_of=as_of,
            )
        )
    return universe
