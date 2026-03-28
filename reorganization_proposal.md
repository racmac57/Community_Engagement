# Reorganization Proposal

**Date:** 2026-03-28
**Status:** Proposal only -- no changes executed

---

## 1. Directory Name Typo

**Current:** `Community_Engagment` (missing 'e')
**Proposed:** `Community_Engagement`

**WARNING:** This rename affects multiple downstream references:
- `config.json` output paths
- `task_schedule.xml` working directory and arguments
- `Combined_Outreach_All.m` OutputFolder path
- `src/___Combined_Outreach_All.m` OutputFolder path
- `Community_Engagment.code-workspace` filename
- Git remote URL (`racmac57/Community_Engagement.git` -- already correct spelling)
- Any parent-level scripts referencing this directory
- Power BI data source configurations

**Recommendation:** Coordinate rename across all references in a single commit. Test Power BI refresh after rename. Consider updating junction or symlink approach.

---

## 2. Files to Archive

Move to `archive/` directory with datestamp prefix:

### OneDrive Sync Duplicates
- `CHANGELOG (1).md`
- `README (1).md`
- `SUMMARY (1).md`
- `task_schedule (1).xml`
- `logs/community_engagement_etl (1).log`
- `logs/main_processor (1).log`
- `src/logs/community_engagement_etl (1).log`
- `src/logs/main_processor (1).log`

### Config Backups
- `config.json.backup_20260219_142331`
- `config.json.backup_20260219_142624`
- `config.json.backup_20260219_143114`
- `config.json.backup_20260219_144204`

### Temp Files
- `tmpclaude-974f-cwd`

---

## 3. Files to Delete (After Verification)

These are one-time debug/analysis scripts that serve no ongoing purpose:

- `debug_csb_structure.py`
- `debug_processors.py`
- `sample_office_distribution.py`
- `test_date_parsing.py`
- `project_scaffold.py`

---

## 4. Redundant Files to Consolidate

### Duplicate M Code
- `Combined_Outreach_All.m` (root) and `src/___Combined_Outreach_All.m` are functionally identical
- **Recommendation:** Keep root copy as canonical. Delete or convert src/ copy to a symlink.

### Duplicate Log Directories
- `logs/` and `src/logs/` both contain log files
- **Recommendation:** Keep `logs/` only. Logger already writes to CWD/logs. Remove `src/logs/`.

### Duplicate Output Directories
- `output/` and `src/output/` both contain exports
- **Recommendation:** Keep `output/` only. `src/output/` contains 5 old files from early development. Archive.

---

## 5. Missing Files to Create

- `requirements.txt` -- README references it but it does not exist. Should contain: `pandas`, `openpyxl`, `pytz`
- Output rotation script or policy -- 30+ timestamped output pairs accumulate without cleanup

---

## 6. Template Files Assessment

These files appear to be generic workspace templates, not project-specific:
- `PYTHON_WORKSPACE_AI_GUIDE.md`
- `PYTHON_WORKSPACE_TEMPLATE.md`

**Recommendation:** Move to `docs/templates/` or archive if not used.

---

## 7. Suggested Folder Structure (After Cleanup)

```
Community_Engagement/           <-- fixed spelling
+-- config.json
+-- production_config.json
+-- requirements.txt            <-- new
+-- .gitignore                  <-- new (created 2026-03-28)
+-- src/
|   +-- main_processor.py
|   +-- processors/
|   +-- utils/
+-- Combined_Outreach_All.m
+-- output/                     <-- only output dir (remove src/output/)
+-- reports/
+-- logs/                       <-- only log dir (remove src/logs/)
+-- backups/
+-- data/
+-- docs/
+-- tests/
+-- documents/                  <-- chat logs / conversation archives
+-- archive/                    <-- moved duplicates, old backups, dead scripts
+-- CLAUDE.md
+-- README.md
+-- CHANGELOG.md
+-- SUMMARY.md
+-- CONTRIBUTING.md
```
