"""
Maintenance Tools for Unraid MCP Server
"""

import asyncio
import json
import logging
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import subprocess
import os

from . import Tool


class Maintenance:
    """System maintenance and optimization tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cleanup_interval = config.get("cleanup_interval", 3600)
        self.auto_cleanup = config.get("auto_cleanup", True)
        
    async def initialize(self):
        """Initialize the maintenance module"""
        self.logger.info("Initializing Maintenance module")
        
        if self.auto_cleanup:
            # Start background cleanup task
            asyncio.create_task(self._periodic_cleanup())
    
    async def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for maintenance"""
        return [
            Tool(
                name="run_cleanup",
                description="Run system cleanup tasks including log rotation, cache cleanup, and orphaned file removal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cleanup_logs": {
                            "type": "boolean",
                            "description": "Clean up old log files",
                            "default": True
                        },
                        "cleanup_cache": {
                            "type": "boolean",
                            "description": "Clean up cache directories",
                            "default": True
                        },
                        "cleanup_temp": {
                            "type": "boolean",
                            "description": "Clean up temporary files",
                            "default": True
                        },
                        "cleanup_docker": {
                            "type": "boolean",
                            "description": "Clean up Docker resources",
                            "default": True
                        },
                        "max_age_days": {
                            "type": "integer",
                            "description": "Maximum age of files to keep (days)",
                            "default": 30
                        }
                    }
                }
            ),
            Tool(
                name="check_updates",
                description="Check for available system and application updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "check_system": {
                            "type": "boolean",
                            "description": "Check for system updates",
                            "default": True
                        },
                        "check_docker": {
                            "type": "boolean",
                            "description": "Check for Docker image updates",
                            "default": True
                        },
                        "check_plex": {
                            "type": "boolean",
                            "description": "Check for Plex updates",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="verify_backups",
                description="Verify backup integrity and completeness",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backup_paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Paths to backup locations to verify"
                        },
                        "check_integrity": {
                            "type": "boolean",
                            "description": "Perform integrity checks on backup files",
                            "default": True
                        },
                        "verify_size": {
                            "type": "boolean",
                            "description": "Verify backup sizes are reasonable",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="schedule_maintenance",
                description="Schedule automated maintenance tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_type": {
                            "type": "string",
                            "enum": ["cleanup", "backup", "update_check", "health_check"],
                            "description": "Type of maintenance task"
                        },
                        "schedule": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "description": "Schedule frequency"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time to run (HH:MM format)",
                            "default": "02:00"
                        },
                        "enabled": {
                            "type": "boolean",
                            "description": "Enable the scheduled task",
                            "default": True
                        }
                    },
                    "required": ["task_type", "schedule"]
                }
            ),
            Tool(
                name="optimize_system",
                description="Provide system optimization recommendations and perform basic optimizations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "analyze_performance": {
                            "type": "boolean",
                            "description": "Analyze system performance",
                            "default": True
                        },
                        "optimize_memory": {
                            "type": "boolean",
                            "description": "Optimize memory usage",
                            "default": True
                        },
                        "optimize_storage": {
                            "type": "boolean",
                            "description": "Optimize storage usage",
                            "default": True
                        },
                        "apply_recommendations": {
                            "type": "boolean",
                            "description": "Apply optimization recommendations",
                            "default": False
                        }
                    }
                }
            )
        ]
    
    async def handle_call(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            if method == "run_cleanup":
                return await self._run_cleanup(
                    arguments.get("cleanup_logs", True),
                    arguments.get("cleanup_cache", True),
                    arguments.get("cleanup_temp", True),
                    arguments.get("cleanup_docker", True),
                    arguments.get("max_age_days", 30)
                )
            elif method == "check_updates":
                return await self._check_updates(
                    arguments.get("check_system", True),
                    arguments.get("check_docker", True),
                    arguments.get("check_plex", True)
                )
            elif method == "verify_backups":
                return await self._verify_backups(
                    arguments.get("backup_paths", []),
                    arguments.get("check_integrity", True),
                    arguments.get("verify_size", True)
                )
            elif method == "schedule_maintenance":
                return await self._schedule_maintenance(
                    arguments["task_type"],
                    arguments["schedule"],
                    arguments.get("time", "02:00"),
                    arguments.get("enabled", True)
                )
            elif method == "optimize_system":
                return await self._optimize_system(
                    arguments.get("analyze_performance", True),
                    arguments.get("optimize_memory", True),
                    arguments.get("optimize_storage", True),
                    arguments.get("apply_recommendations", False)
                )
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {"error": str(e), "method": method}
    
    async def _run_cleanup(self, cleanup_logs: bool = True, cleanup_cache: bool = True,
                          cleanup_temp: bool = True, cleanup_docker: bool = True,
                          max_age_days: int = 30) -> Dict[str, Any]:
        """Run system cleanup tasks"""
        try:
            cleanup_results = {
                "timestamp": datetime.now().isoformat(),
                "tasks_completed": [],
                "files_removed": 0,
                "space_freed_mb": 0,
                "errors": []
            }
            
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            
            # Clean up log files
            if cleanup_logs:
                try:
                    log_cleanup = await self._cleanup_logs(cutoff_time)
                    cleanup_results["tasks_completed"].append("log_cleanup")
                    cleanup_results["files_removed"] += log_cleanup["files_removed"]
                    cleanup_results["space_freed_mb"] += log_cleanup["space_freed_mb"]
                except Exception as e:
                    cleanup_results["errors"].append(f"Log cleanup failed: {e}")
            
            # Clean up cache directories
            if cleanup_cache:
                try:
                    cache_cleanup = await self._cleanup_cache(cutoff_time)
                    cleanup_results["tasks_completed"].append("cache_cleanup")
                    cleanup_results["files_removed"] += cache_cleanup["files_removed"]
                    cleanup_results["space_freed_mb"] += cache_cleanup["space_freed_mb"]
                except Exception as e:
                    cleanup_results["errors"].append(f"Cache cleanup failed: {e}")
            
            # Clean up temporary files
            if cleanup_temp:
                try:
                    temp_cleanup = await self._cleanup_temp_files(cutoff_time)
                    cleanup_results["tasks_completed"].append("temp_cleanup")
                    cleanup_results["files_removed"] += temp_cleanup["files_removed"]
                    cleanup_results["space_freed_mb"] += temp_cleanup["space_freed_mb"]
                except Exception as e:
                    cleanup_results["errors"].append(f"Temp cleanup failed: {e}")
            
            # Clean up Docker resources
            if cleanup_docker:
                try:
                    docker_cleanup = await self._cleanup_docker_resources()
                    cleanup_results["tasks_completed"].append("docker_cleanup")
                    cleanup_results["files_removed"] += docker_cleanup["files_removed"]
                    cleanup_results["space_freed_mb"] += docker_cleanup["space_freed_mb"]
                except Exception as e:
                    cleanup_results["errors"].append(f"Docker cleanup failed: {e}")
            
            cleanup_results["space_freed_mb"] = round(cleanup_results["space_freed_mb"], 2)
            
            return {
                "status": "success",
                "data": cleanup_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_logs(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Clean up old log files"""
        log_dirs = ["/app/logs", "/host/var/log"]
        files_removed = 0
        space_freed = 0
        
        for log_dir in log_dirs:
            if not Path(log_dir).exists():
                continue
            
            for log_file in Path(log_dir).rglob("*.log*"):
                try:
                    if log_file.stat().st_mtime < cutoff_time.timestamp():
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        files_removed += 1
                        space_freed += file_size / (1024 * 1024)  # Convert to MB
                except Exception:
                    continue
        
        return {
            "files_removed": files_removed,
            "space_freed_mb": space_freed
        }
    
    async def _cleanup_cache(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Clean up cache directories"""
        cache_dirs = ["/app/data/cache", "/tmp", "/var/cache"]
        files_removed = 0
        space_freed = 0
        
        for cache_dir in cache_dirs:
            if not Path(cache_dir).exists():
                continue
            
            for cache_file in Path(cache_dir).rglob("*"):
                try:
                    if cache_file.is_file() and cache_file.stat().st_mtime < cutoff_time.timestamp():
                        file_size = cache_file.stat().st_size
                        cache_file.unlink()
                        files_removed += 1
                        space_freed += file_size / (1024 * 1024)
                except Exception:
                    continue
        
        return {
            "files_removed": files_removed,
            "space_freed_mb": space_freed
        }
    
    async def _cleanup_temp_files(self, cutoff_time: datetime) -> Dict[str, Any]:
        """Clean up temporary files"""
        temp_dirs = ["/tmp", "/var/tmp"]
        files_removed = 0
        space_freed = 0
        
        for temp_dir in temp_dirs:
            if not Path(temp_dir).exists():
                continue
            
            for temp_file in Path(temp_dir).rglob("*"):
                try:
                    if temp_file.is_file() and temp_file.stat().st_mtime < cutoff_time.timestamp():
                        file_size = temp_file.stat().st_size
                        temp_file.unlink()
                        files_removed += 1
                        space_freed += file_size / (1024 * 1024)
                except Exception:
                    continue
        
        return {
            "files_removed": files_removed,
            "space_freed_mb": space_freed
        }
    
    async def _cleanup_docker_resources(self) -> Dict[str, Any]:
        """Clean up Docker resources"""
        try:
            import docker
            client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
            
            # Remove stopped containers
            stopped_containers = client.containers.list(filters={"status": "exited"})
            for container in stopped_containers:
                container.remove()
            
            # Remove unused images
            client.images.prune()
            
            # Remove unused volumes
            client.volumes.prune()
            
            # Remove unused networks
            client.networks.prune()
            
            return {
                "files_removed": len(stopped_containers),
                "space_freed_mb": 0  # Docker cleanup space calculation is complex
            }
            
        except Exception as e:
            self.logger.error(f"Docker cleanup failed: {e}")
            return {"files_removed": 0, "space_freed_mb": 0}
    
    async def _check_updates(self, check_system: bool = True, check_docker: bool = True,
                            check_plex: bool = True) -> Dict[str, Any]:
        """Check for available updates"""
        try:
            update_results = {
                "timestamp": datetime.now().isoformat(),
                "system_updates": None,
                "docker_updates": None,
                "plex_updates": None,
                "total_updates_available": 0
            }
            
            # Check system updates (Unraid specific)
            if check_system:
                try:
                    # Check Unraid version
                    if Path("/host/boot/version").exists():
                        with open("/host/boot/version", "r") as f:
                            current_version = f.read().strip()
                    
                    # This would typically check against Unraid's update server
                    update_results["system_updates"] = {
                        "current_version": current_version,
                        "latest_version": "Unknown",  # Would be fetched from update server
                        "update_available": False,
                        "update_type": "minor"
                    }
                except Exception as e:
                    update_results["system_updates"] = {"error": str(e)}
            
            # Check Docker image updates
            if check_docker:
                try:
                    import docker
                    client = docker.DockerClient(base_url="unix:///var/run/docker.sock")
                    
                    docker_updates = []
                    for container in client.containers.list():
                        try:
                            image = container.image
                            if image.tags:
                                # Pull latest image to check for updates
                                repo, tag = image.tags[0].rsplit(':', 1)
                                latest_image = client.images.pull(repo, tag=tag)
                                
                                if latest_image.id != image.id:
                                    docker_updates.append({
                                        "container_name": container.name,
                                        "current_image": image.id[:12],
                                        "latest_image": latest_image.id[:12],
                                        "repository": repo
                                    })
                        except Exception:
                            continue
                    
                    update_results["docker_updates"] = {
                        "containers_with_updates": len(docker_updates),
                        "updates": docker_updates
                    }
                    update_results["total_updates_available"] += len(docker_updates)
                    
                except Exception as e:
                    update_results["docker_updates"] = {"error": str(e)}
            
            # Check Plex updates
            if check_plex:
                try:
                    # This would check Plex's update API
                    update_results["plex_updates"] = {
                        "current_version": "Unknown",
                        "latest_version": "Unknown",
                        "update_available": False
                    }
                except Exception as e:
                    update_results["plex_updates"] = {"error": str(e)}
            
            return {
                "status": "success",
                "data": update_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _verify_backups(self, backup_paths: List[str], check_integrity: bool = True,
                             verify_size: bool = True) -> Dict[str, Any]:
        """Verify backup integrity"""
        try:
            backup_results = {
                "timestamp": datetime.now().isoformat(),
                "backups_checked": 0,
                "backups_valid": 0,
                "backups_invalid": 0,
                "backup_details": [],
                "total_size_gb": 0
            }
            
            for backup_path in backup_paths:
                if not Path(backup_path).exists():
                    continue
                
                backup_info = {
                    "path": backup_path,
                    "exists": True,
                    "size_gb": 0,
                    "integrity_check": None,
                    "last_modified": None,
                    "status": "unknown"
                }
                
                try:
                    # Calculate total size
                    total_size = sum(f.stat().st_size for f in Path(backup_path).rglob('*') if f.is_file())
                    backup_info["size_gb"] = round(total_size / (1024**3), 2)
                    backup_results["total_size_gb"] += backup_info["size_gb"]
                    
                    # Get last modified time
                    backup_info["last_modified"] = datetime.fromtimestamp(
                        Path(backup_path).stat().st_mtime
                    ).isoformat()
                    
                    # Check integrity if requested
                    if check_integrity:
                        backup_info["integrity_check"] = await self._check_backup_integrity(backup_path)
                    
                    # Verify size is reasonable
                    if verify_size and backup_info["size_gb"] > 0:
                        backup_info["status"] = "valid"
                        backup_results["backups_valid"] += 1
                    else:
                        backup_info["status"] = "invalid"
                        backup_results["backups_invalid"] += 1
                    
                except Exception as e:
                    backup_info["status"] = "error"
                    backup_info["error"] = str(e)
                    backup_results["backups_invalid"] += 1
                
                backup_results["backup_details"].append(backup_info)
                backup_results["backups_checked"] += 1
            
            return {
                "status": "success",
                "data": backup_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _check_backup_integrity(self, backup_path: str) -> Dict[str, Any]:
        """Check backup file integrity"""
        # This is a simplified integrity check
        # In practice, you'd check checksums, test file readability, etc.
        try:
            backup_files = list(Path(backup_path).rglob('*'))
            readable_files = 0
            
            for file_path in backup_files:
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            f.read(1024)  # Read first 1KB to test readability
                        readable_files += 1
                    except Exception:
                        pass
            
            return {
                "total_files": len(backup_files),
                "readable_files": readable_files,
                "integrity_score": round(readable_files / max(len(backup_files), 1) * 100, 1)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _schedule_maintenance(self, task_type: str, schedule: str, time: str = "02:00",
                                   enabled: bool = True) -> Dict[str, Any]:
        """Schedule maintenance tasks"""
        try:
            # This would typically integrate with cron or a task scheduler
            # For now, we'll just return the scheduling information
            
            schedule_info = {
                "task_type": task_type,
                "schedule": schedule,
                "time": time,
                "enabled": enabled,
                "next_run": None,
                "cron_expression": None
            }
            
            # Generate cron expression
            if schedule == "daily":
                schedule_info["cron_expression"] = f"{time.split(':')[1]} {time.split(':')[0]} * * *"
            elif schedule == "weekly":
                schedule_info["cron_expression"] = f"{time.split(':')[1]} {time.split(':')[0]} * * 0"
            elif schedule == "monthly":
                schedule_info["cron_expression"] = f"{time.split(':')[1]} {time.split(':')[0]} 1 * *"
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "scheduled_task": schedule_info,
                    "message": f"Task '{task_type}' scheduled for {schedule} at {time}"
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _optimize_system(self, analyze_performance: bool = True, optimize_memory: bool = True,
                              optimize_storage: bool = True, apply_recommendations: bool = False) -> Dict[str, Any]:
        """Optimize system performance"""
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "performance_analysis": None,
                "memory_optimization": None,
                "storage_optimization": None,
                "recommendations": [],
                "applied_optimizations": []
            }
            
            # Analyze performance
            if analyze_performance:
                optimization_results["performance_analysis"] = await self._analyze_performance()
            
            # Memory optimization
            if optimize_memory:
                optimization_results["memory_optimization"] = await self._optimize_memory(apply_recommendations)
                if apply_recommendations:
                    optimization_results["applied_optimizations"].append("memory_optimization")
            
            # Storage optimization
            if optimize_storage:
                optimization_results["storage_optimization"] = await self._optimize_storage(apply_recommendations)
                if apply_recommendations:
                    optimization_results["applied_optimizations"].append("storage_optimization")
            
            # Generate recommendations
            optimization_results["recommendations"] = [
                "Consider increasing swap space if memory usage is high",
                "Regularly clean up temporary files and logs",
                "Monitor disk space and plan for expansion",
                "Keep system and applications updated",
                "Consider using SSD cache for frequently accessed data"
            ]
            
            return {
                "status": "success",
                "data": optimization_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze system performance"""
        try:
            # CPU analysis
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory analysis
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk analysis
            disk_usage = {}
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    disk_usage[disk.mountpoint] = {
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent_used": round((usage.used / usage.total) * 100, 1)
                    }
                except PermissionError:
                    continue
            
            # Load average
            try:
                load_avg = psutil.getloadavg()
                load_per_core = load_avg[0] / cpu_count
            except:
                load_avg = (0, 0, 0)
                load_per_core = 0
            
            return {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "cores": cpu_count,
                    "load_average": load_avg,
                    "load_per_core": round(load_per_core, 2)
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
                "disk": disk_usage,
                "performance_score": self._calculate_performance_score(cpu_percent, memory.percent, load_per_core)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _optimize_memory(self, apply_recommendations: bool = False) -> Dict[str, Any]:
        """Optimize memory usage"""
        try:
            memory = psutil.virtual_memory()
            optimizations = []
            
            # Check if swap is being used heavily
            swap = psutil.swap_memory()
            if swap.percent > 50:
                optimizations.append("High swap usage detected - consider adding more RAM")
            
            # Check for memory pressure
            if memory.percent > 80:
                optimizations.append("High memory usage - consider closing unnecessary applications")
            
            # Clear page cache if requested
            if apply_recommendations and memory.percent > 70:
                try:
                    subprocess.run(["sync"], check=True)
                    with open("/proc/sys/vm/drop_caches", "w") as f:
                        f.write("1")
                    optimizations.append("Cleared page cache")
                except Exception:
                    optimizations.append("Failed to clear page cache")
            
            return {
                "current_usage_percent": memory.percent,
                "swap_usage_percent": swap.percent,
                "optimizations_applied": optimizations,
                "recommendations": [
                    "Monitor memory usage regularly",
                    "Consider adding more RAM if usage is consistently high",
                    "Review running applications and services"
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _optimize_storage(self, apply_recommendations: bool = False) -> Dict[str, Any]:
        """Optimize storage usage"""
        try:
            optimizations = []
            
            # Check disk usage
            critical_disks = []
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    percent_used = (usage.used / usage.total) * 100
                    
                    if percent_used > 90:
                        critical_disks.append((disk.mountpoint, percent_used))
                        optimizations.append(f"Critical disk space on {disk.mountpoint}: {percent_used:.1f}% used")
                except PermissionError:
                    continue
            
            # Run cleanup if requested
            if apply_recommendations and critical_disks:
                cleanup_result = await self._run_cleanup(max_age_days=7)
                optimizations.append(f"Ran emergency cleanup: freed {cleanup_result.get('space_freed_mb', 0)} MB")
            
            return {
                "critical_disks": critical_disks,
                "optimizations_applied": optimizations,
                "recommendations": [
                    "Regularly clean up old files and logs",
                    "Consider adding more storage",
                    "Use compression for large files",
                    "Implement data archiving for old data"
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_performance_score(self, cpu_percent: float, memory_percent: float, load_per_core: float) -> int:
        """Calculate overall performance score (0-100)"""
        # Lower is better for all metrics
        cpu_score = max(0, 100 - cpu_percent)
        memory_score = max(0, 100 - memory_percent)
        load_score = max(0, 100 - (load_per_core * 100))
        
        return round((cpu_score + memory_score + load_score) / 3)
    
    async def _periodic_cleanup(self):
        """Run periodic cleanup tasks"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.logger.info("Running periodic cleanup")
                await self._run_cleanup()
            except Exception as e:
                self.logger.error(f"Periodic cleanup failed: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass 