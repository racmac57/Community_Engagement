# STACP Verification Report — 2026_04 (ce-cad-etl)

Generated: 2026-06-11T04:29:20
Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: **date (col B) + location (col I)**. CAD# (col G) shown for reference only — rarely entered.

| CAD# (ref) | Date | Incident | CAD Location | Officer | Classification | Matched STACP row(s) | STACP Location |
|---|---|---|---|---|---|---|---|

**Match logic:** location normalized (lowercased, non-alphanumerics stripped; e.g. 'M & M Center' = 'MM Center'), then collapsed-equality / containment / token-Jaccard ≥ 0.5.

**Legend:** PRESENT = STACP already has this event (no action). SPLIT_SUGGESTED = a combined STACP row holds 2+ events and CAD matches one — the CAD-backed half is provided below as a paste-ready row. CONFLICT = same-date row(s) exist but no location match. MISSING = STACP has no row that day — a paste-ready row is provided below. These are gap-fills generated from CAD; paste as-is, no follow-up required.

## Duration normalized to 30 min

A CAD span under 2 minutes is a log-only record, not a real event length. These are set to a 0.5 h default in the output CSV — a sensible floor, no per-row judgment needed.

| Date | Officer | Location |
|---|---|---|
| 2026-04-10 | P.O. Arauki Revi 320 | Rothman Center |
| 2026-04-10 | P.O. Arauki Revi 320 | Cigarro Lounge |
| 2026-04-01 | Sgt. Kley Peralta 311 | Civic Center |
| 2026-04-15 | Sgt. Kley Peralta 311 | Civic Center |
| 2026-04-22 | Sgt. Kley Peralta 311 | Headquarters |
| 2026-04-29 | Sgt. Kley Peralta 311 | Mount Olive Baptist Church |
| 2026-04-30 | Sgt. Kley Peralta 311 | Veterans Park |
