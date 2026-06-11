"""
CE CAD ETL — transform the CAD Community Engagement monthly export into the
unified 12-field CSV, route rows by Squad, write a timestamped combined CSV to
PowerBI_Data\\_DropExports, and emit STACP verification + unrouted reports.

Session: ce-etl-wave-plan-cad-routing-squad-mapping-2026-06-11
Priority month: May 2026 (2026_05_CE.xlsx). READ-ONLY against all source
workbooks; the only write target is the _DropExports CSV plus docs/ reports.

TODO(refactor): this is a standalone script reusing src/utils helpers. Once the
CAD CE monthly export is a stable monthly source, fold this into the existing
processor architecture as src/processors/cad_ce_processor.py wired through
main_processor.combine_data(). Do not do that yet — kept standalone on purpose.

Run:
  python scripts/ce_cad_etl.py            # dry-run: waves 1-3, no writes
  python scripts/ce_cad_etl.py --write    # waves 1-4: write CSV + reports
"""

from __future__ import annotations

import argparse
import datetime
import math
import sys
from pathlib import Path

import pandas as pd

# --- robust import of src/utils regardless of CWD -------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
from utils.duration_utils import safe_duration_to_hours  # noqa: E402
from utils.logger_setup import get_project_logger  # noqa: E402
from utils.config_loader import ConfigLoader  # noqa: E402

# --- path-agnostic anchors (repo lives under the OneDrive root) -----------
ONEDRIVE_ROOT = REPO_ROOT.parents[1]  # ...\OneDrive - City of Hackensack
CAD_MONTHLY_DIR = ONEDRIVE_ROOT / "05_EXPORTS" / "_CAD" / "Community_Engagement" / "monthly"
CONTRIB = ONEDRIVE_ROOT / "Shared Folder" / "Compstat" / "Contributions"
STACP_PATH = CONTRIB / "STACP" / "STACP.xlsm"
PATROL_PATH = CONTRIB / "Patrol" / "patrol_monthly.xlsm"
CE_WB_PATH = CONTRIB / "Community_Engagement" / "Community_Engagement_Monthly.xlsx"
DROPEXPORTS = ONEDRIVE_ROOT / "PowerBI_Data" / "_DropExports"
DOCS_DIR = REPO_ROOT / "docs"

DEFAULT_SOURCE = CAD_MONTHLY_DIR / "2026_05_CE.xlsx"
# Target month is derived from the source filename (YYYY_MM_CE.xlsx) at runtime;
# these are defaults overwritten in main(). MONTH_TAG drives doc filenames/titles.
TARGET_YEAR, TARGET_MONTH = 2026, 5
MONTH_TAG = "2026_05"
SHEET = "Sheet1"

# 12-field output contract (exact order)
OUTPUT_COLS = [
    "date", "start_time", "end_time", "event_name", "location", "duration_hours",
    "attendee_count", "office", "division", "attendee_names", "data_source", "processed_date",
]

# the 12 CAD source columns this ETL actually reads (the real contract)
REQUIRED_SOURCE_COLS = [
    "ReportNumberNew", "Time of Call", "Time Out Display", "Time In Display",
    "Incident", "SelfJoinCADNumber::Business Name", "St Number", "StreetName",
    "Officer", "Squad", "DispatcherNew",
]

PATROL_SQUADS = {"A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"}

# Memorial-CAD guard: an officer who is also the DispatcherNew (created the CAD to
# memorialize an event) produces near-zero durations. Treat sub-2-min spans as
# log artifacts and impute a 30-minute default.
MEMORIAL_MAX_HOURS = 2 / 60.0
IMPUTED_HOURS = 0.5

log = get_project_logger("ce_cad_etl", "INFO")


# ---------------------------------------------------------------- helpers
def _blank(v) -> bool:
    if v is None:
        return True
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return str(v).strip() == ""


