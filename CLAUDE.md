# Community Engagement ETL -- CLAUDE.md

> **Repo**: `Community_Engagment` (note: directory name has typo -- should be `Engagement`)
> **Remote**: `racmac57/Community_Engagement.git`
> **Last Updated**: 2026-03-28
> **Maintainer**: R. A. Carucci #261, SSOCC / Hackensack PD
> **AI Assistants Used**: Claude (Excel add-in, Claude Code), Cursor AI

---

## 1. Purpose

ETL pipeline that consolidates community engagement activity from four HPD data sources (Community Engagement, STA&CP, Patrol, CSB) into a single CSV consumed by a Power BI dashboard. Each source is an Excel workbook maintained by its respective bureau; this pipeline standardizes schemas, validates quality, and exports timestamped output files.

---

## 2. Architecture

```
Source Workbooks                       Configuration
  Community_Engagement_Monthly.xlsx       config.json
  STACP.xlsm                                 |
  patrol_monthly.xlsm                        |
  csb_monthly.xlsm (disabled)               |
       |                                     |
       v                                     v
  src/processors/                    src/main_processor.py
  +- community_engagement_processor.py       |
  +- stacp_processor.py                      |
  +- patrol_processor.py (v2)                |
  +- csb_processor.py                        |
  +- excel_processor.py (base class)         |
       |                                     |
       +-------- combine_data() ------------+
                      |
                      v
         output/community_engagement_data_*.csv
                      |
                      v
         Power BI (Combined_Outreach_All.m)
```

---

## 3. File Inventory

### Core Pipeline

| File | Role |
|------|------|
| `src/main_processor.py` | Orchestrator: runs all processors, combines output, validates, exports CSV+Excel |
| `src/processors/excel_processor.py` | Base class: read_excel_source(), standardize_columns(), calculate_duration(), validate_data() |
| `src/processors/community_engagement_processor.py` | Processes Community_Engagement_Monthly.xlsx (sheet `2025_Master`) |
| `src/processors/stacp_processor.py` | Processes STACP.xlsm (sheet `School_Outreach`) |
| `src/processors/patrol_processor.py` | **v2** -- Processes patrol_monthly.xlsm (sheet `Main_Outreach_Combined`); rank stripping, attendee_names |
| `src/processors/csb_processor.py` | Processes csb_monthly.xlsm -- currently **disabled** in config (COMPSTAT data, not outreach) |
| `config.json` | Source file paths, sheet names, output directory, validation rules |
| `production_config.json` | SMTP, Power BI workspace, backup/monitoring settings (credentials blank) |

### Utilities

| File | Role |
|------|------|
| `src/utils/config_loader.py` | Reads and validates config.json |
| `src/utils/logger_setup.py` | Rotating file logger with EST timestamps (pytz) |
| `src/utils/data_validator.py` | File/sheet/column validation; ValidationError exception |
| `src/utils/duration_utils.py` | Converts timedelta/time/string/float to decimal hours for CSV export |
| `src/utils/attendee_utils.py` | STACP attendee parsing with PERSONNEL_ALIASES normalization |
| `src/__init__.py` | Package marker |
| `src/processors/__init__.py` | Package marker |
| `src/utils/__init__.py` | Package marker |

### Power BI M Code

| File | Role |
|------|------|
| `Combined_Outreach_All.m` | Root-level M query -- reads latest output CSV, types columns, renames for PBI |
| `src/___Combined_Outreach_All.m` | Identical copy in src/ (kept for reference; functionally same as root copy) |

### Validation / Debug Scripts (root level)

| File | Role | Status |
|------|------|--------|
| `data_quality_validator.py` | Standalone data quality checks | Active utility |
| `power_bi_export_validator.py` | Verifies exports stay within PBI limits | Active utility |
| `setup_validator.py` | Pre-run environment validation | Active utility |
| `verify_config.py` | Config.json sanity checks | Active utility |
| `validate_m_code_logic.py` | Validates M code transform logic against Python output | Active utility |
| `debug_csb_structure.py` | Debug script for CSB workbook structure | Dead -- one-time debug |
| `debug_processors.py` | Debug script for processor testing | Dead -- one-time debug |
| `sample_office_distribution.py` | Generates office distribution sample | Dead -- one-time analysis |
| `test_date_parsing.py` | Date parsing test script | Dead -- one-time test |
| `integration_test.py` | End-to-end integration test | Active test |
| `deploy_production.py` | Deployment helper | Likely unused |
| `monitor_etl.py` | Monitoring/scheduling helper | Likely unused |
| `project_scaffold.py` | Scaffolding generator | Dead -- ran once |

### Documentation

