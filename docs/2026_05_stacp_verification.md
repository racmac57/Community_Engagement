# STACP Verification Report — May 2026 (ce-cad-etl)

Generated: 2026-06-11T03:22:03
Source: STACP.xlsm!Master_Outreach (READ-ONLY). Match key: **date (col B) + location (col I)**. CAD# (col G) shown for reference only — rarely entered.

| CAD# (ref) | Date | Incident | CAD Location | Officer | Classification | Matched STACP row(s) | STACP Location |
|---|---|---|---|---|---|---|---|
| 26-043977 | 2026-05-13 | Community Engagement - Community Policing | M & M Center | Lt. Anthony DiPersia 266 | **MISSING** | None |  |
| 26-048609 | 2026-05-27 | Community Engagement - School Outreach | M & M Center | Sgt. Mark Del Carpio 156 | **PRESENT** | 321 | MM Center |
| 26-048850 | 2026-05-28 | Community Engagement - Community Policing | Jackson Avenue School | Det. Felix Katsaroans 326 | **CONFLICT** | [322] | r322:Jackson and Fairmount |

**Match logic:** location normalized (lowercased, non-alphanumerics stripped; e.g. 'M & M Center' = 'MM Center'), then collapsed-equality / containment / token-Jaccard ≥ 0.5.

**Legend:** PRESENT = same-date STACP row whose location matches (no action). CONFLICT = same-date row(s) exist but location did not match — review candidates, confirm or add. MISSING = no STACP row on that date — requires manual entry in STACP.xlsm!Master_Outreach.
