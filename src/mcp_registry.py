"""
MCP Server Registry for ZEJZL.NET

Manages multiple MCP server connections with health monitoring,
auto-discovery, and capability introspection.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from src.mcp_client import MCPClient, MCPConnection, MCPConnectionError
from src.mcp_types import MCPTransport, MCPTool, MCPResource, MCPServerInfo
from src.magic import FairyMagic

logger = logging.getLogger("MCPRegistry")


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    transport: str  # "stdio" or "http"
    enabled: bool = True

    # stdio transport config
    command: Optional[List[str]] = None

    # http transport config
    url: Optional[str] = None

    # Connection settings
    timeout: float = 30.0
    auto_reconnect: bool = True
    health_check_interval: int = 60  # seconds

    # Permissions
    allowed_agents: Optional[List[str]] = None  # None = all agents allowed

    # Metadata
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "transport": self.transport,
            "enabled": self.enabled,
            "command": self.command,
            "url": self.url,
            "timeout": self.timeout,
            "auto_reconnect": self.auto_reconnect,
            "health_check_interval": self.health_check_interval,
            "allowed_agents": self.allowed_agents,
            "description": self.description,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary"""
        return cls(
            name=data["name"],
            transport=data["transport"],
            enabled=data.get("enabled", True),
            command=data.get("command"),
            url=data.get("url"),
            timeout=data.get("timeout", 30.0),
            auto_reconnect=data.get("auto_reconnect", True),
            health_check_interval=data.get("health_check_interval", 60),
            allowed_agents=data.get("allowed_agents"),
            description=data.get("description"),
            tags=data.get("tags", [])
        )


@dataclass
class ServerStatus:
    """Runtime status of an MCP server"""
    connected: bool = False
    last_health_check: Optional[datetime] = None
    health_check_passing: bool = False
    connection_attempts: int = 0
    last_error: Optional[str] = None
    uptime_start: Optional[datetime] = None

    # Server capabilities
    server_info: Optional[MCPServerInfo] = None
    tools: List[MCPTool] = field(default_factory=list)
    resources: List[MCPResource] = field(default_factory=list)

    # Metrics
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "connected": self.connected,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_passing": self.health_check_passing,
            "connection_attempts": self.connection_attempts,
            "last_error": self.last_error,
            "uptime_start": self.uptime_start.isoformat() if self.uptime_start else None,
            "server_info": self.server_info.to_dict() if self.server_info else None,
            "tools": [t.to_dict() for t in self.tools],
            "resources": [r.to_dict() for r in self.resources],
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "avg_response_time": self.avg_response_time
        }


