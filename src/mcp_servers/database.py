#!/usr/bin/env python3
"""
Database MCP Server for ZEJZL.NET

Provides database operations via MCP protocol.
Supports SQLite queries, schema introspection, and data operations.
"""

import os
import json
import logging
import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_types import MCPServerInfo, MCPServerCapabilities

logger = logging.getLogger("DatabaseMCPServer")


class DatabaseMCPServer(BaseMCPServer):
    """
    MCP server for database operations.

    Tools:
    - query: Execute SQL query (SELECT only)
    - execute: Execute SQL statement (INSERT, UPDATE, DELETE)
    - list_tables: List all tables
    - describe_table: Get table schema
    - count_rows: Count rows in table
    - get_schema: Get full database schema
    """

    def __init__(self, db_path: str = "data/zejzl.db"):
        super().__init__(name="database", version="1.0.0")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None
        logger.info(f"Database server: {self.db_path}")

    def get_server_info(self) -> MCPServerInfo:
        """Return server information"""
        capabilities = MCPServerCapabilities()

        return MCPServerInfo(
            name="database",
            version="1.0.0",
            capabilities=capabilities,
            protocolVersion="2024-11-05"
        )

    async def register_tools(self):
        """Register database tools"""

        # Tool: query
        self.add_tool(
            name="query",
            description="Execute SQL SELECT query",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT query"
                    },
                    "params": {
                        "type": "array",
                        "description": "Query parameters (optional)",
                        "items": {"type": ["string", "number", "null"]},
                        "default": []
                    }
                },
                "required": ["sql"]
            },
            handler=self._query
        )

        # Tool: execute
        self.add_tool(
            name="execute",
            description="Execute SQL statement (INSERT, UPDATE, DELETE, CREATE)",
            input_schema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL statement"
                    },
                    "params": {
                        "type": "array",
                        "description": "Statement parameters (optional)",
                        "items": {"type": ["string", "number", "null"]},
                        "default": []
                    }
                },
                "required": ["sql"]
            },
            handler=self._execute
        )

        # Tool: list_tables
        self.add_tool(
            name="list_tables",
            description="List all tables in database",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._list_tables
        )

        # Tool: describe_table
        self.add_tool(
            name="describe_table",
            description="Get table schema and column information",
            input_schema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    }
                },
                "required": ["table"]
            },
            handler=self._describe_table
        )

        # Tool: count_rows
        self.add_tool(
            name="count_rows",
            description="Count rows in a table",
            input_schema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Table name"
                    },
                    "where": {
                        "type": "string",
                        "description": "Optional WHERE clause (without 'WHERE' keyword)",
                        "default": None
                    }
                },
                "required": ["table"]
            },
            handler=self._count_rows
        )

        # Tool: get_schema
        self.add_tool(
            name="get_schema",
            description="Get full database schema",
            input_schema={
                "type": "object",
                "properties": {},
                "required": []
            },
            handler=self._get_schema
        )

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.connection is None:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
        return self.connection

    async def _query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SELECT query"""
        sql = args.get("sql", "").strip()
        params = args.get("params", [])

        # Security: ensure it's a SELECT query
        if not sql.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries allowed in query() method")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = []
            if rows:
                columns = [desc[0] for desc in cursor.description]
                for row in rows:
                    results.append(dict(zip(columns, row)))

            return {
                "sql": sql,
                "row_count": len(results),
                "rows": results
            }

        except sqlite3.Error as e:
            raise ValueError(f"SQL error: {e}")

    async def _execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL statement"""
        sql = args.get("sql", "").strip()
        params = args.get("params", [])

        # Security: disallow SELECT in execute (use query instead)
        if sql.upper().startswith("SELECT"):
            raise ValueError("Use query() for SELECT statements")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(sql, params)
            conn.commit()

            return {
                "sql": sql,
                "rows_affected": cursor.rowcount,
                "last_row_id": cursor.lastrowid,
                "success": True
            }

        except sqlite3.Error as e:
            conn.rollback()
            raise ValueError(f"SQL error: {e}")

    async def _list_tables(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )

        tables = [row[0] for row in cursor.fetchall()]

        return {
            "count": len(tables),
            "tables": tables
        }

    async def _describe_table(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get table schema"""
        table_name = args.get("table")

        if not table_name:
            raise ValueError("Table name required")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        if not columns:
            raise ValueError(f"Table not found: {table_name}")

        # Format column information
        column_info = []
        for col in columns:
            column_info.append({
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            })

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]

        return {
            "table": table_name,
            "columns": column_info,
            "row_count": row_count
        }

    async def _count_rows(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Count rows in table"""
        table_name = args.get("table")
        where_clause = args.get("where")

        if not table_name:
            raise ValueError("Table name required")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query
        if where_clause:
            sql = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
        else:
            sql = f"SELECT COUNT(*) FROM {table_name}"

        try:
            cursor.execute(sql)
            count = cursor.fetchone()[0]

            return {
                "table": table_name,
                "where": where_clause,
                "count": count
            }

        except sqlite3.Error as e:
            raise ValueError(f"SQL error: {e}")

    async def _get_schema(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get full database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row[0] for row in cursor.fetchall()]

        # Get schema for each table
        schema = {}
        for table_name in table_names:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            schema[table_name] = {
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default_value": col[4],
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]
            }

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            schema[table_name]["row_count"] = cursor.fetchone()[0]

        return {
            "database": str(self.db_path),
            "table_count": len(schema),
            "schema": schema
        }

    async def cleanup(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")


if __name__ == "__main__":
    # Run server in stdio mode
    import sys

    # Get database path from command line args
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/zejzl.db"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("mcp_database.log")]
    )

    server = DatabaseMCPServer(db_path=db_path)
    server.run()
