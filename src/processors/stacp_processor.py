"""
Community Engagement ETL - STACP Processor
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Process STACP (Special Teams and Community Policing) data
"""

import numpy as np
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.excel_processor import ExcelProcessor
from utils.logger_setup import get_project_logger
from utils.duration_utils import safe_duration_to_hours
from utils.attendee_utils import clean_and_count_attendees

logger = get_project_logger(__name__)


class STACPProcessor(ExcelProcessor):
    """Processor for STACP data source"""

    def __init__(self):
        super().__init__()
        self.office_identifier = "STA&CP"
        self.division_identifier = "STACP"

        # Source-specific column mappings
        self.column_mapping = {
            "School Outreach Conducted ": "event_name",
            "Date": "date",
            "Start Time": "start_time",
            "End Time": "end_time",
            "Location": "location",
            # Excel stores this as timedelta — must convert to float hours before CSV
            "Total Time": "pre_calculated_duration",
        }

        self.attendee_fields = [
            "Attendees",
            "Attendees2",
            "Attendees3",
            "Attendees4",
            "Attendees5",
            "Free Type Attendees",
        ]

    def process_data_source(self, file_path: str, sheet_name: str = "STACP Activities") -> pd.DataFrame:
        """
        Process STACP Excel data

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to process

        Returns:
            Processed DataFrame
        """
        logger.info(f"Processing STACP data from {file_path}")

        df = self.read_excel_source(file_path, sheet_name, {})
        df = self.standardize_columns(df, self.column_mapping)

        # Duration: prefer Total Time (timedelta from Excel); fall back to start/end delta
        if "pre_calculated_duration" in df.columns:
            primary_hours = df["pre_calculated_duration"].apply(
                lambda v: safe_duration_to_hours(v, default=np.nan)
            )
            alt_df = self.calculate_duration(df)
            df["duration_hours"] = primary_hours.combine_first(alt_df["duration_hours"]).fillna(0.5)
            df["duration_hours"] = df["duration_hours"].round(2)
            n_tt = df["pre_calculated_duration"].notna().sum()
            logger.info(
                f"STACP: duration from Total Time where present ({n_tt} rows with Total Time), "
                "else start/end time delta"
            )
        else:
            logger.warning("STACP: Total Time column missing; using start/end only")
            df = self.calculate_duration(df)
            df["duration_hours"] = df["duration_hours"].fillna(0.5).round(2)

        df = self.parse_attendees(df)

        df["office"] = self.office_identifier
        df["division"] = self.division_identifier

        logger.info(f"STACP Processor: Assigned office name '{self.office_identifier}' to {len(df)} records")

        required_fields = ["event_name", "date"]
        validation_results = self.validate_data(df, required_fields)

        logger.info(f"Processing complete: {validation_results['valid_rows']} valid rows")
        return df

    def parse_attendees(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Primary + Attendees2-5 + Free Type; slash/comma splits; PERSONNEL_ALIASES normalization.
        """
        result_df = df.copy()
        counts: List[int] = []
        names: List[str] = []

        for _, row in result_df.iterrows():
            c, n = clean_and_count_attendees(
                row,
                primary_col="Attendees",
                extra_cols=["Attendees2", "Attendees3", "Attendees4", "Attendees5"],
                free_type_col="Free Type Attendees",
            )
            counts.append(c)
            names.append(n)

        result_df["attendee_count"] = counts
        result_df["attendee_names"] = names

        return result_df
