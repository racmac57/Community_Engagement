# STACP Verification Report — May 2026 (ce-cad-etl)

Generated: 2026-06-11T03:45:08
Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: **date (col B) + location (col I)**. CAD# (col G) shown for reference only — rarely entered.

| CAD# (ref) | Date | Incident | CAD Location | Officer | Classification | Matched STACP row(s) | STACP Location |
|---|---|---|---|---|---|---|---|
| 26-043977 | 2026-05-13 | Community Engagement - Community Policing | M & M Center | Lt. Anthony DiPersia 266 | **MISSING** | None |  |
| 26-048609 | 2026-05-27 | Community Engagement - School Outreach | M & M Center | Sgt. Mark Del Carpio 156 | **PRESENT** | 321 | MM Center |
| 26-048850 | 2026-05-28 | Community Engagement - Community Policing | Jackson Avenue School | Det. Felix Katsaroans 326 | **SPLIT_SUGGESTED** | 322 | Jackson and Fairmount |

**Match logic:** location normalized (lowercased, non-alphanumerics stripped; e.g. 'M & M Center' = 'MM Center'), then collapsed-equality / containment / token-Jaccard ≥ 0.5.

**Legend:** PRESENT = same-date STACP row whose location matches (no action). SPLIT_SUGGESTED = a combined STACP row (e.g. 'Jackson and Fairmount') holds 2+ events; CAD matches one — split the row so each event stands alone. CONFLICT = same-date row(s) exist but location did not match — review candidates. MISSING = no STACP row on that date — requires manual entry.

## Proposed Master_Outreach entries (paste-ready)

Generated from the CAD export for MISSING / SPLIT_SUGGESTED rows. Memorial CADs have no real span, so **Start = Time of Call, End = Start + 30 min, Total Time = 0.5 h**. Review before pasting; also TSV at `docs/2026_05_stacp_proposed_entries.csv`.

| Event ID | Date | Start Time | End Time | Total Time | CAD# | School Outreach Conducted | Location | Attendees | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 20260513-001 | 2026-05-13 | 17:23 | 17:53 | 0.5 | 26-043977 | Community Engagement - Community Policing | M & M Center | A. DiPersia | MISSING -> new row |
| 20260528-001 | 2026-05-28 | 10:51 | 11:21 | 0.5 | 26-048850 | Community Engagement - Community Policing | Jackson Avenue School | F. Katsaroans | SPLIT row 322 (Jackson and Fairmount) -> this half |

## Duration imputed (near-zero span)

Rows whose CAD span was under 2 minutes — a log-only/memorial CAD with no real duration — replaced with a 30-minute default in the output CSV. `DispatcherNew` shown for context (officer == dispatcher ⇒ self-logged).

| Date | Officer | DispatcherNew | Location |
|---|---|---|---|
| 2026-05-13 | Lt. Anthony DiPersia 266 | DiPersia_a | M & M Center |
| 2026-05-27 | P.O. Arauki Revi 320 | Sosa_C | Hackensack High School |
| 2026-05-27 | Sgt. Mark Del Carpio 156 | garrett_f | M & M Center |
| 2026-05-30 | P.O. Teudy Luna 391 | garcia_b | Passaic Street |
