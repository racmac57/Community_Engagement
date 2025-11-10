"""
Community Engagement ETL - Setup Validator
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Validate configuration and setup for first-time users
"""

import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any


class SetupValidator:
    """Validates ETL system configuration and setup"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def validate_file_paths(self, config: Dict[str, Any]) -> bool:
        """Check all source files exist"""
        print("Validating source file paths...")
        all_valid = True
        
        for source_name, source_config in config.get('sources', {}).items():
            file_path = source_config.get('file_path', '')
            
            if not file_path:
                self.issues.append(f"Missing file_path for {source_name}")
                all_valid = False
                continue
                
            path_obj = Path(file_path)
            if not path_obj.exists():
                self.issues.append(f"File not found: {file_path} ({source_name})")
                all_valid = False
            elif not path_obj.is_file():
                self.issues.append(f"Path is not a file: {file_path} ({source_name})")
                all_valid = False
            elif path_obj.suffix.lower() not in ['.xlsx', '.xls', '.xlsm']:
                self.warnings.append(f"Unsupported file format: {file_path} ({source_name})")
        
        return all_valid
    
    def verify_excel_structure(self, config: Dict[str, Any]) -> bool:
        """Validate sheet names and columns"""
        print("Verifying Excel file structures...")
        all_valid = True
        
        for source_name, source_config in config.get('sources', {}).items():
            file_path = source_config.get('file_path', '')
            sheet_name = source_config.get('sheet_name', 'Sheet1')
            
            if not Path(file_path).exists():
                continue  # Already flagged in file_paths validation
                
            try:
                excel_file = pd.ExcelFile(file_path)
                
                # Check sheet exists
                if sheet_name not in excel_file.sheet_names:
                    self.issues.append(f"Sheet '{sheet_name}' not found in {source_name}")
                    all_valid = False
                    continue
                
                # Check for data in sheet
                df = pd.read_excel(excel_file, sheet_name, nrows=0)
                if df.empty or len(df.columns) == 0:
                    self.warnings.append(f"Sheet '{sheet_name}' appears empty in {source_name}")
                
                excel_file.close()
                
            except Exception as e:
                self.issues.append(f"Cannot read Excel file {source_name}: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def test_permissions(self, config: Dict[str, Any]) -> bool:
        """Ensure read/write access"""
        print("Testing file and directory permissions...")
        all_valid = True
        
        # Test source file read permissions
        for source_name, source_config in config.get('sources', {}).items():
            file_path = source_config.get('file_path', '')
            if Path(file_path).exists():
                try:
                    with open(file_path, 'rb') as f:
                        f.read(1024)  # Try to read first 1KB
                except PermissionError:
                    self.issues.append(f"No read permission for {file_path} ({source_name})")
                    all_valid = False
                except Exception as e:
                    self.warnings.append(f"Read test failed for {source_name}: {str(e)}")
        
        # Test output directory write permissions
        output_dirs = ['output', 'reports', 'logs', 'backups']
        for dir_name in output_dirs:
            dir_path = Path(dir_name)
            try:
                dir_path.mkdir(exist_ok=True)
                test_file = dir_path / 'test_write.tmp'
                test_file.write_text('test')
                test_file.unlink()
            except PermissionError:
                self.issues.append(f"No write permission for {dir_name} directory")
                all_valid = False
            except Exception as e:
                self.warnings.append(f"Write test failed for {dir_name}: {str(e)}")
        
        return all_valid
    
    def create_sample_config(self) -> Dict[str, Any]:
        """Generate example configuration"""
        sample_config = {
            "sources": {
                "community_engagement": {
                    "file_path": "data/community_engagement.xlsx",
                    "sheet_name": "Events",
                    "description": "Community Engagement division events"
                },
                "stacp": {
                    "file_path": "data/stacp_activities.xlsx",
                    "sheet_name": "Activities",
                    "description": "Special Teams and Community Policing activities"
                },
                "patrol": {
                    "file_path": "data/patrol_events.xlsx",
                    "sheet_name": "Events",
                    "description": "Patrol division community events"
                },
                "csb": {
                    "file_path": "data/csb_programs.xlsx",
                    "sheet_name": "Programs",
                    "description": "Community Services Bureau programs"
                }
            },
            "output_settings": {
                "csv_export": True,
                "excel_export": True,
                "backup_files": True,
                "output_directory": "output"
            },
            "validation_rules": {
                "required_fields": ["event_name", "date"],
                "min_data_quality_score": 80
            }
        }
        
        config_path = Path('config.json')
        with open(config_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"Sample configuration created: {config_path}")
        return sample_config
    
    def run_setup_wizard(self):
        """Interactive setup wizard for first-time configuration"""
        print("=== Community Engagement ETL Setup Wizard ===\n")
        
        # Check if config exists
        if Path('config.json').exists():
            response = input("Configuration file exists. Overwrite? (y/N): ").lower()
            if response != 'y':
                print("Setup cancelled.")
                return
        
        # Create sample config
        config = self.create_sample_config()
        print("\nSample configuration created. Please update file paths in config.json")
        
        # Run validation
        print("\nRunning initial validation...")
        if self.validate_setup():
            print("\n✓ Setup validation passed! System ready to use.")
        else:
            print("\n✗ Setup validation failed. Please fix the issues below:")
            self.print_issues()
            print("\nUpdate config.json and run setup again.")
    
    def validate_setup(self, config_path: str = 'config.json') -> bool:
        """Complete setup validation"""
        if not Path(config_path).exists():
            print(f"Configuration file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Cannot read configuration file: {e}")
            return False
        
        # Run all validations
        file_paths_valid = self.validate_file_paths(config)
        structure_valid = self.verify_excel_structure(config)
        permissions_valid = self.test_permissions(config)
        
        success = file_paths_valid and structure_valid and permissions_valid
        
        if success:
            print("[SUCCESS] All validations passed")
        else:
            self.print_issues()
        
        return success
    
    def print_issues(self):
        """Print validation issues and warnings"""
        if self.issues:
            print("\nIssues found:")
            for issue in self.issues:
                print(f"  [ERROR] {issue}")
        
        if self.warnings:
            print("\nWarnings:")
            for warning in self.warnings:
                print(f"  [WARNING] {warning}")


if __name__ == "__main__":
    validator = SetupValidator()
    
    # Check if this is first run
    if not Path('config.json').exists():
        validator.run_setup_wizard()
    else:
        print("Validating existing configuration...")
        if validator.validate_setup():
            print("Configuration is valid and ready to use.")
        else:
            print("\nTo create new configuration, delete config.json and run again.")