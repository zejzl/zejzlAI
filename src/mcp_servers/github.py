#!/usr/bin/env python3
"""
GitHub API MCP Server for ZEJZL.NET

Provides GitHub operations via MCP protocol.
Supports repository operations, issues, pull requests, and releases.
"""

import os
import json
import logging
import asyncio
import aiohttp
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_types import MCPServerInfo, MCPServerCapabilities

logger = logging.getLogger("GitHubMCPServer")


class GitHubMCPServer(BaseMCPServer):
    """
    MCP server for GitHub API operations.

    Tools:
    - get_repo: Get repository information
    - list_issues: List repository issues
    - create_issue: Create a new issue
    - get_issue: Get specific issue details
    - list_pulls: List pull requests
    - get_file: Get file contents from repository
    - search_repos: Search GitHub repositories
    - get_user: Get user information
    """

    def __init__(self, github_token: Optional[str] = None):
        super().__init__(name="github", version="1.0.0")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.session: aiohttp.ClientSession = None
        self.api_base = "https://api.github.com"

    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        capabilities = MCPServerCapabilities()

        return MCPServerInfo(
            name="github",
            version="1.0.0",
            capabilities=capabilities,
            protocolVersion="2024-11-05"
        )

    async def register_tools(self):
        """Register GitHub tools"""

        # Initialize HTTP session
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ZEJZL-NET-MCP/1.0"
        }

        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
            logger.info("GitHub API: Authenticated mode")
        else:
            logger.warning("GitHub API: Unauthenticated mode (rate limited)")

        self.session = aiohttp.ClientSession(headers=headers)

        # Tool: get_repo
        self.add_tool(
            name="get_repo",
            description="Get repository information",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner (user or organization)"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    }
                },
                "required": ["owner", "repo"]
            },
            handler=self._get_repo
        )

        # Tool: list_issues
        self.add_tool(
            name="list_issues",
            description="List repository issues",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "state": {
                        "type": "string",
                        "description": "Issue state (open, closed, all)",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["owner", "repo"]
            },
            handler=self._list_issues
        )

        # Tool: create_issue
        self.add_tool(
            name="create_issue",
            description="Create a new issue",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "title": {
                        "type": "string",
                        "description": "Issue title"
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue body/description",
                        "default": ""
                    },
                    "labels": {
                        "type": "array",
                        "description": "Issue labels",
                        "items": {"type": "string"},
                        "default": []
                    }
                },
                "required": ["owner", "repo", "title"]
            },
            handler=self._create_issue
        )

        # Tool: get_issue
        self.add_tool(
            name="get_issue",
            description="Get specific issue details",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "issue_number": {
                        "type": "integer",
                        "description": "Issue number"
                    }
                },
                "required": ["owner", "repo", "issue_number"]
            },
            handler=self._get_issue
        )

        # Tool: list_pulls
        self.add_tool(
            name="list_pulls",
            description="List pull requests",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "state": {
                        "type": "string",
                        "description": "PR state (open, closed, all)",
                        "enum": ["open", "closed", "all"],
                        "default": "open"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["owner", "repo"]
            },
            handler=self._list_pulls
        )

        # Tool: get_file
        self.add_tool(
            name="get_file",
            description="Get file contents from repository",
            input_schema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "Repository owner"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Repository name"
                    },
                    "path": {
                        "type": "string",
                        "description": "File path in repository"
                    },
                    "ref": {
                        "type": "string",
                        "description": "Git ref (branch, tag, commit SHA) - default: main",
                        "default": "main"
                    }
                },
                "required": ["owner", "repo", "path"]
            },
            handler=self._get_file
        )

        # Tool: search_repos
        self.add_tool(
            name="search_repos",
            description="Search GitHub repositories",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "sort": {
                        "type": "string",
                        "description": "Sort by (stars, forks, updated)",
                        "enum": ["stars", "forks", "updated"],
                        "default": "stars"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["query"]
            },
            handler=self._search_repos
        )

        # Tool: get_user
        self.add_tool(
            name="get_user",
            description="Get user information",
            input_schema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub username"
                    }
                },
                "required": ["username"]
            },
            handler=self._get_user
        )

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make GitHub API request"""
        url = f"{self.api_base}{endpoint}"

        try:
            if method == "GET":
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    return await self._handle_response(response)

            elif method == "POST":
                async with self.session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    return await self._handle_response(response)

            else:
                raise ValueError(f"Unsupported method: {method}")

        except asyncio.TimeoutError:
            raise ValueError("GitHub API request timed out")
        except aiohttp.ClientError as e:
            raise ValueError(f"GitHub API request failed: {e}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Handle API response"""
        if response.status == 200 or response.status == 201:
            return await response.json()

        elif response.status == 404:
            raise ValueError("Resource not found")

        elif response.status == 401:
            raise ValueError("Unauthorized - invalid or missing GitHub token")

        elif response.status == 403:
            error_data = await response.json()
            if "rate limit" in str(error_data).lower():
                raise ValueError("GitHub API rate limit exceeded")
            raise ValueError("Forbidden - check permissions")

        else:
            error_data = await response.json()
            message = error_data.get("message", "Unknown error")
            raise ValueError(f"GitHub API error ({response.status}): {message}")

    async def _get_repo(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information"""
        owner = args.get("owner")
        repo = args.get("repo")

        endpoint = f"/repos/{owner}/{repo}"
        data = await self._api_request("GET", endpoint)

        return {
            "name": data["name"],
            "full_name": data["full_name"],
            "description": data.get("description"),
            "url": data["html_url"],
            "stars": data["stargazers_count"],
            "forks": data["forks_count"],
            "open_issues": data["open_issues_count"],
            "language": data.get("language"),
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "default_branch": data["default_branch"]
        }

    async def _list_issues(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List repository issues"""
        owner = args.get("owner")
        repo = args.get("repo")
        state = args.get("state", "open")
        max_results = args.get("max_results", 10)

        endpoint = f"/repos/{owner}/{repo}/issues?state={state}&per_page={max_results}"
        data = await self._api_request("GET", endpoint)

        issues = []
        for issue in data:
            # Filter out pull requests (GitHub API returns PRs as issues)
            if "pull_request" not in issue:
                issues.append({
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "body": issue.get("body", "")[:200],  # Truncate
                    "user": issue["user"]["login"],
                    "labels": [label["name"] for label in issue["labels"]],
                    "created_at": issue["created_at"],
                    "url": issue["html_url"]
                })

        return {
            "owner": owner,
            "repo": repo,
            "count": len(issues),
            "issues": issues
        }

    async def _create_issue(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue"""
        if not self.github_token:
            raise ValueError("GitHub token required to create issues")

        owner = args.get("owner")
        repo = args.get("repo")
        title = args.get("title")
        body = args.get("body", "")
        labels = args.get("labels", [])

        endpoint = f"/repos/{owner}/{repo}/issues"
        payload = {
            "title": title,
            "body": body,
            "labels": labels
        }

        data = await self._api_request("POST", endpoint, payload)

        return {
            "number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "url": data["html_url"],
            "created": True
        }

    async def _get_issue(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific issue details"""
        owner = args.get("owner")
        repo = args.get("repo")
        issue_number = args.get("issue_number")

        endpoint = f"/repos/{owner}/{repo}/issues/{issue_number}"
        data = await self._api_request("GET", endpoint)

        return {
            "number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "body": data.get("body", ""),
            "user": data["user"]["login"],
            "labels": [label["name"] for label in data["labels"]],
            "created_at": data["created_at"],
            "updated_at": data["updated_at"],
            "comments": data["comments"],
            "url": data["html_url"]
        }

    async def _list_pulls(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List pull requests"""
        owner = args.get("owner")
        repo = args.get("repo")
        state = args.get("state", "open")
        max_results = args.get("max_results", 10)

        endpoint = f"/repos/{owner}/{repo}/pulls?state={state}&per_page={max_results}"
        data = await self._api_request("GET", endpoint)

        pulls = []
        for pr in data:
            pulls.append({
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "user": pr["user"]["login"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "head": pr["head"]["ref"],
                "base": pr["base"]["ref"],
                "url": pr["html_url"]
            })

        return {
            "owner": owner,
            "repo": repo,
            "count": len(pulls),
            "pulls": pulls
        }

    async def _get_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get file contents from repository"""
        owner = args.get("owner")
        repo = args.get("repo")
        path = args.get("path")
        ref = args.get("ref", "main")

        endpoint = f"/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        data = await self._api_request("GET", endpoint)

        # Decode base64 content
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")

        return {
            "path": path,
            "ref": ref,
            "content": content,
            "size": data["size"],
            "sha": data["sha"],
            "url": data["html_url"]
        }

    async def _search_repos(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search GitHub repositories"""
        query = args.get("query")
        sort = args.get("sort", "stars")
        max_results = args.get("max_results", 10)

        endpoint = f"/search/repositories?q={query}&sort={sort}&per_page={max_results}"
        data = await self._api_request("GET", endpoint)

        repos = []
        for repo in data["items"]:
            repos.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo.get("description"),
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "language": repo.get("language"),
                "updated_at": repo["updated_at"]
            })

        return {
            "query": query,
            "total_count": data["total_count"],
            "count": len(repos),
            "repositories": repos
        }

    async def _get_user(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information"""
        username = args.get("username")

        endpoint = f"/users/{username}"
        data = await self._api_request("GET", endpoint)

        return {
            "login": data["login"],
            "name": data.get("name"),
            "bio": data.get("bio"),
            "company": data.get("company"),
            "location": data.get("location"),
            "email": data.get("email"),
            "public_repos": data["public_repos"],
            "followers": data["followers"],
            "following": data["following"],
            "created_at": data["created_at"],
            "url": data["html_url"]
        }

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
        handlers=[logging.FileHandler("mcp_github.log")]
    )

    server = GitHubMCPServer()
    server.run()
