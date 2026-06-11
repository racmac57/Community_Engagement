"""
Community Engagement ETL - Community Engagement Processor
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Process Community Engagement data with specific column mappings and attendee parsing
"""

import numpy as np
import pandas as pd
import re
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.excel_processor import ExcelProcessor
from utils.logger_setup import get_project_logger
from utils.duration_utils import safe_duration_to_hours

logger = get_project_logger(__name__)


class CommunityEngagementProcessor(ExcelProcessor):
    """Processor for Community Engagement data source"""
    
    def __init__(self):
        super().__init__()
        self.office_identifier = "Community Engagement"
        self.division_identifier = "Outreach"
        
        # Source-specific column mappings
        self.column_mapping = {
            'Community Event': 'event_name',
            'Date of Event': 'date',
            'Start Time': 'start_time',
            'End Time': 'end_time',
            'Event Location': 'location',
            'Event Duration9': 'pre_calculated_duration',  # Use existing calculated duration
            'Member Count': 'pre_calculated_count'  # Use existing member count
        }
        
        # Fields that contain attendee information (member columns)
        self.attendee_fields = ['Participating Member 1', 'Participating Member 2', 'Participating Member 3',
                               'Participating Member 4', 'Participating Member 5', 'Participating Member 6',
                               'Participating Member 7', 'Participating Member 8', 'Participating Member 9', 
                               'Participating Memb 10']
    
    def process_data_source(self, file_path: str, sheet_name: str = 'Sheet1') -> pd.DataFrame:
        """
        Process Community Engagement Excel data
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to process
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing Community Engagement data from {file_path}")
        
        # Read Excel source
        df = self.read_excel_source(file_path, sheet_name, {})
        
        # Standardize columns
        df = self.standardize_columns(df, self.column_mapping)
        
        # Parse attendees (use pre-calculated count if available)
        df = self.process_attendees(df)
        
        # Use pre-calculated duration if available, otherwise calculate from times
        df = self.process_duration(df)
        
        # Add office/division identifiers
        df['office'] = self.office_identifier
        df['division'] = self.division_identifier
        
        # Log office assignment for debugging
        logger.info(f"Community Engagement Processor: Assigned office name '{self.office_identifier}' to {len(df)} records")
        
        # Validate data
        required_fields = ['event_name', 'date']
        validation_results = self.validate_data(df, required_fields)
        
        logger.info(f"Processing complete: {validation_results['valid_rows']} valid rows")
        return df
    
    def parse_attendees(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse attendee fields with comma/slash/ampersand separation
        
        Args:
            df: DataFrame with raw attendee fields
            
        Returns:
            DataFrame with parsed attendee count
        """
        result_df = df.copy()
        
        for idx, row in result_df.iterrows():
            total_attendees = 0
            
            for field in self.attendee_fields:
                if field in result_df.columns and pd.notna(row[field]):
                    attendee_text = str(row[field]).strip()
                    if attendee_text:
                        # Split by comma, slash, or ampersand
                        attendees = re.split(r'[,/&]', attendee_text)
                        # Count non-empty entries
                        valid_attendees = [a.strip() for a in attendees if a.strip()]
                        total_attendees += len(valid_attendees)
            
            result_df.at[idx, 'attendee_count'] = total_attendees
        
        return result_df
    
    def process_attendees(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process attendees using pre-calculated count if available, otherwise parse member fields
        
        Args:
            df: DataFrame with attendee data
            
        Returns:
            DataFrame with attendee_count column
        """
        result_df = df.copy()
        
        # Check if we have pre-calculated member count
        if 'pre_calculated_count' in result_df.columns:
            logger.info("Using pre-calculated member count from Excel")
            for idx, row in result_df.iterrows():
                count_val = row.get('pre_calculated_count')
                
                if pd.notna(count_val):
                    try:
                        # Convert to integer
                        attendee_count = int(float(count_val))
                        result_df.at[idx, 'attendee_count'] = max(attendee_count, 1)  # Minimum 1 attendee
                    except (ValueError, TypeError):
                        logger.warning(f"Failed to parse pre-calculated count for row {idx}: {count_val}")
                        result_df.at[idx, 'attendee_count'] = 1  # Default fallback
                else:
                    result_df.at[idx, 'attendee_count'] = 1  # Default for missing values
        else:
            # Fallback to member field parsing
            logger.info("No pre-calculated count found, parsing member fields")
            result_df = self.parse_attendees(result_df)
        
        return result_df
    
    def process_duration(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process duration using pre-calculated values if available, otherwise calculate from times.
        Uses safe_duration_to_hours for timedelta/time/string/float cells so CSV exports numeric hours.
        """
        result_df = df.copy()

        if "pre_calculated_duration" in result_df.columns:
            logger.info("Using pre-calculated duration from Excel (with start/end fallback where null)")
            primary_hours = result_df["pre_calculated_duration"].apply(
                lambda v: safe_duration_to_hours(v, default=np.nan)
            )
            alt_df = self.calculate_duration(result_df)
            result_df["duration_hours"] = primary_hours.combine_first(alt_df["duration_hours"]).fillna(0.5)
            result_df["duration_hours"] = result_df["duration_hours"].round(2)
        else:
            logger.info("No pre-calculated duration found, calculating from start/end times")
            result_df = self.calculate_duration(result_df)
            result_df["duration_hours"] = result_df["duration_hours"].fillna(0.5).round(2)

        return result_df