def td_to_hhmm(v) -> str:
    """timedelta/time from midnight -> 'HH:MM'; blank if null."""
    if _blank(v):
        return ""
    if isinstance(v, (pd.Timedelta, datetime.timedelta)):
        total = int(v.total_seconds())
        return f"{total // 3600:02d}:{(total % 3600) // 60:02d}"
    if isinstance(v, datetime.time):
        return f"{v.hour:02d}:{v.minute:02d}"
    return ""


def norm_case(v) -> str:
    """Normalize a case/CAD number for comparison: str, strip ws + embedded \\n, drop float .0."""
    if _blank(v):
        return ""
    s = str(v).strip().replace("\n", "").replace("\r", "")
    if s.endswith(".0"):
        s = s[:-2]
    return s


import re as _re

# location stopwords dropped before token comparison (kept small + place-agnostic)
_LOC_STOP = {"the", "and", "of", "at", "a", "an"}


def norm_loc_collapsed(v) -> str:
    """Lowercase, strip all non-alphanumerics -> collapsed key. 'M & M Center' -> 'mmcenter'."""
    if _blank(v):
        return ""
    return _re.sub(r"[^a-z0-9]", "", str(v).lower())


def norm_loc_tokens(v) -> set:
    if _blank(v):
        return set()
    toks = _re.sub(r"[^a-z0-9 ]", " ", str(v).lower()).split()
    return {t for t in toks if t not in _LOC_STOP}


def loc_match(cad_loc, stacp_loc) -> bool:
    """date is matched separately; this decides location equivalence on messy free-text."""
    ca, cb = norm_loc_collapsed(cad_loc), norm_loc_collapsed(stacp_loc)
    if not ca or not cb:
        return False
    if ca == cb or ca in cb or cb in ca:  # 'mmcenter' == 'mmcenter'
        return True
    ta, tb = norm_loc_tokens(cad_loc), norm_loc_tokens(stacp_loc)
    if not ta or not tb:
        return False
    inter = ta & tb
    union = ta | tb
    return len(inter) / len(union) >= 0.5  # Jaccard


_COMBINED_SEP = _re.compile(r"\b(?:and)\b|[/&,]|\+")


def is_combined_loc(v) -> bool:
    """Heuristic: one STACP row crammed with 2+ places ('Jackson and Fairmount', 'A / B')."""
    return bool(_COMBINED_SEP.search(str(v).lower())) if not _blank(v) else False


def loc_partial_match(cad_loc, stacp_loc) -> bool:
    """CAD location matches ONE component of a combined STACP location."""
    ca = norm_loc_tokens(cad_loc)
    if not ca:
        return False
    for part in _re.split(r"\band\b|[/&,]|\+", str(stacp_loc).lower()):
        if loc_match(cad_loc, part):
            return True
    # token containment fallback (e.g. 'jackson' present in combined string)
    cb = norm_loc_tokens(stacp_loc)
    return len(ca & cb) >= 1


def officer_to_stacp_initial(officer) -> str:
    """'Lt. Anthony DiPersia 266' -> 'A. DiPersia' (STACP Attendees convention)."""
    if _blank(officer):
        return ""
    toks = str(officer).strip().split()
    toks = [t for t in toks if not t.rstrip(".").isdigit()]      # drop badge number
    toks = [t for t in toks if not t.endswith(".")]              # drop rank (Lt./Sgt./Det./P.O.)
    if len(toks) >= 2:
        return f"{toks[0][0]}. {' '.join(toks[1:])}"
    return " ".join(toks)


def build_location(biz, st_number, street) -> str:
    if not _blank(biz):
        return str(biz).strip()
    sn = ""
    if not _blank(st_number):
        try:
            sn = str(int(float(st_number)))  # 251.0 -> "251"
        except (TypeError, ValueError):
            sn = str(st_number).strip()
    st = "" if _blank(street) else str(street).strip()
    return f"{sn} {st}".strip()


