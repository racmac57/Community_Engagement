Community Engagement ETL
========================

Overview
--------

This repository automates the consolidation of Hackensack Police Department community engagement activity so it can be reported through Power BI. The ETL pipeline ingests multiple Excel workbooks, standardizes the structure, validates data quality, and exports combined CSV/Excel outputs that Power BI refreshes against.

**Note:** The directory name `Community_Engagment` contains a typo (missing 'e'). The correct spelling is `Community_Engagement`. Do not rename without coordinating downstream references (config.json, task_schedule.xml, M code paths).

Key Features
------------

- Multi-source ingestion covering Community Engagement, STA&CP, Patrol, and CSB datasets.
- Shared processing framework built on `pandas`, with reusable helpers for Excel access, column normalization, and validation.
- Patrol processor v2: rank-prefix stripping, expanded delimiter parsing, attendee_names column for person-level analysis.
- COMPSTAT safety filter prevents CSB productivity data from contaminating outreach output.
- Automated backups, reporting, and export artifacts ready for the Power BI data model.
- Logging with EST timestamps and file rotation.
- Validation tooling (`power_bi_export_validator.py`, `data_quality_validator.py`) keeps output aligned with downstream requirements.

Data Sources
------------

| Source | Workbook | Sheet | Status |
|--------|----------|-------|--------|
| Community Engagement | `Community_Engagement_Monthly.xlsx` | `2025_Master` | Active |
| STA&CP | `STACP.xlsm` | `School_Outreach` | Active |
| Patrol | `patrol_monthly.xlsm` | `Main_Outreach_Combined` | Active |
| CSB | `csb_monthly.xlsm` | `CSB_CommOut` | **Disabled** (COMPSTAT tracker, not outreach) |

Source paths are defined in `config.json` using `C:\Users\carucci_r\...` base paths (resolved via junction at runtime).

Project Structure
-----------------

```
Community_Engagment/
+-- config.json                  # Source paths, sheet names, output config
+-- production_config.json       # SMTP, PBI, backup settings
+-- src/
|   +-- main_processor.py        # Pipeline orchestrator
|   +-- processors/
|   |   +-- excel_processor.py   # Base class
|   |   +-- community_engagement_processor.py
|   |   +-- stacp_processor.py
|   |   +-- patrol_processor.py  # v2 with attendee parsing
|   |   +-- csb_processor.py     # Disabled
|   +-- utils/
|   |   +-- config_loader.py     # JSON config reader
|   |   +-- logger_setup.py      # Rotating logger with EST
|   |   +-- data_validator.py    # File/sheet/column validation
|   |   +-- duration_utils.py    # Duration normalization
|   |   +-- attendee_utils.py    # STACP attendee alias mapping
+-- Combined_Outreach_All.m      # Power BI M code query
+-- output/                      # Timestamped CSV+XLSX exports
+-- reports/                     # Processing summaries
+-- logs/                        # Rotating log files
+-- backups/                     # Source file backups
+-- data/                        # Sample/reference data
+-- docs/                        # Extended documentation
+-- tests/                       # Test scripts
```

Getting Started
---------------

### Prerequisites

- Python 3.8+ with: `pandas`, `openpyxl`, `pytz`
- Source workbooks accessible at paths in `config.json`

### Running the Pipeline

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment"
python src/main_processor.py
```

### Output

The pipeline produces timestamped files in `output/`:
- `community_engagement_data_YYYYMMDD_HHMMSS.csv` -- combined data for Power BI
- `community_engagement_data_YYYYMMDD_HHMMSS.xlsx` -- same with Summary sheet

Power BI M code (`Combined_Outreach_All.m`) auto-discovers the most recent CSV.

### Scheduled Execution

Windows Task Scheduler runs monthly on the 1st at 06:00 EST via `task_schedule.xml`.

Validation and Monitoring
-------------------------

- `power_bi_export_validator.py` -- verifies exports stay within Power BI limits.
- `data_quality_validator.py` -- checks required fields and quality scores.
- `setup_validator.py` -- pre-run environment validation.
- `verify_config.py` -- config.json sanity checks.
- Logs are written to `logs/` with detailed processor status.

Recent Changes
--------------

See `CHANGELOG.md` for full history.

- **2026-03-28:** Documentation audit and refresh (CLAUDE.md, README, CHANGELOG, SUMMARY, docs/).
- **2026-03-11:** STACP source config fixed to `School_Outreach`. Power BI M query updated with Event ID and Row_ID.
- **2026-03-05:** Patrol processor v2 with enhanced attendee parsing.
- **2026-02-13:** CSB source disabled; COMPSTAT safety filter added.

Documentation
-------------

- `CLAUDE.md` -- Comprehensive AI assistant guide with architecture, schemas, and gotchas.
- `docs/etl-pipeline.md` -- ETL pipeline flow documentation.
- `docs/file-inventory.md` -- Complete file inventory with roles.
- `docs/config-reference.md` -- Configuration file reference.

Support
-------

Maintained by R. A. Carucci #261, SSOCC, Hackensack Police Department.
