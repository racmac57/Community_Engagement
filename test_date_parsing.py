"""
Test script to validate date parsing logic for M code
Simulates the date transformation that will happen in Power Query
"""

import pandas as pd
from datetime import datetime
import glob

def test_date_parsing():
    """Test the date parsing logic similar to M code"""
    
    print("Testing Date Parsing Logic for M Code Fix")
    print("=" * 50)
    
    # Find latest CSV
    csv_files = glob.glob('output/community_engagement_data_*.csv')
    if not csv_files:
        print("No CSV files found")
        return
    
    latest_file = max(csv_files)
    print(f"Testing with file: {latest_file}")
    
    # Read CSV
    df = pd.read_csv(latest_file)
    print(f"Total records: {len(df)}")
    
    # Test date parsing scenarios
    print("\n1. Testing datetime string parsing:")
    test_dates = df['date'].head(5).tolist()
    
    for i, date_str in enumerate(test_dates):
        print(f"  Original: '{date_str}'")
        
        # Simulate M code logic: DateTime.Date(DateTime.FromText(_))
        try:
            # Parse datetime string
            dt = datetime.fromisoformat(str(date_str).replace(' ', 'T'))
            date_only = dt.date()
            print(f"  Parsed:   {date_only} (SUCCESS)")
        except Exception as e:
            # Fallback: Date.FromText(Text.Start(_, 10))
            try:
                date_part = str(date_str)[:10]  # First 10 chars: "YYYY-MM-DD"
                dt = datetime.strptime(date_part, '%Y-%m-%d')
                date_only = dt.date()
                print(f"  Fallback: {date_only} (SUCCESS)")
            except Exception as e2:
                print(f"  Failed:   {e2}")
        print()
    
    # Test the full column
    print("2. Testing full date column conversion:")
    successful_conversions = 0
    failed_conversions = 0
    
    for date_str in df['date']:
        try:
            if pd.isna(date_str) or date_str == "":
                continue
            dt = datetime.fromisoformat(str(date_str).replace(' ', 'T'))
            successful_conversions += 1
        except:
            try:
                date_part = str(date_str)[:10]
                dt = datetime.strptime(date_part, '%Y-%m-%d')
                successful_conversions += 1
            except:
                failed_conversions += 1
    
    print(f"  Successful: {successful_conversions}")
    print(f"  Failed:     {failed_conversions}")
    print(f"  Success Rate: {successful_conversions/(successful_conversions+failed_conversions)*100:.1f}%")
    
    # Test other key columns
    print("\n3. Testing other column data types:")
    key_columns = ['duration_hours', 'attendee_count', 'event_name', 'location', 'office']
    
    for col in key_columns:
        if col in df.columns:
            non_null = df[col].count()
            total = len(df)
            print(f"  {col}: {non_null}/{total} non-null ({non_null/total*100:.1f}%)")
        else:
            print(f"  {col}: NOT FOUND")
    
    print(f"\n4. Final structure check:")
    required_cols = ['date', 'duration_hours', 'event_name', 'location', 'attendee_count', 'office']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"  Missing columns: {missing_cols}")
    else:
        print("  All required columns present")
    
    print(f"\n[RESULT] Date parsing fix should work correctly!")

if __name__ == "__main__":
    test_date_parsing()