def route(squad: str):
    """Return (destination, office, division). destination in {csv, sta, csb}."""
    sq = "" if squad is None else str(squad).strip()
    if sq == "COMM ENG":
        return "csv", "COMM ENG", ""
    if sq == "CSB":
        return "csb", "", ""
    if sq == "STA":
        return "sta", "", ""
    if sq in PATROL_SQUADS:
        return "csv", "Patrol", ("Patrol A" if sq.startswith("A") else "Patrol B")
    return "csv", sq, ""  # catch-all


def mtime(p: Path):
    return p.stat().st_mtime if p.exists() else None


# ---------------------------------------------------------------- waves
def wave1_inventory(df: pd.DataFrame, source: Path) -> dict:
    print("\n=== WAVE 1 — Ingest & Inventory ===")
    actual_cols = list(df.columns)
    missing = [c for c in REQUIRED_SOURCE_COLS if c not in actual_cols]
    if missing:
        raise SystemExit(f"FAIL Wave1: missing required source columns: {missing}")

    toc = pd.to_datetime(df["Time of Call"], errors="coerce")
    in_month = (toc.dt.year == TARGET_YEAR) & (toc.dt.month == TARGET_MONTH)
    may_rows = int(in_month.sum())
    out_of_range = int((~in_month).sum())

    squad_counts = (
        df["Squad"].astype(str).str.strip().value_counts().to_dict()
    )

    # duration cols parse as timedelta?
    def is_td(series):
        return series.dropna().map(lambda v: isinstance(v, (pd.Timedelta, datetime.timedelta))).all()

    tout_td = is_td(df["Time Out Display"])
    tin_td = is_td(df["Time In Display"])

    print(f"  source            : {source.name}")
    print(f"  col_count         : {len(actual_cols)} (header len)")
    print(f"  required cols     : ALL {len(REQUIRED_SOURCE_COLS)} PRESENT")
    print(f"  total_rows        : {len(df)}")
    print(f"  in_month_rows     : {may_rows} ({MONTH_TAG})")
    print(f"  out_of_range_rows : {out_of_range}")
    print(f"  squad_counts      : {squad_counts}")
    print(f"  duration timedelta: TimeOut={tout_td} TimeIn={tin_td}")
    print(f"  first 3 rows (Officer | Squad | Time of Call | Incident):")
    for _, r in df.head(3).iterrows():
        print(f"    - {r['Officer']} | {r['Squad']} | {r['Time of Call']} | {r['Incident']}")

    if len(df) == 0:
        raise SystemExit("FAIL Wave1: 0 rows")
    if not (tout_td and tin_td):
        raise SystemExit("FAIL Wave1: duration columns are not timedelta")
    print(f"  TRIPWIRE: {len(df)} | in_month={may_rows} | {out_of_range} | {squad_counts}")
    print("  Wave 1: PASS")

    # conservation inputs from RAW squad values (pre-transform, independent)
    sta_raw = sum(v for k, v in squad_counts.items() if k == "STA")
    csb_raw = sum(v for k, v in squad_counts.items() if k == "CSB")
    return {
        "may_rows": may_rows, "out_of_range": out_of_range,
        "sta_raw": sta_raw, "csb_raw": csb_raw,
        "squad_counts": squad_counts, "in_month": in_month,
    }