class MCPServerRegistry:
    """
    Registry for managing multiple MCP servers.

    Features:
    - Dynamic server registration from config files
    - Health monitoring and auto-reconnection
    - Capability introspection (tools, resources)
    - Agent-based access control
    - Request routing and load balancing
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        magic_system: Optional[FairyMagic] = None
    ):
        self.config_path = config_path or Path("config/mcp_servers.json")
        self.magic = magic_system or FairyMagic()

        # Server management
        self.configs: Dict[str, MCPServerConfig] = {}
        self.clients: Dict[str, MCPClient] = {}
        self.status: Dict[str, ServerStatus] = {}

        # Health monitoring
        self.health_check_tasks: Dict[str, asyncio.Task] = {}
        self.running = False

        # Event callbacks
        self.on_server_connected: Optional[Callable] = None
        self.on_server_disconnected: Optional[Callable] = None
        self.on_health_check_failed: Optional[Callable] = None

    async def start(self):
        """Start the registry and connect to all enabled servers"""
        logger.info("Starting MCP Server Registry")
        self.running = True

        # Load server configurations
        await self.load_config()

        # Connect to all enabled servers
        connection_tasks = []
        for name, config in self.configs.items():
            if config.enabled:
                connection_tasks.append(self._connect_server(name))

        if connection_tasks:
            await asyncio.gather(*connection_tasks, return_exceptions=True)

        logger.info(f"Registry started with {len(self.clients)} active servers")

    async def stop(self):
        """Stop the registry and disconnect all servers"""
        logger.info("Stopping MCP Server Registry")
        self.running = False

        # Cancel health check tasks
        for task in self.health_check_tasks.values():
            task.cancel()

        if self.health_check_tasks:
            await asyncio.gather(
                *self.health_check_tasks.values(),
                return_exceptions=True
            )

        # Disconnect all clients
        disconnect_tasks = []
        for name in list(self.clients.keys()):
            disconnect_tasks.append(self._disconnect_server(name))

        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        logger.info("Registry stopped")

    async def load_config(self, config_path: Optional[Path] = None):
        """Load server configurations from JSON file"""
        path = config_path or self.config_path

        if not path.exists():
            logger.warning(f"Config file not found: {path}")
            logger.info("Creating default configuration")
            await self._create_default_config(path)
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            servers = data.get("servers", [])
            for server_data in servers:
                config = MCPServerConfig.from_dict(server_data)
                self.configs[config.name] = config
                self.status[config.name] = ServerStatus()

            logger.info(f"Loaded {len(self.configs)} server configurations")

        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            raise

    async def save_config(self, config_path: Optional[Path] = None):
        """Save current server configurations to JSON file"""
        path = config_path or self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "servers": [config.to_dict() for config in self.configs.values()]
        }

        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved configuration to {path}")

        except Exception as e:
            logger.error(f"Failed to save config to {path}: {e}")
            raise

    async def _create_default_config(self, path: Path):
        """Create default server configuration file"""
        path.parent.mkdir(parents=True, exist_ok=True)

        default_servers = [
            {
                "name": "filesystem",
                "transport": "stdio",
                "command": ["python", "-m", "mcp.server.filesystem"],
                "enabled": False,
                "description": "Local filesystem access via MCP",
                "tags": ["filesystem", "local"]
            },
            {
                "name": "github",
                "transport": "stdio",
                "command": ["python", "-m", "mcp.server.github"],
                "enabled": False,
                "description": "GitHub API access via MCP",
                "tags": ["github", "api", "vcs"]
            },
            {
                "name": "web-search",
                "transport": "stdio",
                "command": ["python", "-m", "mcp.server.websearch"],
                "enabled": False,
                "description": "Web search capabilities via MCP",
                "tags": ["search", "web"]
            }
        ]

        data = {
            "version": "1.0",
            "servers": default_servers
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Created default configuration at {path}")

    async def register_server(
        self,
        config: MCPServerConfig,
        connect: bool = True
    ) -> bool:
        """
        Register a new MCP server.

        Args:
            config: Server configuration
            connect: Whether to immediately connect

        Returns:
            True if registration successful
        """
        if config.name in self.configs:
            logger.warning(f"Server {config.name} already registered")
            return False

        self.configs[config.name] = config
        self.status[config.name] = ServerStatus()

        logger.info(f"Registered server: {config.name}")

        if connect and config.enabled:
            await self._connect_server(config.name)

        # Save updated configuration
        await self.save_config()

        return True

    async def unregister_server(self, server_name: str) -> bool:
        """
        Unregister an MCP server.

        Args:
            server_name: Name of server to unregister

        Returns:
            True if unregistration successful
        """
        if server_name not in self.configs:
            logger.warning(f"Server {server_name} not found")
            return False

        # Disconnect if connected
        if server_name in self.clients:
            await self._disconnect_server(server_name)

        # Remove from registry
        del self.configs[server_name]
        del self.status[server_name]

        logger.info(f"Unregistered server: {server_name}")

        # Save updated configuration
        await self.save_config()

        return True

    async def _connect_server(self, server_name: str):
        """Connect to an MCP server"""
        config = self.configs.get(server_name)
        status = self.status.get(server_name)

        if not config or not status:
            logger.error(f"Server {server_name} not found in registry")
            return

        if server_name in self.clients:
            logger.warning(f"Server {server_name} already connected")
            return

        logger.info(f"Connecting to MCP server: {server_name}")
        status.connection_attempts += 1

        try:
            # Create client
            transport = MCPTransport.STDIO if config.transport == "stdio" else MCPTransport.HTTP

            client = MCPClient(
                server_name=server_name,
                transport=transport,
                command=config.command,
                url=config.url,
                timeout=config.timeout,
                magic_system=self.magic
            )

            # Connect and initialize
            server_info = await client.connect()

            # Store client and update status
            self.clients[server_name] = client
            status.connected = True
            status.uptime_start = datetime.now()
            status.server_info = server_info
            status.last_error = None

            # Introspect capabilities
            await self._introspect_capabilities(server_name)

            # Start health monitoring
            if config.auto_reconnect:
                self.health_check_tasks[server_name] = asyncio.create_task(
                    self._health_monitor(server_name)
                )

            logger.info(
                f"Connected to {server_name}: {server_info.name} v{server_info.version}"
            )

            # Trigger callback
            if self.on_server_connected:
                await self.on_server_connected(server_name, server_info)

        except Exception as e:
            status.last_error = str(e)
            logger.error(f"Failed to connect to {server_name}: {e}")

    async def _disconnect_server(self, server_name: str):
        """Disconnect from an MCP server"""
        client = self.clients.get(server_name)
        status = self.status.get(server_name)

        if not client:
            return

        logger.info(f"Disconnecting from MCP server: {server_name}")

        # Cancel health monitoring
        if server_name in self.health_check_tasks:
            self.health_check_tasks[server_name].cancel()
            del self.health_check_tasks[server_name]

        # Disconnect client
        try:
            await client.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting from {server_name}: {e}")

        # Update status
        del self.clients[server_name]
        if status:
            status.connected = False
            status.uptime_start = None

        logger.info(f"Disconnected from {server_name}")

        # Trigger callback
        if self.on_server_disconnected:
            await self.on_server_disconnected(server_name)

    async def _introspect_capabilities(self, server_name: str):
        """Discover server capabilities (tools, resources)"""
        client = self.clients.get(server_name)
        status = self.status.get(server_name)

        if not client or not status:
            return

        try:
            # List available tools
            status.tools = await client.list_tools()
            logger.debug(f"{server_name}: {len(status.tools)} tools available")

            # List available resources
            status.resources = await client.list_resources()
            logger.debug(f"{server_name}: {len(status.resources)} resources available")

        except Exception as e:
            logger.warning(f"Failed to introspect {server_name}: {e}")

    async def _health_monitor(self, server_name: str):
        """Background health monitoring for a server"""
        config = self.configs.get(server_name)

        if not config:
            return

        while self.running:
            try:
                await asyncio.sleep(config.health_check_interval)

                client = self.clients.get(server_name)
                status = self.status.get(server_name)

                if not client or not status:
                    break

                # Perform health check
                is_healthy = await client.health_check()
                status.last_health_check = datetime.now()
                status.health_check_passing = is_healthy

                if not is_healthy:
                    logger.warning(f"Health check failed for {server_name}")

                    if config.auto_reconnect:
                        logger.info(f"Attempting to reconnect {server_name}")
                        await self._disconnect_server(server_name)
                        await self._connect_server(server_name)

                    # Trigger callback
                    if self.on_health_check_failed:
                        await self.on_health_check_failed(server_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error for {server_name}: {e}")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None
    ) -> Any:
        """
        Call a tool on an MCP server.

        Args:
            server_name: Target server name
            tool_name: Name of tool to call
            arguments: Tool arguments
            agent_name: Name of calling agent (for access control)

        Returns:
            Tool result

        Raises:
            ValueError: If server not found or access denied
            MCPConnectionError: If server not connected
        """
        # Verify server exists
        config = self.configs.get(server_name)
        if not config:
            raise ValueError(f"Server not found: {server_name}")

        # Check agent permissions
        if agent_name and config.allowed_agents:
            if agent_name not in config.allowed_agents:
                raise ValueError(
                    f"Agent {agent_name} not allowed to access {server_name}"
                )

        # Get client
        client = self.clients.get(server_name)
        if not client:
            raise MCPConnectionError(f"Server {server_name} not connected")

        status = self.status[server_name]

        # Call tool
        start_time = datetime.now()
        try:
            result = await client.call_tool(tool_name, arguments)

            # Update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            status.total_requests += 1
            status.avg_response_time = (
                (status.avg_response_time * (status.total_requests - 1) + response_time)
                / status.total_requests
            )

            return result

        except Exception as e:
            status.failed_requests += 1
            raise

    async def read_resource(
        self,
        server_name: str,
        uri: str,
        agent_name: Optional[str] = None
    ) -> Any:
        """
        Read a resource from an MCP server.

        Args:
            server_name: Target server name
            uri: Resource URI
            agent_name: Name of calling agent (for access control)

        Returns:
            Resource content
        """
        # Verify server and permissions (same as call_tool)
        config = self.configs.get(server_name)
        if not config:
            raise ValueError(f"Server not found: {server_name}")

        if agent_name and config.allowed_agents:
            if agent_name not in config.allowed_agents:
                raise ValueError(
                    f"Agent {agent_name} not allowed to access {server_name}"
                )

        client = self.clients.get(server_name)
        if not client:
            raise MCPConnectionError(f"Server {server_name} not connected")

        return await client.read_resource(uri)

    def get_server_status(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get status information for a server"""
        status = self.status.get(server_name)
        config = self.configs.get(server_name)

        if not status or not config:
            return None

        return {
            "config": config.to_dict(),
            "status": status.to_dict()
        }

    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all servers"""
        return {
            name: self.get_server_status(name)
            for name in self.configs.keys()
        }

    def list_tools(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available tools from all servers or a specific server.

        Args:
            server_name: Optional server name filter

        Returns:
            List of tools with server information
        """
        tools = []

        servers = [server_name] if server_name else self.status.keys()

        for name in servers:
            status = self.status.get(name)
            if not status:
                continue

            for tool in status.tools:
                tools.append({
                    "server": name,
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })

        return tools

    def list_resources(self, server_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available resources from all servers or a specific server.

        Args:
            server_name: Optional server name filter

        Returns:
            List of resources with server information
        """
        resources = []

        servers = [server_name] if server_name else self.status.keys()

        for name in servers:
            status = self.status.get(name)
            if not status:
                continue

            for resource in status.resources:
                resources.append({
                    "server": name,
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                })

        return resources

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics"""
        total_servers = len(self.configs)
        connected_servers = len(self.clients)
        total_tools = sum(len(s.tools) for s in self.status.values())
        total_resources = sum(len(s.resources) for s in self.status.values())

        total_requests = sum(s.total_requests for s in self.status.values())
        total_failures = sum(s.failed_requests for s in self.status.values())

        return {
            "total_servers": total_servers,
            "connected_servers": connected_servers,
            "enabled_servers": sum(1 for c in self.configs.values() if c.enabled),
            "total_tools": total_tools,
            "total_resources": total_resources,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "success_rate": (
                (total_requests - total_failures) / total_requests
                if total_requests > 0 else 0.0
            )
        }
