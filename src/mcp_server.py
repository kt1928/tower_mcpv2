"""
Unraid MCP Server Core Implementation
Simple MCP protocol implementation without external dependencies
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# Add utils and src to path for imports
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))
sys.path.insert(0, str(current_dir))

# Import tool modules
from tools.system_diagnostics import SystemDiagnostics
from tools.docker_management import DockerManagement
from tools.plex_integration import PlexIntegration
from tools.log_analysis import LogAnalysis
from tools.maintenance import Maintenance

from config_manager import ConfigManager


class SimpleMCPServer:
    """Simple MCP Server implementation"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Tool instances
        self.tools: Dict[str, Any] = {}
        
        # Server state
        self.is_initialized = False
        self.start_time = None
        
        # Request ID counter
        self.request_id = 0
        
    async def initialize(self):
        """Initialize the MCP server and all tools"""
        try:
            self.logger.info("Initializing Unraid MCP Server...")
            self.start_time = datetime.now()
            
            # Initialize tool modules
            await self._initialize_tools()
            
            # Setup periodic tasks
            await self._setup_periodic_tasks()
            
            self.is_initialized = True
            self.logger.info("MCP Server initialization complete")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP server: {e}", exc_info=True)
            raise
    
    async def _initialize_tools(self):
        """Initialize all tool modules"""
        tool_configs = self.config.get("tools", {})
        
        # System Diagnostics
        if tool_configs.get("system_diagnostics", {}).get("enabled", True):
            self.tools["system_diagnostics"] = SystemDiagnostics(
                self.config.get("tools.system_diagnostics", {})
            )
            await self.tools["system_diagnostics"].initialize()
            self.logger.info("System Diagnostics tool initialized")
        
        # Docker Management
        if tool_configs.get("docker_management", {}).get("enabled", True):
            self.tools["docker_management"] = DockerManagement(
                self.config.get("tools.docker_management", {})
            )
            await self.tools["docker_management"].initialize()
            self.logger.info("Docker Management tool initialized")
        
        # Plex Integration
        if tool_configs.get("plex_integration", {}).get("enabled", True):
            self.tools["plex_integration"] = PlexIntegration(
                self.config.get("tools.plex_integration", {})
            )
            await self.tools["plex_integration"].initialize()
            self.logger.info("Plex Integration tool initialized")
        
        # Log Analysis
        if tool_configs.get("log_analysis", {}).get("enabled", True):
            self.tools["log_analysis"] = LogAnalysis(
                self.config.get("tools.log_analysis", {})
            )
            await self.tools["log_analysis"].initialize()
            self.logger.info("Log Analysis tool initialized")
        
        # Maintenance
        if tool_configs.get("maintenance", {}).get("enabled", True):
            self.tools["maintenance"] = Maintenance(
                self.config.get("tools.maintenance", {})
            )
            await self.tools["maintenance"].initialize()
            self.logger.info("Maintenance tool initialized")
    
    async def _setup_periodic_tasks(self):
        """Setup periodic background tasks"""
        # Health monitoring task
        asyncio.create_task(self._health_monitor())
        
        # Cleanup tasks
        asyncio.create_task(self._cleanup_tasks())
    
    async def _health_monitor(self):
        """Periodic health monitoring"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Log health status
                if self.is_initialized:
                    self.logger.debug("MCP Server health check passed")
                    
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
    
    async def _cleanup_tasks(self):
        """Periodic cleanup tasks"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Perform cleanup tasks
                for tool_name, tool_instance in self.tools.items():
                    if hasattr(tool_instance, 'cleanup'):
                        try:
                            await tool_instance.cleanup()
                        except Exception as e:
                            self.logger.error(f"Cleanup error in {tool_name}: {e}")
                
                self.logger.debug("Periodic cleanup completed")
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            self.logger.debug(f"Handling MCP request: {method}")
            
            if method == "initialize":
                return await self._handle_initialize(params, request_id)
            elif method == "tools/list":
                return await self._handle_list_tools(params, request_id)
            elif method == "tools/call":
                return await self._handle_call_tool(params, request_id)
            elif method == "resources/list":
                return await self._handle_list_resources(params, request_id)
            elif method == "resources/read":
                return await self._handle_read_resource(params, request_id)
            else:
                return self._create_error_response(
                    request_id, 
                    -32601, 
                    f"Method not found: {method}"
                )
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}", exc_info=True)
            return self._create_error_response(
                request.get("id"), 
                -32603, 
                f"Internal error: {str(e)}"
            )
    
    async def _handle_initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle initialization request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "unraid-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request"""
        tools = []
        
        for tool_name, tool_instance in self.tools.items():
            try:
                tool_definitions = await tool_instance.get_tool_definitions()
                for tool_def in tool_definitions:
                    tools.append({
                        "name": f"{tool_name}.{tool_def.name}",
                        "description": tool_def.description,
                        "inputSchema": tool_def.inputSchema
                    })
            except Exception as e:
                self.logger.error(f"Error getting tools from {tool_name}: {e}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle tools/call request"""
        try:
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            self.logger.debug(f"Handling tool call: {name} with args: {arguments}")
            
            # Parse tool name to get module and method
            if "." in name:
                tool_module, method = name.split(".", 1)
            else:
                tool_module = name
                method = "default"
            
            if tool_module not in self.tools:
                raise ValueError(f"Tool module '{tool_module}' not found")
            
            tool_instance = self.tools[tool_module]
            
            # Call the tool method
            if hasattr(tool_instance, 'handle_call'):
                result = await tool_instance.handle_call(method, arguments)
            else:
                # Fallback to direct method call
                if hasattr(tool_instance, method):
                    method_func = getattr(tool_instance, method)
                    if asyncio.iscoroutinefunction(method_func):
                        result = await method_func(**arguments)
                    else:
                        result = method_func(**arguments)
                else:
                    raise ValueError(f"Method '{method}' not found in tool '{tool_module}'")
            
            # Convert result to MCP format
            if isinstance(result, dict):
                content = [{"type": "text", "text": str(result)}]
            else:
                content = [{"type": "text", "text": str(result)}]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": content
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in tool call {name}: {e}", exc_info=True)
            return self._create_error_response(
                request_id, 
                -32603, 
                f"Tool call error: {str(e)}"
            )
    
    async def _handle_list_resources(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request"""
        uri = params.get("uri", "")
        resources = []
        
        # Add system information as resources
        if uri == "unraid://" or uri == "":
            resources.extend([
                {
                    "uri": "unraid://system/overview",
                    "name": "System Overview",
                    "description": "Current system status and health",
                    "mimeType": "application/json"
                },
                {
                    "uri": "unraid://system/health",
                    "name": "System Health",
                    "description": "Detailed system health information",
                    "mimeType": "application/json"
                },
                {
                    "uri": "unraid://docker/containers",
                    "name": "Docker Containers",
                    "description": "List of running Docker containers",
                    "mimeType": "application/json"
                },
                {
                    "uri": "unraid://plex/status",
                    "name": "Plex Status",
                    "description": "Plex server status and statistics",
                    "mimeType": "application/json"
                }
            ])
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": resources
            }
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle resources/read request"""
        try:
            uri = params.get("uri")
            
            if uri.startswith("unraid://system/overview"):
                # Get system overview
                if "system_diagnostics" in self.tools:
                    result = await self.tools["system_diagnostics"].handle_call("get_system_overview", {})
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [{"type": "text", "text": str(result)}]
                        }
                    }
            
            elif uri.startswith("unraid://system/health"):
                # Get system health
                if "system_diagnostics" in self.tools:
                    result = await self.tools["system_diagnostics"].handle_call("check_system_health", {})
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [{"type": "text", "text": str(result)}]
                        }
                    }
            
            elif uri.startswith("unraid://docker/containers"):
                # Get Docker containers
                if "docker_management" in self.tools:
                    result = await self.tools["docker_management"].handle_call("list_containers", {})
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [{"type": "text", "text": str(result)}]
                        }
                    }
            
            elif uri.startswith("unraid://plex/status"):
                # Get Plex status
                if "plex_integration" in self.tools:
                    result = await self.tools["plex_integration"].handle_call("get_plex_status", {})
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "contents": [{"type": "text", "text": str(result)}]
                        }
                    }
            
            raise ValueError(f"Unknown resource: {uri}")
            
        except Exception as e:
            self.logger.error(f"Error reading resource {uri}: {e}")
            return self._create_error_response(
                request_id, 
                -32603, 
                f"Resource read error: {str(e)}"
            )
    
    def _create_error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": "unraid-mcp-server",
            "version": "1.0.0",
            "description": "MCP Server for Unraid System Management",
            "tools": list(self.tools.keys()),
            "uptime": datetime.now() - self.start_time if self.start_time else None,
            "status": "running" if self.is_initialized else "initializing"
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up MCP server...")
        
        # Cleanup tools
        for tool_name, tool_instance in self.tools.items():
            if hasattr(tool_instance, 'cleanup'):
                try:
                    await tool_instance.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up {tool_name}: {e}")
        
        self.logger.info("MCP server cleanup complete")
    
    async def run(self):
        """Run the MCP server using stdio"""
        # Initialize the server
        await self.initialize()
        
        # Read from stdin and write to stdout
        while True:
            try:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, input)
                
                if not line.strip():
                    continue
                
                # Parse JSON request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON: {e}")
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response
                print(json.dumps(response))
                sys.stdout.flush()
                
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error in MCP server loop: {e}")
                break
        
        await self.cleanup()


# Alias for backward compatibility
UnraidMCPServer = SimpleMCPServer