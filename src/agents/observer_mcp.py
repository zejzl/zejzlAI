"""
MCP-Enhanced Observer Agent for ZEJZL.NET

Enhanced version of Observer agent with MCP tool integration.
Can use external tools for web search, file access, and data gathering.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from src.mcp_agent_mixin import MCPEnhancedAgent, mcp_tool_required

logger = logging.getLogger("ObserverMCPAgent")


class ObserverMCPAgent(MCPEnhancedAgent):
    """
    Observer agent with MCP capabilities.

    Can use MCP tools for:
    - Web search for task context
    - File system access for related documents
    - API calls for real-time data
    """

    def __init__(self):
        super().__init__(name="ObserverMCP")

        self.specialization = "Enhanced Task Analysis with External Tools"
        self.responsibilities = [
            "Analyze incoming tasks using AI and external tools",
            "Gather context from web search and file systems",
            "Break down complex tasks with real-world data",
            "Identify dependencies using external resources"
        ]

        # Load personality if available
        try:
            from src.agent_personality import AGENT_PERSONALITIES
            self.personality = AGENT_PERSONALITIES.get("Observer")
        except ImportError:
            self.personality = None

        self.state = {}

    async def observe(self, task: str, use_mcp: bool = True) -> Dict[str, Any]:
        """
        Analyze and observe a task with optional MCP enhancement.

        Args:
            task: Task description
            use_mcp: Whether to use MCP tools for enhancement

        Returns:
            Observation dictionary with analysis
        """
        logger.info(f"[{self.name}] Observing task: {task}")

        # Get basic AI observation
        observation = await self._ai_observe(task)

        # Enhance with MCP tools if available and requested
        if use_mcp:
            try:
                observation = await self._enhance_with_mcp(task, observation)
            except Exception as e:
                logger.warning(f"[{self.name}] MCP enhancement failed: {e}")
                observation["mcp_enhanced"] = False
                observation["mcp_error"] = str(e)

        return observation

    async def _ai_observe(self, task: str) -> Dict[str, Any]:
        """Basic AI-powered observation"""
        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Create observation prompt
            personality_prompt = ""
            if self.personality:
                personality_prompt = self.personality.get_personality_prompt()

            prompt = f"""{personality_prompt}

Analyze this task: {task}

