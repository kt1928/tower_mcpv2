#!/usr/bin/env python3
"""
Unraid MCP Server - Main Entry Point
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# Add src and utils to path for local imports
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))
sys.path.insert(0, str(current_dir))

from mcp_server import UnraidMCPServer
from logging_config import setup_logging
from config_manager import ConfigManager


class Application:
    """Main application class"""
    
    def __init__(self):
        self.mcp_server = None
        self.config = None
        self.logger = None
        
    async def startup(self):
        """Initialize the application"""
        # Load configuration
        self.config = ConfigManager()
        await self.config.load()
        
        # Setup logging
        self.logger = setup_logging(self.config.get("logging", {}))
        self.logger.info("Starting Unraid MCP Server...")
        
        # Initialize MCP server
        self.mcp_server = UnraidMCPServer(self.config)
        await self.mcp_server.initialize()
        
        self.logger.info("Unraid MCP Server started successfully")
        
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.logger:
            self.logger.info("Shutting down Unraid MCP Server...")
        
        if self.mcp_server:
            await self.mcp_server.cleanup()
            
        if self.logger:
            self.logger.info("Unraid MCP Server stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main application function"""
    app = Application()
    
    try:
        # Setup signal handlers
        app.setup_signal_handlers()
        
        # Initialize application
        await app.startup()
        
        # Get the FastAPI app from MCP server
        fastapi_app = app.mcp_server.get_app()
        
        # Get configuration
        host = app.config.get("server.host", "0.0.0.0")
        port = app.config.get("server.port", 8080)
        
        # Start the server
        config = uvicorn.Config(
            fastapi_app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        
        # Run the server
        await server.serve()
        
    except Exception as e:
        if app.logger:
            app.logger.error(f"Application error: {e}", exc_info=True)
        else:
            print(f"Application error: {e}")
        sys.exit(1)
    finally:
        await app.shutdown()


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)