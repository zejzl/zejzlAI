# MCP Integration Guide for ZEJZL.NET Agents

## Overview

The MCP (Model Context Protocol) integration provides ZEJZL.NET agents with external tool capabilities including:
- Web search and API access
- Filesystem operations
- Database queries
- GitHub integration
- Cloud service access
- And more...

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ZEJZL.NET Pantheon                       │
│  (Observer, Reasoner, Actor, Validator, Executor, etc.)    │
└─────────────────┬───────────────────────────────────────────┘
                  │ Uses MCP Interface
┌─────────────────▼───────────────────────────────────────────┐
│           MCPAgentInterface (src/mcp_agent_integration.py)  │
│  - call_tool()  - read_resource()  - discover_tools()      │
│  - Context Management  - Caching  - Usage Tracking         │
└─────────────────┬───────────────────────────────────────────┘
                  │ Manages
┌─────────────────▼───────────────────────────────────────────┐
│           MCPServerRegistry (src/mcp_registry.py)           │
│  - Multi-server management  - Health monitoring            │
│  - Auto-reconnection  - Access control                     │
└─────────────────┬───────────────────────────────────────────┘
                  │ Connects to
┌─────────────────▼───────────────────────────────────────────┐
│              MCP Servers (External Tools)                   │
│  filesystem │ github │ web-search │ database │ kubernetes  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Initialize MCP System

```python
from src.mcp_agent_integration import initialize_mcp
from src.mcp_agent_mixin import MCPAgentMixin

# Initialize MCP with server config
mcp_interface = await initialize_mcp(
    config_path=Path("config/mcp_servers.json"),
    enable_caching=True
)

# Set global interface for all agents
MCPAgentMixin.set_mcp_interface(mcp_interface)
```

### 2. Add MCP to Existing Agents

**Option A: Using Mixin (Recommended)**

```python
from src.mcp_agent_mixin import MCPAgentMixin

class ObserverAgent(MCPAgentMixin):
    def __init__(self):
        self.name = "Observer"
        # ... rest of init

    async def observe(self, task: str):
        # Use MCP tools
        search_results = await self.mcp_call_tool(
            "search",
            arguments={"query": task}
        )

        # Read MCP resources
        related_docs = await self.mcp_read_resource(
            "file:///docs/related.md"
        )

        # Original observation logic
        observation = {
            "task": task,
            "web_context": search_results,
            "related_docs": related_docs
        }
        return observation
```

**Option B: Using Global Functions**

```python
from src.mcp_agent_integration import agent_call_tool, agent_read_resource

async def my_agent_function(agent_name: str, task: str):
    # Call tools using global functions
    result = await agent_call_tool(
        agent_name=agent_name,
        tool_name="search",
        arguments={"query": task}
    )
    return result
```

### 3. Using MCP-Enhanced Agents

```python
from src.agents.observer_mcp import ObserverMCPAgent

# Create MCP-enhanced observer
observer = ObserverMCPAgent()

# Observe with MCP enhancements
observation = await observer.observe("Build a web scraper", use_mcp=True)

# Check MCP status
status = observer.get_mcp_status()
print(f"MCP enabled: {status['enabled']}")
print(f"Available enhancements: {status['enhancements']}")
```

## Agent Integration Patterns

### Pattern 1: Tool-Enhanced Observation

```python
class EnhancedObserver(MCPAgentMixin):
    async def observe(self, task: str):
        # Discover available tools
        tools = self.mcp_discover_tools(tags=["search", "web"])

        # Use tools for context gathering
        if tools:
            context = await self.mcp_call_tool(
                "search",
                arguments={"query": task, "limit": 5}
            )
        else:
            context = "No external tools available"

        return {"task": task, "context": context}
```

### Pattern 2: Resource-Based Learning

```python
class LearnerAgent(MCPAgentMixin):
    async def learn_from_history(self):
        # Discover historical data resources
        resources = self.mcp_discover_resources(
            mime_type="application/json"
        )

        patterns = []
        for resource in resources:
            data = await self.mcp_read_resource(
                resource["uri"],
                use_cache=True
            )
            patterns.extend(self._analyze_data(data))

        return patterns
```

### Pattern 3: Batch Tool Execution

```python
class ActorAgent(MCPAgentMixin):
    async def execute_plan(self, subtasks: list):
        # Prepare batch tool calls
        tool_calls = [
            {"tool_name": "github_create_issue", "arguments": {"title": t}}
            for t in subtasks
        ]

        # Execute in parallel
        results = await self.mcp_batch_call_tools(
            tool_calls=tool_calls,
            parallel=True
        )

        return results
```

### Pattern 4: Conditional Tool Usage

```python
from src.mcp_agent_mixin import mcp_tool_required

class ValidatorAgent(MCPAgentMixin):
    @mcp_tool_required("test_runner")
    async def validate_code(self, code: str):
        # This method only runs if test_runner tool is available
        result = await self.mcp_call_tool(
            "test_runner",
            arguments={"code": code}
        )
        return result
```

## Configuration

### Server Configuration (config/mcp_servers.json)

