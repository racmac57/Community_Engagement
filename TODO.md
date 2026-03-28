# TODO — Community_Engagement
## Generated from swarm audit 2026-03-28

### CRITICAL Priority
- [x] ~~Directory name typo: `Community_Engagment` (missing 'e').~~ RESOLVED 2026-03-28. Renamed to `Community_Engagement`, all downstream refs updated. Task Scheduler XML needs manual re-import.

### HIGH Priority
- [ ] CSB config inconsistency: config.json `sheet_name` is `26_01` but `csb_processor.py` default is `CSB_CommOut`. Resolve before re-enabling source
- [ ] Verify `task_schedule.xml`: Confirm it is registered in Windows Task Scheduler and functioning

### MEDIUM Priority
- [ ] Create `requirements.txt`: README references `pip install -r requirements.txt` but file does not exist
- [ ] Output retention policy: 30+ timestamped export pairs in `output/`. Decide whether to keep all or implement rotation
- [ ] STACP `additional_sheets`: `25_Presentations` and `25_Training Delivered` declared in config but only primary `sheet_name` is processed. Confirm if these should be processed

### LOW Priority
- [ ] Review dead scripts: debug_csb_structure.py, debug_processors.py, sample_office_distribution.py, test_date_parsing.py, project_scaffold.py, deploy_production.py, monitor_etl.py — confirm safe to archive
