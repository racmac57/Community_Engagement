"""
Community Engagement ETL - Excel Data Processor
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Process Excel files from 6 data sources with standardization and validation
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import re
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_validator import DataValidator, ValidationError
from utils.logger_setup import get_project_logger, log_operation_start, log_operation_end

logger = get_project_logger(__name__)


class ExcelProcessor:
    """Processes Excel files for Community Engagement data sources"""
    
    def __init__(self):
        self.validator = DataValidator()
        self.standard_columns = ['event_name', 'date', 'start_time', 'end_time', 'duration_hours', 'attendee_count']
    
    def read_excel_source(self, file_path: str, sheet_name: str, source_config: Dict[str, Any]) -> pd.DataFrame:
        """
        Read specific sheet/table from Excel files with error handling
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to read
            source_config: Configuration for this data source
            
        Returns:
            DataFrame with raw data
        """
        log_operation_start(logger, "read_excel_source", file=file_path, sheet=sheet_name)
        
        try:
            # Validate file exists and is accessible
            self.validator.validate_file_exists(file_path)
            
            # Try reading with different engines for locked files
            for engine in ['openpyxl', 'xlrd']:
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine=engine)
                    break
                except PermissionError:
                    if engine == 'xlrd':  # Last attempt
                        raise ValidationError(f"File is locked or permission denied: {file_path}")
                except Exception:
                    continue
            
            # Handle missing sheet
            if df.empty:
                raise ValidationError(f"Sheet '{sheet_name}' is empty or not found")
            
            log_operation_end(logger, "read_excel_source", True, rows=len(df), columns=len(df.columns))
            return df
            
        except Exception as e:
            log_operation_end(logger, "read_excel_source", False, error=str(e))
            raise ValidationError(f"Failed to read Excel source: {e}")
    
    def standardize_columns(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Map source columns to standard format
        
        Args:
            df: Source DataFrame
            column_mapping: Mapping of source columns to standard columns
            
        Returns:
            DataFrame with standardized column names
        """
        log_operation_start(logger, "standardize_columns", mapping_count=len(column_mapping))
        
        try:
            # Create copy to avoid modifying original
            standardized_df = df.copy()
            
            # Rename columns based on mapping
            rename_dict = {}
            for source_col, standard_col in column_mapping.items():
                if source_col in standardized_df.columns:
                    rename_dict[source_col] = standard_col
                else:
                    logger.warning(f"Source column '{source_col}' not found in data")
            
            standardized_df = standardized_df.rename(columns=rename_dict)
            
            # Add missing standard columns with default values
            for col in self.standard_columns:
                if col not in standardized_df.columns:
                    standardized_df[col] = None
            
            log_operation_end(logger, "standardize_columns", True, renamed_columns=len(rename_dict))
            return standardized_df
            
        except Exception as e:
            log_operation_end(logger, "standardize_columns", False, error=str(e))
            raise ValidationError(f"Column standardization failed: {e}")
    
    def calculate_duration(self, df: pd.DataFrame, start_col: str = 'start_time', 
                          end_col: str = 'end_time') -> pd.DataFrame:
        """
        Convert start/end times to duration in hours
        
        Args:
            df: DataFrame with time columns
            start_col: Name of start time column
            end_col: Name of end time column
            
        Returns:
            DataFrame with duration_hours column calculated
        """
        log_operation_start(logger, "calculate_duration", start_col=start_col, end_col=end_col)
        
        try:
            result_df = df.copy()
            duration_calculated = 0
            
            for idx, row in result_df.iterrows():
                try:
                    start_time = pd.to_datetime(row[start_col], errors='coerce')
                    end_time = pd.to_datetime(row[end_col], errors='coerce')
                    
                    if pd.notna(start_time) and pd.notna(end_time):
                        duration = end_time - start_time
                        result_df.at[idx, 'duration_hours'] = duration.total_seconds() / 3600
                        duration_calculated += 1
                    else:
                        result_df.at[idx, 'duration_hours'] = None
                        
                except Exception as e:
                    logger.warning(f"Duration calculation failed for row {idx}: {e}")
                    result_df.at[idx, 'duration_hours'] = None
            
            log_operation_end(logger, "calculate_duration", True, calculated=duration_calculated)
            return result_df
            
        except Exception as e:
            log_operation_end(logger, "calculate_duration", False, error=str(e))
            raise ValidationError(f"Duration calculation failed: {e}")
    
    def count_attendees(self, df: pd.DataFrame, member_columns: List[str]) -> pd.DataFrame:
        """
        Parse member fields and count non-empty values
        
        Args:
            df: DataFrame with member columns
            member_columns: List of column names containing member data
            
        Returns:
            DataFrame with attendee_count column
        """
        log_operation_start(logger, "count_attendees", member_columns=len(member_columns))
        
        try:
            result_df = df.copy()
            
            for idx, row in result_df.iterrows():
                count = 0
                for col in member_columns:
                    if col in result_df.columns:
                        value = row[col]
                        if pd.notna(value) and str(value).strip():
                            count += 1
                
                result_df.at[idx, 'attendee_count'] = count
            
            total_events = len(result_df)
            avg_attendance = result_df['attendee_count'].mean() if total_events > 0 else 0
            
            log_operation_end(logger, "count_attendees", True, events=total_events, avg_attendance=f"{avg_attendance:.1f}")
            return result_df
            
        except Exception as e:
            log_operation_end(logger, "count_attendees", False, error=str(e))
            raise ValidationError(f"Attendee counting failed: {e}")
    
    def validate_data(self, df: pd.DataFrame, required_fields: List[str]) -> Dict[str, Any]:
        """
        Check for required fields and data quality
        
        Args:
            df: DataFrame to validate
            required_fields: List of required column names
            
        Returns:
            Dictionary with validation results
        """
        log_operation_start(logger, "validate_data", required_fields=len(required_fields), rows=len(df))
        
        try:
            validation_results = {
                'total_rows': len(df),
                'valid_rows': 0,
                'missing_required_fields': [],
                'empty_rows': 0,
                'data_quality_issues': []
            }
            
            # Check for missing required columns
            missing_cols = [col for col in required_fields if col not in df.columns]
            validation_results['missing_required_fields'] = missing_cols
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return validation_results
            
            # Check data quality row by row
            for idx, row in df.iterrows():
                # Check if row is completely empty
                if row[required_fields].isna().all():
                    validation_results['empty_rows'] += 1
                    continue
                
                # Check for missing required values
                missing_values = [col for col in required_fields if pd.isna(row[col]) or str(row[col]).strip() == '']
                
                if not missing_values:
                    validation_results['valid_rows'] += 1
                else:
                    validation_results['data_quality_issues'].append({
                        'row': idx,
                        'missing_fields': missing_values
                    })
            
            # Calculate validation percentage
            valid_percentage = (validation_results['valid_rows'] / validation_results['total_rows'] * 100) if validation_results['total_rows'] > 0 else 0
            validation_results['valid_percentage'] = round(valid_percentage, 1)
            
            log_operation_end(logger, "validate_data", True, 
                            valid_rows=validation_results['valid_rows'],
                            valid_percentage=f"{valid_percentage:.1f}%")
            
            return validation_results
            
        except Exception as e:
            log_operation_end(logger, "validate_data", False, error=str(e))
            raise ValidationError(f"Data validation failed: {e}")