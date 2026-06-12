# Wave 5 CE Ship Decision — May 2026

**Date:** 2026-06-12  
**Context:** Workbook_Redesign_2026 / Compstat May ship — CE marked PROVISIONAL pending CAD routing validation.  
**Decision owner:** RAC / SSOCC

---

## Decision

**Re-validate and ship May using the CAD-integrated combined feed, with a provisional methodology footnote.**

Do **not** ship pre-CAD workbook-only figures.

---

## Rationale

The ce-cad-etl session (CAD routing + squad mapping + gap-fill anti-join) is **production-ready**:

| Milestone | Status |
|-----------|--------|
| `cad_ce_processor.py` — Squad → office routing | Done (2026-06-11) |
| `main_processor._dedup_cad_gapfill()` | Done |
| May 2026 CAD export in `config.json` | Done (`2026_05_CE.xlsx`) |
| Production run + PBI load path | Verified |
| QA reports (`docs/2026_05_*`) | Done |

### May 2026 figure delta (workbook-only vs CAD-integrated)

| Run | File | Total rows | May 2026 events | May CAD gap-fill |
|-----|------|------------|-----------------|------------------|
| Pre-CAD | `community_engagement_data_20260610_185029.csv` | 582 | 5 (STA&CP only) | 0 |
| CAD-integrated | `community_engagement_data_20260611_154355.csv` | 599 | 15 | 9 |

Shipping workbook-only figures would undercount May by **10 events**.

### May 2026 CAD-integrated breakdown (15 events)

| Office | Count |
|--------|-------|
| Community Engagement | 5 |
| Patrol | 2 |
| STA&CP | 8 |

- **9 rows** retained from CAD gap-fill (`data_source = cad_ce`)
- **1 CAD duplicate dropped** — Del Carpio 5/27 M&M Center (STACP workbook row already present)

---

## Provisional footnote (for CE visual / slide)

> May 2026 includes CAD gap-fill (workbook = system of record; 9 CAD-only events added, 1 duplicate suppressed). CSB-squad CAD excluded. Subject to STACP workbook reconciliation.

---

## Residual gaps (footnote scope — not ship blockers)

1. **CSB squad excluded** — 1 May CAD row unrouted (Det. Carrillo, Victim Support). See `docs/2026_05_unrouted_report.md`.
2. **STACP paste-ready rows** — DiPersia (5/13) and Katsaroans SPLIT (5/28) documented in `docs/2026_05_stacp_verification.md`. Both already captured via CAD gap-fill; workbook paste is cleanup.
3. **Feb/Mar 2026 CAD backfill** — paused; does not block May.
4. **Manual monthly step** — update `config.json` `cad_ce.file_path` each cycle (auto-pick not built yet).

---

## Ship actions

1. Refresh PBI from `output/community_engagement_data_20260611_154355.csv` (or re-run `python src/main_processor.py` if workbooks changed since 2026-06-11).
2. Apply provisional footnote on the Engagement Initiatives by Bureau visual.
3. Optional cleanup: paste STACP proposals from verification report into `Master_Outreach`.

---

## CC routing (one line)

> Wave 5 CE: PROCEED — re-validate against CAD-integrated logic; May ships on 2026-06-11 combined feed with provisional footnote.
