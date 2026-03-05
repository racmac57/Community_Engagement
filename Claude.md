# Community Engagement ETL — Claude.md

> **Repo**: `C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment`
> **Last Updated**: 2026-03-05
> **Maintainer**: R. Carucci, Hackensack PD
> **AI Assistants Used**: Claude (Excel add-in), Cursor AI

---

## 1. Project Overview

This sub-project is the **Community Engagement ETL pipeline** within the larger Master_Automation system. It processes four Excel data sources through Python processor classes, combines them into a single CSV output, and feeds a Power BI dashboard for community engagement analytics.

### Architecture

```
patrol_monthly.xlsm                    config.json
  ├─ Monthly sheets (24_01..26_12)         │
  ├─ Main_Outreach_Combined                │
  ├─ 25_Comm_Outreach                      │
  ├─ MoM (_mom_patrol)                     │
  └─ List_Data                             │
       │                                   │
       ▼                                   ▼
  src/processors/                    src/main_processor.py
  ├─ patrol_processor.py (v2)              │
  ├─ community_engagement_processor.py     │
  ├─ stacp_processor.py                    │
  └─ csb_processor.py                      │
       │                                   │
       └──────── combine_data() ───────────┘
                      │
                      ▼
              output/community_engagement_data_*.csv
                      │
                      ▼
              Power BI (___Combined_Outreach_All.m)
```

---

## 2. Key Files

| File | Purpose |
|------|---------|
| `src/main_processor.py` | Master orchestrator — runs all 4 processors, combines output, exports CSV + Excel |
| `src/processors/patrol_processor.py` | **v2 (2026-03-05)** — Processes patrol_monthly.xlsm Main_Outreach_Combined sheet |
| `src/processors/community_engagement_processor.py` | Processes community engagement source data |
| `src/processors/stacp_processor.py` | Processes STA&CP (Stop, Talk & Connect Program) data |
| `src/processors/csb_processor.py` | Processes CSB (Community Service Bureau) data |
| `src/processors/excel_processor.py` | Shared base class — read_excel_source(), standardize_columns(), calculate_duration(), validate_data() |
| `src/utils/logger_setup.py` | Project-wide logging configuration |
| `src/utils/config_loader.py` | Reads config.json for source file paths |
| `config.json` | Source file paths, sheet names, output directory |
| `src/___Combined_Outreach_All.m` | Power BI M code query that reads the output CSV |
| `patrol_monthly.xlsm` | Source workbook — 44 sheets of patrol tracking data |

---

## 3. Data Sources (patrol_monthly.xlsm)

### 3a. Monthly Patrol Sheets (24_01 -> 26_12)

