# MCP Servers Guide for ZEJZL.NET

## Overview

ZEJZL.NET includes 4 production-ready MCP (Model Context Protocol) servers providing 24 tools for agent operations:

1. **Filesystem Server** (7 tools) - File system operations
2. **Database Server** (6 tools) - SQLite database access
3. **Web Search Server** (3 tools) - DuckDuckGo web search
4. **GitHub Server** (8 tools) - GitHub API integration

## Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Client (Agent)                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ JSON-RPC 2.0 over stdio
┌─────────────────▼───────────────────────────────────────────┐
│                    MCP Server (Tool Provider)               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   BaseMCPServer (Abstract Base Class)               │  │
│  │   - Protocol handling (JSON-RPC 2.0)                │  │
│  │   - Tool registration                               │  │
│  │   - Request routing                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Specific Server Implementation                    │  │
│  │   - Tool handlers                                   │  │
│  │   - Business logic                                  │  │
│  │   - External API integration                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 1. Filesystem Server

### Description
Provides secure file system operations within a configured root directory.

### Tools

#### `read_file`
Read contents of a file.

**Parameters:**
- `path` (string, required): Path to file relative to root
- `encoding` (string, optional): File encoding (default: utf-8)

**Returns:**
```json
{
  "path": "readme.md",
  "content": "file contents here...",
  "size": 1234,
  "encoding": "utf-8"
}
```

**Example:**
```python
result = await agent.mcp_call_tool("read_file", {"path": "readme.md"})
content = result["content"]
```

#### `write_file`
Write contents to a file.

**Parameters:**
- `path` (string, required): Path to file
- `content` (string, required): Content to write
- `encoding` (string, optional): File encoding (default: utf-8)

**Returns:**
```json
{
  "path": "output.txt",
  "bytes_written": 500,
  "success": true
}
```

#### `list_files`
List files in a directory.

**Parameters:**
- `path` (string, optional): Directory path (default: ".")
- `pattern` (string, optional): Glob pattern (default: "*")
- `recursive` (boolean, optional): Search recursively (default: false)

**Returns:**
```json
{
  "directory": "src",
  "pattern": "*.py",
  "recursive": false,
  "count": 5,
  "files": [
    {
      "path": "src/main.py",
      "name": "main.py",
      "type": "file",
      "size": 2048
    }
  ]
}
```

#### `search_files`
Search for files by name pattern.

**Parameters:**
- `pattern` (string, required): Glob pattern (e.g., "**/*.py")
- `path` (string, optional): Search root (default: ".")

**Returns:**
```json
{
  "pattern": "**/*.md",
  "search_root": ".",
  "count": 3,
  "matches": [
    {"path": "readme.md", "name": "readme.md", "size": 1500}
  ]
}
```

#### `file_info`
Get file metadata.

**Parameters:**
- `path` (string, required): Path to file

**Returns:**
```json
{
  "path": "data.json",
  "name": "data.json",
  "type": "file",
  "size": 5120,
  "modified": 1704067200.0,
  "created": 1704060000.0,
  "is_symlink": false
}
```

#### `create_directory`
Create a directory.

**Parameters:**
- `path` (string, required): Directory path
- `parents` (boolean, optional): Create parent directories (default: true)

#### `delete_file`
Delete a file.

**Parameters:**
- `path` (string, required): Path to file

### Starting the Server

```bash
# Run with default root (current directory)
python src/mcp_servers/filesystem.py

# Run with custom root
python src/mcp_servers/filesystem.py /path/to/root
```

### Security Features
- **Path traversal prevention**: All paths validated against root
- **Root restriction**: Cannot access files outside root directory
- **Path resolution**: Symbolic links resolved and validated

---

## 2. Database Server

### Description
Provides SQLite database operations with query and schema introspection capabilities.

### Tools

#### `query`
Execute SQL SELECT query.

**Parameters:**
- `sql` (string, required): SQL SELECT query
- `params` (array, optional): Query parameters

**Returns:**
```json
{
  "sql": "SELECT * FROM users WHERE age > ?",
  "row_count": 10,
  "rows": [
    {"id": 1, "name": "Alice", "age": 30},
    {"id": 2, "name": "Bob", "age": 25}
  ]
}
```

