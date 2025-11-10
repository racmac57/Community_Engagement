"""
Debug Community Engagement ETL Processors
Identifies data processing discrepancies and validation issues
"""

import pandas as pd
import sys
import os
from datetime import datetime, time
import re

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from processors.community_engagement_processor import CommunityEngagementProcessor
from processors.stacp_processor import STACPProcessor
from processors.patrol_processor import PatrolProcessor
from processors.csb_processor import CSBProcessor
from utils.config_loader import ConfigLoader


def test_duration_calculation():
    """Test duration calculation with known values"""
    print("\n=== DURATION CALCULATION TEST ===")
    
    # Test cases: start_time, end_time, expected_hours
    test_cases = [
        ("19:00", "21:00", 2.0),
        ("09:00", "17:00", 8.0), 
        ("14:30", "16:15", 1.75),
        ("23:00", "01:00", 2.0),  # Cross-midnight
        ("08:00", "08:30", 0.5),
        (None, "17:00", 0.5),  # Missing start time
        ("09:00", None, 0.5),  # Missing end time
        ("", "", 0.5),  # Empty strings
    ]
    
    for start_str, end_str, expected in test_cases:
        print(f"\nTesting: {start_str} -> {end_str} (expected: {expected}h)")
        
        # Simulate processor logic
        try:
            if start_str and end_str and start_str != "" and end_str != "":
                if ":" in start_str and ":" in end_str:
                    start_parts = start_str.split(":")
                    end_parts = end_str.split(":")
                    
                    start_time = time(int(start_parts[0]), int(start_parts[1]))
                    end_time = time(int(end_parts[0]), int(end_parts[1]))
                    
                    # Convert to datetime for calculation
                    start_dt = datetime.combine(datetime.today(), start_time)
                    end_dt = datetime.combine(datetime.today(), end_time)
                    
                    # Handle cross-midnight
                    if end_dt <= start_dt:
                        end_dt = end_dt.replace(day=end_dt.day + 1)
                    
                    duration = (end_dt - start_dt).total_seconds() / 3600.0
                    calculated = round(duration, 2)
                else:
                    calculated = 0.5
            else:
                calculated = 0.5
                
            status = "[PASS]" if abs(calculated - expected) < 0.01 else "[FAIL]"
            print(f"  Result: {calculated}h {status}")
            
        except Exception as e:
            print(f"  ERROR: {e}")


def test_attendee_parsing():
    """Test attendee parsing with various formats"""
    print("\n=== ATTENDEE PARSING TEST ===")
    
    test_cases = [
        ("Smith, Jones", 2),
        ("Smith, Jones, Brown", 3),
        ("Smith/Jones", 2), 
        ("Smith & Jones", 2),
        ("Smith,Jones,Brown,Wilson", 4),
        ("Smith, Jones & Brown", 3),
        ("Smith", 1),
        ("", 0),
        (None, 0),
        ("Smith, , Jones", 2),  # Empty names should be filtered
        ("  Smith  ,  Jones  ", 2),  # Whitespace handling
        ("5", 5),  # Numeric count
    ]
    
    for attendee_str, expected in test_cases:
        print(f"\nTesting: '{attendee_str}' (expected: {expected})")
        
        try:
            if not attendee_str:
                calculated = 0
            elif str(attendee_str).isdigit():
                calculated = int(attendee_str)
            else:
                # Split by delimiters and count non-empty names
                attendees = re.split(r'[,/&;]', str(attendee_str))
                valid_attendees = [a.strip() for a in attendees if a.strip()]
                calculated = len(valid_attendees)
            
            status = "[PASS]" if calculated == expected else "[FAIL]"
            print(f"  Result: {calculated} {status}")
            
        except Exception as e:
            print(f"  ERROR: {e}")


def debug_processor_data(processor_name, processor_class, config):
    """Debug a specific processor with real data"""
    print(f"\n=== DEBUGGING {processor_name.upper()} PROCESSOR ===")
    
    try:
        processor = processor_class()
        file_path = config.get('file_path')
        sheet_name = config.get('sheet_name')
        
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            return
        
        print(f"[SUCCESS] File exists: {file_path}")
        print(f"[SUCCESS] Sheet: {sheet_name}")
        print(f"[SUCCESS] Office: {processor.office_identifier}")
        print(f"[SUCCESS] Division: {processor.division_identifier}")
        
        # Read raw Excel data first
        print("\n--- Raw Excel Data ---")
        raw_df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Raw data shape: {raw_df.shape}")
        
        # Show first few rows
        print("Raw columns:", list(raw_df.columns))
        print("Raw data sample:")
        print(raw_df.head(3).to_string())
        
        # Process with processor
        print(f"\n--- {processor_name} Processing ---")
        processed_df = processor.process_data_source(file_path, sheet_name)
        print(f"Processed data shape: {processed_df.shape}")
        
        if len(processed_df) > 0:
            print("Processed columns:", list(processed_df.columns))
            
            # Check key fields
            key_checks = {
                'event_name': processed_df['event_name'].notna().sum(),
                'date': processed_df['date'].notna().sum(),
                'duration_hours': processed_df.get('duration_hours', pd.Series()).notna().sum(),
                'attendee_count': processed_df.get('attendee_count', pd.Series()).notna().sum()
            }
            
            for field, count in key_checks.items():
                percentage = (count / len(processed_df)) * 100 if len(processed_df) > 0 else 0
                print(f"  {field}: {count}/{len(processed_df)} ({percentage:.1f}%)")
            
            print("Processed data sample:")
            sample_cols = ['event_name', 'date', 'duration_hours', 'attendee_count', 'office', 'division']
            available_cols = [col for col in sample_cols if col in processed_df.columns]
            print(processed_df[available_cols].head(3).to_string())
        else:
            print("[ERROR] No data processed")
            
    except Exception as e:
        print(f"[ERROR] Error processing {processor_name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main debugging function"""
    print("Community Engagement ETL - Processor Debugging")
    print("=" * 60)
    
    # Test core functions first
    test_duration_calculation()
    test_attendee_parsing()
    
    # Load configuration
    print(f"\n=== LOADING CONFIGURATION ===")
    try:
        config_loader = ConfigLoader('.')
        config = config_loader.load_config('config.json')
        sources = config.get('sources', {})
        print(f"[SUCCESS] Loaded {len(sources)} source configurations")
    except Exception as e:
        print(f"[ERROR] Configuration error: {e}")
        return
    
    # Debug each processor
    processors = [
        ('community_engagement', CommunityEngagementProcessor),
        ('stacp', STACPProcessor), 
        ('patrol', PatrolProcessor),
        ('csb', CSBProcessor)
    ]
    
    for proc_name, proc_class in processors:
        if proc_name in sources:
            source_config = sources[proc_name]
            if not source_config.get('disabled', False):
                debug_processor_data(proc_name, proc_class, source_config)
            else:
                print(f"\n=== {proc_name.upper()} PROCESSOR ===")
                print("[WARNING] Disabled in configuration")
        else:
            print(f"\n=== {proc_name.upper()} PROCESSOR ===")
            print("[WARNING] Not found in configuration")
    
    print(f"\n{'='*60}")
    print("DEBUGGING COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()