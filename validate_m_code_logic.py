"""
Validate M Code Logic - Simulate the exact transformations
This script mimics the M code transformations to verify compatibility
"""

import pandas as pd
import numpy as np
from datetime import datetime
import glob

def simulate_m_code_transformations():
    """Simulate the exact M code transformations"""
    
    print("Simulating M Code Transformations")
    print("=" * 40)
    
    # 1. Read CSV (simulate Csv.Document + Table.PromoteHeaders)
    csv_files = glob.glob('output/community_engagement_data_*.csv')
    if not csv_files:
        print("No CSV files found")
        return
    
    latest_file = max(csv_files)
    print(f"Reading: {latest_file}")
    df = pd.read_csv(latest_file)
    print(f"Initial rows: {len(df)}")
    
    # 2. Date parsing (simulate DateParsed step)
    print("\n2. Date Parsing:")
    def parse_date(date_str):
        if pd.isna(date_str) or date_str == "":
            return None
        try:
            # DateTime.Date(DateTime.FromText(_))
            dt = datetime.fromisoformat(str(date_str).replace(' ', 'T'))
            return dt.date()
        except:
            try:
                # Date.FromText(Text.Start(_, 10))
                date_part = str(date_str)[:10]
                dt = datetime.strptime(date_part, '%Y-%m-%d')
                return dt.date()
            except:
                return None
    
    df['Date'] = df['date'].apply(parse_date)
    valid_dates = df['Date'].notna().sum()
    print(f"  Valid dates: {valid_dates}/{len(df)} ({valid_dates/len(df)*100:.1f}%)")
    
    # 3. Duration handling (simulate SafeDuration step)
    print("\n3. Duration Parsing:")
    def safe_duration(duration_val):
        if pd.isna(duration_val) or duration_val == "" or str(duration_val).lower() == 'nan':
            return 0.5
        try:
            num_val = float(duration_val)
            return num_val if num_val > 0 else 0.5
        except:
            return 0.5
    
    df['Event Duration (Hours)'] = df['duration_hours'].apply(safe_duration)
    duration_stats = df['Event Duration (Hours)'].describe()
    print(f"  Duration stats: min={duration_stats['min']}, max={duration_stats['max']}, mean={duration_stats['mean']:.2f}")
    
    # 4. Attendee count handling (simulate SafeAttendees step)  
    print("\n4. Attendee Count Parsing:")
    def safe_attendees(attendee_val):
        if pd.isna(attendee_val):
            return 1
        try:
            num_val = int(float(attendee_val))
            return num_val if num_val > 0 else 1
        except:
            return 1
    
    df['Number of Police Department Attendees'] = df['attendee_count'].apply(safe_attendees)
    attendee_stats = df['Number of Police Department Attendees'].describe()
    print(f"  Attendee stats: min={attendee_stats['min']}, max={attendee_stats['max']}, mean={attendee_stats['mean']:.1f}")
    
    # 5. Column selection and renaming (simulate SelectedColumns + RenamedColumns)
    print("\n5. Column Selection and Renaming:")
    final_columns = {
        'Date': df['Date'],
        'Event Duration (Hours)': df['Event Duration (Hours)'],
        'Event Name': df['event_name'],
        'Location of Event': df['location'],
        'Number of Police Department Attendees': df['Number of Police Department Attendees'],
        'Office': df['office']
    }
    
    final_df = pd.DataFrame(final_columns)
    
    # 6. Data filtering (simulate FilteredData)
    print("\n6. Data Filtering:")
    before_filter = len(final_df)
    final_df = final_df[final_df['Date'].notna()]
    after_filter = len(final_df)
    print(f"  Rows before null date filter: {before_filter}")
    print(f"  Rows after null date filter: {after_filter}")
    
    # 7. Duration validation (simulate ValidatedDuration)
    print("\n7. Duration Validation:")
    def validate_duration(duration_val):
        if pd.isna(duration_val) or duration_val <= 0:
            return 0.5
        elif duration_val > 24:
            return 8.0
        else:
            return round(duration_val, 2)
    
    final_df['Event Duration (Hours)'] = final_df['Event Duration (Hours)'].apply(validate_duration)
    
    # 8. Attendee validation (simulate ValidatedAttendees)
    print("\n8. Attendee Validation:")
    def validate_attendees(attendee_val):
        if pd.isna(attendee_val) or attendee_val <= 0:
            return 1
        else:
            return int(attendee_val)
    
    final_df['Number of Police Department Attendees'] = final_df['Number of Police Department Attendees'].apply(validate_attendees)
    
    # 9. Final sort (simulate FinalData)
    final_df = final_df.sort_values('Date')
    
    # Results
    print("\n" + "=" * 40)
    print("FINAL RESULTS")
    print("=" * 40)
    print(f"Total records: {len(final_df)}")
    print(f"Date range: {final_df['Date'].min()} to {final_df['Date'].max()}")
    print(f"Unique offices: {final_df['Office'].nunique()}")
    print(f"Office breakdown:")
    for office, count in final_df['Office'].value_counts().items():
        print(f"  - {office}: {count}")
    
    print(f"\nColumn validation:")
    required_columns = ['Date', 'Event Duration (Hours)', 'Event Name', 'Location of Event', 'Number of Police Department Attendees', 'Office']
    for col in required_columns:
        if col in final_df.columns:
            non_null = final_df[col].notna().sum()
            print(f"  ✓ {col}: {non_null}/{len(final_df)} non-null")
        else:
            print(f"  ✗ {col}: MISSING")
    
    print(f"\nSample final data:")
    print(final_df.head(3).to_string(index=False))
    
    print(f"\n[SUCCESS] M code logic simulation completed successfully!")
    print(f"[SUCCESS] Power BI will receive {len(final_df)} properly formatted records")

if __name__ == "__main__":
    simulate_m_code_transformations()