**Example:**
```python
result = await agent.mcp_call_tool("query", {
    "sql": "SELECT * FROM users WHERE age > ?",
    "params": [25]
})
users = result["rows"]
```

#### `execute`
Execute SQL statement (INSERT, UPDATE, DELETE, CREATE).

**Parameters:**
- `sql` (string, required): SQL statement
- `params` (array, optional): Statement parameters

**Returns:**
```json
{
  "sql": "INSERT INTO users (name, age) VALUES (?, ?)",
  "rows_affected": 1,
  "last_row_id": 5,
  "success": true
}
```

#### `list_tables`
List all tables in database.

**Returns:**
```json
{
  "count": 3,
  "tables": ["users", "posts", "comments"]
}
```

#### `describe_table`
Get table schema and column information.

**Parameters:**
- `table` (string, required): Table name

**Returns:**
```json
{
  "table": "users",
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "not_null": true,
      "default_value": null,
      "primary_key": true
    },
    {
      "name": "name",
      "type": "TEXT",
      "not_null": true,
      "default_value": null,
      "primary_key": false
    }
  ],
  "row_count": 100
}
```

#### `count_rows`
Count rows in a table.

**Parameters:**
- `table` (string, required): Table name
- `where` (string, optional): WHERE clause (without 'WHERE' keyword)

**Returns:**
```json
{
  "table": "users",
  "where": "age > 25",
  "count": 45
}
```

#### `get_schema`
Get full database schema.

**Returns:**
```json
{
  "database": "data/zejzl.db",
  "table_count": 3,
  "schema": {
    "users": {
      "columns": [...],
      "row_count": 100
    }
  }
}
```

### Starting the Server

```bash
# Run with default database
python src/mcp_servers/database.py

# Run with custom database
python src/mcp_servers/database.py /path/to/database.db
```

### Security Features
- **SQL injection prevention**: Parameterized queries only
- **Read/write separation**: `query()` for SELECT, `execute()` for modifications
- **Transaction management**: Automatic commit/rollback

---

## 3. Web Search Server

### Description
Provides web search capabilities using DuckDuckGo (no API key required).

### Tools

#### `search`
Search the web using DuckDuckGo.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results (default: 10, max: 50)
- `region` (string, optional): Region code (default: "wt-wt")

**Returns:**
```json
{
  "query": "artificial intelligence",
  "count": 10,
  "results": [
    {
      "title": "Artificial Intelligence - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
      "snippet": "Artificial intelligence is intelligence demonstrated by machines..."
    }
  ],
  "region": "wt-wt"
}
```

**Example:**
```python
result = await agent.mcp_call_tool("search", {
    "query": "AI trends 2026",
    "max_results": 5
})

for item in result["results"]:
    print(f"{item['title']}: {item['url']}")
```

#### `search_news`
Search news articles.

**Parameters:**
- `query` (string, required): News search query
- `max_results` (integer, optional): Maximum results (default: 10)

**Returns:**
```json
{
  "query": "AI breakthroughs",
  "count": 10,
  "results": [...],
  "type": "news"
}
```

#### `instant_answer`
Get instant answer or summary for a query.

**Parameters:**
- `query` (string, required): Query for instant answer

**Returns:**
```json
{
  "query": "what is AI",
  "answer": "Artificial Intelligence is...",
  "answer_type": "definition",
  "heading": "Artificial Intelligence",
  "abstract": "Full abstract text...",
  "abstract_source": "Wikipedia",
  "abstract_url": "https://...",
  "definition": "...",
  "definition_source": "Oxford",
  "related_topics": [
    {
      "text": "Machine Learning",
      "url": "https://..."
    }
  ]
}
```

### Starting the Server

```bash
python src/mcp_servers/websearch.py
```

### Features
- **No API key required**: Uses DuckDuckGo free search
- **Anonymous searching**: No tracking or personalization
- **News search support**: Dedicated news search endpoint
- **Instant answers**: Quick facts and definitions

---

## 4. GitHub Server