def wave2_transform(df: pd.DataFrame, source: Path, inv: dict):
    print("\n=== WAVE 2 — Transform & Map ===")
    processed = datetime.datetime.now().isoformat(timespec="seconds")
    data_source = f"CAD:CE_monthly:{source.name}"

    out_rows, sta_rows, csb_rows, imputed = [], [], [], []
    for idx, r in df.iterrows():
        if not inv["in_month"].iloc[idx]:
            continue  # out-of-range already counted in Wave 1
        dest, office, division = route(r["Squad"])
        toc = pd.to_datetime(r["Time of Call"], errors="coerce")
        toc_hhmm = "" if pd.isna(toc) else f"{toc.hour:02d}:{toc.minute:02d}"
        rec = {
            "date": toc.date().isoformat() if not pd.isna(toc) else "",
            "start_time": td_to_hhmm(r["Time Out Display"]),
            "end_time": td_to_hhmm(r["Time In Display"]),
            "event_name": "" if _blank(r["Incident"]) else str(r["Incident"]).strip(),
            "location": build_location(
                r["SelfJoinCADNumber::Business Name"], r["St Number"], r["StreetName"]
            ),
            "duration_hours": "",
            "attendee_count": 1,
            "office": office,
            "division": division,
            "attendee_names": "" if _blank(r["Officer"]) else str(r["Officer"]).strip(),
            "data_source": data_source,
            "processed_date": processed,
            "_squad": str(r["Squad"]).strip(),
            "_cad": norm_case(r["ReportNumberNew"]),
            "_toc_hhmm": toc_hhmm,
            "_dispatcher": "" if _blank(r["DispatcherNew"]) else str(r["DispatcherNew"]).strip(),
            "_imputed_duration": False,
        }
        ho = safe_duration_to_hours(r["Time Out Display"], default=float("nan"))
        hi = safe_duration_to_hours(r["Time In Display"], default=float("nan"))
        if not (math.isnan(ho) or math.isnan(hi)):
            dur = round(hi - ho, 4)
            if dur <= -MEMORIAL_MAX_HOURS:  # real time inversion -> stop (data error)
                raise SystemExit(f"FAIL Wave2: negative duration row {idx} ({dur}h)")
            if dur < MEMORIAL_MAX_HOURS:  # near-zero (incl tiny clock-rounded negative) -> memorial
                rec["duration_hours"] = IMPUTED_HOURS
                rec["_imputed_duration"] = True
                if rec["start_time"]:  # keep end_time consistent with imputed span
                    sh, sm = (int(x) for x in rec["start_time"].split(":"))
                    end = (datetime.datetime(2000, 1, 1, sh, sm) +
                           datetime.timedelta(hours=IMPUTED_HOURS))
                    rec["end_time"] = f"{end.hour:02d}:{end.minute:02d}"
                imputed.append(rec)
            else:
                rec["duration_hours"] = dur

        if dest == "csv":
            out_rows.append(rec)
        elif dest == "sta":
            sta_rows.append(rec)
        else:
            csb_rows.append(rec)

    # conservation check — independently derived from raw squad counts
    expected = inv["may_rows"] - inv["sta_raw"] - inv["csb_raw"]
    if len(out_rows) != expected:
        raise SystemExit(
            f"FAIL Wave2 conservation: output={len(out_rows)} != "
            f"may({inv['may_rows']}) - sta({inv['sta_raw']}) - csb({inv['csb_raw']}) = {expected}"
        )
    for rec in out_rows:
        if _blank(rec["office"]):
            raise SystemExit("FAIL Wave2: blank office in output row")

    # duplicate flag on (date, event_name, location, attendee_names) — surface only.
    # location is part of the key: same officer at two locations same day = two real
    # events, not a duplicate.
    seen, dups = {}, []
    for rec in out_rows:
        key = (rec["date"], rec["event_name"], rec["location"], rec["attendee_names"])
        seen.setdefault(key, []).append(rec)
    for key, recs in seen.items():
        if len(recs) > 1:
            dups.append((key, len(recs)))

    print(f"  output_rows : {len(out_rows)} (conservation OK: == {expected})")
    print(f"  sta_rows    : {len(sta_rows)}")
    print(f"  csb_rows    : {len(csb_rows)}")
    print(f"  duplicates  : {len(dups)}")
    print(f"  imputed_30m : {len(imputed)} (sub-2-min memorial CADs -> 0.5h)")
    print(f"  TRIPWIRE: {len(out_rows)+len(sta_rows)+len(csb_rows)} | {len(out_rows)} | "
          f"{len(sta_rows)} | {len(csb_rows)} | {len(dups)} | imputed={len(imputed)}")

    print("\n  --- GATE 2a: transformed output rows (12 fields) ---")
    for rec in out_rows:
        flag = "  <-- duration imputed 0.5h (memorial CAD)" if rec["_imputed_duration"] else ""
        print("   " + " | ".join(f"{c}={rec[c]}" for c in OUTPUT_COLS) + flag)
    print("\n  --- GATE 2b: duplicate flags ---")
    print("    " + ("none" if not dups else str(dups)))
    print("\n  --- GATE 2b2: duration normalized (span < 2 min -> 0.5h default) ---")
    if not imputed:
        print("    none")
    for rec in imputed:
        print(f"    {rec['date']} | {rec['attendee_names']} | {rec['location']} -> 0.5h")
    print("\n  --- GATE 2c: STA rows (-> verification) ---")
    for rec in sta_rows:
        print(f"    CAD#={rec['_cad']} | {rec['date']} | {rec['event_name']} | {rec['attendee_names']}")
    print("\n  --- GATE 2d: CSB rows (-> unrouted) ---")
    for rec in csb_rows:
        print(f"    CAD#={rec['_cad']} | {rec['date']} | {rec['event_name']} | {rec['attendee_names']}")
    print("  Wave 2: PASS")
    return out_rows, sta_rows, csb_rows, dups, imputed


