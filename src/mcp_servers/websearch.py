#!/usr/bin/env python3
"""
Web Search MCP Server for ZEJZL.NET

Provides web search capabilities via MCP protocol.
Uses DuckDuckGo for free, anonymous searching without API keys.
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Any, Dict, List
from urllib.parse import quote_plus

from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_types import MCPServerInfo, MCPServerCapabilities

logger = logging.getLogger("WebSearchMCPServer")


class WebSearchMCPServer(BaseMCPServer):
    """
    MCP server for web search operations.

    Tools:
    - search: Search the web using DuckDuckGo
    - search_news: Search news articles
    - get_instant_answer: Get instant answer/summary
    """

    def __init__(self):
        super().__init__(name="websearch", version="1.0.0")
        self.session: aiohttp.ClientSession = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        capabilities = MCPServerCapabilities()

        return MCPServerInfo(
            name="websearch",
            version="1.0.0",
            capabilities=capabilities,
            protocolVersion="2024-11-05"
        )

    async def register_tools(self):
        """Register web search tools"""

        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )

        # Tool: search
        self.add_tool(
            name="search",
            description="Search the web using DuckDuckGo",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "region": {
                        "type": "string",
                        "description": "Region code (e.g., 'us-en', 'uk-en', default: 'wt-wt')",
                        "default": "wt-wt"
                    }
                },
                "required": ["query"]
            },
            handler=self._search
        )

        # Tool: search_news
        self.add_tool(
            name="search_news",
            description="Search news articles",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "News search query"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": ["query"]
            },
            handler=self._search_news
        )

        # Tool: instant_answer
        self.add_tool(
            name="instant_answer",
            description="Get instant answer or summary for a query",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query for instant answer"
                    }
                },
                "required": ["query"]
            },
            handler=self._instant_answer
        )

    async def _search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Perform web search"""
        query = args.get("query")
        max_results = args.get("max_results", 10)
        region = args.get("region", "wt-wt")

        if not query:
            raise ValueError("Search query required")

        logger.info(f"Searching: {query}")

        try:
            # Use DuckDuckGo HTML API
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&kl={region}"

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise ValueError(f"Search failed with status {response.status}")

                html = await response.text()

                # Parse results (simple text extraction)
                results = self._parse_search_results(html, max_results)

                return {
                    "query": query,
                    "count": len(results),
                    "results": results,
                    "region": region
                }

        except asyncio.TimeoutError:
            raise ValueError("Search request timed out")
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise ValueError(f"Search failed: {e}")

    def _parse_search_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse search results from HTML (simple extraction)"""
        results = []

        # Simple parsing - look for result blocks
        # This is a basic implementation; in production, use BeautifulSoup
        lines = html.split('\n')

        current_result = {}
        in_result = False

        for line in lines:
            # Detect result start
            if 'class="result' in line or 'class=\'result' in line:
                if current_result:
                    results.append(current_result)
                current_result = {}
                in_result = True

            if in_result:
                # Extract title
                if 'class="result__a' in line:
                    # Extract text between > and <
                    start = line.find('>') + 1
                    end = line.find('</a>', start)
                    if start > 0 and end > start:
                        title = line[start:end].strip()
                        if title:
                            current_result['title'] = self._clean_html(title)

                # Extract URL
                if 'href="//' in line or 'href="http' in line:
                    start = line.find('href="') + 6
                    end = line.find('"', start)
                    if start > 5 and end > start:
                        url = line[start:end]
                        if url.startswith('//'):
                            url = 'https:' + url
                        current_result['url'] = url

                # Extract snippet
                if 'class="result__snippet' in line:
                    start = line.find('>') + 1
                    end = line.rfind('<')
                    if start > 0 and end > start:
                        snippet = line[start:end].strip()
                        if snippet:
                            current_result['snippet'] = self._clean_html(snippet)

            if len(results) >= max_results:
                break

        if current_result and len(results) < max_results:
            results.append(current_result)

        return results[:max_results]

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and decode entities"""
        import re
        import html

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = ' '.join(text.split())

        return text

    async def _search_news(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search news articles"""
        query = args.get("query")
        max_results = args.get("max_results", 10)

        if not query:
            raise ValueError("Search query required")

        logger.info(f"Searching news: {query}")

        try:
            # Use DuckDuckGo news search
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}&iar=news&ia=news"

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise ValueError(f"News search failed with status {response.status}")

                html = await response.text()

                # Parse news results
                results = self._parse_search_results(html, max_results)

                return {
                    "query": query,
                    "count": len(results),
                    "results": results,
                    "type": "news"
                }

        except asyncio.TimeoutError:
            raise ValueError("News search request timed out")
        except Exception as e:
            logger.error(f"News search error: {e}")
            raise ValueError(f"News search failed: {e}")

    async def _instant_answer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get instant answer"""
        query = args.get("query")

        if not query:
            raise ValueError("Query required")

        logger.info(f"Getting instant answer: {query}")

        try:
            # Use DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1"

            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    raise ValueError(f"API request failed with status {response.status}")

                data = await response.json()

                # Extract relevant information
                result = {
                    "query": query,
                    "answer": data.get("Answer") or data.get("AbstractText") or "",
                    "answer_type": data.get("AnswerType") or data.get("Type") or "none",
                    "heading": data.get("Heading") or "",
                    "abstract": data.get("Abstract") or "",
                    "abstract_source": data.get("AbstractSource") or "",
                    "abstract_url": data.get("AbstractURL") or "",
                    "definition": data.get("Definition") or "",
                    "definition_source": data.get("DefinitionSource") or ""
                }

                # Add related topics if available
                if data.get("RelatedTopics"):
                    related = []
                    for topic in data["RelatedTopics"][:5]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            related.append({
                                "text": topic.get("Text"),
                                "url": topic.get("FirstURL", "")
                            })
                    result["related_topics"] = related

                return result

        except asyncio.TimeoutError:
            raise ValueError("Instant answer request timed out")
        except Exception as e:
            logger.error(f"Instant answer error: {e}")
            raise ValueError(f"Instant answer failed: {e}")

    async def cleanup(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("HTTP session closed")


if __name__ == "__main__":
    # Run server in stdio mode
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("mcp_websearch.log")]
    )

    server = WebSearchMCPServer()
    server.run()
