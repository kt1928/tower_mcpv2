"""
Tool definitions for Unraid MCP Server
"""

from typing import Dict, Any, Optional


class Tool:
    """Simple Tool class to replace MCP framework dependency"""
    
    def __init__(self, name: str, description: str, inputSchema: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema or {} 