def read_stacp_outreach():
    """Read STACP Master_Outreach positionally (B=date, G=CAD#, H=event). READ-ONLY."""
    import openpyxl
    wb = openpyxl.load_workbook(STACP_PATH, read_only=True, data_only=True)
    ws = wb["Master_Outreach"]
    recs = []
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if i == 1:
            continue  # header
        if row is None or all(c is None for c in row):
            continue
        date_v = row[1] if len(row) > 1 else None
        cad_v = row[6] if len(row) > 6 else None
        event_v = row[7] if len(row) > 7 else None
        loc_v = row[8] if len(row) > 8 else None  # col I = Location
        d = None
        if isinstance(date_v, (datetime.datetime, datetime.date)):
            d = date_v.date() if isinstance(date_v, datetime.datetime) else date_v
        recs.append({"rowidx": i, "date": d, "cad": norm_case(cad_v),
                     "event": "" if event_v is None else str(event_v).strip(),
                     "location": "" if loc_v is None else str(loc_v).strip()})
    wb.close()
    return recs


def wave3_stacp_verify(sta_rows):
    print("\n=== WAVE 3 — STACP Verification (read-only) ===")
    before = mtime(STACP_PATH)
    stacp = read_stacp_outreach()
    by_date = {}
    for r in stacp:
        if r["date"] is not None:
            by_date.setdefault(r["date"], []).append(r)

    # Match key: date + normalized location (CAD# in STACP is rarely entered).
    # PRESENT         = same-date STACP row whose location matches the CAD location.
    # SPLIT_SUGGESTED = same-date STACP row crams 2+ places ('Jackson and Fairmount')
    #                   and the CAD location matches ONE component -> recommend splitting
    #                   the combined row into separate rows.
    # CONFLICT        = same-date STACP row(s) exist but no location match (candidates listed).
    # MISSING         = no same-date STACP row at all.
    results = []
    for rec in sta_rows:
        try:
            rdate = datetime.date.fromisoformat(rec["date"]) if rec["date"] else None
        except ValueError:
            rdate = None
        same_day = by_date.get(rdate, []) if rdate is not None else []
        loc_hit = next((r for r in same_day if loc_match(rec["location"], r["location"])), None)
        split_hit = next((r for r in same_day
                          if is_combined_loc(r["location"]) and loc_partial_match(rec["location"], r["location"])), None)
        if loc_hit is not None:
            cls, matched = "PRESENT", loc_hit["rowidx"]
            matched_loc = loc_hit["location"]
        elif split_hit is not None:
            cls, matched = "SPLIT_SUGGESTED", split_hit["rowidx"]
            matched_loc = split_hit["location"]
        elif same_day:
            cls = "CONFLICT"
            matched = [r["rowidx"] for r in same_day]
            matched_loc = "; ".join(f"r{r['rowidx']}:{r['location']}" for r in same_day)
        else:
            cls, matched, matched_loc = "MISSING", None, ""
        results.append({**rec, "classification": cls, "matched_row": matched,
                        "matched_loc": matched_loc})

    proposals = build_stacp_proposals(results)

    after = mtime(STACP_PATH)
    unchanged = before == after
    counts = {c: sum(1 for r in results if r["classification"] == c)
              for c in ("PRESENT", "SPLIT_SUGGESTED", "CONFLICT", "MISSING")}

    print("  --- STACP VERIFICATION REPORT (match: date + location) ---")
    for r in results:
        print(f"    {r['date']} | CAD_loc={r['location']!r} | {r['classification']} "
              f"| matched_row={r['matched_row']} | stacp_loc={r['matched_loc']!r}")
    print(f"  TRIPWIRE: present={counts['PRESENT']} | split={counts['SPLIT_SUGGESTED']} "
          f"| conflict={counts['CONFLICT']} | missing={counts['MISSING']} "
          f"| stacp_mtime_unchanged={unchanged}")
    if proposals:
        print("  --- PROPOSED Master_Outreach entries (paste-ready) ---")
        for p in proposals:
            print(f"    [{p['_reason']}] {p['Event ID']} | {p['Date']} | {p['Start Time']}-{p['End Time']} "
                  f"| CAD#={p['CAD#']} | {p['School Outreach Conducted']} | {p['Location']} | {p['Attendees']}")
    if len(results) != len(sta_rows):
        raise SystemExit("FAIL Wave3: verification row count mismatch")
    if not unchanged:
        raise SystemExit("FAIL Wave3: STACP.xlsm mtime changed")
    print("  Wave 3: PASS")
    return results, proposals