Return ONLY valid JSON:
{{
    "objective": "clear task goal",
    "requirements": ["requirement 1", "requirement 2"],
    "complexity_level": "Low|Medium|High",
    "estimated_effort": "Low|Medium|High",
    "context": "relevant context",
    "potential_challenges": ["challenge 1", "challenge 2"]
}}"""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",
                conversation_id=f"observer_mcp_{hash(task)}"
            )

            # Parse response
            import json
            import re

            def extract_json(text):
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                return None

            try:
                observation_data = json.loads(response)
            except json.JSONDecodeError:
                observation_data = extract_json(response)
                if not observation_data:
                    observation_data = {
                        "objective": f"Complete: {task}",
                        "requirements": [task],
                        "complexity_level": "Medium",
                        "estimated_effort": "Medium"
                    }

            observation = {
                "task": task,
                "objective": observation_data.get("objective", f"Complete: {task}"),
                "requirements": observation_data.get("requirements", [task]),
                "complexity_level": observation_data.get("complexity_level", "Medium"),
                "estimated_effort": observation_data.get("estimated_effort", "Medium"),
                "context": observation_data.get("context", "AI-generated"),
                "potential_challenges": observation_data.get("potential_challenges", []),
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": True,
                "mcp_enhanced": False
            }

            return observation

        except Exception as e:
            logger.error(f"[{self.name}] AI observation failed: {e}")
            return {
                "task": task,
                "objective": f"Complete: {task}",
                "requirements": [task],
                "complexity_level": "Unknown",
                "estimated_effort": "Unknown",
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }

    async def _enhance_with_mcp(
        self,
        task: str,
        observation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance observation using MCP tools"""
        logger.debug(f"[{self.name}] Enhancing observation with MCP tools")

        enhancements = {}

        # Discover available tools
        try:
            available_tools = self.mcp_discover_tools()
            tool_names = [t["name"] for t in available_tools]

            logger.debug(f"[{self.name}] Available MCP tools: {', '.join(tool_names)}")

            # Try web search if available
            if "search" in tool_names or "web_search" in tool_names:
                enhancements["web_context"] = await self._search_web_context(task)

            # Try file system access if available
            if "list_files" in tool_names or "read_file" in tool_names:
                enhancements["related_files"] = await self._find_related_files(task)

            # Try database access if available
            if "query" in tool_names or "search_db" in tool_names:
                enhancements["database_context"] = await self._query_database_context(task)

            observation["mcp_enhancements"] = enhancements
            observation["mcp_enhanced"] = True
            observation["mcp_tools_used"] = list(enhancements.keys())

        except Exception as e:
            logger.warning(f"[{self.name}] MCP enhancement error: {e}")
            observation["mcp_enhanced"] = False
            observation["mcp_error"] = str(e)

        return observation

    async def _search_web_context(self, task: str) -> Dict[str, Any]:
        """Search web for task-related context"""
        try:
            # Try to call web search tool
            result = await self.mcp_call_tool(
                tool_name="search",
                arguments={"query": task, "limit": 3}
            )

            return {
                "source": "web_search",
                "results": result,
                "status": "success"
            }

        except ValueError as e:
            # Tool not found, try alternative
            try:
                result = await self.mcp_call_tool(
                    tool_name="web_search",
                    arguments={"q": task, "max_results": 3}
                )
                return {
                    "source": "web_search_alt",
                    "results": result,
                    "status": "success"
                }
            except Exception:
                return {"status": "unavailable", "error": str(e)}

        except Exception as e:
            logger.debug(f"[{self.name}] Web search failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def _find_related_files(self, task: str) -> Dict[str, Any]:
        """Find files related to the task"""
        try:
            # Try to list files that might be relevant
            result = await self.mcp_call_tool(
                tool_name="list_files",
                arguments={"pattern": "*.md", "path": "."}
            )

            return {
                "source": "filesystem",
                "files": result,
                "status": "success"
            }

        except Exception as e:
            logger.debug(f"[{self.name}] File search failed: {e}")
            return {"status": "unavailable", "error": str(e)}

    async def _query_database_context(self, task: str) -> Dict[str, Any]:
        """Query database for related context"""
        try:
            # Try to query for related tasks or context
            result = await self.mcp_call_tool(
                tool_name="query",
                arguments={"sql": f"SELECT * FROM tasks WHERE description LIKE '%{task}%' LIMIT 5"}
            )

            return {
                "source": "database",
                "records": result,
                "status": "success"
            }

        except Exception as e:
            logger.debug(f"[{self.name}] Database query failed: {e}")
            return {"status": "unavailable", "error": str(e)}

    async def observe_with_tools(
        self,
        task: str,
        tools: List[str]
    ) -> Dict[str, Any]:
        """
        Observe a task using specific MCP tools.

        Args:
            task: Task description
            tools: List of tool names to use

        Returns:
            Enhanced observation
        """
        logger.info(f"[{self.name}] Observing with specific tools: {', '.join(tools)}")

        # Get basic observation
        observation = await self._ai_observe(task)

        # Call specific tools
        tool_results = {}

        for tool_name in tools:
            try:
                # Determine arguments based on tool name
                if "search" in tool_name.lower():
                    args = {"query": task}
                elif "file" in tool_name.lower():
                    args = {"pattern": "*.md"}
                else:
                    args = {}

                result = await self.mcp_call_tool(tool_name, args)
                tool_results[tool_name] = {
                    "status": "success",
                    "result": result
                }

            except Exception as e:
                tool_results[tool_name] = {
                    "status": "failed",
                    "error": str(e)
                }

        observation["tool_results"] = tool_results
        observation["mcp_enhanced"] = True

        return observation

    def get_available_enhancements(self) -> List[str]:
        """Get list of available MCP enhancements"""
        try:
            tools = self.mcp_discover_tools()
            tool_names = [t["name"] for t in tools]

            enhancements = []

            if any("search" in name.lower() for name in tool_names):
                enhancements.append("web_search")

            if any("file" in name.lower() for name in tool_names):
                enhancements.append("filesystem_access")

            if any("query" in name.lower() or "db" in name.lower() for name in tool_names):
                enhancements.append("database_access")

            return enhancements

        except Exception:
            return []

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP integration status"""
        try:
            tools = self.mcp_discover_tools()
            resources = self.mcp_discover_resources()
            stats = self.mcp_get_stats()

            return {
                "enabled": True,
                "available_tools": len(tools),
                "available_resources": len(resources),
                "usage_stats": stats,
                "enhancements": self.get_available_enhancements()
            }

        except Exception as e:
            return {
                "enabled": False,
                "error": str(e)
            }
