"""
Unraid MCP Server Core Implementation
"""

import asyncio
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from mcp import Server
from mcp.server import NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    LogMessage,
    Resource,
    ReadResourceRequest,
    ReadResourceResult,
    ListResourcesRequest,
    ListResourcesResult,
    PromptRequest,
    PromptResult,
    PromptMessage,
    PromptMessageRole,
)

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


class UnraidMCPServer:
    """Main MCP Server for Unraid management"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Create MCP server
        self.server = Server("unraid-mcp-server")
        
        # Tool instances
        self.tools: Dict[str, Any] = {}
        
        # Server state
        self.is_initialized = False
        self.start_time = None
        
        # Setup MCP handlers
        self._setup_mcp_handlers()
        
    def _setup_mcp_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List all available tools"""
            tools = []
            
            for tool_name, tool_instance in self.tools.items():
                try:
                    tool_definitions = await tool_instance.get_tool_definitions()
                    for tool_def in tool_definitions:
                        # Convert our Tool format to MCP Tool format
                        mcp_tool = Tool(
                            name=f"{tool_name}.{tool_def.name}",
                            description=tool_def.description,
                            inputSchema=tool_def.inputSchema
                        )
                        tools.append(mcp_tool)
                except Exception as e:
                    self.logger.error(f"Error getting tools from {tool_name}: {e}")
            
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
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
                    content = [TextContent(type="text", text=str(result))]
                else:
                    content = [TextContent(type="text", text=str(result))]
                
                return CallToolResult(
                    content=content,
                    isError=False
                )
                
            except Exception as e:
                self.logger.error(f"Error in tool call {name}: {e}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )
        
        @self.server.list_resources()
        async def handle_list_resources(uri: str) -> ListResourcesResult:
            """List available resources"""
            resources = []
            
            # Add system information as resources
            if uri == "unraid://" or uri == "":
                resources.extend([
                    Resource(
                        uri="unraid://system/overview",
                        name="System Overview",
                        description="Current system status and health",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="unraid://system/health",
                        name="System Health",
                        description="Detailed system health information",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="unraid://docker/containers",
                        name="Docker Containers",
                        description="List of running Docker containers",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="unraid://plex/status",
                        name="Plex Status",
                        description="Plex server status and statistics",
                        mimeType="application/json"
                    )
                ])
            
            return ListResourcesResult(resources=resources)
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read a specific resource"""
            try:
                if uri.startswith("unraid://system/overview"):
                    # Get system overview
                    if "system_diagnostics" in self.tools:
                        result = await self.tools["system_diagnostics"].handle_call("get_system_overview", {})
                        return ReadResourceResult(
                            contents=[TextContent(type="text", text=str(result))]
                        )
                
                elif uri.startswith("unraid://system/health"):
                    # Get system health
                    if "system_diagnostics" in self.tools:
                        result = await self.tools["system_diagnostics"].handle_call("check_system_health", {})
                        return ReadResourceResult(
                            contents=[TextContent(type="text", text=str(result))]
                        )
                
                elif uri.startswith("unraid://docker/containers"):
                    # Get Docker containers
                    if "docker_management" in self.tools:
                        result = await self.tools["docker_management"].handle_call("list_containers", {})
                        return ReadResourceResult(
                            contents=[TextContent(type="text", text=str(result))]
                        )
                
                elif uri.startswith("unraid://plex/status"):
                    # Get Plex status
                    if "plex_integration" in self.tools:
                        result = await self.tools["plex_integration"].handle_call("get_plex_status", {})
                        return ReadResourceResult(
                            contents=[TextContent(type="text", text=str(result))]
                        )
                
                raise ValueError(f"Unknown resource: {uri}")
                
            except Exception as e:
                self.logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
        
        @self.server.prompt()
        async def handle_prompt(messages: List[PromptMessage]) -> PromptResult:
            """Handle prompts for additional information"""
            # For now, return a simple response
            # In the future, this could be used for interactive system management
            return PromptResult(
                content=[TextContent(type="text", text="I'm ready to help you manage your Unraid system. What would you like to do?")]
            )
    
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
                    
                    # Send health notification
                    await self.server.notify(
                        "health_check",
                        {"status": "healthy", "timestamp": datetime.now().isoformat()}
                    )
                    
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
        """Run the MCP server"""
        # Initialize the server
        await self.initialize()
        
        # Run the MCP server using stdio
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="unraid-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )