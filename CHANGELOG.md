# Changelog

All notable changes to this project will be documented here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions where possible.

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

