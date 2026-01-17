"""
MCP Agent Mixin for ZEJZL.NET

Provides MCP capabilities to existing agents through composition or inheritance.
Allows agents to seamlessly access MCP tools and resources.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.mcp_agent_integration import MCPAgentInterface, AgentMCPContext

logger = logging.getLogger("MCPAgentMixin")


class MCPAgentMixin:
    """
    Mixin class that adds MCP capabilities to agents.

    Usage:
        class MyAgent(MCPAgentMixin):
            def __init__(self):
                self.name = "MyAgent"
                # ... other init

            async def my_task(self):
                # Use MCP tools
                result = await self.mcp_call_tool("search", {"query": "AI"})
                data = await self.mcp_read_resource("file:///data.json")
    """

    # Class-level MCP interface (shared across all agents)
    _mcp_interface: Optional[MCPAgentInterface] = None

    @classmethod
    def set_mcp_interface(cls, interface: MCPAgentInterface):
        """Set the MCP interface for all agents using this mixin"""
        cls._mcp_interface = interface
        logger.info("MCP interface configured for agents")

    @classmethod
    def get_mcp_interface(cls) -> Optional[MCPAgentInterface]:
        """Get the shared MCP interface"""
        return cls._mcp_interface

    def _ensure_mcp_interface(self):
        """Ensure MCP interface is available"""
        if self._mcp_interface is None:
            raise RuntimeError(
                "MCP interface not initialized. "
                "Call MCPAgentMixin.set_mcp_interface() first."
            )

    def _get_agent_name(self) -> str:
        """Get the agent name (should be defined in agent class)"""
        if hasattr(self, 'name'):
            return self.name
        return self.__class__.__name__

    async def mcp_call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        server_name: Optional[str] = None,
        session_id: str = "default"
    ) -> Any:
        """
        Call an MCP tool from this agent.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments
            server_name: Optional specific server
            session_id: Session identifier

        Returns:
            Tool execution result
        """
        self._ensure_mcp_interface()

        return await self._mcp_interface.call_tool(
            agent_name=self._get_agent_name(),
            tool_name=tool_name,
            arguments=arguments,
            server_name=server_name,
            session_id=session_id
        )

    async def mcp_read_resource(
        self,
        uri: str,
        server_name: Optional[str] = None,
        session_id: str = "default",
        use_cache: bool = True
    ) -> Any:
        """
        Read an MCP resource from this agent.

        Args:
            uri: Resource URI
            server_name: Optional specific server
            session_id: Session identifier
            use_cache: Whether to use cached resource

        Returns:
            Resource content
        """
        self._ensure_mcp_interface()

        return await self._mcp_interface.read_resource(
            agent_name=self._get_agent_name(),
            uri=uri,
            server_name=server_name,
            session_id=session_id,
            use_cache=use_cache
        )

    def mcp_discover_tools(
        self,
        server_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available MCP tools for this agent.

        Args:
            server_name: Optional filter by server
            tags: Optional filter by tags

        Returns:
            List of available tools
        """
        self._ensure_mcp_interface()

        return self._mcp_interface.discover_tools(
            agent_name=self._get_agent_name(),
            server_name=server_name,
            tags=tags
        )

    def mcp_discover_resources(
        self,
        server_name: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover available MCP resources for this agent.

        Args:
            server_name: Optional filter by server
            mime_type: Optional filter by MIME type

        Returns:
            List of available resources
        """
        self._ensure_mcp_interface()

        return self._mcp_interface.discover_resources(
            agent_name=self._get_agent_name(),
            server_name=server_name,
            mime_type=mime_type
        )

    async def mcp_batch_call_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        session_id: str = "default",
        parallel: bool = True
    ) -> List[Any]:
        """
        Call multiple MCP tools in batch.

        Args:
            tool_calls: List of tool call specifications
            session_id: Session identifier
            parallel: Whether to execute in parallel

        Returns:
            List of results
        """
        self._ensure_mcp_interface()

        return await self._mcp_interface.batch_call_tools(
            agent_name=self._get_agent_name(),
            tool_calls=tool_calls,
            session_id=session_id,
            parallel=parallel
        )

    def mcp_get_stats(self, session_id: str = "default") -> Dict[str, Any]:
        """
        Get MCP usage statistics for this agent.

        Args:
            session_id: Session identifier

        Returns:
            Statistics dictionary
        """
        self._ensure_mcp_interface()

        return self._mcp_interface.get_agent_stats(
            agent_name=self._get_agent_name(),
            session_id=session_id
        )


class MCPEnhancedAgent(MCPAgentMixin):
    """
    Base class for agents with built-in MCP support.

    Inheriting from this class automatically provides all MCP methods.
    """

    def __init__(self, name: str):
        self.name = name
        logger.debug(f"MCP-enhanced agent initialized: {name}")

    async def initialize(self):
        """Optional initialization hook for subclasses"""
        pass

    async def cleanup(self):
        """Optional cleanup hook for subclasses"""
        pass


# Helper decorators for MCP-aware agent methods
def mcp_tool_required(tool_name: str, server_name: Optional[str] = None):
    """
    Decorator to ensure an MCP tool is available before executing method.

    Usage:
        @mcp_tool_required("search")
        async def search_task(self, query: str):
            result = await self.mcp_call_tool("search", {"query": query})
            return result
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Check if tool is available
            if not hasattr(self, 'mcp_discover_tools'):
                raise RuntimeError(f"{self.__class__.__name__} does not have MCP capabilities")

            tools = self.mcp_discover_tools(server_name=server_name)
            tool_names = [t["name"] for t in tools]

            if tool_name not in tool_names:
                raise ValueError(
                    f"Required MCP tool '{tool_name}' not available. "
                    f"Available tools: {', '.join(tool_names)}"
                )

            return await func(self, *args, **kwargs)

        return wrapper
    return decorator


def mcp_resource_required(uri_pattern: str):
    """
    Decorator to check if MCP resources matching pattern are available.

    Usage:
        @mcp_resource_required("file:///data/")
        async def process_data(self, filename: str):
            data = await self.mcp_read_resource(f"file:///data/{filename}")
            return data
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Check if resources are available
            if not hasattr(self, 'mcp_discover_resources'):
                raise RuntimeError(f"{self.__class__.__name__} does not have MCP capabilities")

            resources = self.mcp_discover_resources()
            resource_uris = [r["uri"] for r in resources]

            # Check if any resource matches pattern
            matching = [uri for uri in resource_uris if uri_pattern in uri]

            if not matching:
                raise ValueError(
                    f"No MCP resources matching '{uri_pattern}' found. "
                    f"Available: {len(resource_uris)} resources"
                )

            return await func(self, *args, **kwargs)

        return wrapper
    return decorator
