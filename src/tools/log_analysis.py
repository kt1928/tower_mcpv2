"""
Log Analysis Tools for Unraid MCP Server
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiofiles
from pathlib import Path
import glob

from mcp.types import Tool


class LogAnalysis:
    """Intelligent log analysis and monitoring tools"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.watch_paths = config.get("watch_paths", [
            "/host/var/log/syslog",
            "/host/var/log/messages"
        ])
        self.max_lines = config.get("max_lines", 1000)
        self.error_patterns = config.get("error_patterns", [
            r"error",
            r"failed",
            r"critical",
            r"emergency",
            r"alert",
            r"fatal",
            r"exception",
            r"timeout",
            r"connection refused",
            r"permission denied"
        ])
        
    async def initialize(self):
        """Initialize the log analysis module"""
        self.logger.info("Initializing Log Analysis module")
        
        # Verify log paths exist
        for path in self.watch_paths:
            if not Path(path).exists():
                self.logger.warning(f"Log path not found: {path}")
    
    async def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for log analysis"""
        return [
            Tool(
                name="analyze_system_logs",
                description="Analyze system logs for errors, warnings, and patterns",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "log_path": {
                            "type": "string",
                            "description": "Specific log file to analyze (optional)"
                        },
                        "hours_back": {
                            "type": "integer",
                            "description": "Analyze logs from last N hours",
                            "default": 24
                        },
                        "include_patterns": {
                            "type": "boolean",
                            "description": "Include pattern analysis",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="search_logs",
                description="Search logs for specific patterns or keywords",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (regex supported)"
                        },
                        "log_path": {
                            "type": "string",
                            "description": "Specific log file to search (optional)"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Case sensitive search",
                            "default": False
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_error_summary",
                description="Get summary of recent errors and their frequency",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hours_back": {
                            "type": "integer",
                            "description": "Look back N hours for errors",
                            "default": 24
                        },
                        "group_by_source": {
                            "type": "boolean",
                            "description": "Group errors by source/component",
                            "default": True
                        }
                    }
                }
            ),
            Tool(
                name="monitor_log_patterns",
                description="Monitor logs for specific patterns in real-time",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Patterns to monitor"
                        },
                        "duration_seconds": {
                            "type": "integer",
                            "description": "Monitoring duration in seconds",
                            "default": 60
                        },
                        "alert_threshold": {
                            "type": "integer",
                            "description": "Alert if pattern appears more than N times",
                            "default": 5
                        }
                    },
                    "required": ["patterns"]
                }
            ),
            Tool(
                name="generate_log_report",
                description="Generate comprehensive log analysis report",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "hours_back": {
                            "type": "integer",
                            "description": "Analysis period in hours",
                            "default": 24
                        },
                        "include_trends": {
                            "type": "boolean",
                            "description": "Include trend analysis",
                            "default": True
                        },
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include recommendations",
                            "default": True
                        }
                    }
                }
            )
        ]
    
    async def handle_call(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            if method == "analyze_system_logs":
                return await self._analyze_system_logs(
                    arguments.get("log_path"),
                    arguments.get("hours_back", 24),
                    arguments.get("include_patterns", True)
                )
            elif method == "search_logs":
                return await self._search_logs(
                    arguments["query"],
                    arguments.get("log_path"),
                    arguments.get("case_sensitive", False),
                    arguments.get("max_results", 100)
                )
            elif method == "get_error_summary":
                return await self._get_error_summary(
                    arguments.get("hours_back", 24),
                    arguments.get("group_by_source", True)
                )
            elif method == "monitor_log_patterns":
                return await self._monitor_log_patterns(
                    arguments["patterns"],
                    arguments.get("duration_seconds", 60),
                    arguments.get("alert_threshold", 5)
                )
            elif method == "generate_log_report":
                return await self._generate_log_report(
                    arguments.get("hours_back", 24),
                    arguments.get("include_trends", True),
                    arguments.get("include_recommendations", True)
                )
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            self.logger.error(f"Error in {method}: {e}", exc_info=True)
            return {"error": str(e), "method": method}
    
    async def _read_log_file(self, log_path: str, max_lines: int = None) -> List[str]:
        """Read log file and return lines"""
        try:
            lines = []
            max_lines = max_lines or self.max_lines
            
            async with aiofiles.open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read last N lines efficiently
                content = await f.read()
                all_lines = content.splitlines()
                lines = all_lines[-max_lines:] if len(all_lines) > max_lines else all_lines
            
            return lines
        except Exception as e:
            self.logger.error(f"Error reading log file {log_path}: {e}")
            return []
    
    async def _parse_log_line(self, line: str) -> Dict[str, Any]:
        """Parse a log line into structured data"""
        # Common log formats
        patterns = [
            # syslog format
            r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$',
            # ISO format
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+(\S+)\s+([^:]+):\s*(.*)$',
            # Simple timestamp format
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                timestamp_str, host, component, message = match.groups()
                
                # Parse timestamp
                timestamp = None
                try:
                    if 'T' in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    pass
                
                return {
                    "timestamp": timestamp,
                    "host": host,
                    "component": component,
                    "message": message,
                    "raw_line": line
                }
        
        # Fallback for unparseable lines
        return {
            "timestamp": None,
            "host": "unknown",
            "component": "unknown",
            "message": line,
            "raw_line": line
        }
    
    async def _analyze_system_logs(self, log_path: Optional[str] = None, 
                                  hours_back: int = 24, 
                                  include_patterns: bool = True) -> Dict[str, Any]:
        """Analyze system logs"""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "period_hours": hours_back,
                "files_analyzed": [],
                "total_lines": 0,
                "error_count": 0,
                "warning_count": 0,
                "errors": [],
                "warnings": [],
                "patterns": {} if include_patterns else None
            }
            
            # Determine which files to analyze
            if log_path:
                files_to_analyze = [log_path]
            else:
                files_to_analyze = self.watch_paths
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for file_path in files_to_analyze:
                if not Path(file_path).exists():
                    continue
                
                file_analysis = {
                    "file": file_path,
                    "lines_analyzed": 0,
                    "errors": 0,
                    "warnings": 0
                }
                
                lines = await self._read_log_file(file_path)
                file_analysis["lines_analyzed"] = len(lines)
                analysis["total_lines"] += len(lines)
                
                for line in lines:
                    parsed = await self._parse_log_line(line)
                    
                    # Check if line is within time range
                    if parsed["timestamp"] and parsed["timestamp"] < cutoff_time:
                        continue
                    
                    # Check for errors and warnings
                    message_lower = parsed["message"].lower()
                    
                    if any(pattern in message_lower for pattern in self.error_patterns):
                        analysis["error_count"] += 1
                        file_analysis["errors"] += 1
                        analysis["errors"].append({
                            "timestamp": parsed["timestamp"].isoformat() if parsed["timestamp"] else None,
                            "component": parsed["component"],
                            "message": parsed["message"],
                            "file": file_path
                        })
                    elif "warning" in message_lower:
                        analysis["warning_count"] += 1
                        file_analysis["warnings"] += 1
                        analysis["warnings"].append({
                            "timestamp": parsed["timestamp"].isoformat() if parsed["timestamp"] else None,
                            "component": parsed["component"],
                            "message": parsed["message"],
                            "file": file_path
                        })
                
                analysis["files_analyzed"].append(file_analysis)
            
            # Pattern analysis
            if include_patterns:
                analysis["patterns"] = await self._analyze_patterns(analysis["errors"] + analysis["warnings"])
            
            return {
                "status": "success",
                "data": analysis
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _search_logs(self, query: str, log_path: Optional[str] = None, 
                          case_sensitive: bool = False, max_results: int = 100) -> Dict[str, Any]:
        """Search logs for specific patterns"""
        try:
            search_results = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "case_sensitive": case_sensitive,
                "results": [],
                "total_matches": 0
            }
            
            # Determine which files to search
            if log_path:
                files_to_search = [log_path]
            else:
                files_to_search = self.watch_paths
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
            
            for file_path in files_to_search:
                if not Path(file_path).exists():
                    continue
                
                lines = await self._read_log_file(file_path)
                
                for line in lines:
                    if pattern.search(line):
                        parsed = await self._parse_log_line(line)
                        
                        search_results["results"].append({
                            "timestamp": parsed["timestamp"].isoformat() if parsed["timestamp"] else None,
                            "component": parsed["component"],
                            "message": parsed["message"],
                            "file": file_path,
                            "line_number": lines.index(line) + 1
                        })
                        
                        search_results["total_matches"] += 1
                        
                        if len(search_results["results"]) >= max_results:
                            break
                
                if len(search_results["results"]) >= max_results:
                    break
            
            return {
                "status": "success",
                "data": search_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _get_error_summary(self, hours_back: int = 24, 
                                group_by_source: bool = True) -> Dict[str, Any]:
        """Get error summary"""
        try:
            # First get all errors
            analysis_result = await self._analyze_system_logs(hours_back=hours_back, include_patterns=False)
            
            if analysis_result["status"] != "success":
                return analysis_result
            
            errors = analysis_result["data"]["errors"]
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "period_hours": hours_back,
                "total_errors": len(errors),
                "error_frequency": {},
                "top_components": {},
                "error_types": {}
            }
            
            if group_by_source:
                # Group by component/source
                component_counts = {}
                for error in errors:
                    component = error["component"]
                    component_counts[component] = component_counts.get(component, 0) + 1
                
                summary["top_components"] = dict(
                    sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                )
            
            # Analyze error types
            error_types = {}
            for error in errors:
                message_lower = error["message"].lower()
                
                # Categorize errors
                if "timeout" in message_lower:
                    error_types["timeout"] = error_types.get("timeout", 0) + 1
                elif "connection" in message_lower:
                    error_types["connection"] = error_types.get("connection", 0) + 1
                elif "permission" in message_lower:
                    error_types["permission"] = error_types.get("permission", 0) + 1
                elif "disk" in message_lower or "storage" in message_lower:
                    error_types["storage"] = error_types.get("storage", 0) + 1
                elif "memory" in message_lower:
                    error_types["memory"] = error_types.get("memory", 0) + 1
                else:
                    error_types["other"] = error_types.get("other", 0) + 1
            
            summary["error_types"] = error_types
            
            return {
                "status": "success",
                "data": summary
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _monitor_log_patterns(self, patterns: List[str], 
                                   duration_seconds: int = 60, 
                                   alert_threshold: int = 5) -> Dict[str, Any]:
        """Monitor logs for patterns in real-time"""
        try:
            monitoring_results = {
                "timestamp": datetime.now().isoformat(),
                "patterns": patterns,
                "duration_seconds": duration_seconds,
                "alert_threshold": alert_threshold,
                "pattern_counts": {},
                "alerts": []
            }
            
            # Initialize pattern counts
            for pattern in patterns:
                monitoring_results["pattern_counts"][pattern] = 0
            
            # Monitor for specified duration
            start_time = datetime.now()
            end_time = start_time + timedelta(seconds=duration_seconds)
            
            while datetime.now() < end_time:
                # Check all log files
                for log_path in self.watch_paths:
                    if not Path(log_path).exists():
                        continue
                    
                    # Read recent lines
                    lines = await self._read_log_file(log_path, max_lines=100)
                    
                    for line in lines:
                        for pattern in patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                monitoring_results["pattern_counts"][pattern] += 1
                
                # Check for alerts
                for pattern, count in monitoring_results["pattern_counts"].items():
                    if count >= alert_threshold:
                        monitoring_results["alerts"].append({
                            "pattern": pattern,
                            "count": count,
                            "threshold": alert_threshold,
                            "timestamp": datetime.now().isoformat()
                        })
                
                # Wait before next check
                await asyncio.sleep(5)
            
            return {
                "status": "success",
                "data": monitoring_results
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _analyze_patterns(self, log_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in log entries"""
        patterns = {
            "common_phrases": {},
            "component_frequency": {},
            "time_distribution": {}
        }
        
        # Analyze common phrases
        phrase_counts = {}
        for entry in log_entries:
            words = entry["message"].split()
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        patterns["common_phrases"] = dict(
            sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Analyze component frequency
        component_counts = {}
        for entry in log_entries:
            component = entry["component"]
            component_counts[component] = component_counts.get(component, 0) + 1
        
        patterns["component_frequency"] = dict(
            sorted(component_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return patterns
    
    async def _generate_log_report(self, hours_back: int = 24, 
                                  include_trends: bool = True, 
                                  include_recommendations: bool = True) -> Dict[str, Any]:
        """Generate comprehensive log report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "period_hours": hours_back,
                "summary": {},
                "detailed_analysis": {},
                "trends": {} if include_trends else None,
                "recommendations": [] if include_recommendations else None
            }
            
            # Get basic analysis
            analysis_result = await self._analyze_system_logs(hours_back=hours_back, include_patterns=True)
            if analysis_result["status"] == "success":
                report["detailed_analysis"] = analysis_result["data"]
                
                # Create summary
                report["summary"] = {
                    "total_log_lines": analysis_result["data"]["total_lines"],
                    "total_errors": analysis_result["data"]["error_count"],
                    "total_warnings": analysis_result["data"]["warning_count"],
                    "files_analyzed": len(analysis_result["data"]["files_analyzed"]),
                    "error_rate": round(analysis_result["data"]["error_count"] / max(analysis_result["data"]["total_lines"], 1) * 100, 2)
                }
            
            # Generate recommendations
            if include_recommendations:
                if report["summary"]["error_rate"] > 5:
                    report["recommendations"].append("High error rate detected - investigate system issues")
                
                if report["summary"]["total_errors"] > 100:
                    report["recommendations"].append("Large number of errors - review system configuration")
                
                if not report["detailed_analysis"].get("patterns"):
                    report["recommendations"].append("No clear error patterns - consider expanding monitoring")
            
            return {
                "status": "success",
                "data": report
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        pass 