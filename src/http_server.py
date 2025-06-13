"""
HTTP Server Wrapper for Unraid MCP Server
Provides health checks and basic API endpoints while the main server runs as MCP
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

# Add utils and src to path for imports
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))
sys.path.insert(0, str(current_dir))

from config_manager import ConfigManager


class HTTPServer:
    """HTTP server for health checks and basic API"""
    
    def __init__(self, config: ConfigManager, mcp_server=None):
        self.config = config
        self.mcp_server = mcp_server
        self.logger = logging.getLogger(__name__)
        
        self.app = FastAPI(
            title="Unraid MCP Server - HTTP Interface",
            description="HTTP interface for Unraid MCP Server health checks and basic API",
            version="1.0.0"
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with basic info"""
            return {
                "message": "Unraid MCP Server - HTTP Interface",
                "version": "1.0.0",
                "status": "running",
                "mcp_server": "active" if self.mcp_server else "inactive",
                "note": "This is the HTTP interface. For MCP protocol, use stdio connection."
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            health_data = {
                "status": "healthy",
                "server": "unraid-mcp-server-http",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "mcp_server_status": "active" if self.mcp_server else "inactive"
            }
            
            if self.mcp_server:
                try:
                    server_info = await self.mcp_server.get_server_info()
                    health_data.update({
                        "mcp_tools": server_info.get("tools", []),
                        "mcp_uptime": str(server_info.get("uptime", "unknown")),
                        "mcp_status": server_info.get("status", "unknown")
                    })
                except Exception as e:
                    health_data["mcp_error"] = str(e)
            
            return health_data
        
        @self.app.get("/status")
        async def status():
            """Detailed status endpoint"""
            status_data = {
                "http_server": {
                    "status": "running",
                    "port": self.config.get("http.port", 9090),
                    "host": self.config.get("http.host", "0.0.0.0")
                },
                "mcp_server": {
                    "status": "active" if self.mcp_server else "inactive",
                    "protocol": "stdio",
                    "version": "1.0.0"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            if self.mcp_server:
                try:
                    server_info = await self.mcp_server.get_server_info()
                    status_data["mcp_server"].update({
                        "tools": server_info.get("tools", []),
                        "uptime": str(server_info.get("uptime", "unknown")),
                        "description": server_info.get("description", "")
                    })
                except Exception as e:
                    status_data["mcp_server"]["error"] = str(e)
            
            return status_data
        
        @self.app.get("/mcp-info")
        async def mcp_info():
            """MCP protocol information"""
            return {
                "protocol": "mcp",
                "version": "1.0.0",
                "server": "unraid-mcp-server",
                "connection_method": "stdio",
                "description": "This server implements the Model Context Protocol (MCP) for Unraid system management",
                "tools_available": self.mcp_server.tools.keys() if self.mcp_server else [],
                "usage": "Connect using MCP client (e.g., Claude Desktop) with stdio transport"
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            if not self.mcp_server:
                return {"error": "MCP server not available"}
            
            tools_info = {}
            for tool_name, tool_instance in self.mcp_server.tools.items():
                try:
                    tool_definitions = await tool_instance.get_tool_definitions()
                    tools_info[tool_name] = {
                        "tools": [tool.name for tool in tool_definitions],
                        "description": tool_definitions[0].description if tool_definitions else "No description"
                    }
                except Exception as e:
                    tools_info[tool_name] = {"error": str(e)}
            
            return tools_info
    
    async def run(self):
        """Run the HTTP server"""
        host = self.config.get("http.host", "0.0.0.0")
        port = self.config.get("http.port", 9090)
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app"""
        return self.app 