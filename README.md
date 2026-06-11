Community Engagement ETL
========================

Overview
--------

This repository automates the consolidation of Hackensack Police Department community engagement activity so it can be reported through Power BI. The ETL pipeline ingests multiple Excel workbooks, standardizes the structure, validates data quality, and exports combined CSV/Excel outputs that Power BI refreshes against.

**Note:** The directory name `Community_Engagement` contains a typo (missing 'e'). The correct spelling is `Community_Engagement`. Do not rename without coordinating downstream references (config.json, task_schedule.xml, M code paths).

Key Features
------------

- Multi-source ingestion covering Community Engagement, STA&CP, Patrol, CSB, and the CAD CE monthly export.
- Shared processing framework built on `pandas`, with reusable helpers for Excel access, column normalization, and validation.
- Patrol processor v2: rank-prefix stripping, expanded delimiter parsing, attendee_names column for person-level analysis.
- CAD CE source (v1, 2026-06): the CAD Community Engagement monthly export is a fifth, gap-fill source. Rows are routed by Squad to canonical offices, near-zero memorial-CAD spans are normalized to 30 minutes, and a gap-fill anti-join drops any CAD row a workbook already covers (workbook is system of record).
- COMPSTAT safety filter prevents CSB productivity data from contaminating outreach output.
- Automated backups, reporting, and export artifacts ready for the Power BI data model.
- Logging with EST timestamps and file rotation.
- Validation tooling (`power_bi_export_validator.py`, `data_quality_validator.py`) keeps output aligned with downstream requirements.

Data Sources
------------

| Source | Workbook / Export | Sheet | Status |
|--------|----------|-------|--------|
| Community Engagement | `Community_Engagement_Monthly.xlsx` | `Master_Log` | Active |
| STA&CP | `STACP.xlsm` | `Master_Outreach` | Active |
| Patrol | `patrol_monthly.xlsm` | `Main_Outreach_Combined` | Active |
| CSB | `csb_monthly.xlsm` | `26_01` | **Disabled** (COMPSTAT tracker, not outreach) |
| CAD CE | `YYYY_MM_CE.xlsx` (CAD monthly export) | `Sheet1` | Active (v1, gap-fill source) |

Source paths are defined in `config.json` using `C:\Users\carucci_r\...` base paths (resolved via junction at runtime).

### CAD Community Engagement source (gap-fill)

The CAD CE monthly export (`05_EXPORTS\_CAD\Community_Engagement\monthly\YYYY_MM_CE.xlsx`, one
officer per row, tagged with a `Squad`) is processed by `src/processors/cad_ce_processor.py`
(`CADCEProcessor`) as the fifth combined-feed source.

- **Squad routing to canonical office:** `COMM ENG` -> Community Engagement, `A1-A4`/`B1-B4` ->
  Patrol, `STA` -> STA&CP, `CSB` -> excluded, any other -> the Squad value.
- **Memorial-CAD normalization:** a CAD span under 2 minutes (often where the officer is also
  the `DispatcherNew`, i.e. self-logged) is a log-only record, not a real event length. It is
  set to a 0.5 h default; the `end_time` is shifted to match.
- **Gap-fill anti-join** (`main_processor.combine_data._dedup_cad_gapfill`): the manual workbook
  is the system of record. A CAD row is dropped when a non-CAD row already covers the same event
  (key: date + normalized location). CAD only fills holes the workbooks miss.
- **QA companion** `scripts/ce_cad_etl.py`: read-only; emits the STACP verification report
  (date+location match with a combined-row SPLIT guard), paste-ready proposed `Master_Outreach`
  entries for MISSING/SPLIT rows, and the unrouted (CSB) report. It does **not** write the
  production CSV and must not write to `_DropExports`.
- **Monthly maintenance:** update `config.json` `cad_ce.file_path` to the current
  `YYYY_MM_CE.xlsx` before each run.

> **`_DropExports` is not an ETL target.** It is the Power BI visual-export drop zone, swept by
> `06_Workspace_Management/scripts/process_powerbi_exports.py`. The ETL writes the combined CSV to
> `output/`; the CE visual's `Combined_Outreach_All.m` reads the newest file there.

Project Structure
-----------------

```
Community_Engagement/
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
|   +-- processors/
|       +-- cad_ce_processor.py  # 5th source: CAD CE export -> canonical schema + gap-fill key
+-- scripts/
|   +-- ce_cad_etl.py            # QA companion: STACP verify + proposals + unrouted (no prod CSV)
+-- Combined_Outreach_All.m      # Power BI M code query (reads newest output/ CSV)
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
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagement"
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

- **2026-06-11:** CAD CE export integrated as fifth gap-fill source (`cad_ce_processor.py`); gap-fill anti-join, 30-min memorial normalization, canonical-office routing. `scripts/ce_cad_etl.py` QA companion. Config sheet names corrected (`Master_Log`, `Master_Outreach`). Pipeline core + untracked utils committed.
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
