# File Inventory

Complete inventory of all files in the Community_Engagement repository as of 2026-03-28.

## Core Pipeline Files

| File | Purpose | Status |
|------|---------|--------|
| `src/main_processor.py` | Pipeline orchestrator | Active |
| `src/processors/excel_processor.py` | Base processor class | Active |
| `src/processors/community_engagement_processor.py` | CE source processor | Active |
| `src/processors/stacp_processor.py` | STA&CP source processor | Active |
| `src/processors/patrol_processor.py` | Patrol source processor (v2) | Active |
| `src/processors/csb_processor.py` | CSB source processor | Active (source disabled) |
| `config.json` | Source paths and settings | Active |
| `production_config.json` | SMTP/PBI/backup config | Active (credentials blank) |

## Utility Files

| File | Purpose | Status |
|------|---------|--------|
| `src/utils/config_loader.py` | JSON config reader | Active |
| `src/utils/logger_setup.py` | Rotating EST logger | Active |
| `src/utils/data_validator.py` | Validation helpers | Active |
| `src/utils/duration_utils.py` | Duration normalization | Active |
| `src/utils/attendee_utils.py` | STACP attendee aliases | Active |
| `src/__init__.py` | Package marker | Active |
| `src/processors/__init__.py` | Package marker | Active |
| `src/utils/__init__.py` | Package marker | Active |

## Power BI M Code

| File | Purpose | Status |
|------|---------|--------|
| `Combined_Outreach_All.m` | PBI M query (root) | Active |
| `src/___Combined_Outreach_All.m` | PBI M query (src copy) | Redundant -- same as root |

## Validation and Debug Scripts

| File | Purpose | Status |
|------|---------|--------|
| `data_quality_validator.py` | Data quality checks | Active utility |
| `power_bi_export_validator.py` | PBI export limits check | Active utility |
| `setup_validator.py` | Environment validation | Active utility |
| `verify_config.py` | Config sanity checks | Active utility |
| `validate_m_code_logic.py` | M code vs Python validation | Active utility |
| `integration_test.py` | End-to-end test | Active test |
| `tests/test_processors.py` | Processor unit tests | Active test |
| `debug_csb_structure.py` | CSB workbook debug | Dead (one-time) |
| `debug_processors.py` | Processor debug | Dead (one-time) |
| `sample_office_distribution.py` | Office distribution sample | Dead (one-time) |
| `test_date_parsing.py` | Date parsing test | Dead (one-time) |
| `deploy_production.py` | Deployment helper | Likely unused |
| `monitor_etl.py` | Monitoring helper | Likely unused |
| `project_scaffold.py` | Project scaffolding | Dead (ran once) |

## Documentation

| File | Purpose | Status |
|------|---------|--------|
| `CLAUDE.md` | AI assistant guide | Current (2026-03-28) |
| `README.md` | Project readme | Current (2026-03-28) |
| `CHANGELOG.md` | Change history | Current (2026-03-28) |
| `SUMMARY.md` | Status summary | Current (2026-03-28) |
| `Notes.md` | Raw data notes (Aug 2025) | Reference |
| `PYTHON_WORKSPACE_AI_GUIDE.md` | Generic AI guide | Template (not project-specific) |
| `PYTHON_WORKSPACE_TEMPLATE.md` | Generic workspace template | Template (not project-specific) |
| `office_name_debug_report.md` | Office name debug results | One-time artifact |
| `processor_validation_report.md` | Validation results | One-time artifact |
| `docs/cursor_prompt_fix_community_etl.md` | CSB exclusion prompt | Reference |
| `docs/etl-pipeline.md` | Pipeline documentation | Current (2026-03-28) |
| `docs/file-inventory.md` | This file | Current (2026-03-28) |
| `docs/config-reference.md` | Config reference | Current (2026-03-28) |
| `CONTRIBUTING.md` | Contributor guidelines | Stub |
| `reorganization_proposal.md` | Cleanup proposal | Current (2026-03-28) |

## Duplicate / Clutter Files (Candidates for Archival)

| File | Assessment |
|------|-----------|
| `CHANGELOG (1).md` | OneDrive sync duplicate |
| `README (1).md` | OneDrive sync duplicate |
| `SUMMARY (1).md` | OneDrive sync duplicate |
| `config.json.backup_20260219_142331` | Config backup |
| `config.json.backup_20260219_142624` | Config backup |
| `config.json.backup_20260219_143114` | Config backup |
| `config.json.backup_20260219_144204` | Config backup |
| `task_schedule (1).xml` | OneDrive sync duplicate |
| `logs/community_engagement_etl (1).log` | OneDrive sync duplicate |
| `logs/main_processor (1).log` | OneDrive sync duplicate |
| `src/logs/community_engagement_etl (1).log` | OneDrive sync duplicate |
| `src/logs/main_processor (1).log` | OneDrive sync duplicate |
| `tmpclaude-974f-cwd` | Temp file from Claude Code |

## Data / Output Directories

| Directory | Contents | Count |
|-----------|----------|-------|
| `data/` | Sample CSVs | 4 files |
| `output/` | Timestamped CSV+XLSX exports | 30+ pairs |
| `reports/` | Processing + monthly summaries | 30+ pairs |
| `src/output/` | Legacy pre-refactor outputs | 5 pairs |
| `src/reports/` | Legacy pre-refactor reports | 5 pairs |
| `backups/` | Source file backups | Variable |
| `logs/` | Rotating log files | 2+ files |
| `src/logs/` | Legacy log directory | 2+ files |

## Other Files

| File | Purpose |
|------|---------|
| `Community_Engagement.code-workspace` | VS Code workspace |
| `task_schedule.xml` | Windows Task Scheduler config |
| `Engagement Initiatives by Bureau.csv` | Before-update reference |
| `after_update_Engagement Initiatives by Bureau.csv` | After-update reference |
| `.claude/settings.local.json` | Claude Code settings |
| `.gitignore` | Git exclusions (created 2026-03-28) |

## Conversation / Chat Logs (documents/)

| Path | Purpose |
|------|---------|
| `documents/2025_09_04_17_51_17_claude_chat_log.md` | Initial build chat log |
| `documents/Community_Engagement_ETL_CSB_Config_And_Docs/` | CSB config conversation (origin, sidecar, transcript, chunk) |
| `documents/Patrol_Processor_V2_Implementation_And_Documentation/` | Patrol v2 conversation (origin, sidecar, transcript, chunks) |
