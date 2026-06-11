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
TARGET_YEAR, TARGET_MONTH = 2026, 5
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
    "Officer", "Squad", "Summons", "Warning",
]

PATROL_SQUADS = {"A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"}

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
    print(f"  required 12 cols  : ALL PRESENT")
    print(f"  total_rows        : {len(df)}")
    print(f"  may2026_rows      : {may_rows}")
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
    print(f"  TRIPWIRE: {len(df)} | {may_rows} | {out_of_range} | {squad_counts}")
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

    out_rows, sta_rows, csb_rows = [], [], []
    for idx, r in df.iterrows():
        if not inv["in_month"].iloc[idx]:
            continue  # out-of-range already counted in Wave 1
        dest, office, division = route(r["Squad"])
        toc = pd.to_datetime(r["Time of Call"], errors="coerce")
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
        }
        ho = safe_duration_to_hours(r["Time Out Display"], default=float("nan"))
        hi = safe_duration_to_hours(r["Time In Display"], default=float("nan"))
        if not (math.isnan(ho) or math.isnan(hi)):
            dur = round(hi - ho, 4)
            if dur < 0:
                raise SystemExit(f"FAIL Wave2: negative duration row {idx} ({dur}h)")
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

    # duplicate flag on (date, event_name, attendee_names) — surface only
    seen, dups = {}, []
    for rec in out_rows:
        key = (rec["date"], rec["event_name"], rec["attendee_names"])
        seen.setdefault(key, []).append(rec)
    for key, recs in seen.items():
        if len(recs) > 1:
            dups.append((key, len(recs)))

    print(f"  output_rows : {len(out_rows)} (conservation OK: == {expected})")
    print(f"  sta_rows    : {len(sta_rows)}")
    print(f"  csb_rows    : {len(csb_rows)}")
    print(f"  duplicates  : {len(dups)}")
    print(f"  TRIPWIRE: {len(out_rows)+len(sta_rows)+len(csb_rows)} | {len(out_rows)} | "
          f"{len(sta_rows)} | {len(csb_rows)} | {len(dups)}")

    print("\n  --- GATE 2a: transformed output rows (12 fields) ---")
    for rec in out_rows:
        print("   " + " | ".join(f"{c}={rec[c]}" for c in OUTPUT_COLS))
    print("\n  --- GATE 2b: duplicate flags ---")
    print("    " + ("none" if not dups else str(dups)))
    print("\n  --- GATE 2c: STA rows (-> verification) ---")
    for rec in sta_rows:
        print(f"    CAD#={rec['_cad']} | {rec['date']} | {rec['event_name']} | {rec['attendee_names']}")
    print("\n  --- GATE 2d: CSB rows (-> unrouted) ---")
    for rec in csb_rows:
        print(f"    CAD#={rec['_cad']} | {rec['date']} | {rec['event_name']} | {rec['attendee_names']}")
    print("  Wave 2: PASS")
    return out_rows, sta_rows, csb_rows, dups


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
        d = None
        if isinstance(date_v, (datetime.datetime, datetime.date)):
            d = date_v.date() if isinstance(date_v, datetime.datetime) else date_v
        recs.append({"rowidx": i, "date": d, "cad": norm_case(cad_v),
                     "event": "" if event_v is None else str(event_v).strip()})
    wb.close()
    return recs


def wave3_stacp_verify(sta_rows):
    print("\n=== WAVE 3 — STACP Verification (read-only) ===")
    before = mtime(STACP_PATH)
    stacp = read_stacp_outreach()
    by_cad = {r["cad"]: r for r in stacp if r["cad"]}
    by_date = {}
    for r in stacp:
        if r["date"] is not None:
            by_date.setdefault(r["date"], []).append(r["rowidx"])

    results = []
    for rec in sta_rows:
        cad = rec["_cad"]
        try:
            rdate = datetime.date.fromisoformat(rec["date"]) if rec["date"] else None
        except ValueError:
            rdate = None
        if cad and cad in by_cad:
            cls, matched = "PRESENT", by_cad[cad]["rowidx"]
        elif rdate is not None and rdate in by_date:
            cls, matched = "CONFLICT", by_date[rdate]
        else:
            cls, matched = "MISSING", None
        results.append({**rec, "classification": cls, "matched_row": matched})

    after = mtime(STACP_PATH)
    unchanged = before == after
    n_present = sum(1 for r in results if r["classification"] == "PRESENT")
    n_missing = sum(1 for r in results if r["classification"] == "MISSING")
    n_conflict = sum(1 for r in results if r["classification"] == "CONFLICT")

    print("  --- STACP VERIFICATION REPORT ---")
    for r in results:
        print(f"    CAD#={r['_cad'] or '(blank)'} | {r['date']} | {r['event_name']} "
              f"| {r['classification']} | matched_row={r['matched_row']}")
    print(f"  TRIPWIRE: present={n_present} | missing={n_missing} | conflict={n_conflict} "
          f"| stacp_mtime_unchanged={unchanged}")
    if len(results) != len(sta_rows):
        raise SystemExit("FAIL Wave3: verification row count mismatch")
    if not unchanged:
        raise SystemExit("FAIL Wave3: STACP.xlsm mtime changed")
    print("  Wave 3: PASS")
    return results


