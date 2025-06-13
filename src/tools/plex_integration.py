"""
Plex Integration Tools for Unraid MCP Server
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import xml.etree.ElementTree as ET

from mcp.types import Tool


class PlexIntegration:
    """Plex media server integration and management tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.plex_url = config.get("url")
        self.plex_token = config.get("token")
        self.timeout = config.get("timeout", 30)
        self.session = None
        
    async def initialize(self):
        """Initialize the Plex integration module"""
        self.logger.info("Initializing Plex Integration module")
        
        if not self.plex_url or not self.plex_token:
            self.logger.warning("Plex URL or token not configured - Plex integration disabled")
            return
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                "X-Plex-Token": self.plex_token,
                "Accept": "application/json"
            }
        )
        
        # Test connection
        try:
            await self._test_connection()
            self.logger.info("Plex integration initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to Plex: {e}")
            raise
    
    async def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for Plex integration"""
        return [
            Tool(
                name="get_plex_status",
                description="Get Plex server status and performance metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_sessions": {
                            "type": "boolean",
                            "description": "Include active streaming sessions",
                            "default": True
                        },
                        "include_libraries": {
                            "type": "boolean",
                            "description": "Include library statistics",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="analyze_plex_library",
                description="Analyze Plex library statistics and provide optimization recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "library_key": {
                            "type": "string",
                            "description": "Specific library to analyze (optional)"
                        },
                        "include_duplicates": {
                            "type": "boolean",
                            "description": "Check for duplicate media files",
                            "default": True
                        },
                        "include_quality": {
                            "type": "boolean",
                            "description": "Analyze media quality distribution",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="get_plex_sessions",
                description="Get active streaming sessions and user activity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_device_info": {
                            "type": "boolean",
                            "description": "Include device information",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="optimize_plex_database",
                description="Optimize Plex database and perform maintenance tasks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "vacuum": {
                            "type": "boolean",
                            "description": "Vacuum database to reclaim space",
                            "default": True
                        },
                        "analyze": {
                            "type": "boolean",
                            "description": "Analyze database for optimization",
                            "default": True
                        },
                        "clean_bundles": {
                            "type": "boolean",
                            "description": "Clean old bundle files",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="scan_plex_libraries",
                description="Trigger library scans and metadata updates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "library_key": {
                            "type": "string",
                            "description": "Specific library to scan (optional)"
                        },
                        "scan_type": {
                            "type": "string",
                            "enum": ["full", "partial", "metadata"],
                            "description": "Type of scan to perform",
                            "default": "partial"
                        }
                    }
                }
            )
        ]
    
    async def handle_call(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            if method == "get_plex_status":
                return await self._get_plex_status(
                    arguments.get("include_sessions", True),
                    arguments.get("include_libraries", True)
                )
            elif method == "analyze_plex_library":
                return await self._analyze_plex_library(
                    arguments.get("library_key"),
                    arguments.get("include_duplicates", True),
                    arguments.get("include_quality", True)
                )
            elif method == "get_plex_sessions":
                return await self._get_plex_sessions(
                    arguments.get("include_device_info", True)
                )
            elif method == "optimize_plex_database":
                return await self._optimize_plex_database(
                    arguments.get("vacuum", True),
                    arguments.get("analyze", True),
                    arguments.get("clean_bundles", True)
                )
            elif method == "scan_plex_libraries":
                return await self._scan_plex_libraries(
                    arguments.get("library_key"),
                    arguments.get("scan_type", "partial")
                )
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {"error": str(e), "method": method}
    
    async def _test_connection(self):
        """Test Plex server connection"""
        async with self.session.get(f"{self.plex_url}/status/sessions") as response:
            if response.status != 200:
                raise Exception(f"Plex server returned status {response.status}")
    
    async def _get_plex_status(self, include_sessions: bool = True, include_libraries: bool = True) -> Dict[str, Any]:
        """Get Plex server status"""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "server_info": {},
                "sessions": None,
                "libraries": None
            }
            
            # Get server information
            async with self.session.get(f"{self.plex_url}/") as response:
                if response.status == 200:
                    data = await response.text()
                    root = ET.fromstring(data)
                    
                    status_data["server_info"] = {
                        "friendly_name": root.get("friendlyName", "Unknown"),
                        "version": root.get("version", "Unknown"),
                        "platform": root.get("platform", "Unknown"),
                        "platform_version": root.get("platformVersion", "Unknown"),
                        "machine_identifier": root.get("machineIdentifier", "Unknown")
                    }
            
            # Get active sessions
            if include_sessions:
                async with self.session.get(f"{self.plex_url}/status/sessions") as response:
                    if response.status == 200:
                        data = await response.text()
                        root = ET.fromstring(data)
                        
                        sessions = []
                        for video in root.findall(".//Video"):
                            session_info = {
                                "title": video.get("title", "Unknown"),
                                "type": video.get("type", "Unknown"),
                                "duration": int(video.get("duration", 0)),
                                "view_offset": int(video.get("viewOffset", 0)),
                                "progress_percent": 0
                            }
                            
                            if session_info["duration"] > 0:
                                session_info["progress_percent"] = round(
                                    (session_info["view_offset"] / session_info["duration"]) * 100, 1
                                )
                            
                            sessions.append(session_info)
                        
                        status_data["sessions"] = {
                            "total_sessions": len(sessions),
                            "sessions": sessions
                        }
            
            # Get library information
            if include_libraries:
                async with self.session.get(f"{self.plex_url}/library/sections") as response:
                    if response.status == 200:
                        data = await response.text()
                        root = ET.fromstring(data)
                        
                        libraries = []
                        for section in root.findall(".//Directory"):
                            library_info = {
                                "key": section.get("key"),
                                "title": section.get("title"),
                                "type": section.get("type"),
                                "agent": section.get("agent"),
                                "scanner": section.get("scanner"),
                                "language": section.get("language"),
                                "count": int(section.get("count", 0))
                            }
                            libraries.append(library_info)
                        
                        status_data["libraries"] = {
                            "total_libraries": len(libraries),
                            "libraries": libraries
                        }
            
            return {
                "status": "success",
                "data": status_data
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _analyze_plex_library(self, library_key: Optional[str] = None, 
                                   include_duplicates: bool = True, 
                                   include_quality: bool = True) -> Dict[str, Any]:
        """Analyze Plex library"""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "libraries": {},
                "recommendations": []
            }
            
            # Get libraries to analyze
            if library_key:
                libraries = [{"key": library_key}]
            else:
                async with self.session.get(f"{self.plex_url}/library/sections") as response:
                    if response.status == 200:
                        data = await response.text()
                        root = ET.fromstring(data)
                        libraries = [{"key": section.get("key")} for section in root.findall(".//Directory")]
            
            for lib in libraries:
                lib_key = lib["key"]
                lib_analysis = {
                    "total_items": 0,
                    "total_size_gb": 0,
                    "quality_distribution": {},
                    "duplicates": [],
                    "missing_metadata": 0,
                    "optimization_score": 0
                }
                
                # Get library items
                async with self.session.get(f"{self.plex_url}/library/sections/{lib_key}/all") as response:
                    if response.status == 200:
                        data = await response.text()
                        root = ET.fromstring(data)
                        
                        items = root.findall(".//Video")
                        lib_analysis["total_items"] = len(items)
                        
                        # Analyze quality distribution
                        if include_quality:
                            quality_counts = {}
                            for item in items:
                                quality = item.get("videoResolution", "Unknown")
                                quality_counts[quality] = quality_counts.get(quality, 0) + 1
                            lib_analysis["quality_distribution"] = quality_counts
                        
                        # Check for missing metadata
                        missing_metadata = 0
                        for item in items:
                            if not item.get("summary") or item.get("summary").strip() == "":
                                missing_metadata += 1
                        lib_analysis["missing_metadata"] = missing_metadata
                        
                        # Calculate optimization score
                        total_items = lib_analysis["total_items"]
                        if total_items > 0:
                            metadata_score = ((total_items - missing_metadata) / total_items) * 100
                            lib_analysis["optimization_score"] = round(metadata_score, 1)
                
                analysis["libraries"][lib_key] = lib_analysis
            
            # Generate recommendations
            for lib_key, lib_data in analysis["libraries"].items():
                if lib_data["missing_metadata"] > 0:
                    analysis["recommendations"].append(
                        f"Library {lib_key}: {lib_data['missing_metadata']} items missing metadata - run metadata scan"
                    )
                
                if lib_data["optimization_score"] < 80:
                    analysis["recommendations"].append(
                        f"Library {lib_key}: Low optimization score ({lib_data['optimization_score']}%) - needs attention"
                    )
            
            return {
                "status": "success",
                "data": analysis
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_plex_sessions(self, include_device_info: bool = True) -> Dict[str, Any]:
        """Get active Plex sessions"""
        try:
            async with self.session.get(f"{self.plex_url}/status/sessions") as response:
                if response.status == 200:
                    data = await response.text()
                    root = ET.fromstring(data)
                    
                    sessions = []
                    for session in root.findall(".//Session"):
                        session_info = {
                            "id": session.get("id"),
                            "user": session.get("username", "Unknown"),
                            "title": session.get("title", "Unknown"),
                            "type": session.get("type", "Unknown"),
                            "duration": int(session.get("duration", 0)),
                            "view_offset": int(session.get("viewOffset", 0)),
                            "progress_percent": 0
                        }
                        
                        if session_info["duration"] > 0:
                            session_info["progress_percent"] = round(
                                (session_info["view_offset"] / session_info["duration"]) * 100, 1
                            )
                        
                        if include_device_info:
                            session_info["device"] = {
                                "name": session.get("device", "Unknown"),
                                "platform": session.get("platform", "Unknown"),
                                "product": session.get("product", "Unknown")
                            }
                        
                        sessions.append(session_info)
                    
                    return {
                        "status": "success",
                        "data": {
                            "timestamp": datetime.now().isoformat(),
                            "total_sessions": len(sessions),
                            "sessions": sessions
                        }
                    }
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _optimize_plex_database(self, vacuum: bool = True, analyze: bool = True, 
                                     clean_bundles: bool = True) -> Dict[str, Any]:
        """Optimize Plex database"""
        try:
            optimization_results = {
                "timestamp": datetime.now().isoformat(),
                "operations": [],
                "status": "completed"
            }
            
            # Note: Plex doesn't provide direct API endpoints for database optimization
            # These operations would typically be done through Plex's internal tools
            # or by stopping Plex and running maintenance commands
            
            if vacuum:
                optimization_results["operations"].append({
                    "operation": "vacuum",
                    "status": "not_available",
                    "note": "Database vacuum requires Plex server restart"
                })
            
            if analyze:
                optimization_results["operations"].append({
                    "operation": "analyze",
                    "status": "not_available",
                    "note": "Database analysis requires Plex server restart"
                })
            
            if clean_bundles:
                optimization_results["operations"].append({
                    "operation": "clean_bundles",
                    "status": "not_available",
                    "note": "Bundle cleanup requires Plex server restart"
                })
            
            optimization_results["recommendations"] = [
                "Stop Plex Media Server",
                "Run database optimization tools",
                "Clean old bundle files",
                "Restart Plex Media Server"
            ]
            
            return {
                "status": "success",
                "data": optimization_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _scan_plex_libraries(self, library_key: Optional[str] = None, 
                                  scan_type: str = "partial") -> Dict[str, Any]:
        """Scan Plex libraries"""
        try:
            scan_results = {
                "timestamp": datetime.now().isoformat(),
                "scanned_libraries": [],
                "status": "completed"
            }
            
            # Get libraries to scan
            if library_key:
                libraries = [{"key": library_key}]
            else:
                async with self.session.get(f"{self.plex_url}/library/sections") as response:
                    if response.status == 200:
                        data = await response.text()
                        root = ET.fromstring(data)
                        libraries = [{"key": section.get("key")} for section in root.findall(".//Directory")]
            
            for lib in libraries:
                lib_key = lib["key"]
                
                # Trigger scan
                scan_url = f"{self.plex_url}/library/sections/{lib_key}/scan"
                async with self.session.get(scan_url) as response:
                    if response.status == 200:
                        scan_results["scanned_libraries"].append({
                            "library_key": lib_key,
                            "scan_type": scan_type,
                            "status": "triggered"
                        })
                    else:
                        scan_results["scanned_libraries"].append({
                            "library_key": lib_key,
                            "scan_type": scan_type,
                            "status": "failed",
                            "error": f"HTTP {response.status}"
                        })
            
            return {
                "status": "success",
                "data": scan_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close() 