#!/usr/bin/env python3
"""
Health Check Script for Unraid MCP Server
"""

import sys
import requests
import json
import time
from pathlib import Path


def check_health():
    """Perform health check"""
    try:
        # Check if the server is responding
        response = requests.get("http://localhost:8080/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Basic health check passed
            if health_data.get("status") == "healthy":
                print("Health check: PASS")
                return 0
            else:
                print(f"Health check: FAIL - Status: {health_data.get('status', 'unknown')}")
                return 1
        else:
            print(f"Health check: FAIL - HTTP {response.status_code}")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("Health check: FAIL - Connection refused")
        return 1
    except requests.exceptions.Timeout:
        print("Health check: FAIL - Request timeout")
        return 1
    except Exception as e:
        print(f"Health check: FAIL - {e}")
        return 1


def check_process():
    """Check if the main process is running"""
    try:
        import psutil
        
        # Look for the main Python process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'] and '/app/src/main.py' in ' '.join(proc.info['cmdline']):
                    print(f"Process check: PASS - PID {proc.info['pid']}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("Process check: FAIL - Main process not found")
        return False
        
    except ImportError:
        # psutil not available, skip process check
        print("Process check: SKIP - psutil not available")
        return True
    except Exception as e:
        print(f"Process check: FAIL - {e}")
        return False


def check_files():
    """Check if required files exist"""
    required_files = [
        "/app/src/main.py",
        "/app/src/mcp_server.py",
        "/app/config/default_config.json"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"File check: FAIL - Missing files: {missing_files}")
        return False
    else:
        print("File check: PASS")
        return True


def check_directories():
    """Check if required directories exist and are writable"""
    required_dirs = [
        "/app/data",
        "/app/logs",
        "/app/config"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            print(f"Directory check: FAIL - {dir_path} does not exist")
            return False
        if not path.is_dir():
            print(f"Directory check: FAIL - {dir_path} is not a directory")
            return False
        if not os.access(dir_path, os.W_OK):
            print(f"Directory check: FAIL - {dir_path} is not writable")
            return False
    
    print("Directory check: PASS")
    return True


def main():
    """Main health check function"""
    print("Starting health check...")
    
    checks = [
        ("Files", check_files),
        ("Directories", check_directories),
        ("Process", check_process),
        ("HTTP", check_health)
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\nRunning {check_name} check...")
        try:
            if check_name == "HTTP":
                result = check_func() == 0
            else:
                result = check_func()
            
            if not result:
                failed_checks.append(check_name)
        except Exception as e:
            print(f"{check_name} check: ERROR - {e}")
            failed_checks.append(check_name)
    
    print(f"\nHealth check summary:")
    print(f"Total checks: {len(checks)}")
    print(f"Passed: {len(checks) - len(failed_checks)}")
    print(f"Failed: {len(failed_checks)}")
    
    if failed_checks:
        print(f"Failed checks: {', '.join(failed_checks)}")
        return 1
    else:
        print("All health checks passed!")
        return 0


if __name__ == "__main__":
    import os
    exit_code = main()
    sys.exit(exit_code)