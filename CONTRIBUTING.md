# Contributing

## Overview

This ETL pipeline is maintained by the SSOCC (Safe Streets Operations Control Center) at Hackensack PD. Contributions should follow these guidelines.

## Development Setup

1. Python 3.8+ with pandas, openpyxl, pytz
2. Access to source workbooks at paths in config.json
3. VS Code recommended (workspace file included)

## Guidelines

- Test changes against all active sources before committing
- Run `python src/main_processor.py` and verify output in `output/`
- Do not commit real credentials to `production_config.json`
- Do not change `carucci_r` path references (junction-resolved)
- Follow existing code patterns (processor subclasses of ExcelProcessor)
- Update CHANGELOG.md with any pipeline changes

## Adding a New Data Source

1. Create processor in `src/processors/` extending `ExcelProcessor`
2. Add source entry to `config.json` with file_path, sheet_name
3. Register processor in `MainProcessor.__init__()` in `src/main_processor.py`
4. Test with source disabled first (`"disabled": true`)
5. Update documentation (CLAUDE.md, README.md, docs/)

## Reporting Issues

Open an issue on the GitHub repository or contact the ETL operations team.
