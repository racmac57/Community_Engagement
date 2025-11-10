# 🕒 2025-09-04-15-30-00
# Community_Engagement/project_scaffolding.py
# Author: R. A. Carucci
# Purpose: Create directory structure and initial files for Community Engagement data processing project

import os
import json
from pathlib import Path

def create_project_structure():
    """
    Creates the complete directory structure for the Community Engagement project
    """
    base_dir = Path(r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment")
    
    # Directory structure
    directories = [
        "config",
        "src",
        "src/processors",
        "src/utils",
        "data",
        "data/input",
        "data/output",
        "data/backup",
        "logs",
        "docs",
        "tests"
    ]
    
    # Create directories
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {dir_path}")
    
    # Create initial configuration files
    create_config_files(base_dir)
    create_readme(base_dir)
    create_requirements(base_dir)
    create_gitignore(base_dir)
    
    print(f"\n🎉 Project scaffolding complete at: {base_dir}")
    print("\n📋 Next Steps:")
    print("1. Run the data source processor script")
    print("2. Configure file paths in config/paths.json")
    print("3. Test individual data source processors")

def create_config_files(base_dir):
    """Create configuration files"""
    
    # Main configuration
    config = {
        "project_name": "Community Engagement Data Processing",
        "version": "1.0.0",
        "author": "R. A. Carucci",
        "description": "Automated processing of police community engagement data from multiple sources",
        "data_sources": {
            "community_engagement": {
                "file": "Community_Engagement_Monthly.xlsx",
                "sheet": "2025_Master",
                "table": "*25*ce"
            },
            "stacp_outreach": {
                "file": "STACP.xlsm",
                "sheet": "25_School_Outreach",
                "table": "*25*outreach"
            },
            "stacp_presentations": {
                "file": "STACP.xlsm",
                "sheet": "25_Presentations",
                "table": "*25*present"
            },
            "stacp_training": {
                "file": "STACP.xlsm",
                "sheet": "25_Training Delivered",
                "table": "*25*Training"
            },
            "patrol_outreach": {
                "file": "patrol_monthly.xlsm",
                "sheet": "Main_Outreach_Combined",
                "table": "Main_Outreach_Combined"
            },
            "csb_outreach": {
                "file": "csb_monthly.xlsm",
                "sheet": "CSB_CommOut",
                "table": "*csb*commout"
            }
        }
    }
    
    # File paths configuration
    paths = {
        "base_data_dir": r"C:\Users\carucci_r\OneDrive - City of Hackensack\Shared Folder\Compstat\Contributions",
        "community_engagement_dir": "Community_Engagement",
        "stacp_dir": "STACP",
        "patrol_dir": "Patrol",
        "csb_dir": "CSB",
        "output_dir": r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment\data\output",
        "backup_dir": r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment\data\backup",
        "logs_dir": r"C:\Users\carucci_r\OneDrive - City of Hackensack\02_ETL_Scripts\Community_Engagment\logs"
    }
    
    # Column mappings for standardization
    column_mappings = {
        "standard_columns": [
            "Date",
            "Event_Name",
            "Location_of_Event",
            "Event_Duration_Hours",
            "Number_of_Police_Department_Attendees",
            "Office"
        ],
        "source_mappings": {
            "community_engagement": {
                "Date of Event": "Date",
                "Community Event": "Event_Name",
                "Event Location": "Location_of_Event"
            },
            "stacp": {
                "Date": "Date",
                "School Outreach Conducted": "Event_Name",
                "Location": "Location_of_Event"
            },
            "patrol": {
                "Date": "Date",
                "Event Name": "Event_Name",
                "Location": "Location_of_Event"
            },
            "csb": {
                "Date": "Date",
                "Event Name": "Event_Name",
                "Event Location": "Location_of_Event"
            }
        }
    }
    
    # Save configuration files
    with open(base_dir / "config" / "config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    with open(base_dir / "config" / "paths.json", "w") as f:
        json.dump(paths, f, indent=4)
    
    with open(base_dir / "config" / "column_mappings.json", "w") as f:
        json.dump(column_mappings, f, indent=4)
    
    print(f"✅ Created configuration files in {base_dir}/config/")

def create_readme(base_dir):
    """Create README.md file"""
    readme_content = """# Community Engagement Data Processing

## Overview
Automated processing system for police community engagement data from multiple departmental sources.

## Project Structure
```
Community_Engagment/
├── config/           # Configuration files
├── src/             # Source code
│   ├── processors/  # Data source processors
│   └── utils/       # Utility functions
├── data/            # Data directories
│   ├── input/       # Input staging
│   ├── output/      # Processed outputs
│   └── backup/      # Backup files
├── logs/            # Log files
├── docs/            # Documentation
└── tests/           # Test files
```

## Data Sources
1. **Community Engagement** - Monthly community event data
2. **STACP** - School outreach, presentations, and training
3. **Patrol Division** - Community outreach activities
4. **CSB** - Crime Suppression Bureau community events

## Usage
1. Configure file paths in `config/paths.json`
2. Run individual processors or use main processing script
3. Check logs for processing status and errors

## Output
- Standardized CSV files for Power BI consumption
- Combined monthly reports
- Data validation reports

## Author
R. A. Carucci - Principal Analyst
"""
    
    with open(base_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print(f"✅ Created README.md")

def create_requirements(base_dir):
    """Create requirements.txt file"""
    requirements = """pandas>=2.0.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
python-dateutil>=2.8.0
pathlib>=1.0.0
logging>=0.4.0
json5>=0.9.0
"""
    
    with open(base_dir / "requirements.txt", "w") as f:
        f.write(requirements)
    
    print(f"✅ Created requirements.txt")

def create_gitignore(base_dir):
    """Create .gitignore file"""
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# Data files
*.xlsx
*.xls
*.csv
data/input/*
data/backup/*
!data/input/.gitkeep
!data/backup/.gitkeep

# Logs
logs/*.log
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
    
    with open(base_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print(f"✅ Created .gitignore")

if __name__ == "__main__":
    create_project_structure()
