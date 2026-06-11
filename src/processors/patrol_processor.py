"""
Community Engagement ETL - Patrol Processor (v2)
Author: Claude AI Assistant
Updated: 2026-03-05 EST
Purpose: Process Patrol Division community engagement data

Changelog (v2):
- Enhanced parse_attendees() to strip rank prefixes (PO, Sgt, Lt, Det, Cpl, Ofc)
- Standardized delimiter handling: comma, slash, ampersand, semicolon, " and "
- Added name normalization for consistent unique-person identification
- Added fallback logic: if attendee field is empty but event data exists -> count as 1
- Improved edge case handling for non-name entries (e.g., "Squad formation")
"""

import pandas as pd
import re
from typing import Dict, List, Any, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.excel_processor import ExcelProcessor
from utils.logger_setup import get_project_logger

logger = get_project_logger(__name__)

# Rank prefixes to strip (case-insensitive)
RANK_PREFIXES = re.compile(
    r"^(?:PO|Sgt|Lt|Det|Cpl|Ofc|Officer|Sergeant|Lieutenant|Detective|Corporal)\.?\s+",
    re.IGNORECASE,
)

# Delimiters: comma, slash, ampersand, semicolon, and the word " and "
MULTI_NAME_SPLIT = re.compile(r"\s*[,/&;]\s*|\s+and\s+", re.IGNORECASE)

# Entries that are NOT person names
NON_NAME_ENTRIES = {
    "squad formation",
    "n/a",
    "none",
    "tbd",
    "unknown",
}


def normalize_name(raw_name: str) -> str:
    name = raw_name.strip()
    if not name:
        return ""
    name = RANK_PREFIXES.sub("", name).strip()
    name = re.sub(r"^([A-Za-z])\.([^\s])", r"\1. \2", name)
    return name


def parse_patrol_field(text: str) -> Tuple[List[str], int]:
    if not text or not str(text).strip():
        return ([], 0)
    text = str(text).strip()
    if text.isdigit():
        return ([], int(text))
    if text.lower() in NON_NAME_ENTRIES:
        logger.debug(f"Non-name entry detected: '{text}' -> count 0 (fallback applies)")
        return ([text], 0)
    raw_parts = MULTI_NAME_SPLIT.split(text)
    names = [normalize_name(p) for p in raw_parts if normalize_name(p)]
    return (names, len(names))


class PatrolProcessor(ExcelProcessor):

    def __init__(self):
        super().__init__()
        self.office_identifier = "Patrol"
        self.division_identifier = "Patrol"
        self.column_mapping = {
            "Event Type": "event_name",
            "Date": "date",
            "Start Time": "start_time",
            "End Time": "end_time",
            "Event Location": "location",
        }
        self.attendee_fields = ["Patrol Members Assigned"]

    def process_data_source(
        self, file_path: str, sheet_name: str = "Main_Outreach_Combined"
    ) -> pd.DataFrame:
        logger.info(f"Processing Patrol data from {file_path}")
        df = self.read_excel_source(file_path, sheet_name, {})
        df = self.standardize_columns(df, self.column_mapping)
        df = self.parse_attendees(df)
        df = self.calculate_duration(df)
        df["office"] = self.office_identifier
        df["division"] = self.division_identifier
        logger.info(f"Patrol Processor: Assigned office '{self.office_identifier}' to {len(df)} records")
        required_fields = ["event_name", "date"]
        validation_results = self.validate_data(df, required_fields)
        logger.info(f"Processing complete: {validation_results['valid_rows']} valid rows")
        return df

    def parse_attendees(self, df: pd.DataFrame) -> pd.DataFrame:
        result_df = df.copy()
        attendee_counts = []
        attendee_name_lists = []

        for idx, row in result_df.iterrows():
            total_attendees = 0
            all_names: List[str] = []

            for field in self.attendee_fields:
                if field in result_df.columns and pd.notna(row[field]):
                    raw_text = str(row[field]).strip()
                    if raw_text:
                        names, count = parse_patrol_field(raw_text)
                        all_names.extend(names)
                        total_attendees += count

            # Fallback: if count is 0 but row has event data, assume 1
            if total_attendees == 0:
                has_date = pd.notna(row.get("date"))
                has_event = pd.notna(row.get("event_name")) and str(row.get("event_name", "")).strip() != ""
                has_location = pd.notna(row.get("location")) and str(row.get("location", "")).strip() != ""
                if has_date and has_event and has_location:
                    total_attendees = 1
                    logger.debug(f"Row {idx}: attendee field empty but event data present -> defaulting to 1")

            attendee_counts.append(total_attendees)
            attendee_name_lists.append(", ".join(all_names) if all_names else "")

        result_df["attendee_count"] = attendee_counts
        result_df["attendee_names"] = attendee_name_lists

        zero_count = sum(1 for c in attendee_counts if c == 0)
        multi_count = sum(1 for c in attendee_counts if c > 1)
        logger.info(f"Attendee parsing complete: {len(attendee_counts)} rows, {multi_count} multi-person entries, {zero_count} rows with count=0")

        return result_df
