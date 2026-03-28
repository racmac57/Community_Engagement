# Changelog

All notable changes to this project will be documented here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions where possible.

## [2026-03-28]

### Added
- `CLAUDE.md` -- Complete rewrite with full file inventory, ETL pipeline map, output schema, known issues, and tech debt catalog.
- `docs/etl-pipeline.md` -- Dedicated ETL pipeline flow documentation.
- `docs/file-inventory.md` -- Complete file inventory with roles and status.
- `docs/config-reference.md` -- Configuration file reference for config.json and production_config.json.
- `.gitignore` -- Excludes output/, logs/, backups/, __pycache__/, temp files, config backups.
- `CONTRIBUTING.md` -- Contributor guidelines stub.
- `reorganization_proposal.md` -- Proposed cleanup: duplicate removal, directory typo fix, structure improvements.
- `findings.json` -- Audit findings from documentation swarm run.

### Changed
- `README.md` -- Refreshed with current project structure, data sources table, and documentation links.
- `CHANGELOG.md` -- Updated with 2026-03-28 audit entries.
- `SUMMARY.md` -- Refreshed with current status and known issues.

### Identified (not fixed)
- Directory name typo: `Community_Engagment` should be `Community_Engagement`.
- 7 OneDrive sync duplicate files (`(1)` suffix).
- 4 config.json backup files from 2026-02-19.
- Missing `requirements.txt` (README references it).
- No .gitignore was present (now added).

## [2026-03-11]

### Fixed
- **STACP source:** Config updated from sheet `_25_outreach` (does not exist) to `School_Outreach`. Fixes missing Feb 2026 STA&CP incidents in combined output.
- **Config paths:** All source and output paths use base `C:\Users\carucci_r\OneDrive - City of Hackensack` for desktop; laptop uses `RobertCarucci`.

### Changed
- **Power BI M query** (`m_code/community/___Combined_Outreach_All.m`): Added Event ID and Row_ID columns so each event displays as an individual row. Prevents "Engagement Initiatives by Bureau" visual from aggregating multiple events (e.g. 9 LEAD events) into 2 rows.

## [2026-03-05]

### Added
- `Claude.md` -- AI assistant guide with architecture, data sources (patrol_monthly.xlsm sheets), output schema, Patrol v2 design decisions, MoM aggregation logic, and Cursor integration notes.

### Changed
- Patrol processor v2: Rewrote parse_attendees() with rank prefix stripping
  (PO/Sgt/Lt/Det/Cpl/Ofc), expanded delimiter support ([,/&;] + "and"),
  non-name entry detection, and fallback logic for empty attendee fields.
- New attendee_names column added to combined output for person-level analysis.
- Source spreadsheet column G standardized: PO prefixes removed, delimiters normalized.

## [2026-02-13]

### Fixed
- **CSB source:** Updated configuration to use sheet `CSB_CommOut` and table `_csb_commout` in `csb_monthly.xlsm` (path unchanged). Replaced previous sheet `25_Jan`, which was not present in the workbook.
- Default sheet in `src/processors/csb_processor.py` set to `CSB_CommOut` for consistency.

## [2026-01-12]

### Verified
- Confirmed ETL processors correctly process all records from source files. Investigation of missing December 2025 events revealed the issue was outdated ETL output, not a code defect.
- Verified all 31 December 2025 events (17 Community Engagement + 14 STA&CP) are now present in latest output file (`community_engagement_data_20260112_193127.csv`).
- Latest pipeline run generated 558 total records, with all December 2025 events correctly processed.

### Notes
- ETL output must be regenerated when source files are updated. Recommend scheduling regular ETL runs or running manually after source file updates.

## [2025-11-10]

### Added
- Comprehensive project import into Git and initial push to GitHub (`master` branch).
- Updated documentation (`README.md`, `SUMMARY.md`) to reflect current ETL architecture and processing status.

### Fixed
- Resolved file-lock issue on `C:\Users\carucci_r\OneDrive - City of Hackensack\Shared Folder\Compstat\Contributions\STACP\STACP.xlsm`, restoring STA&CP ingestion (269 records from `_25_outreach`).

## [2025-09-04]

### Added
- Initial ETL implementation, including processors for Community Engagement, STA&CP, Patrol, and CSB.
- Power BI integration artifacts (`Combined_Outreach_All.m`) and validation tooling.
- Automated reporting and export generation for Power BI consumption.
