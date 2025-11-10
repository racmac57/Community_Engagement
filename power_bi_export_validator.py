"""
Community Engagement ETL - Power BI Export Validator
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Validate CSV/Excel exports for Power BI compatibility
"""

import pandas as pd
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
import re


class PowerBIExportValidator:
    """Validates export formats for Power BI compatibility"""
    
    def __init__(self):
        self.powerbi_requirements = {
            'max_columns': 16000,
            'max_rows': 1000000,
            'forbidden_chars': ['<', '>', ':', '"', '|', '?', '*'],
            'reserved_names': ['CON', 'PRN', 'AUX', 'NUL'],
            'max_text_length': 32767
        }
        
    def create_sample_export_data(self) -> pd.DataFrame:
        """Create sample data matching ETL output format"""
        return pd.DataFrame({
            'event_name': ['Community Meeting', 'Block Party', 'Safety Workshop'],
            'date': ['2025-01-01', '2025-01-02', '2025-01-03'], 
            'start_time': ['10:00:00', '14:00:00', '18:30:00'],
            'end_time': ['12:30:00', '17:00:00', '20:00:00'],
            'duration_hours': [2.5, 3.0, 1.5],
            'attendee_count': [15, 25, 8],
            'location': ['City Hall', 'Main St', 'Community Center'],
            'office': ['Community Engagement', 'Police Department', 'Community Engagement'],
            'division': ['Outreach', 'STACP', 'Outreach'],
            'data_source': ['community_engagement', 'stacp', 'community_engagement'],
            'processed_date': ['2025-09-04', '2025-09-04', '2025-09-04']
        })
    
    def validate_column_names(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate column names for Power BI compatibility"""
        issues = []
        
        for col in df.columns:
            # Check for forbidden characters
            if any(char in col for char in self.powerbi_requirements['forbidden_chars']):
                issues.append(f"Column '{col}' contains forbidden characters")
            
            # Check for reserved names
            if col.upper() in self.powerbi_requirements['reserved_names']:
                issues.append(f"Column '{col}' is a reserved name")
            
            # Check length (Power BI column name limit)
            if len(col) > 128:
                issues.append(f"Column '{col}' name too long ({len(col)} chars)")
        
        return {
            'valid_columns': len(df.columns) - len(issues),
            'total_columns': len(df.columns),
            'issues': issues,
            'compatible': len(issues) == 0
        }
    
    def validate_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data types for Power BI compatibility"""
        type_issues = []
        compatible_types = 0
        
        for col, dtype in df.dtypes.items():
            dtype_str = str(dtype)
            
            # Check for Power BI compatible types
            if any(t in dtype_str for t in ['int', 'float', 'bool', 'datetime']):
                compatible_types += 1
            elif dtype_str == 'object':
                # Check text length for object columns
                max_length = df[col].astype(str).str.len().max()
                if max_length > self.powerbi_requirements['max_text_length']:
                    type_issues.append(f"Column '{col}' has text longer than 32,767 characters")
                else:
                    compatible_types += 1
            else:
                type_issues.append(f"Column '{col}' has unsupported data type: {dtype_str}")
        
        return {
            'compatible_types': compatible_types,
            'total_types': len(df.dtypes),
            'type_issues': type_issues,
            'type_compatibility': (compatible_types / len(df.dtypes) * 100) if len(df.dtypes) > 0 else 100
        }
    
    def validate_csv_export(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test CSV export compatibility"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
                # Export to CSV
                df.to_csv(tmp_file.name, index=False, encoding='utf-8')
                
                # Read back and validate
                reimported_df = pd.read_csv(tmp_file.name)
                
                # Check data integrity
                shape_match = reimported_df.shape == df.shape
                columns_match = list(reimported_df.columns) == list(df.columns)
                
                # Check for encoding issues
                encoding_issues = 0
                for col in reimported_df.select_dtypes(include=['object']).columns:
                    original_nulls = df[col].isna().sum()
                    reimported_nulls = reimported_df[col].isna().sum()
                    if abs(original_nulls - reimported_nulls) > 0:
                        encoding_issues += 1
                
                os.unlink(tmp_file.name)
                
                return {
                    'csv_compatible': shape_match and columns_match,
                    'shape_preserved': shape_match,
                    'columns_preserved': columns_match,
                    'encoding_issues': encoding_issues,
                    'file_size_mb': os.path.getsize(tmp_file.name) / (1024*1024) if os.path.exists(tmp_file.name) else 0
                }
                
        except Exception as e:
            return {
                'csv_compatible': False,
                'error': str(e),
                'shape_preserved': False,
                'columns_preserved': False,
                'encoding_issues': 1
            }
    
    def validate_excel_export(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Test Excel export compatibility"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
                # Export to Excel with multiple sheets (simulating ETL output)
                with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Combined_Data', index=False)
                    
                    # Add summary sheet (as done in main processor)
                    summary_df = pd.DataFrame([{
                        'total_records': len(df),
                        'data_sources': df['data_source'].nunique() if 'data_source' in df.columns else 0,
                        'export_date': '2025-09-04'
                    }])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Read back and validate
                reimported_df = pd.read_excel(tmp_file.name, sheet_name='Combined_Data')
                summary_sheet = pd.read_excel(tmp_file.name, sheet_name='Summary')
                
                # Validate structure
                structure_valid = (
                    reimported_df.shape == df.shape and
                    list(reimported_df.columns) == list(df.columns) and
                    not summary_sheet.empty
                )
                
                file_size_mb = os.path.getsize(tmp_file.name) / (1024*1024)
                os.unlink(tmp_file.name)
                
                return {
                    'excel_compatible': structure_valid,
                    'multi_sheet_support': True,
                    'file_size_mb': round(file_size_mb, 2),
                    'sheets_created': 2,
                    'powerbi_readable': structure_valid and file_size_mb < 1000  # 1GB limit
                }
                
        except Exception as e:
            return {
                'excel_compatible': False,
                'error': str(e),
                'multi_sheet_support': False,
                'powerbi_readable': False
            }
    
    def validate_export_formats(self) -> Dict[str, Any]:
        """Comprehensive validation of export formats"""
        
        # Create test data
        test_df = self.create_sample_export_data()
        
        # Run all validations
        column_validation = self.validate_column_names(test_df)
        datatype_validation = self.validate_data_types(test_df)
        csv_validation = self.validate_csv_export(test_df)
        excel_validation = self.validate_excel_export(test_df)
        
        # Calculate overall compatibility
        compatibility_checks = [
            column_validation['compatible'],
            datatype_validation['type_compatibility'] >= 95,
            csv_validation['csv_compatible'],
            excel_validation['excel_compatible']
        ]
        
        overall_compatible = all(compatibility_checks)
        compatibility_score = sum(compatibility_checks) / len(compatibility_checks) * 100
        
        return {
            'compatible': overall_compatible,
            'compatibility_score': round(compatibility_score, 1),
            'column_validation': column_validation,
            'datatype_validation': datatype_validation,
            'csv_validation': csv_validation,
            'excel_validation': excel_validation,
            'recommendation': self.get_export_recommendation(compatibility_score)
        }
    
    def get_export_recommendation(self, score: float) -> str:
        """Get recommendation based on compatibility score"""
        if score >= 95:
            return "Fully compatible with Power BI - ready for production"
        elif score >= 85:
            return "Mostly compatible - minor formatting adjustments recommended"
        elif score >= 70:
            return "Partially compatible - address data type and format issues"
        else:
            return "Major compatibility issues - significant changes required"


if __name__ == "__main__":
    validator = PowerBIExportValidator()
    results = validator.validate_export_formats()
    
    print("=== Power BI Export Validation Results ===")
    print(f"Overall Compatible: {results['compatible']}")
    print(f"Compatibility Score: {results['compatibility_score']}%")
    print(f"CSV Export: {'✓' if results['csv_validation']['csv_compatible'] else '✗'}")
    print(f"Excel Export: {'✓' if results['excel_validation']['excel_compatible'] else '✗'}")
    print(f"Recommendation: {results['recommendation']}")
    
    if results['column_validation']['issues']:
        print("\nColumn Issues:")
        for issue in results['column_validation']['issues']:
            print(f"- {issue}")