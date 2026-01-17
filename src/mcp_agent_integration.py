"""
MCP Agent Integration Layer for ZEJZL.NET

Provides high-level API for agents to access MCP tools and resources.
Handles context management, error recovery, and usage tracking.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from src.mcp_registry import MCPServerRegistry
from src.mcp_types import MCPTool, MCPResource
from src.mcp_client import MCPConnectionError, MCPProtocolError, MCPTimeoutError

logger = logging.getLogger("MCPAgentIntegration")


@dataclass
class AgentMCPContext:
    """Context for agent MCP operations"""
    agent_name: str
    session_id: str

    # Usage tracking
    tools_called: int = 0
    resources_read: int = 0
    errors_encountered: int = 0

    # Performance metrics
    total_execution_time: float = 0.0
    avg_tool_latency: float = 0.0

    # History
    recent_operations: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 50

    def record_operation(
        self,
        operation_type: str,
        server_name: str,
        target: str,
        success: bool,
        latency: float,
        error: Optional[str] = None
    ):
        """Record an MCP operation for tracking"""
        operation = {
            "timestamp": datetime.now().isoformat(),
            "type": operation_type,
            "server": server_name,
            "target": target,
            "success": success,
            "latency": latency,
            "error": error
        }

        self.recent_operations.append(operation)

        # Trim history if needed
        if len(self.recent_operations) > self.max_history:
            self.recent_operations = self.recent_operations[-self.max_history:]

        # Update metrics
        self.total_execution_time += latency

        if operation_type == "tool_call":
            if success:
                self.tools_called += 1
                self.avg_tool_latency = (
                    (self.avg_tool_latency * (self.tools_called - 1) + latency)
                    / self.tools_called
                )
            else:
                self.errors_encountered += 1
        elif operation_type == "resource_read":
            if success:
                self.resources_read += 1
            else:
                self.errors_encountered += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get context statistics"""
        return {
            "agent_name": self.agent_name,
            "session_id": self.session_id,
            "tools_called": self.tools_called,
            "resources_read": self.resources_read,
            "errors_encountered": self.errors_encountered,
            "total_execution_time": self.total_execution_time,
            "avg_tool_latency": self.avg_tool_latency,
            "success_rate": (
                (self.tools_called + self.resources_read) /
                (self.tools_called + self.resources_read + self.errors_encountered)
                if (self.tools_called + self.resources_read + self.errors_encountered) > 0
                else 0.0
            )
        }


