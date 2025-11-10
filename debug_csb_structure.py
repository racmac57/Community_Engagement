"""
Debug script to inspect actual CSB sheet structure
Analyzes real column names and data format in csb_monthly.xlsm
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_csb_structure():
    """Inspect the actual CSB sheet structure"""
    
    # CSB file path from config
    csb_file = r"C:\Users\carucci_r\OneDrive - City of Hackensack\Shared Folder\Compstat\Contributions\CSB\csb_monthly.xlsm"
    sheet_name = "25_Jan"
    
    print("=" * 60)
    print("CSB SHEET STRUCTURE ANALYSIS")
    print("=" * 60)
    
    try:
        # Check if file exists
        if not Path(csb_file).exists():
            print(f"[ERROR] FILE NOT FOUND: {csb_file}")
            return
        
        print(f"[SUCCESS] File exists: {csb_file}")
        print(f"[INFO] Analyzing sheet: {sheet_name}")
        print()
        
        # Read Excel file
        print("Reading Excel file...")
        try:
            # First, get all sheet names
            excel_file = pd.ExcelFile(csb_file)
            print(f"[INFO] Available sheets: {excel_file.sheet_names}")
            print()
            
            if sheet_name not in excel_file.sheet_names:
                print(f"[ERROR] Sheet '{sheet_name}' not found!")
                print("Available sheets:")
                for sheet in excel_file.sheet_names:
                    print(f"  - {sheet}")
                return
            
            # Read the specific sheet
            df = pd.read_excel(csb_file, sheet_name=sheet_name)
            
        except Exception as e:
            print(f"[ERROR] Error reading Excel file: {e}")
            return
        
        print(f"[INFO] SHEET DIMENSIONS: {df.shape[0]} rows x {df.shape[1]} columns")
        print()
        
        # Print all column names
        print("[COLUMNS] ALL COLUMN NAMES:")
        print("-" * 40)
        for i, col in enumerate(df.columns, 1):
            print(f"{i:2d}. '{col}' (type: {df[col].dtype})")
        print()
        
        # Show first few rows
        print("[DATA] FIRST 5 ROWS OF DATA:")
        print("-" * 40)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        # Show just first 5 rows, all columns
        print(df.head())
        print()
        
        # Look for event-related columns
        print("[ANALYSIS] POTENTIAL EVENT-RELATED COLUMNS:")
        print("-" * 40)
        event_keywords = ['event', 'name', 'program', 'activity', 'date', 'time', 'location', 'venue', 'member', 'staff', 'attend']
        
        potential_cols = []
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in event_keywords:
                if keyword in col_lower:
                    potential_cols.append(col)
                    break
        
        if potential_cols:
            for col in potential_cols:
                print(f"  • '{col}'")
                # Show sample values for this column
                sample_values = df[col].dropna().head(3).tolist()
                if sample_values:
                    print(f"    Sample values: {sample_values}")
        else:
            print("  No obvious event-related columns found by keyword matching")
        print()
        
        # Check for date columns
        print("[ANALYSIS] DATE/TIME COLUMNS:")
        print("-" * 40)
        date_cols = []
        for col in df.columns:
            # Check if column contains date-like data
            try:
                sample_values = df[col].dropna().head()
                if not sample_values.empty:
                    # Try to parse as datetime
                    pd.to_datetime(sample_values, errors='coerce').dropna()
                    date_cols.append(col)
            except:
                pass
        
        if date_cols:
            for col in date_cols:
                print(f"  • '{col}'")
                sample_values = df[col].dropna().head(3).tolist()
                print(f"    Sample values: {sample_values}")
        else:
            print("  No obvious date/time columns detected")
        print()
        
        # Look for numeric columns that might be counts
        print("[ANALYSIS] NUMERIC COLUMNS (potential counts):")
        print("-" * 40)
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        for col in numeric_cols:
            non_null_count = df[col].count()
            if non_null_count > 0:
                sample_values = df[col].dropna().head(3).tolist()
                print(f"  • '{col}' - {non_null_count} non-null values")
                print(f"    Sample values: {sample_values}")
        print()
        
        # Show columns with most non-null data
        print("[ANALYSIS] COLUMNS BY DATA COMPLETENESS:")
        print("-" * 40)
        completeness = df.count().sort_values(ascending=False)
        for col, count in completeness.head(10).items():
            percentage = (count / len(df)) * 100
            print(f"  {count:2d}/{len(df)} ({percentage:5.1f}%) - '{col}'")
        
        print()
        print("=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_csb_structure()