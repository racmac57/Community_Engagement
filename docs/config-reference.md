# Configuration Reference

## config.json

Primary configuration file for the ETL pipeline. Located at repository root.

### sources

Each source has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `file_path` | string | Absolute path to source workbook (uses `carucci_r` base) |
| `sheet_name` | string | Primary sheet to read |
| `additional_sheets` | array | (STACP only) Extra sheets to process |
| `description` | string | Human-readable description |
| `disabled` | boolean | If true, source is skipped during processing |

### Current sources

```json
{
  "community_engagement": {
    "file_path": "...\\Community_Engagement_Monthly.xlsx",
    "sheet_name": "2025_Master",
    "disabled": false
  },
  "stacp": {
    "file_path": "...\\STACP\\STACP.xlsm",
    "sheet_name": "School_Outreach",
    "additional_sheets": ["25_Presentations", "25_Training Delivered"],
    "disabled": false
  },
  "patrol": {
    "file_path": "...\\Patrol\\patrol_monthly.xlsm",
    "sheet_name": "Main_Outreach_Combined",
    "disabled": false
  },
  "csb": {
    "file_path": "...\\CSB\\csb_monthly.xlsm",
    "sheet_name": "26_01",
    "disabled": true
  }
}
```

**Note:** CSB is disabled because `csb_monthly.xlsm` contains COMPSTAT activity tracking grids, not outreach event logs.

### date_range

| Field | Type | Description |
|-------|------|-------------|
| `rolling_window_months` | int | Number of months for rolling window (13) |
| `enforce_window` | boolean | Whether to enforce the window filter |
| `date_field` | string | Column name for date filtering ("date") |

### output_settings

| Field | Type | Description |
|-------|------|-------------|
| `csv_export` | boolean | Enable CSV export |
| `excel_export` | boolean | Enable Excel export |
| `backup_files` | boolean | Enable source file backups |
| `output_directory` | string | Target directory for exports |
| `reports_directory` | string | Relative path for reports |
| `backups_directory` | string | Relative path for backups |
| `filename_pattern` | string | Pattern for output filenames |

### validation_rules

| Field | Type | Description |
|-------|------|-------------|
| `required_fields` | array | Fields that must be non-null (event_name, date) |
| `min_data_quality_score` | int | Minimum acceptable quality percentage (75) |
| `max_processing_time_minutes` | int | Timeout threshold (30) |

### logging

| Field | Type | Description |
|-------|------|-------------|
| `level` | string | Log level (INFO) |
| `file_rotation` | boolean | Enable log rotation |
| `max_file_size_mb` | int | Max log file size (10 MB) |
| `backup_count` | int | Number of rotated logs to keep (5) |

---

## production_config.json

Extended configuration for production deployment. Contains placeholder/blank credential fields.

### email

SMTP settings for notification emails.

| Field | Value |
|-------|-------|
| `smtp_server` | smtp.office365.com |
| `smtp_port` | 587 |
| `sender_email` | etl@hackensacknj.gov |
| `sender_password` | (blank -- do not commit real values) |
| `recipients` | ["it@hackensacknj.gov"] |

### power_bi

Power BI API settings (all blank/placeholder).

| Field | Description |
|-------|-------------|
| `workspace_id` | PBI workspace GUID |
| `dataset_id` | PBI dataset GUID |
| `client_id` | Azure AD app client ID |
| `client_secret` | Azure AD app client secret |

### backup

| Field | Value |
|-------|-------|
| `retention_months` | 6 |
| `max_backup_size_gb` | 10 |
| `backup_location` | backups |

### monitoring

| Field | Value |
|-------|-------|
| `check_interval_hours` | 1 |
| `log_retention_days` | 30 |

---

## Path Resolution

All paths in config.json use `C:\Users\carucci_r\...` as the base. This resolves via junction:
- `C:\Users\carucci_r` -> `C:\Users\RobertCarucci`
- `C:\Users\RobertCarucci\OneDrive` -> `C:\Users\RobertCarucci\OneDrive - City of Hackensack`

Do NOT change `carucci_r` to `RobertCarucci` in any config file.
