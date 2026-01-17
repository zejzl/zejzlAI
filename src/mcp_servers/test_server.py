#!/usr/bin/env python3
"""
Test MCP Server for ZEJZL.NET
A simple MCP server for testing MCP integration.
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import argparse

logger = logging.getLogger("TestMCPServer")

# Simplified MCP types for testing
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

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.tools:
            result["tools"] = self.tools
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

class TestMCPServer:
    """
    Simple MCP server for testing
    Provides basic file operations and math tools
    """

    def __init__(self, server_name: str = "test_mcp_server"):
        self.server_name = server_name
        self.tools: Dict[str, MCPToolDefinition] = {}

        # Register tools
        self._register_tools()

    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        return MCPServerInfo(
            name=self.server_name,
            version="1.0.0",
            capabilities=MCPServerCapabilities(
                tools={"listChanged": True}
            )
        )

    def _register_tools(self):
        """Register test tools"""
        # Ping tool
        self.register_tool(MCPToolDefinition(
            name="ping",
            description="Test server connectivity",
            input_schema={"type": "object", "properties": {}},
            handler=self._handle_ping
        ))

        # Math tool
        self.register_tool(MCPToolDefinition(
            name="add_numbers",
            description="Add two numbers",
            input_schema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"}
                },
                "required": ["a", "b"]
            },
            handler=self._handle_add_numbers
        ))

        # List directory tool
        self.register_tool(MCPToolDefinition(
            name="list_directory",
            description="List contents of a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to list"}
                },
                "required": ["path"]
            },
            handler=self._handle_list_directory
        ))

        # Read file tool
        self.register_tool(MCPToolDefinition(
            name="read_file",
            description="Read contents of a text file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"]
            },
            handler=self._handle_read_file
        ))

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
                return self._create_error_response(request_id, MCPMethod.METHOD_NOT_FOUND, f"Unknown method: {method}")

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
                "tools": [tool.to_dict() for tool in tools]
            }
        }

    async def _handle_tools_call(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        logger.info(f"Handling tools/call: {tool_name}")

        if not tool_name:
            return self._create_error_response(request_id, MCPErrorCode.INVALID_PARAMS, "Tool name is required")

        tool_def = self.tools.get(tool_name)
        if not tool_def:
            return self._create_error_response(request_id, MCPErrorCode.TOOL_NOT_FOUND, f"Tool not found: {tool_name}")

        try:
            # Call the tool handler
            result = await tool_def.handler(tool_args)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return self._create_error_response(request_id, MCPErrorCode.INTERNAL_ERROR, f"Tool execution failed: {e}")

    def _create_error_response(self, request_id: Any, error_code: MCPErrorCode, message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": error_code,
                "message": message
            }
        }

    # Tool handlers
    async def _handle_ping(self, args: Dict[str, Any]) -> str:
        """Handle ping tool"""
        return f"Pong from {self.server_name}!"

    async def _handle_add_numbers(self, args: Dict[str, Any]) -> str:
        """Handle add_numbers tool"""
        a = args.get("a", 0)
        b = args.get("b", 0)
        result = a + b
        return f"The sum of {a} and {b} is {result}"

    async def _handle_list_directory(self, args: Dict[str, Any]) -> str:
        """Handle list_directory tool"""
        path = args.get("path", ".")

        try:
            if not os.path.exists(path):
                return f"Directory does not exist: {path}"

            if not os.path.isdir(path):
                return f"Path is not a directory: {path}"

            items = os.listdir(path)
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]

            result = f"Contents of directory: {path}\n\n"
            if dirs:
                result += f"Directories ({len(dirs)}):\n"
                for d in sorted(dirs):
                    result += f"  {d}/\n"

            if files:
                result += f"\nFiles ({len(files)}):\n"
                for f in sorted(files):
                    result += f"  {f}\n"

            return result

        except Exception as e:
            return f"Error listing directory {path}: {e}"

    async def _handle_read_file(self, args: Dict[str, Any]) -> str:
        """Handle read_file tool"""
        path = args.get("path", "")

        if not path:
            return "Error: No file path provided"

        try:
            if not os.path.exists(path):
                return f"File does not exist: {path}"

            if not os.path.isfile(path):
                return f"Path is not a file: {path}"

            # Check file size (limit to 1MB for safety)
            size = os.path.getsize(path)
            if size > 1024 * 1024:
                return f"File too large to read: {size} bytes (max 1MB)"

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return f"Contents of file: {path}\n\n{content}"

        except UnicodeDecodeError:
            return f"File appears to be binary or has encoding issues: {path}"
        except Exception as e:
            return f"Error reading file {path}: {e}"


async def main():
    """Main function to run the test MCP server"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test MCP Server for ZEJZL.NET")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args_parsed = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args_parsed.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and start server
    server = TestMCPServer()
    await server.start_stdio_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise