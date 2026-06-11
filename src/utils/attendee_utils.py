"""
STACP attendee parsing: delimiter normalization + optional personnel alias map.
Extend PERSONNEL_ALIASES as new officers appear.
"""

from __future__ import annotations

import re
from typing import Any, List, Tuple

import pandas as pd

# Maps informal / short names to canonical display names (lowercase keys)
PERSONNEL_ALIASES = {
    "del carpio": "Sgt. M. DelCarpio",
    "delcarpio": "Sgt. M. DelCarpio",
    "garrett": "Det. F. Garrett",
    "katsaroans": "Det. F. Katsaroans",
    "henao": "Det. E. Henao",
    "lara-nunez": "Det. C. Lara-Nunez",
    "dominguez": "Sgt. L. Dominguez",
}


def normalize_attendee_name(name: str) -> str:
    """Normalize a single attendee name using the alias lookup."""
    cleaned = name.strip()
    if not cleaned:
        return ""
    lookup_key = cleaned.lower()
    return PERSONNEL_ALIASES.get(lookup_key, cleaned)


def clean_and_count_attendees(
    row: pd.Series,
    primary_col: str = "Attendees",
    extra_cols: List[str] | None = None,
    free_type_col: str = "Free Type Attendees",
) -> Tuple[int, str]:
    """
    Count attendees from primary + extra dropdowns + free-text field.
    Returns (count, comma-separated canonical names).
    """
    if extra_cols is None:
        extra_cols = ["Attendees2", "Attendees3", "Attendees4", "Attendees5"]

    names: List[str] = []

    primary = row.get(primary_col)
    if primary is not None and pd.notna(primary) and str(primary).strip():
        names.append(normalize_attendee_name(str(primary)))

    for col in extra_cols:
        val = row.get(col)
        if val is not None and pd.notna(val) and str(val).strip():
            names.append(normalize_attendee_name(str(val)))

    ft = row.get(free_type_col)
    if ft is not None and pd.notna(ft) and str(ft).strip():
        parts = re.split(r"\s*/\s*|\s*,\s*", str(ft).strip())
        for part in parts:
            normalized = normalize_attendee_name(part)
            if normalized:
                names.append(normalized)

    count = len(names)
    names_csv = ", ".join(names)
    return count, names_csv
