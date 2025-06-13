"""
Dual-Mode Server for Unraid MCP Server
Runs both MCP protocol (stdio) and HTTP interface simultaneously
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src and utils to path for imports
current_dir = Path(__file__).parent
utils_dir = current_dir.parent / "utils"
sys.path.insert(0, str(utils_dir))
sys.path.insert(0, str(current_dir))

from mcp_server import UnraidMCPServer
from http_server import HTTPServer
from logging_config import setup_logging
from config_manager import ConfigManager


class DualServer:
    """Dual-mode server running both MCP and HTTP"""
    
    def __init__(self):
        self.config = None
        self.logger = None
        self.mcp_server = None
        self.http_server = None
        self.tasks = []
        
    async def startup(self):
        """Initialize the application"""
        # Load configuration
        self.config = ConfigManager()
        await self.config.load()
        
        # Setup logging
        self.logger = setup_logging(self.config.get("logging", {}))
        self.logger.info("Starting Unraid MCP Server (Dual Mode)...")
        
        # Initialize MCP server
        self.mcp_server = UnraidMCPServer(self.config)
        await self.mcp_server.initialize()
        
        # Initialize HTTP server
        self.http_server = HTTPServer(self.config, self.mcp_server)
        
        self.logger.info("Dual-mode server initialized successfully")
        
    async def shutdown(self):
        """Cleanup on shutdown"""
        if self.logger:
            self.logger.info("Shutting down Dual-Mode Server...")
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Cleanup MCP server
        if self.mcp_server:
            await self.mcp_server.cleanup()
            
        if self.logger:
            self.logger.info("Dual-Mode Server stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run_mcp_server(self):
        """Run the MCP server"""
        try:
            await self.mcp_server.run()
        except Exception as e:
            self.logger.error(f"MCP server error: {e}", exc_info=True)
    
    async def run_http_server(self):
        """Run the HTTP server"""
        try:
            await self.http_server.run()
        except Exception as e:
            self.logger.error(f"HTTP server error: {e}", exc_info=True)
    
    async def run(self):
        """Run both servers"""
        # Start both servers as concurrent tasks
        mcp_task = asyncio.create_task(self.run_mcp_server())
        http_task = asyncio.create_task(self.run_http_server())
        
        self.tasks = [mcp_task, http_task]
        
        # Wait for both tasks
        try:
            await asyncio.gather(mcp_task, http_task)
        except Exception as e:
            self.logger.error(f"Server error: {e}", exc_info=True)
        finally:
            await self.shutdown()


async def main():
    """Main application function"""
    server = DualServer()
    
    try:
        # Setup signal handlers
        server.setup_signal_handlers()
        
        # Initialize application
        await server.startup()
        
        # Run both servers
        await server.run()
        
    except Exception as e:
        if server.logger:
            server.logger.error(f"Application error: {e}", exc_info=True)
        else:
            print(f"Application error: {e}")
        sys.exit(1)


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