| File | Role | Notes |
|------|------|-------|
| `CLAUDE.md` | This file -- AI assistant guide | Authoritative |
| `README.md` | Project readme | Current |
| `CHANGELOG.md` | Change history | Current through 2026-03-11 |
| `SUMMARY.md` | Status summary | Current through 2026-03-11 |
| `Notes.md` | Raw data notes (Aug 2025 sample data) | Reference |
| `PYTHON_WORKSPACE_AI_GUIDE.md` | Generic AI workspace guide | Template -- not project-specific |
| `PYTHON_WORKSPACE_TEMPLATE.md` | Generic workspace template | Template -- not project-specific |
| `office_name_debug_report.md` | Debug report on office name normalization | One-time artifact |
| `processor_validation_report.md` | Processor validation results | One-time artifact |
| `docs/cursor_prompt_fix_community_etl.md` | Cursor prompt for CSB COMPSTAT exclusion | Reference |

### Duplicate / Clutter Files

| File | Assessment |
|------|-----------|
| `CHANGELOG (1).md` | OneDrive sync duplicate -- archive |
| `README (1).md` | OneDrive sync duplicate -- archive |
| `SUMMARY (1).md` | OneDrive sync duplicate -- archive |
| `config.json.backup_20260219_142331` | Config backup -- archive |
| `config.json.backup_20260219_142624` | Config backup -- archive |
| `config.json.backup_20260219_143114` | Config backup -- archive |
| `config.json.backup_20260219_144204` | Config backup -- archive |
| `task_schedule (1).xml` | OneDrive sync duplicate -- archive |
| `logs/community_engagement_etl (1).log` | OneDrive sync duplicate -- archive |
| `logs/main_processor (1).log` | OneDrive sync duplicate -- archive |
| `src/logs/community_engagement_etl (1).log` | OneDrive sync duplicate -- archive |
| `src/logs/main_processor (1).log` | OneDrive sync duplicate -- archive |
| `tmpclaude-974f-cwd` | Temp file from Claude Code -- delete |

### Data / Output Directories

| Directory | Contents |
|-----------|----------|
| `data/` | Sample CSVs (25_10 prefix) and preview_table.csv |
| `output/` | 30+ timestamped CSV+XLSX export pairs (2025-09 through 2026-03) |
| `reports/` | 30+ monthly_summary and processing_summary pairs |
| `src/output/` | 5 early output pairs (pre-refactor, 2025-09 era) |
| `src/reports/` | 5 early report pairs (pre-refactor) |
| `backups/` | Pipeline-generated backups |
| `logs/` | Rotating log files |
| `src/logs/` | Duplicate log directory from pre-refactor |

### Other

| File | Role |
|------|------|
| `Community_Engagment.code-workspace` | VS Code workspace file |
| `task_schedule.xml` | Windows Task Scheduler config (monthly on 1st at 06:00) |
| `Engagement Initiatives by Bureau.csv` | Before-update reference CSV |
| `after_update_Engagement Initiatives by Bureau.csv` | After-update reference CSV |
| `.claude/settings.local.json` | Claude Code local settings |

---

## 4. ETL Pipeline Map

### Inputs

1. **Community Engagement**: `Community_Engagement_Monthly.xlsx` sheet `2025_Master` -- event log with 10 member columns, pre-calculated duration and count
2. **STA&CP**: `STACP.xlsm` sheet `School_Outreach` -- school outreach events with dropdown attendees + free-text
3. **Patrol**: `patrol_monthly.xlsm` sheet `Main_Outreach_Combined` -- community outreach and Main Street assignments with patrol member names
4. **CSB**: `csb_monthly.xlsm` -- **DISABLED** (COMPSTAT activity grid, not outreach events)

All source paths defined in `config.json` using `C:\Users\carucci_r\...` base (junction resolves at runtime).

### Transforms

1. Each processor reads its sheet via `ExcelProcessor.read_excel_source()`
2. Column mapping via `standardize_columns()` normalizes to: `date`, `start_time`, `end_time`, `event_name`, `location`
3. Duration: pre-calculated where available (CE `Event Duration9`, STACP `Total Time`), else `end - start`, else default 0.5h
4. Attendees: CE uses pre-calculated `Member Count`; STACP uses dropdown + free-text with alias normalization; Patrol v2 uses rank stripping + delimiter parsing
5. Each processor stamps `office` and `division` identifiers
6. `MainProcessor.combine_data()` concatenates all, fills missing `attendee_names`, runs COMPSTAT contamination filter
7. Validation: checks critical fields, calculates quality score

### Outputs

- `output/community_engagement_data_YYYYMMDD_HHMMSS.csv` -- combined data for Power BI
- `output/community_engagement_data_YYYYMMDD_HHMMSS.xlsx` -- same with Summary sheet
- `reports/processing_summary_*.txt` -- run metadata
- `reports/monthly_summary_*.csv` -- aggregated by office/division
- Also copies to `C:\Users\carucci_r\...\PowerBI_Data\_DropExports` (configured but CSV export goes to local output/)

### Power BI Consumption

