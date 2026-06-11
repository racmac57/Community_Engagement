"""
Normalize Excel duration cells (timedelta, time, float, str) to decimal hours for CSV export.
Power BI must receive numeric hours — string '1:00:00' breaks Number.From in M.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Union

import pandas as pd


def safe_duration_to_hours(value: Any, default: Union[float, object] = 0.5) -> Any:
    """
    Convert any duration representation to decimal hours.

    Handles: timedelta, pd.Timedelta, datetime.time, float, int, str ("H:MM:SS", "H:MM", numeric).

    Parameters
    ----------
    value : Any
        Cell value from pandas/openpyxl.
    default : float or sentinel
        Returned for null/unparseable values. Use float('nan') when combining with a fallback column.

    Returns
    -------
    float
        Hours (> 0 when derived from a positive duration), or *default*.
    """
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    if isinstance(value, pd.Timestamp) and pd.isna(value):
        return default

    # Plain numbers (exclude bool)
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        v = float(value)
        return v if v > 0 else default

    # pandas Timedelta (common for CE Event Duration9 from Excel)
    if isinstance(value, pd.Timedelta):
        if pd.isna(value):
            return default
        hours = value.total_seconds() / 3600.0
        return hours if hours > 0 else default

    # datetime.timedelta (common for STACP Total Time from openpyxl)
    if isinstance(value, datetime.timedelta):
        hours = value.total_seconds() / 3600.0
        return hours if hours > 0 else default

    # time-of-day interpreted as elapsed h/m/s (Excel duration-as-clock)
    if isinstance(value, datetime.time):
        hours = value.hour + value.minute / 60.0 + value.second / 3600.0
        return hours if hours > 0 else default

    s = str(value).strip()
    if not s or s.lower() in ("nan", "none", "nat", ""):
        return default

    # "0 days 01:00:00" style
    if "day" in s.lower() and ":" in s:
        parts = s.split()
        try:
            time_part = parts[-1]
            h, m, sec = _parse_hms_triplet(time_part)
            if h is not None:
                hours = h + m / 60.0 + sec / 3600.0
                return hours if hours > 0 else default
        except (ValueError, IndexError):
            pass

    match = re.match(r"^(\d+):(\d{1,2})(?::(\d{1,2}))?$", s)
    if match:
        h, m, sec = int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)
        hours = h + m / 60.0 + sec / 3600.0
        return hours if hours > 0 else default

    try:
        hours = float(s)
        return hours if hours > 0 else default
    except ValueError:
        return default


def _parse_hms_triplet(time_part: str) -> tuple:
    """Return (h, m, sec) ints or raise."""
    bits = time_part.split(":")
    if len(bits) == 3:
        return int(bits[0]), int(bits[1]), int(bits[2])
    if len(bits) == 2:
        return int(bits[0]), int(bits[1]), 0
    raise ValueError("not h:m:s")
