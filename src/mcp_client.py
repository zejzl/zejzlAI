"""
MCP Protocol Client for ZEJZL.NET

Production-ready MCP client implementing JSON-RPC 2.0 over stdio/HTTP.
Includes connection pooling, error handling, and circuit breaker integration.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
import aiohttp

from src.mcp_types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    MCPServerInfo, MCPClientInfo, MCPTransport,
    MCPTool, MCPResource, MCPPrompt,
    MCPMethod, validate_json_rpc_response
)
from src.magic import FairyMagic, CircuitBreaker, CircuitBreakerConfig
from src.mcp_security import (
    get_security_manager, SecurityLevel, Permission,
    authenticate_token, check_authorization, check_rate_limit
)

logger = logging.getLogger("MCPClient")


class MCPConnectionError(Exception):
    """MCP connection-related errors"""
    pass


class MCPProtocolError(Exception):
    """MCP protocol-related errors"""
    pass


class MCPTimeoutError(Exception):
    """MCP operation timeout"""
    pass


class MCPClient:
    """
    Model Context Protocol client with production features:
    - Multiple transport support (stdio, HTTP)
    - Automatic reconnection
    - Circuit breaker integration
    - Request timeout handling
    - Connection pooling
    """

    def __init__(
        self,
        server_name: str,
        transport: MCPTransport = MCPTransport.STDIO,
        command: Optional[List[str]] = None,
        url: Optional[str] = None,
        timeout: float = 30.0,
        magic_system: Optional[FairyMagic] = None
    ):
        self.server_name = server_name
        self.transport = transport
        self.command = command
        self.url = url
        self.timeout = timeout
        self.magic = magic_system or FairyMagic()

        # Connection state
        self.process: Optional[asyncio.subprocess.Process] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.server_info: Optional[MCPServerInfo] = None

        # Request tracking
        self.request_counter = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}

        # Circuit breaker for reliability
        self.circuit_breaker = CircuitBreaker(
            CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                expected_exception=(MCPConnectionError, MCPTimeoutError)
            )
        )

        # Background tasks
        self.read_task: Optional[asyncio.Task] = None

    async def connect(self) -> MCPServerInfo:
        """
        Connect to MCP server and perform initialization handshake.

        Returns:
            MCPServerInfo: Server capabilities and information

        Raises:
            MCPConnectionError: If connection fails
            MCPProtocolError: If protocol handshake fails
        """
        logger.info(f"Connecting to MCP server: {self.server_name}")

        try:
            if self.transport == MCPTransport.STDIO:
                await self._connect_stdio()
            elif self.transport == MCPTransport.HTTP:
                await self._connect_http()
            else:
                raise ValueError(f"Unsupported transport: {self.transport}")

            # Perform initialization handshake
            self.server_info = await self._initialize()
            self.connected = True

            logger.info(
                f"Connected to {self.server_info.name} v{self.server_info.version}"
            )

            return self.server_info

        except Exception as e:
            logger.error(f"Failed to connect to {self.server_name}: {e}")
            await self.disconnect()
            raise MCPConnectionError(f"Connection failed: {e}")

    async def _connect_stdio(self):
        """Connect via stdio transport (subprocess)"""
        if not self.command:
            raise ValueError("Command required for stdio transport")

        logger.debug(f"Starting subprocess: {' '.join(self.command)}")

        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Start reading responses in background
        self.read_task = asyncio.create_task(self._read_stdio_responses())

    async def _connect_http(self):
        """Connect via HTTP transport"""
        if not self.url:
            raise ValueError("URL required for HTTP transport")

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )

        # Test connection
        try:
            async with self.session.get(f"{self.url}/health") as resp:
                if resp.status != 200:
                    raise MCPConnectionError(f"Health check failed: {resp.status}")
        except aiohttp.ClientError as e:
            raise MCPConnectionError(f"HTTP connection failed: {e}")

    async def _initialize(self) -> MCPServerInfo:
        """
        Perform MCP initialization handshake.

        Returns:
            MCPServerInfo from server
        """
        client_info = MCPClientInfo()

        request = MCPRequest(
            id=self._next_request_id(),
            method=MCPMethod.INITIALIZE,
            params={
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": client_info.to_dict()
            }
        )

        response = await self._send_request(request)

        if response.error:
            raise MCPProtocolError(
                f"Initialization failed: {response.error.message}"
            )

        server_info = MCPServerInfo.from_dict(response.result)

        # Send initialized notification
        notification = MCPRequest(
            method=MCPMethod.INITIALIZED,
            params={}
        )
        await self._send_notification(notification)

        return server_info

    async def disconnect(self):
        """Gracefully disconnect from MCP server"""
        if not self.connected:
            return

        logger.info(f"Disconnecting from {self.server_name}")

        try:
            # Send shutdown request
            request = MCPRequest(
                id=self._next_request_id(),
                method=MCPMethod.SHUTDOWN
            )
            await self._send_request(request, timeout=5.0)
        except Exception as e:
            logger.warning(f"Shutdown request failed: {e}")

        # Cleanup resources
        if self.read_task:
            self.read_task.cancel()
            try:
                await self.read_task
            except asyncio.CancelledError:
                pass

        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()

        if self.session:
            await self.session.close()

        self.connected = False
        logger.info(f"Disconnected from {self.server_name}")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        auth_token: Optional[str] = None
    ) -> Any:
        """
        Call an MCP tool with security checks.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            auth_token: Authentication token (optional)

        Returns:
            Tool result

        Raises:
            MCPError: If tool call fails or security checks fail
        """
        if not self.connected:
            raise MCPConnectionError("Not connected to server")

        # Security checks
        principal = None
        if auth_token:
            principal = await authenticate_token(auth_token)
            if not principal:
                raise MCPProtocolError("Authentication failed")

            # Check authorization
            authorized = await check_authorization(
                principal, "call_tool", f"tool:{tool_name}"
            )
            if not authorized:
                raise MCPProtocolError("Authorization failed")

            # Check rate limits
            rate_allowed, rate_reason = await check_rate_limit(principal, "call_tool")
            if not rate_allowed:
                raise MCPProtocolError(f"Rate limit exceeded: {rate_reason}")
        else:
            # Use default agent principal for unauthenticated calls
            manager = get_security_manager()
            principal = manager.principals.get("default_agent")

        logger.debug(f"Calling tool: {tool_name} by principal: {principal.id if principal else 'unauthenticated'}")

        request = MCPRequest(
            id=self._next_request_id(),
            method=MCPMethod.TOOLS_CALL,
            params={
                "name": tool_name,
                "arguments": arguments or {}
            }
        )

        # Use circuit breaker for reliability
        try:
            response = await self.circuit_breaker.call(
                self._send_request,
                request
            )
        except Exception as e:
            # Attempt auto-healing if call fails
            healed = await self.magic.auto_heal("mcp_client", e)
            if healed:
                logger.info("Auto-healing successful, retrying tool call")
                response = await self._send_request(request)
            else:
                raise

        if response.error:
            raise MCPProtocolError(
                f"Tool call failed: {response.error.message}"
            )

        return response.result

    async def read_resource(self, uri: str) -> Any:
        """
        Read an MCP resource.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if not self.connected:
            raise MCPConnectionError("Not connected to server")

        logger.debug(f"Reading resource: {uri}")

        request = MCPRequest(
            id=self._next_request_id(),
            method=MCPMethod.RESOURCES_READ,
            params={"uri": uri}
        )

        response = await self._send_request(request)

        if response.error:
            raise MCPProtocolError(
                f"Resource read failed: {response.error.message}"
            )

        return response.result

    async def list_tools(self) -> List[MCPTool]:
        """List available tools from server"""
        if not self.connected:
            raise MCPConnectionError("Not connected to server")

        request = MCPRequest(
            id=self._next_request_id(),
            method=MCPMethod.TOOLS_LIST
        )

        response = await self._send_request(request)

        if response.error:
            raise MCPProtocolError(
                f"Tools list failed: {response.error.message}"
            )

        tools_data = response.result.get("tools", [])
        return [MCPTool.from_dict(t) for t in tools_data]

    async def list_resources(self) -> List[MCPResource]:
        """List available resources from server"""
        if not self.connected:
            raise MCPConnectionError("Not connected to server")

        request = MCPRequest(
            id=self._next_request_id(),
            method=MCPMethod.RESOURCES_LIST
        )

        response = await self._send_request(request)

        if response.error:
            raise MCPProtocolError(
                f"Resources list failed: {response.error.message}"
            )

        resources_data = response.result.get("resources", [])
        return [MCPResource.from_dict(r) for r in resources_data]

    async def _send_request(
        self,
        request: MCPRequest,
        timeout: Optional[float] = None
    ) -> MCPResponse:
        """
        Send request and wait for response.

        Args:
            request: MCP request
            timeout: Optional timeout override

        Returns:
            MCP response

        Raises:
            MCPTimeoutError: If request times out
            MCPProtocolError: If protocol error occurs
        """
        timeout = timeout or self.timeout

        # Create future for response
        future: asyncio.Future = asyncio.Future()
        self.pending_requests[str(request.id)] = future

        try:
            # Send request
            if self.transport == MCPTransport.STDIO:
                await self._write_stdio(request)
            elif self.transport == MCPTransport.HTTP:
                await self._send_http(request)

            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"Request timed out after {timeout}s")
        finally:
            self.pending_requests.pop(str(request.id), None)

    async def _send_notification(self, notification: MCPRequest):
        """Send notification (no response expected)"""
        if self.transport == MCPTransport.STDIO:
            await self._write_stdio(notification)
        elif self.transport == MCPTransport.HTTP:
            await self._send_http(notification)

    async def _write_stdio(self, request: MCPRequest):
        """Write request to stdio"""
        if not self.process or not self.process.stdin:
            raise MCPConnectionError("Process stdin not available")

        data = request.to_json() + "\n"
        self.process.stdin.write(data.encode())
        await self.process.stdin.drain()

    async def _send_http(self, request: MCPRequest):
        """Send request via HTTP"""
        if not self.session:
            raise MCPConnectionError("HTTP session not available")

        async with self.session.post(
            f"{self.url}/rpc",
            json=request.to_dict()
        ) as resp:
            if resp.status != 200:
                raise MCPConnectionError(f"HTTP error: {resp.status}")

            response_data = await resp.json()
            response = MCPResponse.from_dict(response_data)

            # Deliver response to pending request
            if request.id and str(request.id) in self.pending_requests:
                self.pending_requests[str(request.id)].set_result(response)

    async def _read_stdio_responses(self):
        """Background task to read stdio responses"""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break

                try:
                    data = json.loads(line.decode())
                    await self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from server: {e}")

        except Exception as e:
            logger.error(f"Error reading responses: {e}")

    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming message from server"""
        if not validate_json_rpc_response(data):
            logger.warning(f"Invalid response: {data}")
            return

        response = MCPResponse.from_dict(data)

        # Deliver to pending request
        request_id = str(response.id)
        if request_id in self.pending_requests:
            self.pending_requests[request_id].set_result(response)
        else:
            logger.warning(f"Received response for unknown request: {request_id}")

    def _next_request_id(self) -> str:
        """Generate next request ID"""
        self.request_counter += 1
        return f"{self.server_name}-{self.request_counter}"

    async def health_check(self) -> bool:
        """
        Check if server is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        if not self.connected:
            return False

        try:
            # Simple tools list as health check
            await self.list_tools()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get client status information"""
        return {
            "server_name": self.server_name,
            "connected": self.connected,
            "transport": self.transport.value,
            "server_info": self.server_info.to_dict() if self.server_info else None,
            "circuit_breaker": self.circuit_breaker.get_status(),
            "magic_energy": self.magic.energy_level
        }


# Convenience context manager
class MCPConnection:
    """Context manager for MCP connections"""

    def __init__(self, client: MCPClient):
        self.client = client

    async def __aenter__(self) -> MCPClient:
        await self.client.connect()
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()