`Combined_Outreach_All.m` dynamically discovers the most recent CSV in the `output/` folder, promotes headers, casts types, renames to PBI column names (`Date`, `Event Duration (Hours)`, `Event Name`, `Location of Event`, `Number of Police Department Attendees`, `Office`), filters nulls, validates ranges, and sorts ascending.

---

## 5. Output Schema

| Column | Type | Notes |
|--------|------|-------|
| date | date | Event date |
| start_time | time/null | Often empty |
| end_time | time/null | Often empty |
| event_name | string | Event name or type |
| location | string | Event location |
| duration_hours | float | Decimal hours (default 0.5) |
| attendee_count | int | Number of personnel |
| office | string | Source bureau identifier |
| division | string | Division identifier |
| attendee_names | string | Comma-separated names (Patrol v2; blank for others unless STACP) |
| data_source | string | Processor key name |
| processed_date | string | YYYY-MM-DD of processing run |

---

## 6. Key Business Logic and Gotchas

- **CSB is disabled**: `config.json` `sources.csb.disabled: true`. The CSB workbook contains COMPSTAT productivity tracking (arrests, stops, etc.), not outreach events. Safety net `_remove_compstat_contamination()` also strips these patterns post-concat.
- **Patrol v2 attendee parsing**: Strips rank prefixes (PO, Sgt, Lt, Det, Cpl, Ofc), splits on comma/slash/ampersand/semicolon/and. Non-name entries (squad formation, n/a, tbd) produce count 0 with fallback to 1 if event data exists.
- **STACP PERSONNEL_ALIASES**: `attendee_utils.py` maps informal names to canonical display names. Must be extended as new officers appear.
- **Duration fallback chain**: pre-calculated column > start/end time delta > 0.5h default.
- **M code forces minimums**: duration 0.5h min (0 -> 0.5, >24 -> 8.0), attendee count 1 min (0 -> 1). This can inflate counts for empty-field rows.
- **SUMMARY.md says CE sheet is `_25_ce`** but config.json says `2025_Master`. The config.json value is authoritative.
- **config.json sheet name for STACP** was corrected from `_25_outreach` to `School_Outreach` (2026-03-11).

---

## 7. Known Issues / Tech Debt

1. **Directory name typo**: `Community_Engagment` missing 'e' -- should be `Community_Engagement`. Downstream references in config, task scheduler, M code all use the typo. Renaming requires coordinated update.
2. **Duplicate M code files**: `Combined_Outreach_All.m` (root) and `src/___Combined_Outreach_All.m` are functionally identical. Should consolidate.
3. **OneDrive sync duplicates**: Multiple `(1)` files from sync conflicts (CHANGELOG, README, SUMMARY, logs, task_schedule).
4. **Config backup proliferation**: 4 `.backup_*` files in root from 2026-02-19.
5. **Stale output accumulation**: 30+ timestamped output pairs in `output/` and `reports/` -- no cleanup policy.
6. **src/output/ and src/reports/**: Legacy output directories from pre-refactor; 5 old files each. Dead.
7. **src/logs/**: Duplicate log directory.
8. **No .gitignore**: Output, logs, backups, __pycache__, and temp files are not excluded from git.
9. **No requirements.txt**: README references `pip install -r requirements.txt` but the file does not exist.
10. **production_config.json**: Has blank credential fields (smtp password, PBI client_id/secret). Not a security issue currently but should not be committed with real values.
11. **sys.path manipulation**: Multiple processors use `sys.path.append()` hacks instead of proper package installs.
12. **pytz dependency**: `logger_setup.py` requires pytz but no requirements.txt declares it.

---

## 8. Path Resolution

OneDrive root resolves via two junctions:
1. Profile: `C:\Users\carucci_r` -> `C:\Users\RobertCarucci`
2. OneDrive: `C:\Users\RobertCarucci\OneDrive` -> `C:\Users\RobertCarucci\OneDrive - City of Hackensack`

### Rules for AI agents
- DO NOT change `carucci_r` to `RobertCarucci` in scripts or configs
- DO NOT rename `PowerBI_Data` to anything else
- `config.json` and `task_schedule.xml` use `carucci_r` paths -- correct and intentional
- If a path appears broken, check junction status before editing any file

---

## 9. Running the Pipeline

```powershell
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment"
python src/main_processor.py
```

Dependencies: `pandas`, `openpyxl`, `pytz` (Python 3.8+).

Windows Task Scheduler runs monthly on the 1st at 06:00 via `task_schedule.xml`.

---

## 10. Relationship to Parent Workspace

This repo is one of 5 ETL workflows under `02_ETL_Scripts/`:
1. Arrests
2. **Community Engagement** (this repo)
3. Overtime/TimeOff
4. Response Times
5. Summons

The parent `06_Workspace_Management` has its own Claude.md covering orchestration across all workflows.
