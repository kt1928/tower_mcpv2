#!/usr/bin/env python3
"""
Initialize configuration for Unraid MCP Server
"""

import os
import json
import logging
from pathlib import Path


def create_default_config():
    """Create default configuration if it doesn't exist"""
    config_dir = Path("/app/config")
    config_file = config_dir / "default_config.json"
    
    if config_file.exists():
        print("Default configuration already exists")
        return
    
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": int(os.getenv("MCP_PORT", "8080")),
            "workers": int(os.getenv("MAX_WORKERS", "4")),
            "enable_auth": os.getenv("ENABLE_AUTH", "false").lower() == "true",
            "api_key": os.getenv("API_KEY")
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/app/logs/unraid-mcp-server.log",
            "max_size": "10MB",
            "backup_count": 5
        },
        "tools": {
            "system_diagnostics": {
                "enabled": os.getenv("ENABLE_SYSTEM_DIAGNOSTICS", "true").lower() == "true",
                "cache_ttl": 60,
                "temperature_unit": "celsius"
            },
            "docker_management": {
                "enabled": os.getenv("ENABLE_DOCKER_MANAGEMENT", "true").lower() == "true",
                "socket_path": "/var/run/docker.sock",
                "auto_cleanup": False
            },
            "plex_integration": {
                "enabled": os.getenv("ENABLE_PLEX_INTEGRATION", "true").lower() == "true",
                "url": os.getenv("PLEX_URL"),
                "token": os.getenv("PLEX_TOKEN"),
                "timeout": 30
            },
            "log_analysis": {
                "enabled": os.getenv("ENABLE_LOG_ANALYSIS", "true").lower() == "true",
                "watch_paths": [
                    "/host/var/log/syslog",
                    "/host/var/log/messages"
                ],
                "max_lines": 1000
            },
            "maintenance": {
                "enabled": os.getenv("ENABLE_MAINTENANCE", "true").lower() == "true",
                "cleanup_interval": int(os.getenv("CLEANUP_INTERVAL", "3600"))
            }
        },
        "unraid": {
            "host": os.getenv("UNRAID_HOST", "unraid.local"),
            "paths": {
                "boot": "/host/boot",
                "proc": "/host/proc",
                "sys": "/host/sys",
                "var_log": "/host/var/log"
            }
        }
    }
    
    config_dir.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created default configuration: {config_file}")


def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        "/app/data",
        "/app/logs", 
        "/app/config",
        "/app/data/cache",
        "/app/data/databases"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")


def main():
    """Main initialization function"""
    print("Initializing Unraid MCP Server configuration...")
    
    try:
        ensure_directories()
        create_default_config()
        print("Configuration initialization complete!")
        return 0
    except Exception as e:
        print(f"Configuration initialization failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main()) 