STACP_PROPOSAL_COLS = [
    "Event ID", "Date", "Start Time", "End Time", "Total Time", "CAD#",
    "School Outreach Conducted", "Location", "Attendees",
]


def build_stacp_proposals(results):
    """Generate paste-ready Master_Outreach rows from CAD data for rows STACP is
    missing (MISSING) or where a combined STACP row should be split (SPLIT_SUGGESTED).
    Start = Time of Call; End = Start + 30 min (memorial CADs lack a real span)."""
    proposals = []
    for r in results:
        cls = r["classification"]
        if cls not in ("MISSING", "SPLIT_SUGGESTED"):
            continue
        start = r.get("_toc_hhmm") or r.get("start_time") or ""
        end = ""
        if start:
            sh, sm = (int(x) for x in start.split(":"))
            e = datetime.datetime(2000, 1, 1, sh, sm) + datetime.timedelta(hours=IMPUTED_HOURS)
            end = f"{e.hour:02d}:{e.minute:02d}"
        eid = r["date"].replace("-", "") + "-001" if r["date"] else ""
        proposals.append({
            "Event ID": eid,
            "Date": r["date"],
            "Start Time": start,
            "End Time": end,
            "Total Time": IMPUTED_HOURS,
            "CAD#": r["_cad"],
            "School Outreach Conducted": r["event_name"],
            "Location": r["location"],
            "Attendees": officer_to_stacp_initial(r["attendee_names"]),
            "_reason": ("MISSING -> new row" if cls == "MISSING"
                        else f"SPLIT row {r['matched_row']} ({r['matched_loc']}) -> this half"),
        })
    return proposals


