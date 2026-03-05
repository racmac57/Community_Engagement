Summary
=======

Current Status (2026-03-05)
---------------------------

- Patrol processor v2: Enhanced attendee parsing with rank stripping, expanded delimiters, and new `attendee_names` column in combined output.
- CSB source reads from sheet `_csb_commout` in `csb_monthly.xlsm` (config and `src/processors/csb_processor.py`).
- Pipeline processes four data sources:
  - Community Engagement: from `Community_Engagement_Monthly.xlsx`, sheet `_25_ce`.
  - STA&CP: from `STACP.xlsm`, sheet `_25_outreach`.
  - Patrol: from `patrol_monthly.xlsm`, sheet `Main_Outreach_Combined`.
  - CSB: from `csb_monthly.xlsm`, sheet `_csb_commout`.
- Combined output is written to `output/community_engagement_data_YYYYMMDD_HHMMSS.csv` (and `.xlsx`). Schema: `date`, `start_time`, `end_time`, `event_name`, `location`, `duration_hours`, `attendee_count`, `office`, `division`, `attendee_names` (Patrol v2). Power BI M query `src/___Combined_Outreach_All.m` uses the most recent file in `output/`.

Key Actions Completed
---------------------

- Patrol processor v2: Rank stripping, expanded delimiters, `attendee_names` column, fallback logic for empty attendee fields.
- Updated CSB config and processor default to sheet `_csb_commout` (fixes "Worksheet named '25_Jan' not found").
- Documentation updated (README, CHANGELOG, SUMMARY).

Next Steps
----------

- Run `python src/main_processor.py` from project root after source file updates to refresh output for Power BI.
- Configure scheduled execution via `monitor_etl.py` or Windows Task Scheduler to keep output current.
- Refresh Power BI report after ETL runs to display latest community engagement data.

