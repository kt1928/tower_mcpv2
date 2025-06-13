"""
Unraid MCP Server Core Implementation
"""

import asyncio
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Add utils and src to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent / "utils"))
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
        self.app = FastAPI(
            title="Unraid MCP Server",
            description="MCP Server for Unraid System Management",
            version="1.0.0"
        )
        
        # Tool instances
        self.tools: Dict[str, Any] = {}
        
        # Server state
        self.is_initialized = False
        self.start_time = None
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with basic info"""
            return {
                "message": "Unraid MCP Server",
                "version": "1.0.0",
                "status": "running",
                "tools": list(self.tools.keys())
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            uptime = datetime.now() - self.start_time if self.start_time else None
            
            health_data = {
                "status": "healthy" if self.is_initialized else "initializing",
                "server": "unraid-mcp-server",
                "version": "1.0.0",
                "uptime_seconds": uptime.total_seconds() if uptime else 0,
                "tools_count": len(self.tools),
                "timestamp": datetime.now().isoformat()
            }
            
            # Tool-specific health checks
            for tool_name, tool_instance in self.tools.items():
                if hasattr(tool_instance, 'health_check'):
                    try:
                        tool_health = await tool_instance.health_check()
                        health_data[f"{tool_name}_health"] = tool_health
                    except Exception as e:
                        health_data[f"{tool_name}_health"] = {"error": str(e)}
            
            return health_data
        
        @self.app.get("/tools")
        async def list_tools():
            """List available tools"""
            tools_info = {}
            for tool_name, tool_instance in self.tools.items():
                try:
                    tool_definitions = await tool_instance.get_tool_definitions()
                    tools_info[tool_name] = {
                        "tools": [tool.name for tool in tool_definitions],
                        "description": tool_definitions[0].description if tool_definitions else "No description"
                    }
                except Exception as e:
                    tools_info[tool_name] = {"error": str(e)}
            
            return tools_info
        
        @self.app.post("/tools/{tool_name}/{method}")
        async def call_tool(tool_name: str, method: str, arguments: Dict[str, Any] = None):
            """Call a specific tool method"""
            if arguments is None:
                arguments = {}
            
            try:
                result = await self._handle_tool_call(tool_name, method, arguments)
                return JSONResponse(content=result)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/mcp")
        async def mcp_endpoint():
            """MCP protocol endpoint for compatibility"""
            return {
                "protocol": "mcp",
                "version": "1.0.0",
                "server": "unraid-mcp-server",
                "tools": list(self.tools.keys())
            }
        
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
        """Get server information"""
        return {
            "name": "unraid-mcp-server",
            "version": "1.0.0",
            "status": "running" if self.is_initialized else "initializing",
            "tools": list(self.tools.keys()),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        self.logger.info("Cleaning up MCP server...")
        
        # Cleanup tool instances
        for tool_name, tool_instance in self.tools.items():
            if hasattr(tool_instance, 'cleanup'):
                try:
                    await tool_instance.cleanup()
                except Exception as e:
                    self.logger.error(f"Error cleaning up {tool_name}: {e}")
        
        self.logger.info("MCP server cleanup complete")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application"""
        return self.app