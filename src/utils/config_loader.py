"""
Community Engagement ETL - Configuration Loader
Author: Claude AI Assistant
Created: 2025-09-04 EST
Purpose: Load and validate JSON configuration files
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass


class ConfigLoader:
    """Handles loading and validation of JSON configuration files"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize with optional config directory path"""
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / 'configs'
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load JSON configuration file
        
        Args:
            config_name: Name of config file (with or without .json extension)
            
        Returns:
            Dictionary containing configuration data
            
        Raises:
            ConfigError: If file not found or invalid JSON
        """
        config_path = self._get_config_path(config_name)
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.info(f"Successfully loaded config: {config_path}")
            return config_data
            
        except FileNotFoundError:
            error_msg = f"Configuration file not found: {config_path}"
            logger.error(error_msg)
            raise ConfigError(error_msg)
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in config file {config_path}: {e}"
            logger.error(error_msg)
            raise ConfigError(error_msg)
    
    def validate_paths(self, config: Dict[str, Any], path_keys: list) -> bool:
        """
        Validate that specified path keys exist in config and point to valid paths
        
        Args:
            config: Configuration dictionary
            path_keys: List of keys that should contain file/directory paths
            
        Returns:
            True if all paths are valid
            
        Raises:
            ConfigError: If any path is missing or invalid
        """
        for key in path_keys:
            if key not in config:
                raise ConfigError(f"Missing required path key: {key}")
            
            path_value = config[key]
            if not isinstance(path_value, str):
                raise ConfigError(f"Path key '{key}' must be a string")
            
            path = Path(path_value)
            if not path.exists():
                logger.warning(f"Path does not exist: {path} (key: {key})")
        
        logger.info(f"Validated {len(path_keys)} path keys")
        return True
    
    def _get_config_path(self, config_name: str) -> Path:
        """Get full path to configuration file"""
        if not config_name.endswith('.json'):
            config_name += '.json'
        
        return self.config_dir / config_name
    
    def list_configs(self) -> list:
        """List available configuration files"""
        if not self.config_dir.exists():
            return []
        
        return [f.stem for f in self.config_dir.glob('*.json')]