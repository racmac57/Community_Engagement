"""
CAD Community Engagement processor — the fifth combined-feed source.

Reads a CAD CE monthly export (YYYY_MM_CE.xlsx, Sheet1) where each row is one
officer's CE call tagged with a Squad, and returns the canonical 12-field schema
so main_processor.combine_data() can union it with the four workbook sources.

Routing (Squad -> canonical office/division), matching the existing processors:
  COMM ENG          -> office 'Community Engagement', division 'Outreach'
  A1-A4 / B1-B4     -> office 'Patrol',               division 'Patrol'
  STA               -> office 'STA&CP',               division 'STACP'
  CSB               -> EXCLUDED (disabled; COMPSTAT safety filter also catches it)
  any other         -> office = Squad value,          division ''

De-dup is NOT done here — it needs the other sources. combine_data() calls the
gap-fill anti-join (see cad_dedup_key); workbook rows win, CAD only fills holes.

Memorial-CAD guard: a sub-2-minute span (incl. tiny clock-rounded negatives) is a
log-only record, not a real event length -> imputed to 0.5 h, end_time shifted.
"""

from __future__ import annotations

import datetime
import math
import re

import pandas as pd

from processors.excel_processor import ExcelProcessor
from utils.duration_utils import safe_duration_to_hours
from utils.logger_setup import get_project_logger

logger = get_project_logger("cad_ce_processor", "INFO")

PATROL_SQUADS = {"A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"}
MEMORIAL_MAX_HOURS = 2 / 60.0
IMPUTED_HOURS = 0.5

CANONICAL_COLS = [
    "date", "start_time", "end_time", "event_name", "location",
    "duration_hours", "attendee_count", "office", "division", "attendee_names",
]

# CAD source columns this processor reads (exact headers)
_BIZ = "SelfJoinCADNumber::Business Name"


# ----------------------------------------------------------------- shared keys
def _norm_loc_key(v) -> str:
    """Collapse a location to a comparison key: lowercase, strip non-alphanumerics.
    'M & M Center' -> 'mmcenter'. Used by the combine_data gap-fill anti-join too."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return re.sub(r"[^a-z0-9]", "", str(v).lower())


def _norm_officer_key(v) -> str:
    """Last-name-ish key from an officer/attendee string; '' if unusable."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    toks = [t for t in str(v).strip().split() if not t.rstrip(".").isdigit() and not t.endswith(".")]
    return toks[-1].lower() if toks else ""


def _norm_date_key(d) -> str:
    """Canonical YYYY-MM-DD. Sources disagree on type (CAD = ISO str,
    STACP/others = pandas Timestamp) — coerce both to the same string."""
    if d is None or (isinstance(d, float) and pd.isna(d)) or str(d).strip() == "":
        return ""
    try:
        return pd.to_datetime(d).date().isoformat()
    except (ValueError, TypeError):
        return str(d)


def cad_dedup_key(date, location, officer=None):
    """Gap-fill key. Officer is included only when provided on BOTH sides by the
    caller; workbook CE rows often lack officer names, so the practical key is
    (date, normalized location)."""
    base = (_norm_date_key(date), _norm_loc_key(location))
    return base + (_norm_officer_key(officer),) if officer else base


# ----------------------------------------------------------------- helpers
def _blank(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return str(v).strip() == ""


def _td_to_hhmm(v) -> str:
    if _blank(v):
        return ""
    if isinstance(v, (pd.Timedelta, datetime.timedelta)):
        total = int(v.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    if isinstance(v, datetime.time):
        return f"{v.hour:02d}:{v.minute:02d}"
    return ""


def _build_location(biz, st_number, street) -> str:
    if not _blank(biz):
        return str(biz).strip()
    sn = ""
    if not _blank(st_number):
        try:
            sn = str(int(float(st_number)))
        except (TypeError, ValueError):
            sn = str(st_number).strip()
    st = "" if _blank(street) else str(street).strip()
    return f"{sn} {st}".strip()


def _route(squad):
    """(include?, office, division). include=False -> drop (CSB)."""
    sq = "" if squad is None else str(squad).strip()
    if sq == "COMM ENG":
        return True, "Community Engagement", "Outreach"
    if sq == "CSB":
        return False, "", ""
    if sq == "STA":
        return True, "STA&CP", "STACP"
    if sq in PATROL_SQUADS:
        return True, "Patrol", "Patrol"
    return True, sq, ""  # catch-all


class CADCEProcessor(ExcelProcessor):
    """Transforms the CAD CE monthly export into the canonical combined-feed schema."""

    def __init__(self):
        super().__init__()
        self.office_identifier = "Community Engagement"  # default; per-row by squad
        self.division_identifier = "Outreach"

    def process_data_source(self, file_path: str, sheet_name: str = "Sheet1") -> pd.DataFrame:
        logger.info(f"Processing CAD CE export from {file_path}")
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")

        out = []
        imputed = 0
        for _, r in df.iterrows():
            include, office, division = _route(r.get("Squad"))
            if not include:
                continue
            toc = pd.to_datetime(r.get("Time of Call"), errors="coerce")
            start = _td_to_hhmm(r.get("Time Out Display"))
            end = _td_to_hhmm(r.get("Time In Display"))

            duration = ""
            ho = safe_duration_to_hours(r.get("Time Out Display"), default=float("nan"))
            hi = safe_duration_to_hours(r.get("Time In Display"), default=float("nan"))
            if not (math.isnan(ho) or math.isnan(hi)):
                dur = round(hi - ho, 4)
                if dur < MEMORIAL_MAX_HOURS:  # near-zero / tiny-negative -> memorial
                    duration = IMPUTED_HOURS
                    imputed += 1
                    if start:  # keep end consistent with imputed span
                        sh, sm = (int(x) for x in start.split(":"))
                        e = datetime.datetime(2000, 1, 1, sh, sm) + datetime.timedelta(hours=IMPUTED_HOURS)
                        end = f"{e.hour:02d}:{e.minute:02d}"
                else:
                    duration = dur

            out.append({
                "date": toc.date().isoformat() if not pd.isna(toc) else "",
                "start_time": start,
                "end_time": end,
                "event_name": "" if _blank(r.get("Incident")) else str(r.get("Incident")).strip(),
                "location": _build_location(r.get(_BIZ), r.get("St Number"), r.get("StreetName")),
                "duration_hours": duration,
                "attendee_count": 1,
                "office": office,
                "division": division,
                "attendee_names": "" if _blank(r.get("Officer")) else str(r.get("Officer")).strip(),
            })

        result = pd.DataFrame(out, columns=CANONICAL_COLS)
        logger.info(f"CAD CE: {len(result)} rows routed to combined feed "
                    f"(CSB excluded; {imputed} durations imputed to {IMPUTED_HOURS}h)")
        return result