# ---------------------------------------------------------------- write
def wave4_write(out_rows, sta_results, csb_rows, source: Path, dups):
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

    _write_stacp_report(sta_results)
    _write_unrouted_report(csb_rows)

    after = {p: mtime(p) for p in before}
    unmodified = all(before[p] == after[p] for p in before)
    if not unmodified:
        raise SystemExit("FAIL Wave4: a source workbook mtime changed")

    print(f"  csv_path  : {csv_path}")
    print(f"  csv_rows  : {len(out_df)}")
    print(f"  csv_cols  : {len(out_df.columns)}")
    print(f"  TRIPWIRE: {len(out_df)} | {len(out_df.columns)} | "
          f"source_workbooks_unmodified={unmodified} | docs_written=True")
    print("  first 3 rows:")
    for _, r in out_df.head(3).iterrows():
        print("   " + " | ".join(f"{c}={r[c]}" for c in OUTPUT_COLS))
    print("  Wave 4: PASS")
    return csv_path


def _write_stacp_report(results):
    lines = [
        "# STACP Verification Report — May 2026 (ce-cad-etl)", "",
        f"Generated: {datetime.datetime.now().isoformat(timespec='seconds')}",
        "Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: CAD# (col G) "
        "primary, date (col B) fallback.", "",
        "| CAD# | Date | Incident | Officer | Classification | Matched STACP row |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r['_cad'] or '(blank)'} | {r['date']} | {r['event_name']} "
                     f"| {r['attendee_names']} | **{r['classification']}** | {r['matched_row']} |")
    lines += ["", "**Legend:** PRESENT = CAD# found in Master_Outreach (no action). "
              "CONFLICT = no CAD# match but a same-date row exists (review candidate row). "
              "MISSING = neither — requires manual entry in STACP.xlsm!Master_Outreach.", ""]
    (DOCS_DIR / "2026_05_stacp_verification.md").write_text("\n".join(lines), encoding="utf-8")


def _write_unrouted_report(csb_rows):
    lines = [
        "# Unrouted Report — May 2026 (ce-cad-etl)", "",
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
    (DOCS_DIR / "2026_05_unrouted_report.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="CE CAD ETL — May 2026")
    ap.add_argument("--source", default=str(DEFAULT_SOURCE), help="CAD CE monthly export path")
    ap.add_argument("--write", action="store_true", help="Wave 4: write CSV + reports (default: dry-run)")
    args = ap.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"FAIL: source not found: {source}")

    df = pd.read_excel(source, sheet_name=SHEET, engine="openpyxl")
    df["ReportNumberNew"] = df["ReportNumberNew"].apply(norm_case)  # preserve case-number string

    inv = wave1_inventory(df, source)
    out_rows, sta_rows, csb_rows, dups = wave2_transform(df, source, inv)
    sta_results = wave3_stacp_verify(sta_rows)

    if args.write:
        csv_path = wave4_write(out_rows, sta_results, csb_rows, source, dups)
        print("\n=== COMPLETION ===")
        print(f"  Source: {source.name} | CAD rows {len(df)} | May rows {inv['may_rows']} | "
              f"Output {len(out_rows)} | STA verify {len(sta_rows)} | CSB unrouted {len(csb_rows)} | "
              f"dups {len(dups)}")
        print(f"  CSV: {csv_path}")
    else:
        print("\n[DRY-RUN] Waves 1-3 complete, no writes. Re-run with --write for Wave 4.")


if __name__ == "__main__":
    main()
