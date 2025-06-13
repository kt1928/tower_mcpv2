"""
Unraid MCP Server Core Implementation
"""

import asyncio
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from mcp import McpServer
from mcp.types import Tool, Resource

# Add utils to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))

# Import tool modules
from tools.system_diagnostics import SystemDiagnostics
from tools.docker_management import DockerManagement
from tools.plex_integration import PlexIntegration
from tools.log_analysis import LogAnalysis
from tools.maintenance import Maintenance

from config_manager import ConfigManager


class UnraidMCPServer:
    """Main MCP Server for Unraid management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.mcp_server = McpServer("unraid-mcp-server")
        
        # Tool instances
        self.tools: Dict[str, Any] = {}
        
        # Server state
        self.is_initialized = False
        self.start_time = None
        
    async def initialize(self):
        """Initialize the MCP server and all tools"""
        try:
            self.logger.info("Initializing Unraid MCP Server...")
            self.start_time = datetime.now()
            
            # Initialize tool modules
            await self._initialize_tools()
            
            # Register tools with MCP server
            await self._register_tools()
            
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
    
    async def _register_tools(self):
        """Register all tools with the MCP server"""
        for tool_name, tool_instance in self.tools.items():
            # Get tool definitions from each module
            tool_definitions = await tool_instance.get_tool_definitions()
            
            for tool_def in tool_definitions:
                # Register tool with MCP server
                @self.mcp_server.tool(tool_def)
                async def tool_handler(arguments: Dict[str, Any], tool_name=tool_name, method=tool_def.name):
                    return await self._handle_tool_call(tool_name, method, arguments)
                
                self.logger.debug(f"Registered tool: {tool_def.name}")
        
        self.logger.info(f"Registered {sum(len(await t.get_tool_definitions()) for t in self.tools.values())} tools")
    
    async def _handle_tool_call(self, tool_name: str, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls and route to appropriate tool module"""
        try:
            self.logger.debug(f"Handling tool call: {tool_name}.{method} with args: {arguments}")
            
            if tool_name not in self.tools:
                raise ValueError(f"Tool module '{tool_name}' not found")
            
            tool_instance = self.tools[tool_name]
            result = await tool_instance.handle_call(method, arguments)
            
            self.logger.debug(f"Tool call result: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error handling tool call {tool_name}.{method}: {e}", exc_info=True)
            return {
                "error": str(e),
                "tool": tool_name,
                "method": method,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _setup_periodic_tasks(self):
        """Setup periodic background tasks"""
        # Health monitoring
        asyncio.create_task(self._health_monitor())
        
        # Cleanup tasks
        asyncio.create_task(self._cleanup_tasks())
        
        # Tool-specific periodic tasks
        for tool_instance in self.tools.values():
            if hasattr(tool_instance, 'start_periodic_tasks'):
                asyncio.create_task(tool_instance.start_periodic_tasks())
    
    async def _health_monitor(self):
        """Monitor server health"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Basic health checks
                uptime = datetime.now() - self.start_time if self.start_time else None
                
                health_data = {
                    "status": "healthy",
                    "uptime_seconds": uptime.total_seconds() if uptime else 0,
                    "tools_count": len(self.tools),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Tool-specific health checks
                for tool_name, tool_instance in self.tools.items():
                    if hasattr(tool_instance, 'health_check'):
                        tool_health = await tool_instance.health_check()
                        health_data[f"{tool_name}_health"] = tool_health
                
                self.logger.debug(f"Health check: {health_data}")
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}", exc_info=True)
    
    async def _cleanup_tasks(self):
        """Periodic cleanup tasks"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Cleanup old logs, cache files, etc.
                for tool_instance in self.tools.values():
                    if hasattr(tool_instance, 'cleanup'):
                        await tool_instance.cleanup()
                
                self.logger.debug("Periodic cleanup completed")
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}", exc_info=True)
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information and status"""
        uptime = datetime.now() - self.start_time if self.start_time else None
        
        return {
            "name": "unraid-mcp-server",
            "version": "1.0.0",
            "status": "running" if self.is_initialized else "initializing",
            "uptime_seconds": uptime.total_seconds() if uptime else 0,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "tools": {
                name: {
                    "status": "active",
                    "tool_count": len(await tool.get_tool_definitions())
                }
                for name, tool in self.tools.items()
            }
        }
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            self.logger.info("Cleaning up MCP server...")
            
            # Cleanup all tools
            for tool_name, tool_instance in self.tools.items():
                if hasattr(tool_instance, 'cleanup'):
                    await tool_instance.cleanup()
                    self.logger.debug(f"Cleaned up tool: {tool_name}")
            
            self.is_initialized = False
            self.logger.info("MCP server cleanup complete")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)