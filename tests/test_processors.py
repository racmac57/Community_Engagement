"""
Community Engagement ETL - Testing and Validation Framework
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Test processors with sample data and generate validation reports
"""

import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.processors.community_engagement_processor import CommunityEngagementProcessor
from src.processors.stacp_processor import STACPProcessor
from src.processors.patrol_processor import PatrolProcessor
from src.processors.csb_processor import CSBProcessor


class ProcessorTester:
    """Testing framework for all processors"""
    
    def __init__(self):
        self.processors = {
            'community_engagement': CommunityEngagementProcessor(),
            'stacp': STACPProcessor(),
            'patrol': PatrolProcessor(),
            'csb': CSBProcessor()
        }
        self.test_results = {}
    
    def generate_sample_data(self, processor_type: str) -> pd.DataFrame:
        """Generate sample data for testing"""
        base_date = datetime(2025, 1, 1)
        
        if processor_type == 'community_engagement':
            return pd.DataFrame({
                'Event Name': ['Community Meeting', 'Block Party', 'Safety Workshop'],
                'Event Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
                'Start Time': ['10:00', '14:00', '18:00'],
                'End Time': ['12:00', '16:00', '20:00'],
                'Attendees': ['John, Jane, Bob', 'Mary/Tom & Lisa', '15'],
                'Members Present': ['Officer Smith, Chief Jones', '', 'Sgt. Wilson']
            })
        elif processor_type == 'stacp':
            return pd.DataFrame({
                'Activity': ['Community Walk', 'Youth Program', 'Senior Meeting'],
                'Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
                'Time Start': ['09:00', '13:00', '15:00'],
                'Time End': ['11:00', '15:00', '17:00'],
                'Officer': ['Officer A', 'Officer B', 'Officer C'],
                'Participants': ['8', 'Smith/Jones & Brown', '12'],
                'Community Members': ['10', '5', 'Wilson, Davis, Lee']
            })
        elif processor_type == 'patrol':
            return pd.DataFrame({
                'Event Type': ['Community Contact', 'Business Check', 'School Visit'],
                'Event Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
                'Start': ['08:00', '12:00', '16:00'],
                'End': ['10:00', '14:00', '18:00'],
                'Beat': ['Beat 1', 'Beat 2', 'Beat 3'],
                'Officers': ['123 456', '789', '101 102 103'],
                'Citizens': ['5', 'Manager & Staff', 'Principal, Teachers']
            })
        else:  # csb
            return pd.DataFrame({
                'Program Name': ['Youth Basketball', 'Senior Center', 'Community Garden'],
                'Program Date': ['2025-01-01', '2025-01-02', '2025-01-03'],
                'Start Time': ['10:00', '14:00', '09:00'],
                'End Time': ['12:00', '16:00', '11:00'],
                'Staff': ['Coach A, Coach B', 'Director', 'Volunteer C & D'],
                'Volunteers': ['2', 'Helper 1/Helper 2', ''],
                'Participants': ['20', '15', '8']
            })
    
    def test_file_access(self, processor_type: str) -> dict:
        """Test file access validation"""
        processor = self.processors[processor_type]
        sample_data = self.generate_sample_data(processor_type)
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            sample_data.to_excel(tmp_file.name, index=False, sheet_name='Test')
            
            try:
                result = processor.read_excel_source(tmp_file.name, 'Test', {})
                os.unlink(tmp_file.name)
                return {'status': 'PASS', 'rows_read': len(result)}
            except Exception as e:
                os.unlink(tmp_file.name)
                return {'status': 'FAIL', 'error': str(e)}
    
    def test_column_mapping(self, processor_type: str) -> dict:
        """Test column mapping accuracy"""
        processor = self.processors[processor_type]
        sample_data = self.generate_sample_data(processor_type)
        
        try:
            mapped_data = processor.standardize_columns(sample_data, processor.column_mapping)
            expected_cols = {'event_name', 'date', 'start_time', 'end_time', 'attendee_count', 'duration_hours'}
            actual_cols = set(mapped_data.columns)
            
            return {
                'status': 'PASS' if expected_cols.issubset(actual_cols) else 'FAIL',
                'mapped_columns': len(processor.column_mapping),
                'standard_columns_present': len(expected_cols.intersection(actual_cols))
            }
        except Exception as e:
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_duration_calculation(self, processor_type: str) -> dict:
        """Test duration calculation correctness"""
        processor = self.processors[processor_type]
        sample_data = self.generate_sample_data(processor_type)
        mapped_data = processor.standardize_columns(sample_data, processor.column_mapping)
        
        try:
            result = processor.calculate_duration(mapped_data)
            calculated_durations = result['duration_hours'].dropna()
            
            return {
                'status': 'PASS' if len(calculated_durations) > 0 else 'FAIL',
                'calculated_count': len(calculated_durations),
                'avg_duration': round(calculated_durations.mean(), 2) if len(calculated_durations) > 0 else 0
            }
        except Exception as e:
            return {'status': 'FAIL', 'error': str(e)}
    
    def test_attendee_counting(self, processor_type: str) -> dict:
        """Test attendee counting logic"""
        processor = self.processors[processor_type]
        sample_data = self.generate_sample_data(processor_type)
        mapped_data = processor.standardize_columns(sample_data, processor.column_mapping)
        
        try:
            result = processor.parse_attendees(mapped_data)
            attendee_counts = result['attendee_count'].dropna()
            
            return {
                'status': 'PASS' if len(attendee_counts) > 0 else 'FAIL',
                'events_with_counts': len(attendee_counts),
                'total_attendees': int(attendee_counts.sum()) if len(attendee_counts) > 0 else 0,
                'avg_per_event': round(attendee_counts.mean(), 1) if len(attendee_counts) > 0 else 0
            }
        except Exception as e:
            return {'status': 'FAIL', 'error': str(e)}
    
    def run_all_tests(self) -> dict:
        """Run all test cases and generate validation report"""
        print("=== Community Engagement ETL Testing Framework ===\n")
        
        for processor_type in self.processors.keys():
            print(f"Testing {processor_type.upper()} Processor:")
            
            # Run test cases
            tests = {
                'File Access': self.test_file_access(processor_type),
                'Column Mapping': self.test_column_mapping(processor_type),
                'Duration Calculation': self.test_duration_calculation(processor_type),
                'Attendee Counting': self.test_attendee_counting(processor_type)
            }
            
            # Store results
            self.test_results[processor_type] = tests
            
            # Display results
            for test_name, result in tests.items():
                status = result['status']
                print(f"  {test_name}: {status}")
                if status == 'PASS':
                    if 'rows_read' in result:
                        print(f"    - Read {result['rows_read']} rows successfully")
                    if 'mapped_columns' in result:
                        print(f"    - Mapped {result['mapped_columns']} columns")
                    if 'calculated_count' in result:
                        print(f"    - Calculated {result['calculated_count']} durations (avg: {result['avg_duration']}h)")
                    if 'total_attendees' in result:
                        print(f"    - Counted {result['total_attendees']} total attendees (avg: {result['avg_per_event']}/event)")
                else:
                    print(f"    - Error: {result.get('error', 'Unknown error')}")
            print()
        
        return self.test_results


if __name__ == "__main__":
    tester = ProcessorTester()
    results = tester.run_all_tests()
    
    # Summary
    total_tests = sum(len(tests) for tests in results.values())
    passed_tests = sum(1 for tests in results.values() for test in tests.values() if test['status'] == 'PASS')
    
    print(f"=== Test Summary ===")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")