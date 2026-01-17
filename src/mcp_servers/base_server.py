"""
Base MCP Server Implementation

Provides JSON-RPC 2.0 protocol handling and common server functionality.
Subclass this to create specific MCP servers.
"""

import sys
import json
import logging
import asyncio
from typing import Any, Dict, List, Optional, Callable
from abc import ABC, abstractmethod

from src.mcp_types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    MCPTool, MCPResource, MCPServerInfo, MCPServerCapabilities,
    MCPMethod, validate_json_rpc_request
)

logger = logging.getLogger("MCPServer")


class BaseMCPServer(ABC):
    """
    Base class for MCP servers implementing JSON-RPC 2.0 over stdio.

    Subclass this and implement:
    - get_server_info(): Return server name, version, capabilities
    - register_tools(): Register available tools
    - register_resources(): Register available resources (optional)
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.initialized = False

        # Tool and resource registries
        self.tools: Dict[str, MCPTool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.resource_handlers: Dict[str, Callable] = {}

        # Protocol handlers
        self.method_handlers = {
            MCPMethod.INITIALIZE: self._handle_initialize,
            MCPMethod.TOOLS_LIST: self._handle_tools_list,
            MCPMethod.TOOLS_CALL: self._handle_tools_call,
            MCPMethod.RESOURCES_LIST: self._handle_resources_list,
            MCPMethod.RESOURCES_READ: self._handle_resources_read,
            MCPMethod.SHUTDOWN: self._handle_shutdown
        }

    @abstractmethod
    def get_server_info(self) -> MCPServerInfo:
        """
        Return server information for initialization response.

        Returns:
            MCPServerInfo with name, version, and capabilities
        """
        pass

    @abstractmethod
    async def register_tools(self):
        """
        Register available tools.

        Use self.add_tool() to register each tool.
        """
        pass

    async def register_resources(self):
        """
        Register available resources (optional).

        Use self.add_resource() to register each resource.
        """
        pass

    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable
    ):
        """
        Register a tool with the server.

        Args:
            name: Tool name
            description: Tool description
            input_schema: JSON Schema for tool parameters
            handler: Async function to handle tool calls
        """
        tool = MCPTool(
            name=name,
            description=description,
            inputSchema=input_schema
        )

        self.tools[name] = tool
        self.tool_handlers[name] = handler

        logger.debug(f"Registered tool: {name}")

    def add_resource(
        self,
        uri: str,
        name: str,
        description: str,
        mime_type: str,
        handler: Callable
    ):
        """
        Register a resource with the server.

        Args:
            uri: Resource URI
            name: Resource name
            description: Resource description
            mime_type: MIME type
            handler: Async function to read resource
        """
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mimeType=mime_type
        )

        self.resources[uri] = resource
        self.resource_handlers[uri] = handler

        logger.debug(f"Registered resource: {uri}")

    async def start(self):
        """
        Start the MCP server (stdio mode).

        Reads JSON-RPC messages from stdin and writes responses to stdout.
        """
        logger.info(f"Starting MCP server: {self.name} v{self.version}")

        # Register tools and resources
        await self.register_tools()
        await self.register_resources()

        logger.info(
            f"Server ready with {len(self.tools)} tools and {len(self.resources)} resources"
        )

        # Main message loop
        try:
            while True:
                line = sys.stdin.readline()

                if not line:
                    # EOF reached
                    break

                try:
                    request_data = json.loads(line)
                    response = await self._handle_message(request_data)

                    if response:
                        output = response.to_json()
                        print(output, flush=True)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = MCPResponse(
                        id=None,
                        error=MCPError(
                            code=MCPErrorCode.PARSE_ERROR.value,
                            message=f"Parse error: {e}"
                        )
                    )
                    print(error_response.to_json(), flush=True)

                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    error_response = MCPResponse(
                        id=None,
                        error=MCPError(
                            code=MCPErrorCode.INTERNAL_ERROR.value,
                            message=f"Internal error: {e}"
                        )
                    )
                    print(error_response.to_json(), flush=True)

        except KeyboardInterrupt:
            logger.info("Server interrupted by user")

        except Exception as e:
            logger.error(f"Server error: {e}")

        finally:
            await self.cleanup()
            logger.info("Server stopped")

    async def _handle_message(self, data: Dict[str, Any]) -> Optional[MCPResponse]:
        """Handle incoming JSON-RPC message"""

        # Validate request
        if not validate_json_rpc_request(data):
            return MCPResponse(
                id=data.get("id"),
                error=MCPError(
                    code=MCPErrorCode.INVALID_REQUEST.value,
                    message="Invalid JSON-RPC request"
                )
            )

        request = MCPRequest.from_dict(data)

        # Handle notifications (no response expected)
        if request.id is None:
            logger.debug(f"Received notification: {request.method}")
            return None

        # Route to method handler
        handler = self.method_handlers.get(request.method)

        if not handler:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Method not found: {request.method}"
                )
            )

        try:
            result = await handler(request)

            return MCPResponse(
                id=request.id,
                result=result
            )

        except Exception as e:
            logger.error(f"Handler error for {request.method}: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message=str(e)
                )
            )

    async def _handle_initialize(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle initialize request"""
        if self.initialized:
            raise ValueError("Server already initialized")

        self.initialized = True

        # Get server info from subclass
        server_info = self.get_server_info()

        logger.info(f"Server initialized: {server_info.name} v{server_info.version}")

        return server_info.to_dict()

    async def _handle_tools_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle tools/list request"""
        if not self.initialized:
            raise ValueError("Server not initialized")

        tools_list = [tool.to_dict() for tool in self.tools.values()]

        return {"tools": tools_list}

    async def _handle_tools_call(self, request: MCPRequest) -> Any:
        """Handle tools/call request"""
        if not self.initialized:
            raise ValueError("Server not initialized")

        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Tool name required")

        if tool_name not in self.tool_handlers:
            raise ValueError(f"Tool not found: {tool_name}")

        logger.debug(f"Calling tool: {tool_name}")

        # Call tool handler
        handler = self.tool_handlers[tool_name]
        result = await handler(arguments)

        return result

    async def _handle_resources_list(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle resources/list request"""
        if not self.initialized:
            raise ValueError("Server not initialized")

        resources_list = [resource.to_dict() for resource in self.resources.values()]

        return {"resources": resources_list}

    async def _handle_resources_read(self, request: MCPRequest) -> Any:
        """Handle resources/read request"""
        if not self.initialized:
            raise ValueError("Server not initialized")

        params = request.params or {}
        uri = params.get("uri")

        if not uri:
            raise ValueError("Resource URI required")

        if uri not in self.resource_handlers:
            raise ValueError(f"Resource not found: {uri}")

        logger.debug(f"Reading resource: {uri}")

        # Call resource handler
        handler = self.resource_handlers[uri]
        content = await handler()

        return content

    async def _handle_shutdown(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle shutdown request"""
        logger.info("Shutdown requested")
        await self.cleanup()
        return {}

    async def cleanup(self):
        """Cleanup server resources (override in subclass if needed)"""
        pass

    def run(self):
        """Run the server (blocking)"""
        asyncio.run(self.start())