```json
{
  "version": "1.0",
  "servers": [
    {
      "name": "filesystem",
      "transport": "stdio",
      "command": ["python", "-m", "mcp.server.filesystem", "--root", "."],
      "enabled": true,
      "timeout": 30.0,
      "auto_reconnect": true,
      "health_check_interval": 60,
      "allowed_agents": null,
      "description": "Local filesystem access",
      "tags": ["filesystem", "local", "storage"]
    },
    {
      "name": "web-search",
      "transport": "stdio",
      "command": ["python", "-m", "mcp.server.websearch"],
      "enabled": true,
      "allowed_agents": ["Observer", "Reasoner", "Actor"],
      "description": "Web search capabilities",
      "tags": ["search", "web", "internet"]
    }
  ]
}
```

### Agent Access Control

Restrict which agents can access specific MCP servers:

```json
{
  "name": "database",
  "allowed_agents": ["Memory", "Analyzer", "Learner"],
  "description": "Only memory/analytics agents can access database"
}
```

## Usage Tracking and Analytics

### Get Agent MCP Statistics

```python
# Get stats for specific agent
stats = observer.mcp_get_stats(session_id="default")

print(f"Tools called: {stats['tools_called']}")
print(f"Resources read: {stats['resources_read']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg latency: {stats['avg_tool_latency']:.3f}s")
```

### Get All Agent Statistics

```python
from src.mcp_agent_integration import get_mcp_interface

interface = get_mcp_interface()
all_stats = interface.get_all_agent_stats()

for agent_key, stats in all_stats.items():
    print(f"{agent_key}: {stats['tools_called']} tools called")
```

## Integration with Pantheon Orchestration

### Full 9-Agent Integration Example

```python
import asyncio
from pathlib import Path
from src.mcp_agent_integration import initialize_mcp
from src.mcp_agent_mixin import MCPAgentMixin

# Import pantheon agents
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent
# ... etc

async def run_pantheon_with_mcp(task: str):
    # Initialize MCP
    mcp_interface = await initialize_mcp()
    MCPAgentMixin.set_mcp_interface(mcp_interface)

    # Create agents (with MCP mixin if modified)
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    # Pantheon execution flow
    observation = await observer.observe(task)

    # If observer has MCP, it can enhance observation
    if isinstance(observer, MCPAgentMixin):
        web_context = await observer.mcp_call_tool(
            "search",
            arguments={"query": task}
        )
        observation["web_context"] = web_context

    # Continue with reasoner, actor, etc.
    plan = await reasoner.reason(observation)
    result = await actor.act(plan)

    # Cleanup
    from src.mcp_agent_integration import shutdown_mcp
    await shutdown_mcp()

    return result

# Run
result = asyncio.run(run_pantheon_with_mcp("Build a web scraper"))
```

## Error Handling

```python
from src.mcp_client import MCPConnectionError, MCPTimeoutError

async def safe_tool_call(agent):
    try:
        result = await agent.mcp_call_tool(
            "search",
            arguments={"query": "AI"},
            timeout=10.0
        )
        return result

    except MCPConnectionError as e:
        print(f"Connection failed: {e}")
        # Fallback behavior
        return {"error": "MCP unavailable"}

    except MCPTimeoutError as e:
        print(f"Tool call timed out: {e}")
        return {"error": "Timeout"}

    except ValueError as e:
        print(f"Tool not found or access denied: {e}")
        return {"error": "Access denied"}
```

## Best Practices

### 1. Always Initialize MCP Before Agent Usage

```python
# At startup
mcp_interface = await initialize_mcp()
MCPAgentMixin.set_mcp_interface(mcp_interface)

# Use agents
agent = MyAgent()
result = await agent.mcp_call_tool(...)
```

### 2. Use Caching for Repeated Resource Access

```python
# First read: fetches from MCP server
data1 = await agent.mcp_read_resource("file:///data.json", use_cache=True)

# Second read: served from cache (faster)
data2 = await agent.mcp_read_resource("file:///data.json", use_cache=True)
```

### 3. Discover Tools Before Usage

```python
# Check available tools
tools = agent.mcp_discover_tools()
tool_names = [t["name"] for t in tools]

if "search" in tool_names:
    result = await agent.mcp_call_tool("search", {"query": "AI"})
else:
    # Fallback behavior
    result = default_search(query)
```

### 4. Use Batch Calls for Multiple Operations

```python
# Faster: parallel execution
tool_calls = [
    {"tool_name": "search", "arguments": {"query": "AI"}},
    {"tool_name": "search", "arguments": {"query": "ML"}},
    {"tool_name": "search", "arguments": {"query": "DL"}}
]

results = await agent.mcp_batch_call_tools(tool_calls, parallel=True)
```

### 5. Monitor Agent MCP Usage

```python
# Periodically check stats
stats = agent.mcp_get_stats()

if stats['success_rate'] < 0.8:
    print("Warning: Low MCP success rate")

if stats['avg_tool_latency'] > 5.0:
    print("Warning: High tool latency")
```

## Next Steps

1. **Enable MCP servers** in `config/mcp_servers.json`
2. **Add MCP mixin** to existing agents
3. **Test with real tools** (filesystem, web search, etc.)
4. **Implement custom MCP servers** for domain-specific tools
5. **Add security layer** for production use

## See Also

- `test_mcp_client.py` - MCP protocol tests
- `test_mcp_registry.py` - Server registry tests
- `test_mcp_agent_integration.py` - Agent integration tests
- `src/agents/observer_mcp.py` - Example MCP-enhanced agent
- Model Context Protocol specification: https://modelcontextprotocol.io
