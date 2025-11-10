"""
Community Engagement ETL - STACP Processor
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Process STACP (Special Teams and Community Policing) data
"""

import pandas as pd
import re
from typing import Dict, List, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.excel_processor import ExcelProcessor
from utils.logger_setup import get_project_logger

logger = get_project_logger(__name__)


class STACPProcessor(ExcelProcessor):
    """Processor for STACP data source"""
    
    def __init__(self):
        super().__init__()
        self.office_identifier = "STA&CP"
        self.division_identifier = "STACP"
        
        # Source-specific column mappings
        self.column_mapping = {
            'School Outreach Conducted ': 'event_name',
            'Date': 'date',
            'Start Time': 'start_time',
            'End Time': 'end_time',
            'Location': 'location'
        }
        
        # Fields that contain attendee information
        self.attendee_fields = ['Attendees', 'Attendees2', 'Attendees3', 'Attendees4', 'Attendees5', 'Free Type Attendees']
    
    def process_data_source(self, file_path: str, sheet_name: str = 'STACP Activities') -> pd.DataFrame:
        """
        Process STACP Excel data
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to process
            
        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing STACP data from {file_path}")
        
        # Read Excel source
        df = self.read_excel_source(file_path, sheet_name, {})
        
        # Standardize columns
        df = self.standardize_columns(df, self.column_mapping)
        
        # Parse attendees
        df = self.parse_attendees(df)
        
        # Calculate duration
        df = self.calculate_duration(df)
        
        # Add office/division identifiers
        df['office'] = self.office_identifier
        df['division'] = self.division_identifier
        
        # Log office assignment for debugging
        logger.info(f"STACP Processor: Assigned office name '{self.office_identifier}' to {len(df)} records")
        
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
                        # Handle numeric entries (participant counts)
                        if attendee_text.isdigit():
                            total_attendees += int(attendee_text)
                        else:
                            # Split by comma, slash, or ampersand for names
                            attendees = re.split(r'[,/&]', attendee_text)
                            valid_attendees = [a.strip() for a in attendees if a.strip()]
                            total_attendees += len(valid_attendees)
            
            result_df.at[idx, 'attendee_count'] = total_attendees
        
        return result_df