### Description
Provides GitHub API operations for repository management, issues, and pull requests.

### Tools

#### `get_repo`
Get repository information.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name

**Returns:**
```json
{
  "name": "zejzl_net",
  "full_name": "anthropics/zejzl_net",
  "description": "Multi-agent AI framework",
  "url": "https://github.com/anthropics/zejzl_net",
  "stars": 150,
  "forks": 25,
  "open_issues": 5,
  "language": "Python",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2026-01-17T00:00:00Z",
  "default_branch": "main"
}
```

#### `list_issues`
List repository issues.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `state` (string, optional): Issue state (open/closed/all, default: open)
- `max_results` (integer, optional): Maximum results (default: 10)

**Returns:**
```json
{
  "owner": "anthropics",
  "repo": "zejzl_net",
  "count": 5,
  "issues": [
    {
      "number": 10,
      "title": "Add MCP support",
      "state": "open",
      "body": "We should add MCP...",
      "user": "developer",
      "labels": ["enhancement", "priority"],
      "created_at": "2026-01-15T00:00:00Z",
      "url": "https://github.com/.../issues/10"
    }
  ]
}
```

#### `create_issue`
Create a new issue (requires authentication).

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `title` (string, required): Issue title
- `body` (string, optional): Issue body
- `labels` (array, optional): Issue labels

**Returns:**
```json
{
  "number": 11,
  "title": "New feature request",
  "state": "open",
  "url": "https://github.com/.../issues/11",
  "created": true
}
```

**Note:** Requires `GITHUB_TOKEN` environment variable.

#### `get_issue`
Get specific issue details.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `issue_number` (integer, required): Issue number

#### `list_pulls`
List pull requests.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `state` (string, optional): PR state (default: open)
- `max_results` (integer, optional): Maximum results (default: 10)

#### `get_file`
Get file contents from repository.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `path` (string, required): File path in repository
- `ref` (string, optional): Git ref (branch/tag/commit, default: main)

**Returns:**
```json
{
  "path": "readme.md",
  "ref": "main",
  "content": "# ZEJZL.NET\n\n...",
  "size": 2048,
  "sha": "abc123...",
  "url": "https://github.com/.../blob/main/readme.md"
}
```

#### `search_repos`
Search GitHub repositories.

**Parameters:**
- `query` (string, required): Search query
- `sort` (string, optional): Sort by (stars/forks/updated, default: stars)
- `max_results` (integer, optional): Maximum results (default: 10)

**Returns:**
```json
{
  "query": "AI framework python",
  "total_count": 5000,
  "count": 10,
  "repositories": [
    {
      "name": "langchain",
      "full_name": "langchain-ai/langchain",
      "description": "Building applications with LLMs",
      "url": "https://github.com/langchain-ai/langchain",
      "stars": 50000,
      "forks": 5000,
      "language": "Python",
      "updated_at": "2026-01-17T00:00:00Z"
    }
  ]
}
```

#### `get_user`
Get user information.

**Parameters:**
- `username` (string, required): GitHub username

**Returns:**
```json
{
  "login": "anthropics",
  "name": "Anthropic",
  "bio": "AI safety company",
  "company": "Anthropic",
  "location": "San Francisco",
  "email": null,
  "public_repos": 20,
  "followers": 1000,
  "following": 50,
  "created_at": "2021-01-01T00:00:00Z",
  "url": "https://github.com/anthropics"
}
```

### Starting the Server

```bash
# Unauthenticated (rate limited)
python src/mcp_servers/github.py

# Authenticated (higher rate limits)
export GITHUB_TOKEN=your_token_here
python src/mcp_servers/github.py
```

### Authentication

Set `GITHUB_TOKEN` environment variable for authenticated access:
- Unauthenticated: 60 requests/hour
- Authenticated: 5000 requests/hour

Generate token at: https://github.com/settings/tokens

### Rate Limiting
- Automatic rate limit detection
- Error messages include rate limit info
- Recommended: Use authentication for production

---

## Creating Custom MCP Servers

### Basic Template

