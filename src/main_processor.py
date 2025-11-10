"""
Community Engagement ETL - Main Processing Script
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Orchestrate all data processing, validation, and reporting
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import shutil
import os
from typing import Dict, List, Any, Optional

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from processors.community_engagement_processor import CommunityEngagementProcessor
from processors.stacp_processor import STACPProcessor
from processors.patrol_processor import PatrolProcessor
from processors.csb_processor import CSBProcessor
from utils.logger_setup import setup_logger, log_operation_start, log_operation_end
from utils.config_loader import ConfigLoader
from utils.data_validator import ValidationError

logger = setup_logger('main_processor')


class MainProcessor:
    """Main processor orchestrating all data sources"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize main processor with configuration"""
        self.config_loader = ConfigLoader(config_dir)
        self.processors = {
            'community_engagement': CommunityEngagementProcessor(),
            'stacp': STACPProcessor(),
            'patrol': PatrolProcessor(),
            'csb': CSBProcessor()
        }
        self.processed_data = {}
        self.processing_summary = {
            'start_time': None,
            'end_time': None,
            'sources_processed': 0,
            'total_records': 0,
            'validation_results': {},
            'errors': []
        }
    
    def backup_files(self, file_paths: List[str], backup_dir: str = 'backups') -> bool:
        """Create backup copies of original files"""
        log_operation_start(logger, "backup_files", files=len(file_paths))
        
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for file_path in file_paths:
                source_file = Path(file_path)
                if source_file.exists():
                    backup_file = backup_path / f"{source_file.stem}_{timestamp}{source_file.suffix}"
                    shutil.copy2(source_file, backup_file)
                    logger.info(f"Backed up: {source_file} -> {backup_file}")
                else:
                    logger.warning(f"Source file not found for backup: {file_path}")
            
            log_operation_end(logger, "backup_files", True, backed_up=len(file_paths))
            return True
            
        except Exception as e:
            log_operation_end(logger, "backup_files", False, error=str(e))
            self.processing_summary['errors'].append(f"Backup failed: {e}")
            return False
    
    def process_all_sources(self, source_configs: Dict[str, Dict]) -> Dict[str, pd.DataFrame]:
        """Run all individual processors"""
        log_operation_start(logger, "process_all_sources", sources=len(source_configs))
        self.processing_summary['start_time'] = datetime.now()
        
        for source_name, config in source_configs.items():
            try:
                # Skip disabled sources
                if config.get('disabled', False):
                    logger.info(f"Skipping disabled source: {source_name}")
                    continue
                    
                logger.info(f"Processing {source_name}...")
                
                if source_name not in self.processors:
                    error_msg = f"No processor found for source: {source_name}"
                    logger.error(error_msg)
                    self.processing_summary['errors'].append(error_msg)
                    continue
                
                processor = self.processors[source_name]
                file_path = config.get('file_path')
                sheet_name = config.get('sheet_name', 'Sheet1')
                
                if not file_path or not Path(file_path).exists():
                    error_msg = f"File not found for {source_name}: {file_path}"
                    logger.error(error_msg)
                    self.processing_summary['errors'].append(error_msg)
                    continue
                
                # Process the data source
                processed_df = processor.process_data_source(file_path, sheet_name)
                self.processed_data[source_name] = processed_df
                
                # Update summary
                self.processing_summary['sources_processed'] += 1
                self.processing_summary['total_records'] += len(processed_df)
                
                logger.info(f"Successfully processed {source_name}: {len(processed_df)} records")
                
            except Exception as e:
                error_msg = f"Failed to process {source_name}: {e}"
                logger.error(error_msg)
                self.processing_summary['errors'].append(error_msg)
        
        log_operation_end(logger, "process_all_sources", True, 
                         sources_processed=self.processing_summary['sources_processed'])
        return self.processed_data
    
    def combine_data(self) -> pd.DataFrame:
        """Merge all sources into standardized format"""
        log_operation_start(logger, "combine_data", sources=len(self.processed_data))
        
        try:
            if not self.processed_data:
                raise ValidationError("No processed data available to combine")
            
            combined_dfs = []
            for source_name, df in self.processed_data.items():
                # Add source identifier
                df_copy = df.copy()
                df_copy['data_source'] = source_name
                df_copy['processed_date'] = datetime.now().strftime('%Y-%m-%d')
                combined_dfs.append(df_copy)
            
            # Combine all dataframes
            combined_df = pd.concat(combined_dfs, ignore_index=True, sort=False)
            
            # Validate combined data
            validation_results = self.validate_combined_data(combined_df)
            self.processing_summary['validation_results'] = validation_results
            
            log_operation_end(logger, "combine_data", True, total_records=len(combined_df))
            return combined_df
            
        except Exception as e:
            log_operation_end(logger, "combine_data", False, error=str(e))
            self.processing_summary['errors'].append(f"Data combination failed: {e}")
            raise
    
    def validate_combined_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data consistency between sources"""
        validation = {
            'total_records': len(df),
            'date_range': {},
            'source_breakdown': df['data_source'].value_counts().to_dict() if 'data_source' in df.columns else {},
            'missing_critical_fields': 0,
            'data_quality_score': 0
        }
        
        # Try to get date range safely
        if 'date' in df.columns:
            try:
                # Convert dates to datetime and get min/max
                date_series = pd.to_datetime(df['date'], errors='coerce').dropna()
                if not date_series.empty:
                    validation['date_range'] = {
                        'start': date_series.min().strftime('%Y-%m-%d'),
                        'end': date_series.max().strftime('%Y-%m-%d')
                    }
            except Exception as e:
                validation['date_range'] = {'error': str(e)}
        
        # Check for missing critical fields
        critical_fields = ['event_name', 'date', 'office', 'division']
        for field in critical_fields:
            if field in df.columns:
                validation['missing_critical_fields'] += df[field].isna().sum()
        
        # Calculate data quality score
        total_possible = len(df) * len(critical_fields)
        if total_possible > 0:
            validation['data_quality_score'] = round(
                ((total_possible - validation['missing_critical_fields']) / total_possible) * 100, 1
            )
        
        return validation
    
    def generate_reports(self, df: pd.DataFrame, output_dir: str = 'reports') -> Dict[str, str]:
        """Create monthly summaries and reports"""
        log_operation_start(logger, "generate_reports")
        
        try:
            reports_path = Path(output_dir)
            reports_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_files = {}
            
            # Processing summary report
            summary_file = reports_path / f'processing_summary_{timestamp}.txt'
            with open(summary_file, 'w') as f:
                f.write("=== Community Engagement ETL Processing Summary ===\n\n")
                f.write(f"Processing Date: {self.processing_summary['start_time']}\n")
                f.write(f"Sources Processed: {self.processing_summary['sources_processed']}\n")
                f.write(f"Total Records: {self.processing_summary['total_records']}\n")
                f.write(f"Data Quality Score: {self.processing_summary['validation_results'].get('data_quality_score', 'N/A')}%\n\n")
                
                if self.processing_summary['errors']:
                    f.write("Errors Encountered:\n")
                    for error in self.processing_summary['errors']:
                        f.write(f"- {error}\n")
            
            report_files['summary'] = str(summary_file)
            
            # Monthly summary if data available
            if not df.empty and 'date' in df.columns:
                monthly_summary = df.groupby(['office', 'division']).agg({
                    'event_name': 'count',
                    'attendee_count': ['sum', 'mean'],
                    'duration_hours': ['sum', 'mean']
                }).round(2)
                
                monthly_file = reports_path / f'monthly_summary_{timestamp}.csv'
                monthly_summary.to_csv(monthly_file)
                report_files['monthly'] = str(monthly_file)
            
            log_operation_end(logger, "generate_reports", True, reports_generated=len(report_files))
            return report_files
            
        except Exception as e:
            log_operation_end(logger, "generate_reports", False, error=str(e))
            self.processing_summary['errors'].append(f"Report generation failed: {e}")
            return {}
    
    def export_data(self, df: pd.DataFrame, output_dir: str = 'output', 
                   formats: List[str] = ['csv', 'excel']) -> Dict[str, str]:
        """Save to CSV/Excel for Power BI"""
        log_operation_start(logger, "export_data", formats=formats)
        
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_files = {}
            
            if 'csv' in formats:
                csv_file = output_path / f'community_engagement_data_{timestamp}.csv'
                df.to_csv(csv_file, index=False)
                export_files['csv'] = str(csv_file)
            
            if 'excel' in formats:
                excel_file = output_path / f'community_engagement_data_{timestamp}.xlsx'
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Combined_Data', index=False)
                    
                    # Add summary sheet
                    summary_df = pd.DataFrame([self.processing_summary['validation_results']])
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                export_files['excel'] = str(excel_file)
            
            self.processing_summary['end_time'] = datetime.now()
            log_operation_end(logger, "export_data", True, files_exported=len(export_files))
            return export_files
            
        except Exception as e:
            log_operation_end(logger, "export_data", False, error=str(e))
            self.processing_summary['errors'].append(f"Data export failed: {e}")
            return {}


if __name__ == "__main__":
    # Load configuration from config.json
    # Set config directory to parent directory
    config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processor = MainProcessor(config_dir)
    
    try:
        config = processor.config_loader.load_config('config.json')
        source_configs = config.get('sources', {})
        
        if not source_configs:
            raise Exception("No source configurations found in config.json")
            
        print(f"Loaded configuration for {len(source_configs)} sources")
        
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        print("Using fallback configuration...")
        # Fallback configuration
        source_configs = {
            'community_engagement': {'file_path': 'data/community_engagement.xlsx', 'sheet_name': 'Events'},
            'stacp': {'file_path': 'data/stacp_activities.xlsx', 'sheet_name': 'Activities'},
            'patrol': {'file_path': 'data/patrol_events.xlsx', 'sheet_name': 'Events'},
            'csb': {'file_path': 'data/csb_programs.xlsx', 'sheet_name': 'Programs'}
        }
    
    try:
        # Process all sources
        processed_data = processor.process_all_sources(source_configs)
        combined_data = processor.combine_data()
        
        # Generate outputs
        reports = processor.generate_reports(combined_data)
        exports = processor.export_data(combined_data)
        
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")