| Attribute | Detail |
|-----------|--------|
| **Sheet naming** | `YY_MM` (e.g., `24_01` = January 2024, `26_12` = December 2026) |
| **Table naming** | `_YY_MM` (underscore prefix, e.g., `_24_01`, `_26_03`) |
| **Row labels (col A)** | 19 tracked items: Arrive Program Referral, BWC Reviews, Calls for Service, CDS Arrest(s), Catalytic Converter Theft(s), DUI Arrest(s), DV Arrest(s), DV Incident(s), Handle with Care Notifications, Mental Health Calls, Motor Vehicle Stops, Narcan Deployment, Overdose(s), Pursuit Review, Self-Initiated Arrest(s), Tasks, Total Moving Summons, Total Parking Summons, Use of Force Review |
| **Day columns** | Numbered 01-31 depending on month length |
| **Total column** | `=SUM(B{row}:{lastDayCol}{row})` — last column of each sheet |
| **Month lengths** | 31-day: B:AF->AG (cols B-AF, Total=AG). 30-day: B:AE->AF. 28/29-day: B:AC/AD->AD/AE |
| **Formatting** | Alternating gray (#D9D9D9) / white rows, bold centered headers, medium outer borders |
| **Freeze panes** | Column A + Row 1 frozen on 2025+ and 2026 sheets |

### 3b. MoM Sheet (_mom_patrol table)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Month-over-month aggregation of all monthly sheet totals |
| **Headers (row 1)** | Column A = "Tracked Items", then `MM-YY` format (e.g., `06-23`, `01-24`, `02-26`) |
| **Row labels** | 18 tracked items (excludes "Catalytic Converter Theft(s)" from monthly sheets) |
| **Formula pattern** | `=XLOOKUP($A{row}, '{sheetName}'!$A$2:$A$20, '{sheetName}'!${totalCol}$2:${totalCol}$20)` |
| **Coverage** | 06-23 through 12-26 (columns B through AR), with placeholder columns for 01-27 onward |
| **Table name** | `_mom_patrol` |

### 3c. Main_Outreach_Combined

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Combined log of all Community Outreach and Main Street patrol assignments |
| **Columns** | A: Date, B: Start Time, C: End Time, D: Event Type, E: Event Name, F: Event Location, G: Patrol Members Assigned |
| **Row count** | 90 data rows (48 Main Street + 42 Community Outreach) + 22 empty rows for future entry |
| **Data range** | 2024-01-02 through 2025-11-15 (growing as data is entered) |
| **Event Types** | "Community Outreach" or "Main Street" (dropdown from List_Data!E2:E4) |
| **Data validation on G** | Prompt: "Enter LAST NAME only (no rank/PO prefix). Multiple names: separate with comma and space." |
| **Data validation on D** | Dropdown: blank / Community Outreach / Main Street |
| **All data is static** | No formulas — values are manually entered or pasted from source sheets |
| **Fed by (2024)** | Side tables in 24_01, 24_02, 24_03 sheets (columns AF-AK for Main Street, AH-AK for Comm Outreach) |
| **Fed by (2025)** | 25_Comm_Outreach sheet (columns A-F for Main Street, H-N for Community Outreach) |

### 3d. 25_Comm_Outreach

| Attribute | Detail |
|-----------|--------|
| **Purpose** | 2025 source data for Main Street and Community Outreach events |
| **Layout** | Dual sub-tables: A1:F (Main Street assignments), H1:N (Community Outreach events) |
| **Columns (Main St)** | Date, Start Time, End Time, Event Name, Location, Name of Member Assigned Main Street |
| **Columns (Comm Out)** | Date, Start Time, End Time, Location, Address, Name of Community Outreach Event, Name of Patrol Personnel |

### 3e. List_Data

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Reference data for dropdowns and lookups |
| **Columns A-C** | Month, Days Assigned, Days in Month (historical tracking since Jan 2023) |
| **Column E** | Event Type dropdown values: (blank), "Community Outreach", "Main Street" |

### 3f. 23_JUN_DEC

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Legacy data for June-December 2023 (pre-monthly-sheet format) |

---

## 4. Output Schema (Combined CSV)

The output CSV produced by main_processor.py has these columns in order:

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| date | date | All processors | Event date |
| start_time | time/null | All processors | Mostly empty for patrol data |
| end_time | time/null | All processors | Mostly empty for patrol data |
| event_name | string | All processors | Main St. Patrol, Summer Concert, etc. |
| location | string | All processors | Main St., HACPAC, etc. |
| duration_hours | float | Calculated | end_time minus start_time (0 if missing) |
| attendee_count | int | All processors | Number of personnel assigned |
| office | string | Per processor | Patrol, CSB, etc. |
| division | string | Per processor | Patrol, Community Engagement, etc. |
| attendee_names | string | Patrol only | NEW in v2: Comma-separated normalized names (blank for non-patrol) |

---

## 5. Patrol Processor v2: Design Decisions (2026-03-05)

### Problem Statement

The Patrol Members Assigned column (G) in Main_Outreach_Combined had inconsistent data entry:
- Rank prefix inconsistency: PO Tabares (Main Street) vs Tabares (Community Outreach) — same person counted as two in PBI
- Delimiter inconsistency: Commas, slashes, and mixed spacing
- Name variants: P.Lopez vs P. Lopez, Rivera vs B. Rivera vs W. Rivera
- Non-name entries: Squad formation counted as 1 person
- Empty cells: M code forced attendee_count to 1 when zero, inflating counts

### Solution: v2 Changes

#### Spreadsheet standardization (37 cells in column G):
1. Stripped all PO rank prefixes to last name only
2. Normalized all delimiters to comma + space
3. Fixed spacing (e.g., P.Lopez to P. Lopez)
4. Updated data validation prompt to enforce the standard going forward
5. Result: 42 unique personnel names in consistent format

#### Python processor enhancements:
1. `normalize_name()`: Strips rank prefixes (PO, Sgt, Lt, Det, Cpl, Ofc), fixes spacing
2. `parse_patrol_field()`: Splits on comma/slash/ampersand/semicolon and word 'and', filters non-name entries
3. Fallback logic: If attendee field empty but date + event + location exist, count as 1
4. New `attendee_names` column: Comma-separated normalized names for person-level PBI analysis
5. Non-name detection: Squad formation, N/A, TBD etc. produce count 0, fallback applies

#### Key constants (in patrol_processor.py):
- `RANK_PREFIXES`: regex matching PO, Sgt, Lt, Det, Cpl, Ofc (and full words), case-insensitive
- `MULTI_NAME_SPLIT`: regex splitting on comma, slash, ampersand, semicolon, and the word 'and'
- `NON_NAME_ENTRIES`: set containing 'squad formation', 'n/a', 'none', 'tbd', 'unknown'

### Backward Compatibility

- `attendee_count` column output is identical to v1 for correctly-formatted entries
- `attendee_names` is appended after division: Power BI M query (Table.SelectColumns) ignores unknown columns
- No changes needed to config.json, excel_processor.py, other processors, or M code

---

## 6. Data Validation Rules (patrol_monthly.xlsm)

| Sheet | Column | Rule | Prompt |
|-------|--------|------|--------|
| Main_Outreach_Combined | D (Event Type) | Dropdown: List_Data!E2:E4 | Select Event Type: blank / Main Street / Community Outreach |
| Main_Outreach_Combined | G (Patrol Members) | Input message (no restriction) | Enter LAST NAME only (no rank/PO prefix). Separate with comma and space. |

---

## 7. MoM Aggregation Logic

The MoM sheet uses XLOOKUP to dynamically pull Total column values from each monthly sheet.

**Formula pattern:** `XLOOKUP($A{row}, 'sheetName'!$A$2:$A$20, 'sheetName'!${totalCol}$2:${totalCol}$20)`

**Mapping examples:**
- MoM header 01-24 → sheet 24_01, total column AF (31-day)
- MoM header 02-24 → sheet 24_02, total column AD (29-day, leap year)
- MoM header 04-26 → sheet 26_04, total column AF (30-day)

**Note:** MoM has 18 tracked items vs. monthly sheets 19 (Catalytic Converter Theft(s) excluded). XLOOKUP matches on item name.

---

## 8. Known Issues and Data Gaps

| Issue | Status | Notes |
|-------|--------|-------|
| Start Time / End Time mostly empty | Known | Only 1 value across all sources (1300 for Jan 7, 2025). |
| 5 rows with missing Location/Event/Patrol | Known | No source data to backfill. Requires manual entry. |
| Squad formation in row 21 | Known | Non-name entry, unknown count. v2 returns count 0, fallback sets to 1. |
| Revi possibly truncated | Known | Treated as valid name by v2 processor. |
| Table oversized (22 empty rows) | Intentional | Left for data entry person. |

---

## 9. Running the Pipeline

### Prerequisites
- Python 3.x with pandas, openpyxl
- config.json configured with correct file paths
- patrol_monthly.xlsm accessible at configured path

### Execution

```powershell
cd 02_ETL_Scripts\Community_Engagment
python src/main_processor.py
```

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| FileNotFoundError | Wrong config.json path | Verify patrol_monthly.xlsm path |
| KeyError: Patrol Members Assigned | Column renamed | Check col G header |
| attendee_count all zeros | Empty column G | Verify G2:G91 has data |
| M query error in Power BI | Column order changed | attendee_names must be last |
| XLOOKUP returns 0 | Monthly sheet empty | Enter daily data; MoM pulls automatically |

---

## 10. Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-03-05 | patrol_processor v2 | Rewrote parse_attendees() with rank stripping, expanded delimiters, non-name detection, fallback logic, new attendee_names column. |
| 2026-03-05 | main_processor | Added attendee_names handling, patrol-specific logging, CSV export column ordering. |
| 2026-03-05 | Workbook | Created 10 monthly sheets (26_03-26_12) with named tables, SUM formulas, MoM XLOOKUP aggregation. Added 9 missing entries. |
| 2026-03-05 | Documentation | Cursor integration prompt, CHANGELOG.md, SUMMARY.md, README.md updates. |

---

## 11. Relationship to Master_Automation

This repo (`02_ETL_Scripts/Community_Engagment`) is one of 5 ETL workflows:

1. Arrests: `02_ETL_Scripts/Arrests/`
2. Community Engagement: `02_ETL_Scripts/Community_Engagment/` (this repo)
3. Overtime: `02_ETL_Scripts/Overtime_TimeOff/`
4. Response Times: `02_ETL_Scripts/Response_Times/`
5. Summons: `02_ETL_Scripts/Summons/`

The Master_Automation root has its own Claude.md covering ALL 5 workflows, the PowerShell orchestrator (run_all_etl.ps1), and the full Power BI M code query catalog. This file documents only the Community Engagement sub-project.

---

## 12. Cursor AI Integration Notes

The Cursor integration prompt (in Cursor_Prompt sheet of patrol_monthly.xlsm) provides:
- Full project structure and data flow context
- 5 specific integration steps for main_processor.py
- Complete patrol_processor.py v2 source code
- Verification checklist with 11 unit test assertions

**Constraints given to Cursor:**
- Do NOT modify excel_processor.py, config.json, or other processor files
- Do NOT change the Power BI M query (new column is additive)
- `parse_patrol_field()` and `normalize_name()` are module-level (not class methods) by design
