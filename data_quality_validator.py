"""
Community Engagement ETL - Data Quality Validator
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Cross-source validation and data quality assessment
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import tempfile


class DataQualityValidator:
    """Validates data quality across all sources"""
    
    def __init__(self):
        self.quality_thresholds = {
            'completeness': 85,  # % of required fields filled
            'consistency': 90,   # % of data format consistency
            'accuracy': 80,      # % of valid data values
            'uniqueness': 95     # % of unique records
        }
        self.critical_fields = ['event_name', 'date', 'office', 'division']
    
    def validate_data_completeness(self, df: pd.DataFrame) -> Dict[str, float]:
        """Check completeness of critical fields"""
        if df.empty:
            return {'completeness_score': 0, 'missing_critical': 100}
        
        total_cells = len(df) * len(self.critical_fields)
        missing_cells = 0
        
        for field in self.critical_fields:
            if field in df.columns:
                missing_cells += df[field].isna().sum()
            else:
                missing_cells += len(df)  # Entire column missing
        
        completeness_score = ((total_cells - missing_cells) / total_cells * 100) if total_cells > 0 else 0
        
        return {
            'completeness_score': round(completeness_score, 1),
            'missing_critical': round((missing_cells / total_cells * 100), 1) if total_cells > 0 else 100
        }
    
    def validate_data_consistency(self, df: pd.DataFrame) -> Dict[str, float]:
        """Check format consistency across records"""
        consistency_issues = 0
        total_checks = 0
        
        # Date format consistency
        if 'date' in df.columns:
            date_formats = df['date'].dropna().apply(lambda x: type(x).__name__)
            total_checks += len(date_formats)
            if len(date_formats.unique()) > 1:
                consistency_issues += len(date_formats) - date_formats.value_counts().iloc[0]
        
        # Duration value consistency (should be numeric)
        if 'duration_hours' in df.columns:
            duration_values = df['duration_hours'].dropna()
            total_checks += len(duration_values)
            non_numeric = sum(1 for val in duration_values if not isinstance(val, (int, float)))
            consistency_issues += non_numeric
        
        # Attendee count consistency (should be numeric)
        if 'attendee_count' in df.columns:
            attendee_values = df['attendee_count'].dropna()
            total_checks += len(attendee_values)
            non_numeric = sum(1 for val in attendee_values if not isinstance(val, (int, float)) or val < 0)
            consistency_issues += non_numeric
        
        consistency_score = ((total_checks - consistency_issues) / total_checks * 100) if total_checks > 0 else 100
        
        return {
            'consistency_score': round(consistency_score, 1),
            'format_issues': consistency_issues,
            'total_checked': total_checks
        }
    
    def validate_data_accuracy(self, df: pd.DataFrame) -> Dict[str, float]:
        """Check data accuracy and logical validity"""
        accuracy_issues = 0
        total_validations = 0
        
        # Duration logical validation (0-24 hours reasonable)
        if 'duration_hours' in df.columns:
            durations = df['duration_hours'].dropna()
            total_validations += len(durations)
            invalid_durations = sum(1 for d in durations if not (0 <= d <= 24))
            accuracy_issues += invalid_durations
        
        # Attendee count logical validation (0-1000 reasonable)
        if 'attendee_count' in df.columns:
            counts = df['attendee_count'].dropna()
            total_validations += len(counts)
            invalid_counts = sum(1 for c in counts if not (0 <= c <= 1000))
            accuracy_issues += invalid_counts
        
        # Date logical validation (within reasonable range)
        if 'date' in df.columns:
            try:
                dates = pd.to_datetime(df['date'], errors='coerce').dropna()
                total_validations += len(dates)
                current_year = datetime.now().year
                invalid_dates = sum(1 for d in dates if not (2020 <= d.year <= current_year + 1))
                accuracy_issues += invalid_dates
            except:
                accuracy_issues += len(df)
        
        accuracy_score = ((total_validations - accuracy_issues) / total_validations * 100) if total_validations > 0 else 100
        
        return {
            'accuracy_score': round(accuracy_score, 1),
            'logical_issues': accuracy_issues,
            'total_validated': total_validations
        }
    
    def validate_uniqueness(self, df: pd.DataFrame) -> Dict[str, float]:
        """Check for duplicate records"""
        if df.empty:
            return {'uniqueness_score': 100, 'duplicate_count': 0}
        
        # Check duplicates based on key fields
        key_fields = ['event_name', 'date', 'office', 'division']
        available_keys = [field for field in key_fields if field in df.columns]
        
        if not available_keys:
            return {'uniqueness_score': 100, 'duplicate_count': 0}
        
        duplicate_count = df.duplicated(subset=available_keys).sum()
        uniqueness_score = ((len(df) - duplicate_count) / len(df) * 100) if len(df) > 0 else 100
        
        return {
            'uniqueness_score': round(uniqueness_score, 1),
            'duplicate_count': duplicate_count
        }
    
    def run_cross_source_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation across all data sources"""
        
        # Create sample combined dataset for testing
        sample_data = pd.DataFrame({
            'event_name': ['Meeting A', 'Event B', 'Program C', ''],
            'date': ['2025-01-01', '2025-01-02', 'invalid_date', '2025-01-04'],
            'duration_hours': [2.0, 1.5, -1.0, 25.0],  # Invalid: negative and >24
            'attendee_count': [15, 20, 1500, 5],  # Invalid: >1000
            'office': ['Police', 'Community', 'Police', 'Community'],
            'division': ['STACP', 'Engagement', 'Patrol', '']
        })
        
        # Run all validation checks
        completeness = self.validate_data_completeness(sample_data)
        consistency = self.validate_data_consistency(sample_data)
        accuracy = self.validate_data_accuracy(sample_data)
        uniqueness = self.validate_uniqueness(sample_data)
        
        # Calculate overall score
        scores = [
            completeness['completeness_score'],
            consistency['consistency_score'], 
            accuracy['accuracy_score'],
            uniqueness['uniqueness_score']
        ]
        overall_score = sum(scores) / len(scores)
        
        return {
            'overall_score': round(overall_score, 1),
            'completeness': completeness,
            'consistency': consistency,
            'accuracy': accuracy,
            'uniqueness': uniqueness,
            'recommendation': self.get_quality_recommendation(overall_score)
        }
    
    def get_quality_recommendation(self, score: float) -> str:
        """Get recommendation based on quality score"""
        if score >= 90:
            return "Excellent data quality - ready for production"
        elif score >= 80:
            return "Good data quality - minor issues to address"
        elif score >= 70:
            return "Fair data quality - review and fix critical issues"
        else:
            return "Poor data quality - major cleanup required before use"


if __name__ == "__main__":
    validator = DataQualityValidator()
    results = validator.run_cross_source_validation()
    
    print("=== Data Quality Validation Results ===")
    print(f"Overall Score: {results['overall_score']}%")
    print(f"Recommendation: {results['recommendation']}")
    print(f"Completeness: {results['completeness']['completeness_score']}%")
    print(f"Consistency: {results['consistency']['consistency_score']}%")
    print(f"Accuracy: {results['accuracy']['accuracy_score']}%")
    print(f"Uniqueness: {results['uniqueness']['uniqueness_score']}%")