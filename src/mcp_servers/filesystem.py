#!/usr/bin/env python3
"""
Filesystem MCP Server for ZEJZL.NET

Provides file system operations via MCP protocol.
Supports reading, writing, listing, and searching files.
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List
import glob

from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_types import MCPServerInfo, MCPServerCapabilities

logger = logging.getLogger("FilesystemMCPServer")


class FilesystemMCPServer(BaseMCPServer):
    """
    MCP server for filesystem operations.

    Tools:
    - read_file: Read file contents
    - write_file: Write file contents
    - list_files: List files in directory
    - search_files: Search for files by pattern
    - file_info: Get file metadata
    - create_directory: Create directory
    - delete_file: Delete file
    """

    def __init__(self, root_path: str = "."):
        super().__init__(name="filesystem", version="1.0.0")
        self.root_path = Path(root_path).resolve()
        logger.info(f"Filesystem server root: {self.root_path}")

    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        capabilities = MCPServerCapabilities()

        return MCPServerInfo(
            name="filesystem",
            version="1.0.0",
            capabilities=capabilities,
            protocolVersion="2024-11-05"
        )

    async def register_tools(self):
        """Register filesystem tools"""

        # Tool: read_file
        self.add_tool(
            name="read_file",
            description="Read contents of a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to root)"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    }
                },
                "required": ["path"]
            },
            handler=self._read_file
        )

        # Tool: write_file
        self.add_tool(
            name="write_file",
            description="Write contents to a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to root)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "File encoding (default: utf-8)",
                        "default": "utf-8"
                    }
                },
                "required": ["path", "content"]
            },
            handler=self._write_file
        )

        # Tool: list_files
        self.add_tool(
            name="list_files",
            description="List files in a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (relative to root, default: '.')",
                        "default": "."
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern filter (e.g., '*.py')",
                        "default": "*"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search recursively",
                        "default": False
                    }
                },
                "required": []
            },
            handler=self._list_files
        )

        # Tool: search_files
        self.add_tool(
            name="search_files",
            description="Search for files by name pattern",
            input_schema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py')"
                    },
                    "path": {
                        "type": "string",
                        "description": "Search root (relative, default: '.')",
                        "default": "."
                    }
                },
                "required": ["pattern"]
            },
            handler=self._search_files
        )

        # Tool: file_info
        self.add_tool(
            name="file_info",
            description="Get file metadata (size, modified time, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to root)"
                    }
                },
                "required": ["path"]
            },
            handler=self._file_info
        )

        # Tool: create_directory
        self.add_tool(
            name="create_directory",
            description="Create a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (relative to root)"
                    },
                    "parents": {
                        "type": "boolean",
                        "description": "Create parent directories (default: True)",
                        "default": True
                    }
                },
                "required": ["path"]
            },
            handler=self._create_directory
        )

        # Tool: delete_file
        self.add_tool(
            name="delete_file",
            description="Delete a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file (relative to root)"
                    }
                },
                "required": ["path"]
            },
            handler=self._delete_file
        )

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve and validate path within root"""
        full_path = (self.root_path / relative_path).resolve()

        # Security check: ensure path is within root
        if not str(full_path).startswith(str(self.root_path)):
            raise ValueError(f"Path outside root directory: {relative_path}")

        return full_path

    async def _read_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        path_str = args.get("path")
        encoding = args.get("encoding", "utf-8")

        full_path = self._resolve_path(path_str)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path_str}")

        if not full_path.is_file():
            raise ValueError(f"Not a file: {path_str}")

        try:
            content = full_path.read_text(encoding=encoding)

            return {
                "path": path_str,
                "content": content,
                "size": full_path.stat().st_size,
                "encoding": encoding
            }

        except UnicodeDecodeError:
            # Try reading as binary
            content_bytes = full_path.read_bytes()
            return {
                "path": path_str,
                "content": content_bytes.hex(),
                "size": len(content_bytes),
                "encoding": "binary",
                "note": "File read as binary (hex encoded)"
            }

    async def _write_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Write file contents"""
        path_str = args.get("path")
        content = args.get("content")
        encoding = args.get("encoding", "utf-8")

        full_path = self._resolve_path(path_str)

        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        full_path.write_text(content, encoding=encoding)

        return {
            "path": path_str,
            "bytes_written": len(content.encode(encoding)),
            "success": True
        }

    async def _list_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List files in directory"""
        path_str = args.get("path", ".")
        pattern = args.get("pattern", "*")
        recursive = args.get("recursive", False)

        full_path = self._resolve_path(path_str)

        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path_str}")

        if not full_path.is_dir():
            raise ValueError(f"Not a directory: {path_str}")

        # List files
        if recursive:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = pattern

        files = []
        for item in full_path.glob(glob_pattern):
            rel_path = item.relative_to(self.root_path)

            file_info = {
                "path": str(rel_path),
                "name": item.name,
                "type": "file" if item.is_file() else "directory",
                "size": item.stat().st_size if item.is_file() else None
            }

            files.append(file_info)

        return {
            "directory": path_str,
            "pattern": pattern,
            "recursive": recursive,
            "count": len(files),
            "files": files
        }

    async def _search_files(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by pattern"""
        pattern = args.get("pattern")
        path_str = args.get("path", ".")

        full_path = self._resolve_path(path_str)

        if not full_path.exists():
            raise FileNotFoundError(f"Search root not found: {path_str}")

        # Search files
        matches = []
        for item in full_path.glob(pattern):
            if item.is_file():
                rel_path = item.relative_to(self.root_path)
                matches.append({
                    "path": str(rel_path),
                    "name": item.name,
                    "size": item.stat().st_size
                })

        return {
            "pattern": pattern,
            "search_root": path_str,
            "count": len(matches),
            "matches": matches
        }

    async def _file_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get file metadata"""
        path_str = args.get("path")

        full_path = self._resolve_path(path_str)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path_str}")

        stat = full_path.stat()

        return {
            "path": path_str,
            "name": full_path.name,
            "type": "file" if full_path.is_file() else "directory",
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_symlink": full_path.is_symlink()
        }

    async def _create_directory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create directory"""
        path_str = args.get("path")
        parents = args.get("parents", True)

        full_path = self._resolve_path(path_str)

        if full_path.exists():
            raise ValueError(f"Path already exists: {path_str}")

        # Create directory
        full_path.mkdir(parents=parents, exist_ok=False)

        return {
            "path": path_str,
            "created": True
        }

    async def _delete_file(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete file"""
        path_str = args.get("path")

        full_path = self._resolve_path(path_str)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path_str}")

        if full_path.is_dir():
            raise ValueError(f"Cannot delete directory (use rmdir): {path_str}")

        # Delete file
        full_path.unlink()

        return {
            "path": path_str,
            "deleted": True
        }


if __name__ == "__main__":
    # Run server in stdio mode
    import sys

    # Get root path from command line args
    root = sys.argv[1] if len(sys.argv) > 1 else "."

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("mcp_filesystem.log")]
    )

    server = FilesystemMCPServer(root_path=root)
    server.run()
