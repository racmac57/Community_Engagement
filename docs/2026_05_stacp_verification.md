# STACP Verification Report — May 2026 (ce-cad-etl)

Generated: 2026-06-11T03:51:05
Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: **date (col B) + location (col I)**. CAD# (col G) shown for reference only — rarely entered.

| CAD# (ref) | Date | Incident | CAD Location | Officer | Classification | Matched STACP row(s) | STACP Location |
|---|---|---|---|---|---|---|---|
| 26-043977 | 2026-05-13 | Community Engagement - Community Policing | M & M Center | Lt. Anthony DiPersia 266 | **MISSING** | None |  |
| 26-048609 | 2026-05-27 | Community Engagement - School Outreach | M & M Center | Sgt. Mark Del Carpio 156 | **PRESENT** | 321 | MM Center |
| 26-048850 | 2026-05-28 | Community Engagement - Community Policing | Jackson Avenue School | Det. Felix Katsaroans 326 | **SPLIT_SUGGESTED** | 322 | Jackson and Fairmount |

**Match logic:** location normalized (lowercased, non-alphanumerics stripped; e.g. 'M & M Center' = 'MM Center'), then collapsed-equality / containment / token-Jaccard ≥ 0.5.

**Legend:** PRESENT = STACP already has this event (no action). SPLIT_SUGGESTED = a combined STACP row holds 2+ events and CAD matches one — the CAD-backed half is provided below as a paste-ready row. CONFLICT = same-date row(s) exist but no location match. MISSING = STACP has no row that day — a paste-ready row is provided below. These are gap-fills generated from CAD; paste as-is, no follow-up required.

## Proposed Master_Outreach entries (paste-ready)

Generated from the CAD export for MISSING / SPLIT_SUGGESTED rows. Memorial CADs have no real span, so **Start = Time of Call, End = Start + 30 min, Total Time = 0.5 h**. Review before pasting; also TSV at `docs/2026_05_stacp_proposed_entries.csv`.

| Event ID | Date | Start Time | End Time | Total Time | CAD# | School Outreach Conducted | Location | Attendees | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 20260513-001 | 2026-05-13 | 17:23 | 17:53 | 0.5 | 26-043977 | Community Engagement - Community Policing | M & M Center | A. DiPersia | MISSING -> new row |
| 20260528-001 | 2026-05-28 | 10:51 | 11:21 | 0.5 | 26-048850 | Community Engagement - Community Policing | Jackson Avenue School | F. Katsaroans | SPLIT row 322 (Jackson and Fairmount) -> this half |

## Duration normalized to 30 min

A CAD span under 2 minutes is a log-only record, not a real event length. These are set to a 0.5 h default in the output CSV — a sensible floor, no per-row judgment needed.

| Date | Officer | Location |
|---|---|---|
| 2026-05-13 | Lt. Anthony DiPersia 266 | M & M Center |
| 2026-05-27 | P.O. Arauki Revi 320 | Hackensack High School |
| 2026-05-27 | Sgt. Mark Del Carpio 156 | M & M Center |
| 2026-05-30 | P.O. Teudy Luna 391 | Passaic Street |
