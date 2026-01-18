#!/usr/bin/env python3
"""
Mock MCP Server for Testing

Simple MCP server implementations for integration testing.
Supports both stdio and HTTP transports.
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List
import uuid
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_types import MCPMethod, MCPRequest, MCPResponse, MCPError, MCPErrorCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockMCPServer")


class MockMCPServer:
    """Base mock MCP server"""

    def __init__(self, server_name: str = "mock_server"):
        self.server_name = server_name
        self.server_version = "1.0.0"
        self.protocol_version = "2024-11-05"

        # Mock capabilities
        self.tools = [
            {
                "name": "echo",
                "description": "Echo back the input message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "add_numbers",
                "description": "Add two numbers together",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            },
            {
                "name": "list_files",
                "description": "List files in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Directory path"}
                    },
                    "required": ["path"]
                }
            }
        ]

        self.resources = [
            {
                "uri": "file:///tmp/mock_data.txt",
                "name": "Mock Data File",
                "description": "A mock data file for testing",
                "mimeType": "text/plain"
            },
            {
                "uri": "file:///tmp/mock_config.json",
                "name": "Mock Config",
                "description": "Mock configuration file",
                "mimeType": "application/json"
            }
        ]

        # Create temporary files for resources
        self.temp_dir = tempfile.mkdtemp()
        self.create_mock_files()

    def create_mock_files(self):
        """Create mock resource files"""
        # Mock data file
        data_file = os.path.join(self.temp_dir, "mock_data.txt")
        with open(data_file, 'w') as f:
            f.write("This is mock data for testing MCP resource access.\n")
            f.write("It contains multiple lines of text.\n")

        # Mock config file
        config_file = os.path.join(self.temp_dir, "mock_config.json")
        config_data = {
            "server": self.server_name,
            "version": self.server_version,
            "mock": True,
            "capabilities": ["tools", "resources"]
        }
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.server_name,
            "version": self.server_version,
            "protocolVersion": self.protocol_version,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"listChanged": True}
            }
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")

            if method == MCPMethod.INITIALIZE:
                return self.handle_initialize(req_id, params)
            elif method == MCPMethod.TOOLS_LIST:
                return self.handle_tools_list(req_id)
            elif method == MCPMethod.TOOLS_CALL:
                return await self.handle_tools_call(req_id, params)
            elif method == MCPMethod.RESOURCES_LIST:
                return self.handle_resources_list(req_id)
            elif method == MCPMethod.RESOURCES_READ:
                return await self.handle_resources_read(req_id, params)
            elif method == MCPMethod.SHUTDOWN:
                return self.handle_shutdown(req_id)
            else:
                return self.create_error_response(req_id, MCPErrorCode.METHOD_NOT_FOUND,
                                                f"Method not found: {method}")

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self.create_error_response(request.get("id"), MCPErrorCode.INTERNAL_ERROR, str(e))

    def handle_initialize(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        client_info = params.get("clientInfo", {})

        response = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "serverInfo": self.get_server_info(),
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"listChanged": True}
                }
            }
        }
        return response

    def handle_tools_list(self, req_id: Any) -> Dict[str, Any]:
        """Handle tools/list request"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": self.tools
            }
        }

    async def handle_tools_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})

        if tool_name == "echo":
            message = tool_args.get("message", "")
            result = {"echoed": message}
        elif tool_name == "add_numbers":
            a = tool_args.get("a", 0)
            b = tool_args.get("b", 0)
            result = {"sum": a + b}
        elif tool_name == "list_files":
            path = tool_args.get("path", ".")
            try:
                files = os.listdir(path)
                result = {"files": files}
            except Exception as e:
                return self.create_error_response(req_id, MCPErrorCode.INTERNAL_ERROR,
                                                f"Failed to list directory: {e}")
        else:
            return self.create_error_response(req_id, MCPErrorCode.INVALID_REQUEST,
                                            f"Unknown tool: {tool_name}")

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }

    def handle_resources_list(self, req_id: Any) -> Dict[str, Any]:
        """Handle resources/list request"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "resources": self.resources
            }
        }

    async def handle_resources_read(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request"""
        uri = params.get("uri")

        if uri == "file:///tmp/mock_data.txt":
            content = "This is mock data for testing MCP resource access.\nIt contains multiple lines of text.\n"
            result = {
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": content
                }]
            }
        elif uri == "file:///tmp/mock_config.json":
            config_data = {
                "server": self.server_name,
                "version": self.server_version,
                "mock": True,
                "capabilities": ["tools", "resources"]
            }
            content = json.dumps(config_data, indent=2)
            result = {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": content
                }]
            }
        else:
            return self.create_error_response(req_id, MCPErrorCode.INVALID_REQUEST,
                                            f"Unknown resource: {uri}")

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }

    def handle_shutdown(self, req_id: Any) -> Dict[str, Any]:
        """Handle shutdown request"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    def create_error_response(self, req_id: Any, error_code: int, message: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": error_code,
                "message": message
            }
        }


class MockMCPServerStdio(MockMCPServer):
    """Mock MCP server for stdio transport"""

    def __init__(self, server_name: str = "mock_stdio_server"):
        super().__init__(server_name)

    async def run_stdio(self):
        """Run the server in stdio mode"""
        logger.info(f"Starting mock MCP server (stdio): {self.server_name}")

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
                    request = json.loads(line)
                    logger.debug(f"Received request: {request}")

                    response = await self.handle_request(request)
                    logger.debug(f"Sending response: {response}")

                    # Write response to stdout
                    print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = self.create_error_response(None, MCPErrorCode.PARSE_ERROR, "Invalid JSON")
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")


async def run_mock_stdio_server():
    """Run the mock stdio server"""
    server = MockMCPServerStdio()
    await server.run_stdio()


if __name__ == "__main__":
    # Determine which server to run based on arguments
    if len(sys.argv) > 1 and sys.argv[1] == "stdio":
        asyncio.run(run_mock_stdio_server())
    else:
        print("Usage: python mock_mcp_server.py stdio")
        sys.exit(1)