```python
from src.mcp_servers.base_server import BaseMCPServer
from src.mcp_types import MCPServerInfo, MCPServerCapabilities

class MyCustomServer(BaseMCPServer):
    def __init__(self):
        super().__init__(name="my-server", version="1.0.0")
        # Initialize resources

    def get_server_info(self) -> MCPServerInfo:
        capabilities = MCPServerCapabilities()
        return MCPServerInfo(
            name="my-server",
            version="1.0.0",
            capabilities=capabilities,
            protocolVersion="2024-11-05"
        )

    async def register_tools(self):
        # Define tool handler
        async def my_tool_handler(args):
            param = args.get("param")
            # Tool logic here
            return {"result": f"processed {param}"}

        # Register tool
        self.add_tool(
            name="my_tool",
            description="Does something useful",
            input_schema={
                "type": "object",
                "properties": {
                    "param": {
                        "type": "string",
                        "description": "Input parameter"
                    }
                },
                "required": ["param"]
            },
            handler=my_tool_handler
        )

if __name__ == "__main__":
    server = MyCustomServer()
    server.run()
```

### Tool Handler Guidelines

1. **Always async**: Tool handlers must be `async def`
2. **Accept dict**: Handler receives `args: Dict[str, Any]`
3. **Return serializable**: Return JSON-serializable data
4. **Raise on errors**: Raise `ValueError` for errors
5. **Validate inputs**: Check required parameters
6. **Handle timeouts**: Use asyncio timeout protection

### Best Practices

1. **Security**:
   - Validate all inputs
   - Sanitize user-provided data
   - Use parameterized queries for databases
   - Implement rate limiting

2. **Error Handling**:
   - Provide clear error messages
   - Use appropriate error codes
   - Log errors for debugging

3. **Performance**:
   - Use async operations
   - Implement caching where appropriate
   - Set reasonable timeouts

4. **Logging**:
   - Log important operations
   - Use appropriate log levels
   - Include context in log messages

---

## Configuration with Registry

### config/mcp_servers.json

```json
{
  "version": "1.0",
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["python", "src/mcp_servers/filesystem.py", "."],
      "enabled": true,
      "timeout": 30.0,
      "auto_reconnect": true,
      "health_check_interval": 60,
      "allowed_agents": null,
      "description": "Local filesystem access",
      "tags": ["filesystem", "local", "storage"]
    },
    {
      "name": "database",
      "transport": "stdio",
      "command": ["python", "src/mcp_servers/database.py", "data/zejzl.db"],
      "enabled": true,
      "allowed_agents": ["Memory", "Analyzer", "Learner"],
      "description": "SQLite database access",
      "tags": ["database", "sql", "analytics"]
    },
    {
      "name": "websearch",
      "transport": "stdio",
      "command": ["python", "src/mcp_servers/websearch.py"],
      "enabled": true,
      "allowed_agents": ["Observer", "Reasoner"],
      "description": "Web search via DuckDuckGo",
      "tags": ["search", "web", "information"]
    },
    {
      "name": "github",
      "transport": "stdio",
      "command": ["python", "src/mcp_servers/github.py"],
      "enabled": false,
      "description": "GitHub API integration",
      "tags": ["github", "vcs", "collaboration"]
    }
  ]
}
```

## Testing Servers

### Manual Testing with stdio

```bash
# Start server
python src/mcp_servers/filesystem.py

# Send initialize request (in another terminal)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python src/mcp_servers/filesystem.py
```

### Testing with Agent Integration

```python
from src.mcp_agent_integration import initialize_mcp
from src.mcp_agent_mixin import MCPAgentMixin

# Initialize MCP
interface = await initialize_mcp()
MCPAgentMixin.set_mcp_interface(interface)

# Create agent with MCP
class TestAgent(MCPAgentMixin):
    def __init__(self):
        self.name = "TestAgent"

agent = TestAgent()

# Call tools
files = await agent.mcp_call_tool("list_files", {"path": "src"})
result = await agent.mcp_call_tool("search", {"query": "AI"})
```

## See Also

- **MCP_INTEGRATION_GUIDE.md**: Agent integration patterns
- **test_mcp_servers.py**: Server test suite
- **Model Context Protocol**: https://modelcontextprotocol.io
