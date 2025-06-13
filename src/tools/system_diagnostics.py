"""
System Diagnostics Tools for Unraid MCP Server
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import psutil
import glob
import os

from . import Tool


class SystemDiagnostics:
    """System monitoring and diagnostics tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.host_paths = {
            "proc": "/host/proc",
            "sys": "/host/sys",
            "boot": "/host/boot",
            "var_log": "/host/var/log"
        }
        
    async def initialize(self):
        """Initialize the system diagnostics module"""
        self.logger.info("Initializing System Diagnostics module")
        
        # Verify host paths are mounted
        for name, path in self.host_paths.items():
            if not os.path.exists(path):
                self.logger.warning(f"Host path not mounted: {name} -> {path}")
    
    async def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for system diagnostics"""
        return [
            Tool(
                name="get_system_overview",
                description="Get comprehensive system overview including CPU, memory, disk usage, and temperatures",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_details": {
                            "type": "boolean",
                            "description": "Include detailed breakdown of resources",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_disk_health",
                description="Get SMART disk health status for all drives",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "device": {
                            "type": "string",
                            "description": "Specific device to check (optional, checks all if not specified)"
                        }
                    }
                }
            ),
            Tool(
                name="get_temperature_status",
                description="Get temperature readings from all sensors",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "fahrenheit": {
                            "type": "boolean",
                            "description": "Return temperatures in Fahrenheit instead of Celsius",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_network_status",
                description="Get network interface status and statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "interface": {
                            "type": "string",
                            "description": "Specific interface to check (optional)"
                        }
                    }
                }
            ),
            Tool(
                name="get_process_info",
                description="Get information about running processes",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sort_by": {
                            "type": "string",
                            "enum": ["cpu", "memory", "name"],
                            "description": "Sort processes by criteria",
                            "default": "cpu"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of processes to return",
                            "default": 20
                        }
                    }
                }
            ),
            Tool(
                name="check_system_health",
                description="Comprehensive system health check with recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include optimization recommendations",
                            "default": True
                        }
                    }
                }
            )
        ]
    
    async def handle_call(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            if method == "get_system_overview":
                return await self._get_system_overview(arguments.get("include_details", False))
            elif method == "get_disk_health":
                return await self._get_disk_health(arguments.get("device"))
            elif method == "get_temperature_status":
                return await self._get_temperature_status(arguments.get("fahrenheit", False))
            elif method == "get_network_status":
                return await self._get_network_status(arguments.get("interface"))
            elif method == "get_process_info":
                return await self._get_process_info(
                    arguments.get("sort_by", "cpu"),
                    arguments.get("limit", 20)
                )
            elif method == "check_system_health":
                return await self._check_system_health(arguments.get("include_recommendations", True))
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {"error": str(e), "method": method}
    
    async def _get_system_overview(self, include_details: bool) -> Dict[str, Any]:
        """Get system overview"""
        try:
            # CPU information
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)
            
            # Memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk information
            disk_usage = {}
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    disk_usage[disk.mountpoint] = {
                        "device": disk.device,
                        "fstype": disk.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": round((usage.used / usage.total) * 100, 1)
                    }
                except PermissionError:
                    continue
            
            # Boot time and uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            overview = {
                "timestamp": datetime.now().isoformat(),
                "uptime": {
                    "boot_time": boot_time.isoformat(),
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_days": uptime.days,
                    "uptime_hours": uptime.seconds // 3600
                },
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores_physical": cpu_count,
                    "cores_logical": cpu_count_logical
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "percent_used": swap.percent
                },
                "disk": disk_usage
            }
            
            if include_details:
                # Add detailed CPU per-core stats
                overview["cpu"]["per_core_usage"] = psutil.cpu_percent(percpu=True)
                
                # Add detailed memory breakdown
                overview["memory"]["details"] = {
                    "buffers_gb": round(memory.buffers / (1024**3), 2),
                    "cached_gb": round(memory.cached / (1024**3), 2),
                    "shared_gb": round(memory.shared / (1024**3), 2)
                }
                
                # Add load averages
                try:
                    load_avg = os.getloadavg()
                    overview["load_average"] = {
                        "1min": load_avg[0],
                        "5min": load_avg[1],
                        "15min": load_avg[2]
                    }
                except:
                    pass
            
            return {"status": "success", "data": overview}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_disk_health(self, device: Optional[str] = None) -> Dict[str, Any]:
        """Get SMART disk health status"""
        try:
            result = {"timestamp": datetime.now().isoformat(), "drives": {}}
            
            # Get list of drives to check
            if device:
                drives = [device]
            else:
                # Auto-detect drives
                drives = []
                for device_pattern in ["/dev/sd*", "/dev/nvme*", "/dev/hd*"]:
                    drives.extend(glob.glob(device_pattern))
            
            for drive in drives:
                try:
                    # Run smartctl command
                    cmd = ["smartctl", "-A", "-H", "--json", drive]
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await proc.communicate()
                    
                    if proc.returncode == 0 or proc.returncode == 4:  # 4 can indicate some SMART issues but data is still readable
                        smart_data = json.loads(stdout.decode())
                        
                        # Extract key health information
                        health_info = {
                            "device": drive,
                            "model": smart_data.get("model_name", "Unknown"),
                            "serial": smart_data.get("serial_number", "Unknown"),
                            "health_status": smart_data.get("smart_status", {}).get("passed", False),
                            "temperature": None,
                            "power_on_hours": None,
                            "reallocated_sectors": None,
                            "pending_sectors": None
                        }
                        
                        # Extract temperature
                        if "temperature" in smart_data:
                            health_info["temperature"] = smart_data["temperature"].get("current", None)
                        
                        # Extract SMART attributes
                        if "ata_smart_attributes" in smart_data:
                            attrs = smart_data["ata_smart_attributes"]["table"]
                            for attr in attrs:
                                if attr["id"] == 9:  # Power On Hours
                                    health_info["power_on_hours"] = attr["raw"]["value"]
                                elif attr["id"] == 5:  # Reallocated Sectors
                                    health_info["reallocated_sectors"] = attr["raw"]["value"]
                                elif attr["id"] == 197:  # Current Pending Sectors
                                    health_info["pending_sectors"] = attr["raw"]["value"]
                        
                        result["drives"][drive] = health_info
                    else:
                        result["drives"][drive] = {
                            "device": drive,
                            "error": f"Failed to read SMART data: {stderr.decode()}"
                        }
                        
                except Exception as e:
                    result["drives"][drive] = {
                        "device": drive,
                        "error": str(e)
                    }
            
            return {"status": "success", "data": result}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_temperature_status(self, fahrenheit: bool = False) -> Dict[str, Any]:
        """Get temperature readings"""
        try:
            temperatures = {}
            
            # Get CPU temperatures
            try:
                cpu_temps = psutil.sensors_temperatures()
                if cpu_temps:
                    for name, entries in cpu_temps.items():
                        for entry in entries:
                            temp = entry.current
                            if fahrenheit:
                                temp = (temp * 9/5) + 32
                            
                            temp_key = f"{name}_{entry.label}" if entry.label else name
                            temperatures[temp_key] = {
                                "current": round(temp, 1),
                                "high": round((entry.high * 9/5) + 32 if entry.high and fahrenheit else entry.high or 0, 1),
                                "critical": round((entry.critical * 9/5) + 32 if entry.critical and fahrenheit else entry.critical or 0, 1),
                                "unit": "°F" if fahrenheit else "°C"
                            }
            except:
                pass
            
            # Try to get disk temperatures from SMART data
            try:
                for device_pattern in ["/dev/sd*", "/dev/nvme*"]:
                    for drive in glob.glob(device_pattern):
                        cmd = ["smartctl", "-A", "--json", drive]
                        proc = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await proc.communicate()
                        
                        if proc.returncode == 0 or proc.returncode == 4:
                            smart_data = json.loads(stdout.decode())
                            if "temperature" in smart_data:
                                temp = smart_data["temperature"]["current"]
                                if fahrenheit:
                                    temp = (temp * 9/5) + 32
                                
                                drive_name = os.path.basename(drive)
                                temperatures[f"disk_{drive_name}"] = {
                                    "current": round(temp, 1),
                                    "unit": "°F" if fahrenheit else "°C"
                                }
            except:
                pass
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "temperatures": temperatures,
                    "unit": "°F" if fahrenheit else "°C"
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_network_status(self, interface: Optional[str] = None) -> Dict[str, Any]:
        """Get network status and statistics"""
        try:
            network_info = {"timestamp": datetime.now().isoformat(), "interfaces": {}}
            
            # Get network interfaces
            net_io = psutil.net_io_counters(pernic=True)
            net_addrs = psutil.net_if_addrs()
            net_stats = psutil.net_if_stats()
            
            interfaces_to_check = [interface] if interface else net_io.keys()
            
            for iface in interfaces_to_check:
                if iface in net_io:
                    iface_info = {
                        "name": iface,
                        "is_up": net_stats[iface].isup if iface in net_stats else False,
                        "speed_mbps": net_stats[iface].speed if iface in net_stats else 0,
                        "mtu": net_stats[iface].mtu if iface in net_stats else 0,
                        "addresses": [],
                        "statistics": {
                            "bytes_sent": net_io[iface].bytes_sent,
                            "bytes_recv": net_io[iface].bytes_recv,
                            "packets_sent": net_io[iface].packets_sent,
                            "packets_recv": net_io[iface].packets_recv,
                            "errors_in": net_io[iface].errin,
                            "errors_out": net_io[iface].errout,
                            "drops_in": net_io[iface].dropin,
                            "drops_out": net_io[iface].dropout
                        }
                    }
                    
                    # Add IP addresses
                    if iface in net_addrs:
                        for addr in net_addrs[iface]:
                            iface_info["addresses"].append({
                                "family": addr.family.name,
                                "address": addr.address,
                                "netmask": addr.netmask,
                                "broadcast": addr.broadcast
                            })
                    
                    network_info["interfaces"][iface] = iface_info
            
            return {"status": "success", "data": network_info}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_process_info(self, sort_by: str, limit: int) -> Dict[str, Any]:
        """Get process information"""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'memory_info', 'create_time']):
                try:
                    pinfo = proc.info
                    pinfo['cpu_percent'] = proc.cpu_percent()
                    pinfo['memory_mb'] = round(pinfo['memory_info'].rss / (1024 * 1024), 1)
                    pinfo['create_time'] = datetime.fromtimestamp(pinfo['create_time']).isoformat()
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x.get('name', '').lower())
            
            # Limit results
            processes = processes[:limit]
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "total_processes": len(psutil.pids()),
                    "processes": processes,
                    "sorted_by": sort_by,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _check_system_health(self, include_recommendations: bool) -> Dict[str, Any]:
        """Comprehensive system health check"""
        try:
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "overall_status": "healthy",
                "checks": {},
                "warnings": [],
                "errors": [],
                "recommendations": [] if include_recommendations else None
            }
            
            # CPU health check
            cpu_percent = psutil.cpu_percent(interval=1)
            health_report["checks"]["cpu"] = {
                "status": "warning" if cpu_percent > 80 else "healthy",
                "usage_percent": cpu_percent
            }
            if cpu_percent > 80:
                health_report["warnings"].append(f"High CPU usage: {cpu_percent}%")
                if include_recommendations:
                    health_report["recommendations"].append("Consider identifying high CPU processes and optimizing workloads")
            
            # Memory health check
            memory = psutil.virtual_memory()
            health_report["checks"]["memory"] = {
                "status": "warning" if memory.percent > 85 else "healthy",
                "usage_percent": memory.percent
            }
            if memory.percent > 85:
                health_report["warnings"].append(f"High memory usage: {memory.percent}%")
                if include_recommendations:
                    health_report["recommendations"].append("Consider adding more RAM or reducing memory-intensive applications")
            
            # Disk space health check
            critical_disks = []
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    percent_used = (usage.used / usage.total) * 100
                    if percent_used > 90:
                        critical_disks.append((disk.mountpoint, percent_used))
                except:
                    continue
            
            health_report["checks"]["disk_space"] = {
                "status": "error" if critical_disks else "healthy",
                "critical_disks": critical_disks
            }
            if critical_disks:
                for mount, percent in critical_disks:
                    health_report["errors"].append(f"Critical disk space on {mount}: {percent:.1f}% used")
                    if include_recommendations:
                        health_report["recommendations"].append(f"Free up space on {mount} or add more storage")
            
            # Load average check (if available)
            try:
                load_avg = os.getloadavg()
                cpu_count = psutil.cpu_count()
                load_per_core = load_avg[0] / cpu_count
                
                health_report["checks"]["load_average"] = {
                    "status": "warning" if load_per_core > 0.8 else "healthy",
                    "load_1min": load_avg[0],
                    "load_per_core": round(load_per_core, 2)
                }
                if load_per_core > 0.8:
                    health_report["warnings"].append(f"High system load: {load_per_core:.2f} per core")
                    if include_recommendations:
                        health_report["recommendations"].append("System may be overloaded, consider reducing concurrent tasks")
            except:
                pass
            
            # Set overall status
            if health_report["errors"]:
                health_report["overall_status"] = "critical"
            elif health_report["warnings"]:
                health_report["overall_status"] = "warning"
            
            return {"status": "success", "data": health_report}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}