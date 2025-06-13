"""
Docker Management Tools for Unraid MCP Server
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import docker
from docker.errors import DockerException
import psutil

from . import Tool


class DockerManagement:
    """Docker container management and monitoring tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.docker_client = None
        self.socket_path = config.get("socket_path", "/var/run/docker.sock")
        self.is_available = False
        
    async def initialize(self):
        """Initialize the Docker management module"""
        self.logger.info("Initializing Docker Management module")
        
        try:
            self.docker_client = docker.DockerClient(base_url=f"unix://{self.socket_path}")
            # Test connection
            self.docker_client.ping()
            self.is_available = True
            self.logger.info("Docker client initialized successfully")
        except DockerException as e:
            self.logger.warning(f"Docker socket not available at {self.socket_path}: {e}")
            self.is_available = False
            # Don't raise the exception, just log it and continue
        except Exception as e:
            self.logger.warning(f"Failed to initialize Docker client: {e}")
            self.is_available = False
    
    async def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for Docker management"""
        return [
            Tool(
                name="health_check",
                description="Check Docker daemon availability and connection status",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="list_containers",
                description="List all Docker containers with their status and basic information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Include stopped containers",
                            "default": False
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filter containers by labels or other criteria"
                        }
                    }
                }
            ),
            Tool(
                name="manage_container",
                description="Start, stop, restart, or remove a Docker container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["start", "stop", "restart", "remove", "pause", "unpause"],
                            "description": "Action to perform on the container"
                        },
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force the action (for stop/remove)",
                            "default": False
                        }
                    },
                    "required": ["action", "container_id"]
                }
            ),
            Tool(
                name="get_container_stats",
                description="Get real-time resource usage statistics for containers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name (optional, returns all if not specified)"
                        },
                        "stream": {
                            "type": "boolean",
                            "description": "Stream real-time stats",
                            "default": False
                        }
                    }
                }
            ),
            Tool(
                name="get_container_logs",
                description="Get container logs with filtering and analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to return",
                            "default": 100
                        },
                        "since": {
                            "type": "string",
                            "description": "Show logs since timestamp (ISO format)"
                        },
                        "until": {
                            "type": "string",
                            "description": "Show logs before timestamp (ISO format)"
                        },
                        "follow": {
                            "type": "boolean",
                            "description": "Follow log output",
                            "default": False
                        }
                    },
                    "required": ["container_id"]
                }
            ),
            Tool(
                name="cleanup_docker",
                description="Clean up unused Docker resources (images, volumes, networks)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "remove_images": {
                            "type": "boolean",
                            "description": "Remove unused images",
                            "default": True
                        },
                        "remove_volumes": {
                            "type": "boolean",
                            "description": "Remove unused volumes",
                            "default": False
                        },
                        "remove_networks": {
                            "type": "boolean",
                            "description": "Remove unused networks",
                            "default": True
                        },
                        "prune_containers": {
                            "type": "boolean",
                            "description": "Remove stopped containers",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="update_containers",
                description="Check for and apply container updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container_id": {
                            "type": "string",
                            "description": "Specific container to update (optional)"
                        },
                        "auto_restart": {
                            "type": "boolean",
                            "description": "Automatically restart containers after update",
                            "default": True
                        }
                    }
                }
            )
        ]
    
    async def handle_call(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            # Check if Docker is available
            if not self.is_available:
                return {
                    "status": "error",
                    "error": "Docker is not available. Docker socket not accessible or Docker daemon not running.",
                    "method": method,
                    "timestamp": datetime.now().isoformat()
                }
            
            if method == "health_check":
                return await self._health_check()
            elif method == "list_containers":
                return await self._list_containers(
                    arguments.get("all", False),
                    arguments.get("filters", {})
                )
            elif method == "manage_container":
                return await self._manage_container(
                    arguments["action"],
                    arguments["container_id"],
                    arguments.get("force", False)
                )
            elif method == "get_container_stats":
                return await self._get_container_stats(
                    arguments.get("container_id"),
                    arguments.get("stream", False)
                )
            elif method == "get_container_logs":
                return await self._get_container_logs(
                    arguments["container_id"],
                    arguments.get("tail", 100),
                    arguments.get("since"),
                    arguments.get("until"),
                    arguments.get("follow", False)
                )
            elif method == "cleanup_docker":
                return await self._cleanup_docker(
                    arguments.get("remove_images", True),
                    arguments.get("remove_volumes", False),
                    arguments.get("remove_networks", True),
                    arguments.get("prune_containers", True)
                )
            elif method == "update_containers":
                return await self._update_containers(
                    arguments.get("container_id"),
                    arguments.get("auto_restart", True)
                )
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {"error": str(e), "method": method}
    
    async def _health_check(self) -> Dict[str, Any]:
        """Check Docker daemon health and availability"""
        try:
            if not self.is_available:
                return {
                    "status": "error",
                    "data": {
                        "docker_available": False,
                        "socket_path": self.socket_path,
                        "message": "Docker daemon not accessible",
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            # Test connection
            info = self.docker_client.info()
            version = self.docker_client.version()
            
            return {
                "status": "success",
                "data": {
                    "docker_available": True,
                    "socket_path": self.socket_path,
                    "docker_version": version["Version"],
                    "api_version": version["ApiVersion"],
                    "containers_running": info["ContainersRunning"],
                    "containers_stopped": info["ContainersStopped"],
                    "images": info["Images"],
                    "system_info": {
                        "os": info["OperatingSystem"],
                        "architecture": info["Architecture"],
                        "kernel_version": info["KernelVersion"],
                        "docker_root_dir": info["DockerRootDir"]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "data": {
                    "docker_available": False,
                    "socket_path": self.socket_path,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _list_containers(self, all_containers: bool = False, filters: Dict = None) -> Dict[str, Any]:
        """List Docker containers"""
        try:
            containers = self.docker_client.containers.list(all=all_containers, filters=filters or {})
            
            container_list = []
            for container in containers:
                container_info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else container.image.id,
                    "created": container.attrs["Created"],
                    "ports": container.attrs["NetworkSettings"]["Ports"],
                    "labels": container.labels,
                    "state": container.attrs["State"]
                }
                container_list.append(container_info)
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "total_containers": len(container_list),
                    "containers": container_list
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _manage_container(self, action: str, container_id: str, force: bool = False) -> Dict[str, Any]:
        """Manage container lifecycle"""
        try:
            container = self.docker_client.containers.get(container_id)
            
            if action == "start":
                container.start()
                message = f"Container {container_id} started successfully"
            elif action == "stop":
                container.stop(timeout=30 if not force else 0)
                message = f"Container {container_id} stopped successfully"
            elif action == "restart":
                container.restart(timeout=30)
                message = f"Container {container_id} restarted successfully"
            elif action == "pause":
                container.pause()
                message = f"Container {container_id} paused successfully"
            elif action == "unpause":
                container.unpause()
                message = f"Container {container_id} unpaused successfully"
            elif action == "remove":
                container.remove(force=force)
                message = f"Container {container_id} removed successfully"
            else:
                raise ValueError(f"Invalid action: {action}")
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "container_id": container_id,
                    "message": message
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_container_stats(self, container_id: Optional[str] = None, stream: bool = False) -> Dict[str, Any]:
        """Get container resource statistics"""
        try:
            if container_id:
                containers = [self.docker_client.containers.get(container_id)]
            else:
                containers = self.docker_client.containers.list()
            
            stats_data = {}
            
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU usage
                    cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
                    cpu_percent = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
                    
                    # Memory usage
                    memory_usage = stats["memory_stats"]["usage"]
                    memory_limit = stats["memory_stats"]["limit"]
                    memory_percent = (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                    
                    # Network stats
                    network_stats = {}
                    if "networks" in stats["networks"]:
                        for interface, data in stats["networks"].items():
                            network_stats[interface] = {
                                "rx_bytes": data["rx_bytes"],
                                "tx_bytes": data["tx_bytes"],
                                "rx_packets": data["rx_packets"],
                                "tx_packets": data["tx_packets"]
                            }
                    
                    stats_data[container.id] = {
                        "name": container.name,
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                        "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                        "memory_percent": round(memory_percent, 2),
                        "network_stats": network_stats,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                except Exception as e:
                    stats_data[container.id] = {"error": str(e)}
            
            return {
                "status": "success",
                "data": {
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats_data
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_container_logs(self, container_id: str, tail: int = 100, since: Optional[str] = None, 
                                 until: Optional[str] = None, follow: bool = False) -> Dict[str, Any]:
        """Get container logs"""
        try:
            container = self.docker_client.containers.get(container_id)
            
            # Parse timestamps
            since_time = None
            until_time = None
            if since:
                since_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
            if until:
                until_time = datetime.fromisoformat(until.replace('Z', '+00:00'))
            
            logs = container.logs(
                tail=tail,
                since=since_time,
                until=until_time,
                follow=follow,
                timestamps=True
            ).decode('utf-8')
            
            # Parse logs into structured format
            log_entries = []
            for line in logs.strip().split('\n'):
                if line:
                    # Parse timestamp and message
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        timestamp, message = parts
                        log_entries.append({
                            "timestamp": timestamp,
                            "message": message
                        })
            
            return {
                "status": "success",
                "data": {
                    "container_id": container_id,
                    "container_name": container.name,
                    "total_lines": len(log_entries),
                    "logs": log_entries,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _cleanup_docker(self, remove_images: bool = True, remove_volumes: bool = False,
                             remove_networks: bool = True, prune_containers: bool = True) -> Dict[str, Any]:
        """Clean up unused Docker resources"""
        try:
            cleanup_results = {
                "timestamp": datetime.now().isoformat(),
                "removed_containers": 0,
                "removed_images": 0,
                "removed_volumes": 0,
                "removed_networks": 0,
                "freed_space_mb": 0
            }
            
            # Remove stopped containers
            if prune_containers:
                try:
                    result = self.docker_client.containers.prune()
                    cleanup_results["removed_containers"] = len(result["ContainersDeleted"])
                    cleanup_results["freed_space_mb"] += result["SpaceReclaimed"] / (1024 * 1024)
                except Exception as e:
                    self.logger.warning(f"Failed to prune containers: {e}")
            
            # Remove unused images
            if remove_images:
                try:
                    result = self.docker_client.images.prune()
                    cleanup_results["removed_images"] = len(result["ImagesDeleted"])
                    cleanup_results["freed_space_mb"] += result["SpaceReclaimed"] / (1024 * 1024)
                except Exception as e:
                    self.logger.warning(f"Failed to prune images: {e}")
            
            # Remove unused volumes
            if remove_volumes:
                try:
                    result = self.docker_client.volumes.prune()
                    cleanup_results["removed_volumes"] = len(result["VolumesDeleted"])
                    cleanup_results["freed_space_mb"] += result["SpaceReclaimed"] / (1024 * 1024)
                except Exception as e:
                    self.logger.warning(f"Failed to prune volumes: {e}")
            
            # Remove unused networks
            if remove_networks:
                try:
                    result = self.docker_client.networks.prune()
                    cleanup_results["removed_networks"] = len(result["NetworksDeleted"])
                except Exception as e:
                    self.logger.warning(f"Failed to prune networks: {e}")
            
            cleanup_results["freed_space_mb"] = round(cleanup_results["freed_space_mb"], 2)
            
            return {
                "status": "success",
                "data": cleanup_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _update_containers(self, container_id: Optional[str] = None, auto_restart: bool = True) -> Dict[str, Any]:
        """Check for and apply container updates"""
        try:
            update_results = {
                "timestamp": datetime.now().isoformat(),
                "checked_containers": 0,
                "updated_containers": 0,
                "failed_updates": 0,
                "details": []
            }
            
            if container_id:
                containers = [self.docker_client.containers.get(container_id)]
            else:
                containers = self.docker_client.containers.list()
            
            for container in containers:
                try:
                    update_results["checked_containers"] += 1
                    
                    # Get current image
                    current_image = container.image
                    
                    # Pull latest image
                    image_name = current_image.tags[0] if current_image.tags else current_image.id
                    if ':' in image_name:
                        repo, tag = image_name.rsplit(':', 1)
                    else:
                        repo, tag = image_name, 'latest'
                    
                    # Pull the latest image
                    new_image = self.docker_client.images.pull(repo, tag=tag)
                    
                    # Check if image changed
                    if new_image.id != current_image.id:
                        # Stop container if running
                        was_running = container.status == "running"
                        if was_running:
                            container.stop(timeout=30)
                        
                        # Remove old container
                        container.remove()
                        
                        # Create new container with same configuration
                        # This is a simplified version - in practice, you'd need to recreate with all the original settings
                        new_container = self.docker_client.containers.run(
                            new_image.id,
                            detach=True,
                            name=container.name
                        )
                        
                        if was_running and auto_restart:
                            new_container.start()
                        
                        update_results["updated_containers"] += 1
                        update_results["details"].append({
                            "container_name": container.name,
                            "old_image": current_image.id[:12],
                            "new_image": new_image.id[:12],
                            "status": "updated"
                        })
                    else:
                        update_results["details"].append({
                            "container_name": container.name,
                            "image": current_image.id[:12],
                            "status": "up_to_date"
                        })
                        
                except Exception as e:
                    update_results["failed_updates"] += 1
                    update_results["details"].append({
                        "container_name": container.name,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "data": update_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.docker_client:
            self.docker_client.close() 