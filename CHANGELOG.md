# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [2026-06-12] — wave5-ce-ship-decision
### Added
- `docs/2026_06_wave5_ce_ship_decision.md` — Wave 5 / May 2026 ship decision for CC and Compstat: re-validate against CAD-integrated logic; do not ship pre-CAD workbook-only figures; provisional footnote text and residual-gap inventory.

### Changed
- `SUMMARY.md` — May ship posture, corrected known-issues list, next steps aligned to CAD-integrated feed.
- `CLAUDE.md` — section 6.6 May 2026 ship decision; Last Updated 2026-06-12.
- `README.md` — link to Wave 5 ship decision doc.

## [2026-06-11] — cad-ce-integration
### Added
- `src/processors/cad_ce_processor.py` -- `CADCEProcessor`, the fifth combined-feed source. Transforms the CAD CE monthly export (`05_EXPORTS/_CAD/Community_Engagement/monthly/YYYY_MM_CE.xlsx`, `Sheet1`) to the canonical 12-field schema. Routes by Squad to canonical offices (COMM ENG->Community Engagement, A1-A4/B1-B4->Patrol, STA->STA&CP, CSB excluded, other->squad). Imputes sub-2-min memorial spans to 0.5 h.
- `main_processor.combine_data._dedup_cad_gapfill` -- gap-fill anti-join. Drops a CAD row when a non-CAD (workbook) row already covers the same event (key: date + normalized location; date types coerced since STACP dates are Timestamps and CAD dates are ISO strings). Workbook is system of record.
- `config.json` -- new `cad_ce` source entry (monthly `file_path`, requires monthly update).
- `scripts/ce_cad_etl.py` -- QA companion (added across earlier session waves): STACP verification (date+location match, SPLIT_SUGGESTED combined-row guard), paste-ready proposed `Master_Outreach` entries for MISSING/SPLIT rows, unrouted (CSB) report.
- `src/utils/duration_utils.py`, `src/utils/attendee_utils.py` -- committed for the first time (were untracked since the 2025-11-10 import; the pipeline imports them).

### Changed
- `config.json` -- source sheet names corrected to current truth: Community Engagement `Master_Log` (was `2025_Master`), STA&CP `Master_Outreach` (was `School_Outreach`), CSB `26_01`.
- `scripts/ce_cad_etl.py` -- demoted from production writer to QA-only; no longer writes the production CSV or anything to `_DropExports`. Production CSV is produced by `main_processor -> output/`.

### Fixed
- Verified the CE visual (`Combined_Outreach_All.m`) reads `output/` and auto-selects the newest `community_engagement_data_*.csv`; CAD-integrated feed loads on refresh with no routing step. May 2026 combined feed: 599 rows, CAD contributes 9 gap-fill rows, one true duplicate (Del Carpio 5-27 M&M Center vs STACP "Youth Night") dropped.

### Notes
- `_DropExports` is the Power BI visual-export drop zone (routed by `process_powerbi_exports.py`), NOT an ETL output target. Earlier in-session writes there were pulled and archived.
- Snapshot commit captured the pipeline core (processors, `main_processor`, utils) that evolved uncommitted since the 2025-11-10 initial import.

## [2026-03-28] — swarm-run
### Added
- `CLAUDE.md` -- Complete rewrite with full file inventory, ETL pipeline map, output schema, known issues, and tech debt catalog
- `docs/etl-pipeline.md` -- Dedicated ETL pipeline flow documentation
- `docs/file-inventory.md` -- Complete file inventory with roles and status
- `docs/config-reference.md` -- Configuration file reference for config.json and production_config.json
- `.gitignore` -- Excludes output/, logs/, backups/, __pycache__/, temp files, config backups
- `CONTRIBUTING.md` -- Contributor guidelines stub
- `reorganization_proposal.md` -- Proposed cleanup: duplicate removal, directory typo fix, structure improvements
- `findings.json` -- Audit findings from documentation swarm run

### Changed
- `README.md` -- Refreshed with current project structure, data sources table, and documentation links
- `CHANGELOG.md` -- Updated with 2026-03-28 audit entries
- `SUMMARY.md` -- Refreshed with current status and known issues

### Deprecated
- 7 dead debug/scaffold scripts identified for archival (debug_csb_structure.py, debug_processors.py, sample_office_distribution.py, test_date_parsing.py, project_scaffold.py, deploy_production.py, monitor_etl.py)

### Security
- `production_config.json` contains blank credential fields -- added to `.gitignore` and removed from git tracking

## [2026-03-11]
### Fixed
- **STACP source:** Config updated from sheet `_25_outreach` (does not exist) to `School_Outreach`. Fixes missing Feb 2026 STA&CP incidents in combined output.
- **Config paths:** All source and output paths use base `C:\Users\carucci_r\OneDrive - City of Hackensack` for desktop; laptop uses `RobertCarucci`.

### Changed
- **Power BI M query** (`m_code/community/___Combined_Outreach_All.m`): Added Event ID and Row_ID columns so each event displays as an individual row. Prevents "Engagement Initiatives by Bureau" visual from aggregating multiple events.

## [2026-03-05]
### Added
- `Claude.md` -- AI assistant guide with architecture, data sources, output schema, Patrol v2 design decisions, MoM aggregation logic, and Cursor integration notes.

### Changed
- Patrol processor v2: Rewrote parse_attendees() with rank prefix stripping (PO/Sgt/Lt/Det/Cpl/Ofc), expanded delimiter support, non-name entry detection, and fallback logic for empty attendee fields.
- New attendee_names column added to combined output for person-level analysis.
- Source spreadsheet column G standardized: PO prefixes removed, delimiters normalized.

## [2026-02-13]
### Fixed
- **CSB source:** Updated configuration to use sheet `CSB_CommOut` and table `_csb_commout` in `csb_monthly.xlsm`. Replaced previous sheet `25_Jan`, which was not present in the workbook.
- Default sheet in `src/processors/csb_processor.py` set to `CSB_CommOut` for consistency.

## [2026-01-12]
### Verified
- Confirmed ETL processors correctly process all records from source files. Investigation of missing December 2025 events revealed the issue was outdated ETL output, not a code defect.
- Verified all 31 December 2025 events (17 Community Engagement + 14 STA&CP) are now present in latest output file.
- Latest pipeline run generated 558 total records, with all December 2025 events correctly processed.

## [2025-11-10]
### Added
- Comprehensive project import into Git and initial push to GitHub (`master` branch).
- Updated documentation (`README.md`, `SUMMARY.md`) to reflect current ETL architecture and processing status.

### Fixed
- Resolved file-lock issue on STACP.xlsm, restoring STA&CP ingestion (269 records from `_25_outreach`).

## [2025-09-04]
### Added
- Initial ETL implementation, including processors for Community Engagement, STA&CP, Patrol, and CSB.
- Power BI integration artifacts (`Combined_Outreach_All.m`) and validation tooling.
- Automated reporting and export generation for Power BI consumption.
