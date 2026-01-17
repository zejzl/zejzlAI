"""
Base MCP Server Implementation for ZEJZL.NET
Provides foundation for building MCP (Model Context Protocol) servers.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import argparse

logger = logging.getLogger("MCPServer")

# Simplified MCP types for server implementation
class MCPErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    RESOURCE_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002

class MCPMethod:
    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    SHUTDOWN = "shutdown"

@dataclass
class MCPTool:
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema
        }

@dataclass
class MCPServerCapabilities:
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools:
            result["tools"] = self.tools
        if self.resources:
            result["resources"] = self.resources
        if self.prompts:
            result["prompts"] = self.prompts
        return result

@dataclass
class MCPServerInfo:
    name: str
    version: str
    capabilities: MCPServerCapabilities

@dataclass
class MCPToolDefinition:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Any]
    
    def to_mcp_tool(self) -> MCPTool:
        """Convert to MCP protocol format"""
        return MCPTool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema
        )

class BaseMCPServer(ABC):
    """
    Base class for MCP servers providing JSON-RPC 2.0 over stdio.
    Subclasses should implement specific tools, resources, and prompts.
    """
    
    def __init__(self, server_name: str = "base_mcp_server"):
        self.server_name = server_name
        self.tools: Dict[str, MCPToolDefinition] = {}
        
        # Register default handlers
        self._register_default_tools()
        self._register_custom_tools()
    
    @abstractmethod
    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        pass
    
    def _register_default_tools(self):
        """Register default MCP tools (ping, etc.)"""
        self.register_tool(MCPToolDefinition(
            name="ping",
            description="Test server connectivity",
            input_schema={"type": "object", "properties": {}},
            handler=self._handle_ping
        ))
    
    def _register_custom_tools(self):
        """Override in subclasses to register custom tools"""
        pass
    
    def register_tool(self, tool_def: MCPToolDefinition):
        """Register a tool"""
        self.tools[tool_def.name] = tool_def
        logger.info(f"Registered tool: {tool_def.name}")
    
    async def start_stdio_server(self):
        """Start the server listening on stdin/stdout"""
        logger.info(f"Starting MCP server: {self.server_name}")
        
        try:
            while True:
                # Read line from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse JSON-RPC request
                    request_data = json.loads(line)
                    logger.debug(f"Received request: {request_data}")
                    
                    # Process request
                    response = await self.process_request(request_data)
                    
                    # Send response
                    if response:
                        response_json = json.dumps(response, default=str)
                        print(response_json, flush=True)
                        logger.debug(f"Sent response: {response_json}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = self._create_error_response(None, MCPErrorCode.PARSE_ERROR, f"Invalid JSON: {e}")
                    print(json.dumps(error_response), flush=True)
                    
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    error_response = self._create_error_response(None, MCPErrorCode.INTERNAL_ERROR, str(e))
                    print(json.dumps(error_response), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    
    async def process_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a JSON-RPC request"""
        try:
            # Validate JSON-RPC 2.0 format
            if not isinstance(request_data, dict):
                return self._create_error_response(None, MCPErrorCode.INVALID_REQUEST, "Request must be an object")
            
            jsonrpc = request_data.get("jsonrpc")
            if jsonrpc != "2.0":
                return self._create_error_response(None, MCPErrorCode.INVALID_REQUEST, "Invalid JSON-RPC version")
            
            request_id = request_data.get("id")
            method = request_data.get("method")
            params = request_data.get("params", {})
            
            if not method:
                return self._create_error_response(request_id, MCPErrorCode.INVALID_REQUEST, "Method is required")
            
            # Route to appropriate handler
            if method == MCPMethod.INITIALIZE:
                return await self._handle_initialize(request_id, params)
            elif method == MCPMethod.TOOLS_LIST:
                return await self._handle_tools_list(request_id)
            elif method == MCPMethod.TOOLS_CALL:
                return await self._handle_tools_call(request_id, params)
            else:
                return self._create_error_response(request_id, MCPErrorCode.METHOD_NOT_FOUND, f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Error in process_request: {e}")
            return self._create_error_response(request_data.get("id"), MCPErrorCode.INTERNAL_ERROR, str(e))
    
    async def _handle_initialize(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        logger.info("Handling initialize request")
        
        # Get server info
        server_info = self.get_server_info()
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": server_info.capabilities.to_dict(),
                "serverInfo": {
                    "name": server_info.name,
                    "version": server_info.version
                }
            }
        }
    
    async def _handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request"""
        logger.debug("Handling tools/list request")
        
        tools = [tool.to_mcp_tool() for tool in self.tools.values()]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [tool.to_dict()
