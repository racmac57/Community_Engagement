"""
Community Engagement ETL - CSB Processor
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Process CSB (Community Services Bureau) statistics data
Note: CSB tracks daily activity counts rather than individual events
"""

import pandas as pd
import re
from typing import Dict, List, Any
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.excel_processor import ExcelProcessor
from utils.logger_setup import get_project_logger

logger = get_project_logger(__name__)


class CSBProcessor(ExcelProcessor):
    """Processor for Community Services Bureau statistics data"""
    
    def __init__(self):
        super().__init__()
        self.office_identifier = "Crime Suppression Bureau"  
        self.division_identifier = "Community Services Bureau"
        
        # CSB tracks statistics, not individual events
        # We'll convert daily counts to summary events
    
    def process_data_source(self, file_path: str, sheet_name: str = '25_Jan') -> pd.DataFrame:
        """
        Process CSB statistics data and convert to event-like format
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to process (e.g., '25_Jan')
            
        Returns:
            Processed DataFrame in standardized format
        """
        logger.info(f"Processing CSB statistics data from {file_path}, sheet {sheet_name}")
        
        try:
            # Read the statistics sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Read CSB data: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Convert statistics to event-like records
            events_df = self.convert_statistics_to_events(df, sheet_name)
            
            # Add office/division identifiers
            events_df['office'] = self.office_identifier
            events_df['division'] = self.division_identifier
            events_df['data_source'] = 'csb'
            
            # Log office assignment for debugging
            logger.info(f"CSB Processor: Assigned office name '{self.office_identifier}' to {len(events_df)} records")
            
            logger.info(f"Converted to {len(events_df)} event records")
            return events_df
            
        except Exception as e:
            logger.error(f"Error processing CSB data: {e}")
            # Return empty DataFrame with required columns
            return pd.DataFrame(columns=['event_name', 'date', 'attendee_count', 'office', 'division'])
    
    def convert_statistics_to_events(self, df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """
        Convert CSB statistics format to event records
        
        Args:
            df: DataFrame with CSB statistics (rows=activities, cols=days)
            sheet_name: Sheet name to extract month/year info
            
        Returns:
            DataFrame with event-like records
        """
        events_list = []
        
        # Extract month/year from sheet name (e.g., '25_Jan' -> 2025, January)
        month_year = self.parse_sheet_date(sheet_name)
        
        # Process each activity type (row)
        for _, row in df.iterrows():
            activity_name = row.get('Tracked Items')
            if pd.isna(activity_name) or not str(activity_name).strip():
                continue
                
            activity_name = str(activity_name).strip()
            
            # Look for daily counts in numeric columns
            for col in df.columns:
                if col == 'Tracked Items':
                    continue
                    
                # Check if this is a day column (numeric or 'Total')
                daily_count = row.get(col)
                
                if pd.notna(daily_count) and daily_count > 0:
                    try:
                        count_value = float(daily_count)
                        if count_value > 0:
                            # Create event record for this day/activity
                            if col == 'Total':
                                # Monthly summary
                                event_date = f"{month_year['year']}-{month_year['month']:02d}-01"
                                event_name = f"{activity_name} (Monthly Total)"
                            else:
                                # Daily count - try to parse day
                                try:
                                    day = int(col)
                                    if 1 <= day <= 31:
                                        event_date = f"{month_year['year']}-{month_year['month']:02d}-{day:02d}"
                                        event_name = f"{activity_name}"
                                    else:
                                        continue
                                except ValueError:
                                    continue
                            
                            events_list.append({
                                'event_name': event_name,
                                'date': event_date,
                                'attendee_count': int(count_value),
                                'description': f"CSB {activity_name} - Count: {int(count_value)}",
                                'location': 'Various',
                                'start_time': '08:00',
                                'end_time': '17:00',
                                'duration_hours': 8.0
                            })
                    except (ValueError, TypeError):
                        continue
        
        return pd.DataFrame(events_list)
    
    def parse_sheet_date(self, sheet_name: str) -> Dict[str, int]:
        """
        Parse sheet name to extract month/year
        
        Args:
            sheet_name: Sheet name like '25_Jan', '25_Feb', etc.
            
        Returns:
            Dict with 'year' and 'month' keys
        """
        month_map = {
            'Jan': 1, 'Feb': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
        
        try:
            # Split by underscore: '25_Jan' -> ['25', 'Jan']
            parts = sheet_name.split('_')
            if len(parts) >= 2:
                year_part = parts[0]
                month_part = parts[1]
                
                # Convert year: '25' -> 2025
                year = 2000 + int(year_part)
                
                # Convert month: 'Jan' -> 1
                month = month_map.get(month_part, 1)
                
                return {'year': year, 'month': month}
        except (ValueError, IndexError):
            pass
        
        # Default to current year, January
        current_year = datetime.now().year
        return {'year': current_year, 'month': 1}