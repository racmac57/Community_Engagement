Community Engagement ETL
=========================

Overview
--------

This repository automates the consolidation of Hackensack Police Department community engagement activity so it can be reported through Power BI. The ETL pipeline ingests multiple Excel workbooks, standardises the structure, validates data quality, and exports combined CSV/Excel outputs that Power BI refreshes against.

Key Features
------------

- Multi-source ingestion covering Community Engagement, STA&CP, Patrol, and CSB datasets.
- Shared processing framework built on `pandas`, with reusable helpers for Excel access, column normalisation, and validation.
- Automated backups, reporting, and export artefacts ready for the Power BI data model.
- Logging and validation tooling (`power_bi_export_validator.py`, `data_quality_validator.py`) that keeps the output aligned with downstream requirements.

Recent Updates
--------------

- **2026-03-05:** Patrol processor v2: Enhanced attendee parsing (rank stripping, expanded delimiters, non-name detection, fallback logic). New `attendee_names` column in combined output for person-level analysis. CSV/Excel export column order updated; Power BI M query remains backward compatible.
- **2026-02-13:** CSB source configuration updated to sheet `CSB_CommOut` and table `_csb_commout` in `csb_monthly.xlsm`. Run `python src/main_processor.py` from the project root to regenerate output for Power BI / `___Combined_Outreach_All.m`.
- **2026-01-12:** Verified ETL processors correctly process all records from source files. Latest run generated 558 total records, including all 31 December 2025 events (17 Community Engagement + 14 STA&CP). Latest export: `output/community_engagement_data_20260112_193127.*`.
- **2025-11-10:** Successfully ingested the STA&CP workbook (`STACP.xlsm`, table `_25_outreach` on `25_School_Outreach`) after resolving file-lock issues. Combined output now contains 504 records with STA&CP events flagged as `Office = "STA&CP"`.
- **2025-11-10:** End-to-end run of `src/main_processor.py` generated refreshed exports (`output/community_engagement_data_20251110_113422.*`) that Power BI can consume immediately.
- **2025-11-10:** Repository initialised and synchronised with GitHub (`master` branch).

Project Structure
-----------------

- `src/main_processor.py` – orchestrates all processors, backups, reports, and exports.
- `src/processors/` – source-specific processors (Community Engagement, STA&CP, Patrol, CSB) built on the shared `ExcelProcessor`.
- `src/utils/` – configuration loader, logging setup, data validation helpers.
- `config.json` / `production_config.json` – source file locations and deployment settings.
- `output/`, `reports/`, `logs/` – generated artefacts from each pipeline run.
- `data/` – sample CSV extracts mirroring October 2025 data for quick analysis.

Getting Started
---------------

1. Install dependencies (Python 3.12+): `pip install -r requirements.txt`.
2. Ensure source workbooks are accessible at the paths defined in `config.json`.
3. Run the pipeline: `python src/main_processor.py`.
4. Review the latest combined CSV/Excel in `output/` and refresh the Power BI dataset (the M query `Combined_Outreach_All.m` automatically pulls the most recent file).

Validation & Monitoring
-----------------------

- Use `power_bi_export_validator.py` to verify that exports stay within Power BI limits.
- `monitor_etl.py` and `deploy_production.py` support scheduling and deployment workflows.
- Logs are written to `logs/` and include detailed status for each processor.

Support
-------

For questions or issue tracking, open an issue on the GitHub repository or email the ETL operations team at `etl@hackensacknj.gov`.

