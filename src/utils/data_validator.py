"""
Community Engagement ETL - Data Validator
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Validate Excel files, sheets, and column structures
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class DataValidator:
    """Handles validation of Excel files and data structures"""
    
    def __init__(self):
        """Initialize the data validator"""
        self.supported_formats = {'.xlsx', '.xls', '.xlsm'}
    
    def validate_file_exists(self, file_path: str) -> Path:
        """
        Validate that file exists and is accessible
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            Path object if valid
            
        Raises:
            ValidationError: If file doesn't exist or is inaccessible
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ValidationError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValidationError(f"Path is not a file: {file_path}")
        
        if path.suffix.lower() not in self.supported_formats:
            raise ValidationError(f"Unsupported file format: {path.suffix}")
        
        logger.info(f"File validation passed: {file_path}")
        return path
    
    def validate_excel_structure(self, file_path: str, 
                                required_sheets: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Validate Excel file structure and return sheet information
        
        Args:
            file_path: Path to Excel file
            required_sheets: List of sheet names that must exist
            
        Returns:
            Dictionary mapping sheet names to column lists
            
        Raises:
            ValidationError: If file structure is invalid
        """
        path = self.validate_file_exists(file_path)
        
        try:
            excel_file = pd.ExcelFile(path)
            sheet_names = excel_file.sheet_names
            
            if not sheet_names:
                raise ValidationError("Excel file contains no sheets")
            
            if required_sheets:
                missing_sheets = set(required_sheets) - set(sheet_names)
                if missing_sheets:
                    raise ValidationError(f"Missing required sheets: {list(missing_sheets)}")
            
            sheet_info = {}
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name, nrows=0)
                    sheet_info[sheet_name] = df.columns.tolist()
                except Exception as e:
                    logger.warning(f"Could not read sheet '{sheet_name}': {e}")
                    sheet_info[sheet_name] = []
            
            excel_file.close()
            logger.info(f"Excel structure validation passed: {len(sheet_names)} sheets found")
            return sheet_info
            
        except Exception as e:
            raise ValidationError(f"Failed to validate Excel file structure: {e}")
    
    def validate_columns(self, file_path: str, sheet_name: str, 
                        required_columns: List[str]) -> bool:
        """
        Validate that required columns exist in specified sheet
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to check
            required_columns: List of column names that must exist
            
        Returns:
            True if all required columns exist
            
        Raises:
            ValidationError: If columns are missing or sheet doesn't exist
        """
        try:
            df = pd.read_excel(file_path, sheet_name, nrows=0)
            existing_columns = set(df.columns)
            required_set = set(required_columns)
            
            missing_columns = required_set - existing_columns
            if missing_columns:
                raise ValidationError(
                    f"Missing required columns in sheet '{sheet_name}': {list(missing_columns)}"
                )
            
            logger.info(f"Column validation passed for sheet '{sheet_name}': {len(required_columns)} columns found")
            return True
            
        except FileNotFoundError:
            raise ValidationError(f"File not found: {file_path}")
        except ValueError as e:
            raise ValidationError(f"Sheet '{sheet_name}' not found in file: {file_path}")
        except Exception as e:
            raise ValidationError(f"Column validation failed: {e}")
    
    def get_data_summary(self, file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Get summary information about data in specified sheet
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to analyze
            
        Returns:
            Dictionary with data summary information
        """
        try:
            df = pd.read_excel(file_path, sheet_name)
            
            summary = {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': df.columns.tolist(),
                'empty_rows': df.isnull().all(axis=1).sum(),
                'duplicate_rows': df.duplicated().sum()
            }
            
            logger.info(f"Generated data summary for sheet '{sheet_name}': {summary['row_count']} rows")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate data summary: {e}")
            return {}