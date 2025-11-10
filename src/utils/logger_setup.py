"""
Community Engagement ETL - Logger Setup
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Configure logging with file rotation and EST timestamps
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import pytz
from typing import Optional


class ESTFormatter(logging.Formatter):
    """Custom formatter that uses EST timezone for timestamps"""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.est_tz = pytz.timezone('US/Eastern')
    
    def formatTime(self, record, datefmt=None):
        """Override to use EST timezone"""
        dt = datetime.fromtimestamp(record.created, tz=self.est_tz)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime('%Y-%m-%d %H:%M:%S EST')


def setup_logger(name: str = 'community_engagement_etl',
                log_dir: Optional[str] = None,
                log_level: str = 'INFO',
                max_bytes: int = 10 * 1024 * 1024,  # 10MB
                backup_count: int = 5) -> logging.Logger:
    """
    Set up logger with file rotation and EST timestamps
    
    Args:
        name: Logger name
        log_dir: Directory for log files (defaults to ./logs)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if not specified
    if log_dir is None:
        log_dir = Path.cwd() / 'logs'
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters with EST timezone
    detailed_formatter = ESTFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s'
    )
    
    console_formatter = ESTFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s'
    )
    
    # File handler with rotation
    log_file = log_dir / f'{name}.log'
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Log setup completion
    logger.info(f"Logger '{name}' initialized - Log file: {log_file}")
    logger.info(f"Log rotation: {max_bytes:,} bytes, {backup_count} backups")
    
    return logger


def get_project_logger(module_name: str, log_level: str = 'INFO') -> logging.Logger:
    """
    Get a logger with project-specific configuration
    
    Args:
        module_name: Name of the module requesting the logger
        log_level: Logging level for console output
        
    Returns:
        Configured logger instance
    """
    logger_name = f'community_engagement_etl.{module_name}'
    
    # Check if main logger already exists
    main_logger = logging.getLogger('community_engagement_etl')
    if not main_logger.handlers:
        # Set up main logger if it doesn't exist
        setup_logger('community_engagement_etl', log_level=log_level)
    
    # Return child logger
    return logging.getLogger(logger_name)


def log_operation_start(logger: logging.Logger, operation: str, **kwargs):
    """Log the start of an operation with parameters"""
    params_str = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
    logger.info(f"Starting {operation}" + (f" with {params_str}" if params_str else ""))


def log_operation_end(logger: logging.Logger, operation: str, success: bool = True, 
                     duration: Optional[float] = None, **kwargs):
    """Log the end of an operation with results"""
    status = "completed successfully" if success else "failed"
    duration_str = f" in {duration:.2f}s" if duration else ""
    results_str = ', '.join([f'{k}={v}' for k, v in kwargs.items()])
    
    message = f"Operation {operation} {status}{duration_str}"
    if results_str:
        message += f" - {results_str}"
    
    if success:
        logger.info(message)
    else:
        logger.error(message)