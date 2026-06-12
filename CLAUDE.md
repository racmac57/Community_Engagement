# Community Engagement ETL -- CLAUDE.md

> **Repo**: `Community_Engagement`
> **Remote**: `racmac57/Community_Engagement.git`
> **Last Updated**: 2026-06-12
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
| `src/processors/community_engagement_processor.py` | Processes Community_Engagement_Monthly.xlsx (sheet `Master_Log`) |
| `src/processors/stacp_processor.py` | Processes STACP.xlsm (sheet `Master_Outreach`) |
| `src/processors/patrol_processor.py` | **v2** -- Processes patrol_monthly.xlsm (sheet `Main_Outreach_Combined`); rank stripping, attendee_names |
| `src/processors/csb_processor.py` | Processes csb_monthly.xlsm -- currently **disabled** in config (COMPSTAT data, not outreach) |
| `src/processors/cad_ce_processor.py` | **v1 (2026-06)** -- `CADCEProcessor`: 5th source. CAD CE export (`YYYY_MM_CE.xlsx`, `Sheet1`) -> canonical schema; Squad routing, 30-min memorial imputation; exports `cad_dedup_key` for the gap-fill anti-join |
| `scripts/ce_cad_etl.py` | QA companion (read-only): STACP verification (date+location, SPLIT guard), paste-ready `Master_Outreach` proposals, unrouted report. Writes only `docs/`; never the production CSV or `_DropExports` |
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
| `CHANGELOG.md` | Change history | Current through 2026-06-11 |
| `SUMMARY.md` | Status summary | Current through 2026-06-11 |
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
| `Community_Engagement.code-workspace` | VS Code workspace file |
| `task_schedule.xml` | Windows Task Scheduler config (monthly on 1st at 06:00) |
| `Engagement Initiatives by Bureau.csv` | Before-update reference CSV |
| `after_update_Engagement Initiatives by Bureau.csv` | After-update reference CSV |
| `.claude/settings.local.json` | Claude Code local settings |

---

## 4. ETL Pipeline Map

### Inputs

1. **Community Engagement**: `Community_Engagement_Monthly.xlsx` sheet `Master_Log` -- event log with 10 member columns, pre-calculated duration and count
2. **STA&CP**: `STACP.xlsm` sheet `Master_Outreach` -- school outreach events with dropdown attendees + free-text
3. **Patrol**: `patrol_monthly.xlsm` sheet `Main_Outreach_Combined` -- community outreach and Main Street assignments with patrol member names
4. **CSB**: `csb_monthly.xlsm` -- **DISABLED** (COMPSTAT activity grid, not outreach events)
5. **CAD CE** (v1, 2026-06): `YYYY_MM_CE.xlsx` sheet `Sheet1` -- CAD Community Engagement monthly export, one officer per row, tagged with a `Squad`. A **gap-fill** source (`cad_ce_processor.py`); see section 6.5.

All source paths defined in `config.json` using `C:\Users\carucci_r\...` base (junction resolves at runtime).

### Transforms

1. Each processor reads its sheet via `ExcelProcessor.read_excel_source()`
2. Column mapping via `standardize_columns()` normalizes to: `date`, `start_time`, `end_time`, `event_name`, `location`
3. Duration: pre-calculated where available (CE `Event Duration9`, STACP `Total Time`), else `end - start`, else default 0.5h
4. Attendees: CE uses pre-calculated `Member Count`; STACP uses dropdown + free-text with alias normalization; Patrol v2 uses rank stripping + delimiter parsing
5. Each processor stamps `office` and `division` identifiers
6. `MainProcessor.combine_data()` concatenates all, fills missing `attendee_names`, runs COMPSTAT contamination filter, then `_dedup_cad_gapfill()` (drops CAD rows a workbook already covers)
7. Validation: checks critical fields, calculates quality score

### Outputs

- `output/community_engagement_data_YYYYMMDD_HHMMSS.csv` -- combined data for Power BI
- `output/community_engagement_data_YYYYMMDD_HHMMSS.xlsx` -- same with Summary sheet
- `reports/processing_summary_*.txt` -- run metadata
- `reports/monthly_summary_*.csv` -- aggregated by office/division
- **Production target is local `output/`.** `Combined_Outreach_All.m` reads the newest CSV there. `config.json` `output_settings.output_directory` names `_DropExports`, but `main_processor.export_data()` ignores it (hardcoded `output/`). **Do NOT wire export to `_DropExports`** -- that is the Power BI visual-export drop zone (see section 6.5), not an ETL target.

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
- **config.json sheet name for STACP** is `Master_Outreach` (current). README/older docs referencing `School_Outreach`/`_25_outreach` are stale; config.json is authoritative.

---

## 6.5 CAD CE Source and Gap-Fill (v1, 2026-06)

The CAD CE monthly export is the fifth combined-feed source, processed by
`src/processors/cad_ce_processor.py` (`CADCEProcessor`). It exists to **fill gaps** the
manually-maintained workbooks miss (e.g. months staff have not yet logged), not to replace them.