# ---------------------------------------------------------------- write
def wave4_write(out_rows, sta_results, csb_rows, source: Path, dups, imputed, proposals):
    print("\n=== WAVE 4 — Write CSV + reports ===")
    before = {p: mtime(p) for p in (source, STACP_PATH, PATROL_PATH, CE_WB_PATH)}

    DROPEXPORTS.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # filename pattern from config (already points at _DropExports); dir derived path-agnostically
    pattern = "community_engagement_data_{timestamp}.csv"
    try:
        cfg = ConfigLoader(config_dir=str(REPO_ROOT)).load_config("config")
        pattern = cfg.get("output_settings", {}).get("filename_pattern", pattern)
    except Exception as e:  # config optional; derive fallback
        log.warning(f"config read failed, using default filename pattern: {e}")
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = DROPEXPORTS / pattern.format(timestamp=ts)

    out_df = pd.DataFrame([{c: r[c] for c in OUTPUT_COLS} for r in out_rows], columns=OUTPUT_COLS)
    if list(out_df.columns) != OUTPUT_COLS:
        raise SystemExit("FAIL Wave4: column order mismatch")
    for _, r in out_df.iterrows():
        if _blank(r["office"]):
            raise SystemExit("FAIL Wave4: blank office")
        if not str(r["date"]).startswith(f"{TARGET_YEAR}-{TARGET_MONTH:02d}-"):
            raise SystemExit(f"FAIL Wave4: date outside target month: {r['date']}")
    if csv_path.exists():  # archive-first: never overwrite
        raise SystemExit(f"FAIL Wave4: target exists (won't overwrite): {csv_path}")
    out_df.to_csv(csv_path, index=False)

    _write_stacp_report(sta_results, imputed)
    _write_unrouted_report(csb_rows)
    proposals_path = _write_proposals_csv(proposals)

    after = {p: mtime(p) for p in before}
    unmodified = all(before[p] == after[p] for p in before)
    if not unmodified:
        raise SystemExit("FAIL Wave4: a source workbook mtime changed")

    print(f"  csv_path  : {csv_path}")
    print(f"  csv_rows  : {len(out_df)}")
    print(f"  csv_cols  : {len(out_df.columns)}")
    print(f"  proposals : {len(proposals)} -> {proposals_path.name if proposals_path else '(none)'}")
    print(f"  TRIPWIRE: {len(out_df)} | {len(out_df.columns)} | "
          f"source_workbooks_unmodified={unmodified} | docs_written=True")
    print("  first 3 rows:")
    for _, r in out_df.head(3).iterrows():
        print("   " + " | ".join(f"{c}={r[c]}" for c in OUTPUT_COLS))
    print("  Wave 4: PASS")
    return csv_path


def _write_stacp_report(results, imputed=None):
    lines = [
        f"# STACP Verification Report — {MONTH_TAG} (ce-cad-etl)", "",
        f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: **date (col B) + "
        "location (col I)**. CAD# (col G) shown for reference only — rarely entered.", "",
        "| CAD# (ref) | Date | Incident | CAD Location | Officer | Classification | Matched STACP row(s) | STACP Location |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['_cad'] or '(blank)'} | {r['date']} | {r['event_name']} "
                     f"| {r['location']} | {r['attendee_names']} | **{r['classification']}** "
                     f"| {r['matched_row']} | {r['matched_loc']} |")
    lines += ["", "**Match logic:** location normalized (lowercased, non-alphanumerics stripped; "
              "e.g. 'M & M Center' = 'MM Center'), then collapsed-equality / containment / "
              "token-Jaccard ≥ 0.5.", "",
              "**Legend:** PRESENT = STACP already has this event (no action). "
              "SPLIT_SUGGESTED = a combined STACP row holds 2+ events and CAD matches one — the "
              "CAD-backed half is provided below as a paste-ready row. "
              "CONFLICT = same-date row(s) exist but no location match. "
              "MISSING = STACP has no row that day — a paste-ready row is provided below. "
              "These are gap-fills generated from CAD; paste as-is, no follow-up required.", ""]

    # paste-ready proposed entries
    proposals = build_stacp_proposals(results)
    if proposals:
        lines += ["## Proposed Master_Outreach entries (paste-ready)", "",
                  "Generated from the CAD export for MISSING / SPLIT_SUGGESTED rows. "
                  "Memorial CADs have no real span, so **Start = Time of Call, End = Start + 30 min, "
                  "Total Time = 0.5 h**. Review before pasting; also TSV at "
                  f"`docs/{MONTH_TAG}_stacp_proposed_entries.csv`.", "",
                  "| " + " | ".join(STACP_PROPOSAL_COLS) + " | Reason |",
                  "|" + "---|" * (len(STACP_PROPOSAL_COLS) + 1)]
        for p in proposals:
            lines.append("| " + " | ".join(str(p[c]) for c in STACP_PROPOSAL_COLS) +
                         f" | {p['_reason']} |")
        lines.append("")

    if imputed:
        lines += ["## Duration normalized to 30 min", "",
                  "A CAD span under 2 minutes is a log-only record, not a real event length. "
                  "These are set to a 0.5 h default in the output CSV — a sensible floor, no "
                  "per-row judgment needed.", "",
                  "| Date | Officer | Location |", "|---|---|---|"]
        for r in imputed:
            lines.append(f"| {r['date']} | {r['attendee_names']} | {r['location']} |")
        lines.append("")

    (DOCS_DIR / f"{MONTH_TAG}_stacp_verification.md").write_text("\n".join(lines), encoding="utf-8")


