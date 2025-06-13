"""
Configuration Manager for Unraid MCP Server
"""

import os
import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration loading and access"""
    
    def __init__(self):
        self.config: Dict[str, Any] = {}
        self.config_path = Path("/app/config")
        self.default_config_file = self.config_path / "default_config.json"
        self.user_config_file = self.config_path / "config.json"
        self.logger = logging.getLogger(__name__)
        
    async def load(self):
        """Load configuration from files and environment variables"""
        # Start with default configuration
        if self.default_config_file.exists():
            with open(self.default_config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = self._get_default_config()
            
        # Override with user configuration if it exists
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, 'r') as f:
                    user_config = json.load(f)
                    self._merge_config(self.config, user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load user config: {e}")
        
        # Override with environment variables
        self._load_from_environment()
        
        # Ensure required directories exist
        self._ensure_directories()
        
        self.logger.info("Configuration loaded successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "workers": 4,
                "enable_auth": False,
                "api_key": None
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "/app/logs/unraid-mcp-server.log",
                "max_size": "10MB",
                "backup_count": 5
            },
            "tools": {
                "system_diagnostics": {"enabled": True},
                "docker_management": {"enabled": True},
                "plex_integration": {"enabled": True},
                "log_analysis": {"enabled": True},
                "maintenance": {"enabled": True}
            }
        }
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        env_mappings = {
            "LOG_LEVEL": ("logging", "level"),
            "MCP_PORT": ("server", "port"),
            "UNRAID_HOST": ("unraid", "host"),
            "PLEX_URL": ("tools", "plex_integration", "url"),
            "PLEX_TOKEN": ("tools", "plex_integration", "token"),
            "ENABLE_SYSTEM_DIAGNOSTICS": ("tools", "system_diagnostics", "enabled"),
            "ENABLE_DOCKER_MANAGEMENT": ("tools", "docker_management", "enabled"),
            "ENABLE_PLEX_INTEGRATION": ("tools", "plex_integration", "enabled"),
            "ENABLE_LOG_ANALYSIS": ("tools", "log_analysis", "enabled"),
            "ENABLE_MAINTENANCE": ("tools", "maintenance", "enabled"),
            "ENABLE_AUTH": ("server", "enable_auth"),
            "API_KEY": ("server", "api_key"),
            "MAX_WORKERS": ("server", "workers"),
            "CACHE_TTL": ("cache", "ttl"),
            "HEALTH_CHECK_INTERVAL": ("health", "check_interval"),
            "CLEANUP_INTERVAL": ("tools", "maintenance", "cleanup_interval")
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif self._is_float(value):
                    value = float(value)
                
                # Set the value in config
                self._set_nested_value(self.config, config_path, value)
    
    def _is_float(self, value: str) -> bool:
        """Check if string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _set_nested_value(self, config: Dict[str, Any], path: tuple, value: Any):
        """Set a nested configuration value"""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            Path("/app/data"),
            Path("/app/logs"),
            Path("/app/config"),
            Path("/app/data/cache"),
            Path("/app/data/databases")
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        current = self.config
        
        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save_user_config(self):
        """Save current configuration to user config file"""
        try:
            with open(self.user_config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("User configuration saved")
        except Exception as e:
            self.logger.error(f"Failed to save user config: {e}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self.config.copy()
    
    def validate(self) -> bool:
        """Validate configuration"""
        required_keys = [
            "server.host",
            "server.port",
            "logging.level"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                self.logger.error(f"Required configuration key missing: {key}")
                return False
        
        # Validate port range
        port = self.get("server.port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            self.logger.error(f"Invalid port number: {port}")
            return False
        
        # Validate logging level
        log_level = self.get("logging.level")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            self.logger.error(f"Invalid log level: {log_level}")
            return False
        
        return True