Summary
=======

Current Status (2026-02-13)
---------------------------

- CSB source now reads from sheet **CSB_CommOut**, table `_csb_commout` in `csb_monthly.xlsm` (config and `src/processors/csb_processor.py` updated).
- Pipeline processes four data sources:
  - Community Engagement: from `Community_Engagement_Monthly.xlsx`, sheet `2025_Master`.
  - STA&CP: from `STACP.xlsm`, sheet `25_School_Outreach`.
  - Patrol: from `patrol_monthly.xlsm`, sheet `Main_Outreach_Combined`.
  - CSB: from `csb_monthly.xlsm`, sheet `CSB_CommOut` (table `_csb_commout`).
- Combined output is written to `output/community_engagement_data_YYYYMMDD_HHMMSS.csv` (and `.xlsx`). Power BI M query `src/___Combined_Outreach_All.m` uses the most recent file in `output/`.

Key Actions Completed
---------------------

- Updated CSB config and processor default to sheet `CSB_CommOut` (fixes "Worksheet named '25_Jan' not found").
- Documentation updated (README, CHANGELOG, SUMMARY).

Next Steps
----------

- Run `python src/main_processor.py` from project root after source file updates to refresh output for Power BI.
- Configure scheduled execution via `monitor_etl.py` or Windows Task Scheduler to keep output current.
- Refresh Power BI report after ETL runs to display latest community engagement data.