def _write_proposals_csv(proposals):
    if not proposals:
        return None
    path = DOCS_DIR / f"{MONTH_TAG}_stacp_proposed_entries.csv"
    df = pd.DataFrame([{c: p[c] for c in STACP_PROPOSAL_COLS} for p in proposals],
                      columns=STACP_PROPOSAL_COLS)
    df.to_csv(path, index=False)
    return path


def _write_unrouted_report(csb_rows):
    lines = [
        f"# Unrouted Report — {MONTH_TAG} (ce-cad-etl)", "",
        f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "Rows excluded from the combined CSV. Reason: **CSB disabled** "
        "(csb_monthly.xlsm is COMPSTAT activity tracking, not an outreach event log).", "",
        "| CAD# | Date | Incident | Officer | Squad | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for r in csb_rows:
        lines.append(f"| {r['_cad'] or '(blank)'} | {r['date']} | {r['event_name']} "
                     f"| {r['attendee_names']} | {r['_squad']} | CSB disabled |")
    if not csb_rows:
        lines.append("| _none_ | | | | | |")
    lines.append("")
    (DOCS_DIR / f"{MONTH_TAG}_unrouted_report.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="CE CAD ETL — month derived from source filename")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE), help="CAD CE monthly export path")
    ap.add_argument("--write", action="store_true", help="Wave 4: write CSV + reports (default: dry-run)")
    args = ap.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"FAIL: source not found: {source}")

    # derive target year/month + doc tag from filename 'YYYY_MM_CE.xlsx'
    m = _re.match(r"(\d{4})_(\d{2})_CE", source.stem)
    if not m:
        raise SystemExit(f"FAIL: cannot parse YYYY_MM from filename: {source.name}")
    global TARGET_YEAR, TARGET_MONTH, MONTH_TAG
    TARGET_YEAR, TARGET_MONTH = int(m.group(1)), int(m.group(2))
    MONTH_TAG = f"{TARGET_YEAR}_{TARGET_MONTH:02d}"
    print(f"[target] {MONTH_TAG} from {source.name}")

    df = pd.read_excel(source, sheet_name=SHEET, engine="openpyxl")
    df["ReportNumberNew"] = df["ReportNumberNew"].apply(norm_case)  # preserve case-number string

    inv = wave1_inventory(df, source)
    out_rows, sta_rows, csb_rows, dups, imputed = wave2_transform(df, source, inv)
    sta_results, proposals = wave3_stacp_verify(sta_rows)

    if args.write:
        csv_path = wave4_write(out_rows, sta_results, csb_rows, source, dups, imputed, proposals)
        print("\n=== COMPLETION ===")
        print(f"  Source: {source.name} | CAD rows {len(df)} | in-month rows {inv['may_rows']} | "
              f"Output {len(out_rows)} | STA verify {len(sta_rows)} | CSB unrouted {len(csb_rows)} | "
              f"dups {len(dups)} | imputed {len(imputed)} | proposals {len(proposals)}")
        print(f"  CSV: {csv_path}")
    else:
        print("\n[DRY-RUN] Waves 1-3 complete, no writes. Re-run with --write for Wave 4.")


if __name__ == "__main__":
    main()
