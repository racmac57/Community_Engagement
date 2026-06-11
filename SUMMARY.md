Summary
=======

Current Status (2026-06-11)
----------------------------

- Pipeline processes four active sources (Community Engagement, STA&CP, Patrol, CAD CE). CSB is disabled.
- CAD CE (v1, 2026-06): the CAD Community Engagement monthly export is a fifth, gap-fill source via `cad_ce_processor.py`. Routes by Squad to canonical offices, normalizes sub-2-min memorial spans to 0.5 h, and a gap-fill anti-join (`_dedup_cad_gapfill`) drops any CAD row a workbook already covers (workbook is system of record).
- Patrol processor v2: Enhanced attendee parsing with rank stripping, expanded delimiters, and `attendee_names` column.
- CSB source disabled in config.json. COMPSTAT safety filter in main_processor.py prevents contamination even if re-enabled prematurely.
- Sheet names (config truth): Community Engagement `Master_Log`, STA&CP `Master_Outreach`, Patrol `Main_Outreach_Combined`, CAD CE `Sheet1`.
- Config paths use base `C:\Users\carucci_r\OneDrive - City of Hackensack` (junction resolves at runtime).
- `output/` is the production target; the CE visual `Combined_Outreach_All.m` reads the newest CSV there. `_DropExports` is the PBI visual-export drop zone, NOT an ETL target.

Active Sources
--------------

| Source | Workbook / Export | Sheet | Office Label |
|--------|----------|-------|-------------|
| Community Engagement | `Community_Engagement_Monthly.xlsx` | `Master_Log` | Community Engagement |
| STA&CP | `STACP.xlsm` | `Master_Outreach` | STA&CP |
| Patrol | `patrol_monthly.xlsm` | `Main_Outreach_Combined` | Patrol |
| CAD CE | `YYYY_MM_CE.xlsx` (CAD monthly export) | `Sheet1` | per Squad (CE / Patrol / STA&CP) |
| CSB | `csb_monthly.xlsm` | `26_01` | **DISABLED** |

Output
------

- Combined CSV: `output/community_engagement_data_YYYYMMDD_HHMMSS.csv`
- Schema: date, start_time, end_time, event_name, location, duration_hours, attendee_count, office, division, attendee_names, data_source, processed_date
- Power BI M query (`Combined_Outreach_All.m`) auto-discovers latest CSV, renames columns for dashboard.

Known Issues
------------

1. Directory name typo: `Community_Engagement` (missing 'e').
2. No requirements.txt file (deps: pandas, openpyxl, pytz).
3. Stale output accumulation: 30+ timestamped files with no cleanup policy.
4. OneDrive sync duplicates: 7 files with `(1)` suffix need archiving.
5. SUMMARY.md previously stated CE sheet as `_25_ce` -- config.json `2025_Master` is authoritative.

Next Steps
----------

- Run `python src/main_processor.py` from project root after source file updates.
- Before each monthly run, update `config.json` `cad_ce.file_path` to the current `YYYY_MM_CE.xlsx` (candidate: auto-pick newest in the monthly dir).
- Backfill Feb / Mar 2026 CAD CE (paused 2026-06-11).
- Paste the May STACP proposals (`docs/2026_05_stacp_proposed_entries.csv`, DiPersia MISSING + Katsaroans SPLIT) into `Master_Outreach`.
- Create `requirements.txt` with pinned versions.
- Implement output rotation/cleanup policy.
- Evaluate directory rename (`Engagment` -> `Engagement`) with downstream impact analysis.

See the Notion "Power BI Monthly Report - Non-critical Task Tracker" for the full open-task list.
