#!/usr/bin/env python3
"""
Sample Office Distribution Analysis
Shows office name distribution by data source for debugging
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_office_distribution(csv_file_path: str):
    """
    Analyze office name distribution in the output CSV file
    
    Args:
        csv_file_path: Path to the CSV output file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file_path)
        
        print("=== Office Name Distribution Analysis ===")
        print(f"Total Records: {len(df)}")
        print()
        
        # Office distribution
        if 'office' in df.columns:
            office_counts = df['office'].value_counts()
            print("Office Name Distribution:")
            for office, count in office_counts.items():
                percentage = (count / len(df)) * 100
                print(f"  {office}: {count} records ({percentage:.1f}%)")
            print()
        
        # Data source distribution
        if 'data_source' in df.columns:
            source_counts = df['data_source'].value_counts()
            print("Data Source Distribution:")
            for source, count in source_counts.items():
                percentage = (count / len(df)) * 100
                print(f"  {source}: {count} records ({percentage:.1f}%)")
            print()
        
        # Cross-tabulation of office vs data_source
        if 'office' in df.columns and 'data_source' in df.columns:
            print("Office Name by Data Source:")
            crosstab = pd.crosstab(df['data_source'], df['office'], margins=True)
            print(crosstab)
            print()
        
        # Sample records from each office
        if 'office' in df.columns:
            print("Sample Records by Office:")
            for office in df['office'].unique():
                if pd.notna(office):
                    sample = df[df['office'] == office].head(2)
                    print(f"\n{office} (showing {len(sample)} of {len(df[df['office'] == office])} records):")
                    for idx, row in sample.iterrows():
                        event_name = row.get('event_name', 'N/A')
                        date = row.get('date', 'N/A')
                        data_source = row.get('data_source', 'N/A')
                        print(f"  - {event_name} ({date}) [Source: {data_source}]")
        
        # Check for any "Police Department" entries
        police_dept_count = 0
        if 'office' in df.columns:
            police_dept_count = df[df['office'].str.contains('Police Department', na=False)].shape[0]
        
        print(f"\n=== Police Department Check ===")
        print(f"Records with 'Police Department' in office field: {police_dept_count}")
        
        if police_dept_count == 0:
            print("✅ No 'Police Department' entries found in office field")
        else:
            print("❌ Found 'Police Department' entries in office field:")
            police_records = df[df['office'].str.contains('Police Department', na=False)]
            for idx, row in police_records.iterrows():
                print(f"  Row {idx}: {row.get('event_name', 'N/A')} - Office: {row.get('office', 'N/A')}")
        
    except Exception as e:
        print(f"Error analyzing file: {e}")

def main():
    """Main function to run the analysis"""
    # Look for the most recent output file
    output_dir = Path("src/output")
    if not output_dir.exists():
        output_dir = Path("output")
    
    if output_dir.exists():
        csv_files = list(output_dir.glob("community_engagement_data_*.csv"))
        if csv_files:
            # Get the most recent file
            latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
            print(f"Analyzing: {latest_file}")
            analyze_office_distribution(str(latest_file))
        else:
            print("No community engagement CSV files found in output directory")
    else:
        print("Output directory not found")

if __name__ == "__main__":
    main()
