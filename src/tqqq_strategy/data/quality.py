"""Data quality checks for canonical strategy inputs."""

from __future__ import annotations

import pandas as pd

from tqqq_strategy.data.schema import (
    CANONICAL_PRIMARY_KEY_COLUMNS,
    CANONICAL_REQUIRED_COLUMNS,
)


def validate_canonical(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate canonical schema constraints and return (ok, errors)."""
    errs: list[str] = []

    missing = [col for col in CANONICAL_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        errs.append(f"missing required columns: {', '.join(missing)}")

    if all(col in df.columns for col in CANONICAL_PRIMARY_KEY_COLUMNS):
        duplicate_mask = df.duplicated(
            subset=list(CANONICAL_PRIMARY_KEY_COLUMNS),
            keep=False,
        )
        if bool(duplicate_mask.any()):
            duplicate_count = int(duplicate_mask.sum())
            key_str = ",".join(CANONICAL_PRIMARY_KEY_COLUMNS)
            errs.append(
                f"duplicate canonical keys found for ({key_str}): {duplicate_count} row(s)"
            )

    return (len(errs) == 0, errs)