- **Squad -> canonical office** (so CAD rows land in the right bureau bucket): `COMM ENG` ->
  `Community Engagement`/`Outreach`; `A1-A4`,`B1-B4` -> `Patrol`/`Patrol`; `STA` -> `STA&CP`/`STACP`;
  `CSB` -> **excluded**; any other -> the Squad value.
- **Memorial-CAD normalization**: a CAD span `< 2 minutes` (often the officer is also the
  `DispatcherNew`, i.e. self-logged a CAD just to memorialize an event) is a log artifact, not a
  real length. It is set to a `0.5 h` default and `end_time` is shifted to match. A small negative
  span (clock-rounded) is treated the same; only `<= -2 min` (true inversion) raises an error.
- **Gap-fill anti-join** (`main_processor._dedup_cad_gapfill`): the workbook is the **system of
  record**. A CAD row is dropped when a non-CAD row shares its `date + normalized location`
  (locations normalized by lowercasing + stripping non-alphanumerics, so `M & M Center` == `MM
  Center`; dates coerced because STACP dates are pandas `Timestamp` and CAD dates are ISO strings).
  CAD only adds events no workbook already has.
- **QA companion** `scripts/ce_cad_etl.py` (read-only, writes only `docs/`): STACP verification
  (date+location match; a `SPLIT_SUGGESTED` class flags a combined STACP row like "Jackson and
  Fairmount" that crams two events), paste-ready proposed `Master_Outreach` rows for MISSING/SPLIT
  cases, and the unrouted (CSB) report. It does **not** write the production CSV.
- **Monthly maintenance**: update `config.json` `cad_ce.file_path` to the current `YYYY_MM_CE.xlsx`
  before each run. (Open task: have the processor auto-pick the newest export in the monthly dir.)

## 6.6 May 2026 Ship Decision (Wave 5, 2026-06-12)

CE was marked PROVISIONAL pending CAD routing validation. **Decision: ship May on the
CAD-integrated feed with a provisional footnote** — not on pre-CAD workbook-only figures.

- **Authoritative May output:** `output/community_engagement_data_20260611_154355.csv` (599 rows;
  May 2026 = 15 events, 9 CAD gap-fill, 1 CAD duplicate dropped vs STACP).
- **Do not ship:** `community_engagement_data_20260610_185029.csv` (582 rows; May = 5 STA&CP-only,
  no CAD) — undercounts May by 10 events.
- **Provisional footnote:** CAD gap-fill additive only; workbook is system of record; CSB-squad
  CAD excluded; STACP reconciliation optional (DiPersia + Katsaroans already in CAD gap-fill).
- **Full decision doc:** `docs/2026_06_wave5_ce_ship_decision.md`

---

## Style Instructions (embedded -- for AI assistants editing this repo)

These are project conventions, established 2026-06. Follow them unless the user overrides.

- **`_DropExports` is sacred.** Never write ETL output there. It is the Power BI visual-export
  drop zone, swept by `06_Workspace_Management/scripts/process_powerbi_exports.py` (routes by regex
  `match_pattern` in `visual_export_mapping.json`). ETL output goes to `output/`.
- **Workbook is the system of record; CAD gap-fills.** When CAD and a workbook describe the same
  event, the workbook wins. Do not change this to a naive union (double-counts the visual).
- **Gap-fill scope is bounded.** Generate paste-ready proposals for missing data; do NOT author
  reporting that tells the user to chase other units, file emails, or scrutinize an officer's CAD
  conduct (esp. higher rank). Keep QA output neutral. Imputing 30 min for a memorial CAD is the
  policy -- a floor, applied automatically, no per-row judgment.
- **No fabricated schema.** Resolve every column name, sheet name, and path from the real file
  (CAD export uses display headers like `SelfJoinCADNumber::Business Name`; STACP header
  `School Outreach Conducted ` has a trailing space). Force `ReportNumberNew` to string dtype.
- **Path-agnostic code.** Derive the OneDrive root from the repo location (`REPO_ROOT.parents[1]`)
  or `config_loader`; no hardcoded user paths in deliverable scripts. Keep `carucci_r` in paths.
- **Archive-first.** Never hard-delete an output; move superseded files to an `archive/` subfolder
  with a datestamp.
- **Reuse `src/utils`.** `duration_utils.safe_duration_to_hours` (timedelta/time/str/float ->
  hours), `config_loader`, `logger_setup`. Do not reinvent these.
- **Commit discipline.** The pipeline core sat uncommitted for ~7 months (Nov 2025 -> Jun 2026).
  Commit per change; do not let shared files (`main_processor.py`, processors, `config.json`) drift.

---

## 7. Known Issues / Tech Debt

1. ~~**Directory name typo**~~: RESOLVED 2026-03-28. Renamed from `Community_Engagment` to `Community_Engagement`. All downstream references updated. Task Scheduler XML still needs manual re-import.
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
cd "C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagement"
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