class MCPAgentInterface:
    """
    High-level interface for agents to access MCP capabilities.

    Provides:
    - Simple tool calling with automatic routing
    - Resource access with caching
    - Context management per agent
    - Error handling and retries
    - Usage tracking and analytics
    """

    def __init__(
        self,
        registry: MCPServerRegistry,
        enable_caching: bool = True,
        default_timeout: float = 30.0
    ):
        self.registry = registry
        self.enable_caching = enable_caching
        self.default_timeout = default_timeout

        # Context management
        self.contexts: Dict[str, AgentMCPContext] = {}

        # Resource cache
        self.resource_cache: Dict[str, tuple[Any, datetime]] = {}
        self.cache_ttl = 300  # 5 minutes

        # Tool shortcuts (tool_name -> server_name mapping)
        self.tool_shortcuts: Dict[str, str] = {}

        # Event callbacks
        self.on_tool_called: Optional[Callable] = None
        self.on_resource_read: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

    def get_context(self, agent_name: str, session_id: str = "default") -> AgentMCPContext:
        """Get or create context for an agent"""
        context_key = f"{agent_name}:{session_id}"

        if context_key not in self.contexts:
            self.contexts[context_key] = AgentMCPContext(
                agent_name=agent_name,
                session_id=session_id
            )

        return self.contexts[context_key]

    async def call_tool(
        self,
        agent_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None,
        session_id: str = "default",
        timeout: Optional[float] = None
    ) -> Any:
        """
        Call an MCP tool from an agent.

        Args:
            agent_name: Name of the calling agent
            tool_name: Name of tool to call
            arguments: Tool arguments
            server_name: Optional specific server (auto-discovers if not provided)
            session_id: Session identifier for context tracking
            timeout: Optional timeout override

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or access denied
            MCPConnectionError: If server connection fails
            MCPTimeoutError: If operation times out
        """
        context = self.get_context(agent_name, session_id)
        start_time = datetime.now()

        # Auto-discover server if not provided
        if not server_name:
            server_name = await self._find_tool_server(tool_name)
            if not server_name:
                raise ValueError(f"Tool '{tool_name}' not found in any connected server")

        logger.info(f"Agent {agent_name} calling tool {tool_name} on {server_name}")

        try:
            # Call tool through registry
            result = await asyncio.wait_for(
                self.registry.call_tool(
                    server_name=server_name,
                    tool_name=tool_name,
                    arguments=arguments,
                    agent_name=agent_name
                ),
                timeout=timeout or self.default_timeout
            )

            # Record success
            latency = (datetime.now() - start_time).total_seconds()
            context.record_operation(
                operation_type="tool_call",
                server_name=server_name,
                target=tool_name,
                success=True,
                latency=latency
            )

            # Trigger callback
            if self.on_tool_called:
                await self.on_tool_called(agent_name, server_name, tool_name, result)

            logger.debug(f"Tool call successful: {tool_name} ({latency:.3f}s)")
            return result

        except asyncio.TimeoutError:
            latency = (datetime.now() - start_time).total_seconds()
            error = f"Tool call timed out after {timeout or self.default_timeout}s"

            context.record_operation(
                operation_type="tool_call",
                server_name=server_name,
                target=tool_name,
                success=False,
                latency=latency,
                error=error
            )

            if self.on_error:
                await self.on_error(agent_name, "timeout", error)

            raise MCPTimeoutError(error)

        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            context.record_operation(
                operation_type="tool_call",
                server_name=server_name,
                target=tool_name,
                success=False,
                latency=latency,
                error=error_msg
            )

            if self.on_error:
                await self.on_error(agent_name, "tool_call_error", error_msg)

            logger.error(f"Tool call failed: {tool_name} - {error_msg}")
            raise

    async def read_resource(
        self,
        agent_name: str,
        uri: str,
        server_name: Optional[str] = None,
        session_id: str = "default",
        use_cache: bool = True
    ) -> Any:
        """
        Read an MCP resource from an agent.

        Args:
            agent_name: Name of the calling agent
            uri: Resource URI
            server_name: Optional specific server (auto-discovers if not provided)
            session_id: Session identifier for context tracking
            use_cache: Whether to use cached resource (if available)

        Returns:
            Resource content
        """
        context = self.get_context(agent_name, session_id)
        start_time = datetime.now()

        # Check cache if enabled
        if use_cache and self.enable_caching:
            cached_result = self._get_cached_resource(uri)
            if cached_result is not None:
                logger.debug(f"Resource cache hit: {uri}")
                return cached_result

        # Auto-discover server if not provided
        if not server_name:
            server_name = await self._find_resource_server(uri)
            if not server_name:
                raise ValueError(f"Resource '{uri}' not found in any connected server")

        logger.info(f"Agent {agent_name} reading resource {uri} from {server_name}")

        try:
            # Read resource through registry
            result = await self.registry.read_resource(
                server_name=server_name,
                uri=uri,
                agent_name=agent_name
            )

            # Cache result if enabled
            if self.enable_caching:
                self._cache_resource(uri, result)

            # Record success
            latency = (datetime.now() - start_time).total_seconds()
            context.record_operation(
                operation_type="resource_read",
                server_name=server_name,
                target=uri,
                success=True,
                latency=latency
            )

            # Trigger callback
            if self.on_resource_read:
                await self.on_resource_read(agent_name, server_name, uri, result)

            logger.debug(f"Resource read successful: {uri} ({latency:.3f}s)")
            return result

        except Exception as e:
            latency = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)

            context.record_operation(
                operation_type="resource_read",
                server_name=server_name,
                target=uri,
                success=False,
                latency=latency,
                error=error_msg
            )

            if self.on_error:
                await self.on_error(agent_name, "resource_read_error", error_msg)

            logger.error(f"Resource read failed: {uri} - {error_msg}")
            raise

    async def _find_tool_server(self, tool_name: str) -> Optional[str]:
        """Find which server provides a specific tool"""
        # Check shortcut cache first
        if tool_name in self.tool_shortcuts:
            return self.tool_shortcuts[tool_name]

        # Search through all registered servers
        all_tools = self.registry.list_tools()

        for tool_info in all_tools:
            if tool_info["name"] == tool_name:
                server_name = tool_info["server"]
                # Cache for future lookups
                self.tool_shortcuts[tool_name] = server_name
                return server_name

        return None

    async def _find_resource_server(self, uri: str) -> Optional[str]:
        """Find which server provides a specific resource"""
        # Search through all registered servers
        all_resources = self.registry.list_resources()

        for resource_info in all_resources:
            if resource_info["uri"] == uri:
                return resource_info["server"]

        return None

    def _get_cached_resource(self, uri: str) -> Optional[Any]:
        """Get cached resource if valid"""
        if uri not in self.resource_cache:
            return None

        content, cached_at = self.resource_cache[uri]

        # Check if cache is still valid
        age = (datetime.now() - cached_at).total_seconds()
        if age > self.cache_ttl:
            # Cache expired
            del self.resource_cache[uri]
            return None

        return content

    def _cache_resource(self, uri: str, content: Any):
        """Cache a resource"""
        self.resource_cache[uri] = (content, datetime.now())

    def clear_cache(self):
        """Clear resource cache"""
        self.resource_cache.clear()
        logger.info("Resource cache cleared")

    def discover_tools(
        self,
        agent_name: str,
        server_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available tools for an agent.

        Args:
            agent_name: Name of the agent
            server_name: Optional filter by server
            tags: Optional filter by tags

        Returns:
            List of available tools with metadata
        """
        all_tools = self.registry.list_tools(server_name)

        # Filter by agent permissions
        accessible_tools = []

        for tool_info in all_tools:
            server = tool_info["server"]
            config = self.registry.configs.get(server)

            if not config:
                continue

            # Check if agent has access
            if config.allowed_agents and agent_name not in config.allowed_agents:
                continue

            # Filter by tags if provided
            if tags:
                if not any(tag in config.tags for tag in tags):
                    continue

            accessible_tools.append({
                "name": tool_info["name"],
                "server": server,
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"],
                "tags": config.tags
            })

        return accessible_tools

    def discover_resources(
        self,
        agent_name: str,
        server_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available resources for an agent.

        Args:
            agent_name: Name of the agent
            server_name: Optional filter by server
            mime_type: Optional filter by MIME type

        Returns:
            List of available resources with metadata
        """
        all_resources = self.registry.list_resources(server_name)

        # Filter by agent permissions
        accessible_resources = []

        for resource_info in all_resources:
            server = resource_info["server"]
            config = self.registry.configs.get(server)

            if not config:
                continue

            # Check if agent has access
            if config.allowed_agents and agent_name not in config.allowed_agents:
                continue

            # Filter by MIME type if provided
            if mime_type and resource_info.get("mimeType") != mime_type:
                continue

            accessible_resources.append({
                "uri": resource_info["uri"],
                "server": server,
                "name": resource_info["name"],
                "description": resource_info["description"],
                "mimeType": resource_info.get("mimeType")
            })

        return accessible_resources

    def get_agent_stats(self, agent_name: str, session_id: str = "default") -> Dict[str, Any]:
        """Get statistics for an agent's MCP usage"""
        context = self.get_context(agent_name, session_id)
        return context.get_stats()

    def get_all_agent_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all agents"""
        return {
            context_key: context.get_stats()
            for context_key, context in self.contexts.items()
        }

    async def batch_call_tools(
        self,
        agent_name: str,
        tool_calls: List[Dict[str, Any]],
        session_id: str = "default",
        parallel: bool = True
    ) -> List[Any]:
        """
        Call multiple tools in batch.

        Args:
            agent_name: Name of the calling agent
            tool_calls: List of tool call specifications
                Each item: {"tool_name": str, "arguments": dict, "server_name": str (optional)}
            session_id: Session identifier
            parallel: Whether to execute calls in parallel

        Returns:
            List of results (in same order as tool_calls)
        """
        if parallel:
            # Execute all calls concurrently
            tasks = [
                self.call_tool(
                    agent_name=agent_name,
                    tool_name=call["tool_name"],
                    arguments=call.get("arguments"),
                    server_name=call.get("server_name"),
                    session_id=session_id
                )
                for call in tool_calls
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        else:
            # Execute sequentially
            results = []
            for call in tool_calls:
                try:
                    result = await self.call_tool(
                        agent_name=agent_name,
                        tool_name=call["tool_name"],
                        arguments=call.get("arguments"),
                        server_name=call.get("server_name"),
                        session_id=session_id
                    )
                    results.append(result)
                except Exception as e:
                    results.append(e)

            return results


# Convenience functions for direct agent usage
async def agent_call_tool(
    agent_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    mcp_interface: Optional[MCPAgentInterface] = None
) -> Any:
    """
    Convenience function for agents to call MCP tools.
    Uses global MCP interface if not provided.
    """
    if mcp_interface is None:
        raise ValueError("MCP interface not initialized. Call initialize_mcp() first.")

    return await mcp_interface.call_tool(
        agent_name=agent_name,
        tool_name=tool_name,
        arguments=arguments
    )


async def agent_read_resource(
    agent_name: str,
    uri: str,
    mcp_interface: Optional[MCPAgentInterface] = None
) -> Any:
    """
    Convenience function for agents to read MCP resources.
    Uses global MCP interface if not provided.
    """
    if mcp_interface is None:
        raise ValueError("MCP interface not initialized. Call initialize_mcp() first.")

    return await mcp_interface.read_resource(
        agent_name=agent_name,
        uri=uri
    )


def agent_discover_tools(
    agent_name: str,
    mcp_interface: Optional[MCPAgentInterface] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function for agents to discover available tools.
    """
    if mcp_interface is None:
        raise ValueError("MCP interface not initialized. Call initialize_mcp() first.")

    return mcp_interface.discover_tools(agent_name=agent_name)


# Global MCP interface instance (optional)
_global_mcp_interface: Optional[MCPAgentInterface] = None


async def initialize_mcp(
    config_path: Optional[Path] = None,
    enable_caching: bool = True
) -> MCPAgentInterface:
    """
    Initialize global MCP interface for agent usage.

    Args:
        config_path: Path to MCP server configuration
        enable_caching: Whether to enable resource caching

    Returns:
        Initialized MCP interface
    """
    global _global_mcp_interface

    # Create and start registry
    registry = MCPServerRegistry(config_path=config_path)
    await registry.start()

    # Create interface
    _global_mcp_interface = MCPAgentInterface(
        registry=registry,
        enable_caching=enable_caching
    )

    logger.info("MCP agent interface initialized")
    return _global_mcp_interface


def get_mcp_interface() -> Optional[MCPAgentInterface]:
    """Get the global MCP interface"""
    return _global_mcp_interface


async def shutdown_mcp():
    """Shutdown global MCP interface"""
    global _global_mcp_interface

    if _global_mcp_interface:
        await _global_mcp_interface.registry.stop()
        _global_mcp_interface = None
        logger.info("MCP agent interface shutdown")
