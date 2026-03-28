Summary
=======

Current Status (2026-03-28)
----------------------------

- Pipeline processes three active data sources (Community Engagement, STA&CP, Patrol). CSB is disabled.
- Patrol processor v2: Enhanced attendee parsing with rank stripping, expanded delimiters, and `attendee_names` column.
- CSB source disabled in config.json. COMPSTAT safety filter in main_processor.py prevents contamination even if re-enabled prematurely.
- STACP reads from sheet `School_Outreach` in `STACP.xlsm`.
- Config paths use base `C:\Users\carucci_r\OneDrive - City of Hackensack` (junction resolves at runtime).

Active Sources
--------------

| Source | Workbook | Sheet | Office Label |
|--------|----------|-------|-------------|
| Community Engagement | `Community_Engagement_Monthly.xlsx` | `2025_Master` | Community Engagement |
| STA&CP | `STACP.xlsm` | `School_Outreach` | STA&CP |
| Patrol | `patrol_monthly.xlsm` | `Main_Outreach_Combined` | Patrol |
| CSB | `csb_monthly.xlsm` | `CSB_CommOut` | **DISABLED** |

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
- Create `requirements.txt` with pinned versions.
- Implement output rotation/cleanup policy.
- Archive duplicate and backup files per `reorganization_proposal.md`.
- Evaluate directory rename (`Engagment` -> `Engagement`) with downstream impact analysis.
