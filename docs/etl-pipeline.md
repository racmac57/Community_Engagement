# ETL Pipeline Documentation

## Pipeline Overview

The Community Engagement ETL pipeline consolidates four HPD data sources into a single combined CSV for Power BI consumption.

## Data Flow

```
[1] Source Workbooks (Excel)
    |
    v
[2] Per-Source Processors (Python)
    |-- community_engagement_processor.py  -->  Community_Engagement_Monthly.xlsx : 2025_Master
    |-- stacp_processor.py                 -->  STACP.xlsm : School_Outreach
    |-- patrol_processor.py (v2)           -->  patrol_monthly.xlsm : Main_Outreach_Combined
    |-- csb_processor.py                   -->  csb_monthly.xlsm : CSB_CommOut [DISABLED]
    |
    v
[3] MainProcessor.combine_data()
    |-- pd.concat all processor outputs
    |-- Fill missing attendee_names column
    |-- COMPSTAT contamination filter (_remove_compstat_contamination)
    |-- Validate combined data (quality score)
    |
    v
[4] Export
    |-- output/community_engagement_data_YYYYMMDD_HHMMSS.csv
    |-- output/community_engagement_data_YYYYMMDD_HHMMSS.xlsx (with Summary sheet)
    |-- reports/processing_summary_*.txt
    |-- reports/monthly_summary_*.csv
    |
    v
[5] Power BI
    |-- Combined_Outreach_All.m reads latest CSV from output/
    |-- Types columns, renames for dashboard, validates ranges
    |-- Feeds "Engagement Initiatives by Bureau" and related visuals
```

## Processor Details

### Community Engagement Processor
- **Input**: `Community_Engagement_Monthly.xlsx`, sheet `2025_Master`
- **Column mapping**: Community Event -> event_name, Date of Event -> date, Event Location -> location
- **Duration**: Pre-calculated `Event Duration9` column (timedelta); falls back to start/end delta
- **Attendees**: Pre-calculated `Member Count` column; falls back to parsing 10 individual member columns
- **Office/Division**: "Community Engagement" / "Outreach"

### STACP Processor
- **Input**: `STACP.xlsm`, sheet `School_Outreach`
- **Column mapping**: School Outreach Conducted -> event_name, Date -> date, Location -> location
- **Duration**: Pre-calculated `Total Time` column (timedelta); falls back to start/end delta
- **Attendees**: Primary dropdown (Attendees) + 4 extra dropdowns (Attendees2-5) + Free Type Attendees field. Uses PERSONNEL_ALIASES for name normalization.
- **Office/Division**: "STA&CP" / "STACP"

### Patrol Processor (v2)
- **Input**: `patrol_monthly.xlsm`, sheet `Main_Outreach_Combined`
- **Column mapping**: Event Type -> event_name, Date -> date, Event Location -> location
- **Duration**: Calculated from Start Time / End Time
- **Attendees (v2)**: Parses `Patrol Members Assigned` column with:
  - Rank prefix stripping (PO, Sgt, Lt, Det, Cpl, Ofc)
  - Multi-delimiter splitting (comma, slash, ampersand, semicolon, "and")
  - Non-name detection (squad formation, n/a, tbd, etc.)
  - Fallback: if count=0 but event data exists, default to 1
  - Produces `attendee_names` column with normalized comma-separated names
- **Office/Division**: "Patrol" / "Patrol"

### CSB Processor (DISABLED)
- **Input**: `csb_monthly.xlsm`, sheet `CSB_CommOut`
- **Status**: Disabled in config.json. The workbook contains COMPSTAT activity grids (arrests, stops, warrants), not outreach event logs.
- **Re-enable**: Only when CSB_CommOut sheet contains real outreach rows. Update processor to match new layout.

## COMPSTAT Safety Filter

`MainProcessor._remove_compstat_contamination()` runs after concat on every pipeline execution. It removes rows where:
- `office` matches "crime suppression bureau" or "csb" (case-insensitive), OR
- `event_name` matches productivity patterns like "(Monthly Total)", "Arrests", "Motor Vehicle Stops", etc.

This provides defense-in-depth even when the CSB source is disabled.

## Scheduling

Windows Task Scheduler runs `src/main_processor.py` monthly on the 1st at 06:00 EST. Configuration in `task_schedule.xml`.

## Configuration

All source paths and settings are in `config.json`. See `docs/config-reference.md` for details.
