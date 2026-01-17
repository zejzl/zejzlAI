# AGENTS.md - Coding Guidelines for ZEJZL.NET

This document provides essential information for agentic coding assistants working in the ZEJZL.NET repository. It includes build/test commands, code style guidelines, and development practices.

## Project Overview

ZEJZL.NET is an async message bus AI framework implementing a 9-agent "Pantheon" orchestration system for multi-AI collaboration. The framework supports multiple AI providers (ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, Zai) and uses a hybrid persistence layer (Redis primary + SQLite fallback).

## Build, Lint, and Test Commands

### Build Commands
- **Install dependencies**: `pip install -e .`
- **Build package**: `python -m build` (if build package installed)
- **Editable install**: `pip install -e .`

### Test Commands
The project uses manual integration tests rather than formal unit testing frameworks. Run tests using:

- **Full Pantheon test**: `python 9agent_pantheon_test.py`
- **Single agent test**: `python single_session_test_loop.py`
- **Interactive demo**: `python interactive_session_example.py`
- **Provider integration test**: `python ai_framework.py chat chatgpt "test message"`

### Lint and Format Commands
No automated linting/formatting tools are currently configured. Follow the style guidelines below manually.

For manual code quality checks, use:
- **Type checking**: `python -m mypy src/agents/learner.py`
- **Style checking**: `python -m pylint src/agents/learner.py`
- **PEP 8 compliance**: `python -m flake8 src/agents/learner.py`

### Running a Single Test
Since formal unit tests don't exist, "running a single test" means executing one of the integration test files:

```bash
# Test specific agent functionality
python -c "import asyncio; from src.agents.observer import ObserverAgent; obs = ObserverAgent(); asyncio.run(obs.observe('test task'))"
```

## Magic System (Self-Healing)

ZEJZL.NET includes an advanced fairy magic system for self-healing and agent enhancement:

### Components
- **FairyMagic**: Core magic system with energy management and healing
- **CircuitBreaker**: Automatic failure recovery for system components
- **Blue Spark Healing**: Energy-based healing with preference learning
- **Acorn Vitality Boost**: Performance enhancement for agents
- **Fairy Shield**: Protection mechanism for critical operations

### Integration
The magic system is automatically integrated into the AsyncMessageBus for:
- Pre-task vitality boosts for improved performance
- Automatic healing on provider failures
- Circuit breaker protection for cascading failure prevention
- Real-time energy management and ritual casting

### Usage
```python
from src.magic import FairyMagic

magic = FairyMagic()
boost = await magic.acorn_vitality_boost("agent_name", {"max_tokens": 1024})
healed = await magic.blue_spark_heal("component", "error_description")
```

## Code Style Guidelines

### Import Organization
Follow this exact import order with section headers:

```python
# --- 1. Future Imports (Must be first) ---
from __future__ import annotations

# --- 2. Standard Library Imports ---
import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any

# --- 3. Third-Party Library Imports ---
import aiohttp
import redis.asyncio as aioredis

# --- 4. Local Application Imports ---
from src.agents.observer import ObserverAgent
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `ObserverAgent`, `AIProvider`)
- **Methods/Functions**: snake_case (e.g., `observe()`, `generate_response()`)
- **Variables**: snake_case (e.g., `api_key`, `conversation_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_CONFIG`)
- **Files**: snake_case (e.g., `ai_framework.py`, `observer.py`)

### Type Hints
Use comprehensive type hints:
- `typing.Optional` for nullable types
- `typing.Union` for multiple possible types
- `typing.List`, `typing.Dict` for collections
- Generic types where appropriate

```python
async def generate_response(self, message: Message, history: List[Message]) -> str:
    pass

def process_data(self, data: Optional[Dict[str, Any]]) -> Union[str, None]:
    pass
```

### Async/Await Patterns
- All agent methods are `async def`
- Use `await` for all async operations
- Return structured dictionaries with timestamps
- Handle exceptions appropriately

```python
async def observe(self, task: str) -> Dict[str, Any]:
    try:
        result = {
            "task": task,
            "data": "observation_data",
            "timestamp": asyncio.get_event_loop().time(),
        }
        return result
    except Exception as e:
        logger.error(f"Observation failed: {e}")
        raise
```

### Error Handling
- Use try/except blocks for API calls and I/O operations
- Log errors with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Re-raise exceptions after logging unless handled
- Use specific exception types when possible

```python
try:
    response = await self.client.post(url, json=data)
    response.raise_for_status()
    return await response.json()
except aiohttp.ClientError as e:
    logger.error(f"API request failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Logging
- Use structured logging with consistent format
- Include agent/provider names in log messages
- Use appropriate log levels

```python
logger = logging.getLogger("ObserverAgent")

# In methods:
logger.debug(f"[{self.name}] Processing task: {task}")
logger.info(f"[{self.name}] Operation completed successfully")
logger.warning(f"[{self.name}] Non-critical issue: {issue}")
logger.error(f"[{self.name}] Critical error: {error}")
```

### Docstrings
Use Google-style docstrings:

```python
class ObserverAgent:
    """
    Observer Agent for Pantheon 9-Agent System.

    Responsible for gathering observations from environment, APIs, or files.
    """

    async def observe(self, task: str) -> Dict[str, Any]:
        """
        Gather observations for the given task.

        Args:
            task: The task description to observe

        Returns:
            Dictionary containing observation data with timestamp
        """
```

### Code Structure
- **Agent Classes**: Inherit from base classes, implement required async methods
- **Data Structures**: Use dataclasses for structured data
- **Configuration**: Use TOML format stored in persistence layer
- **Persistence**: Dual-write to Redis (primary) + SQLite (fallback)

### File Organization
- **Main framework**: `ai_framework.py` (core logic)
- **Agents**: `src/agents/{agent_name}.py`
- **Tests**: Integration tests as standalone Python files
- **Configuration**: `.env` for secrets, TOML for runtime config

## Development Workflow

### Adding New Features
1. Understand the async message bus architecture
2. Follow existing patterns in `ai_framework.py`
3. Implement agents in `src/agents/`
4. Update imports in `src/agents/__init__.py`
5. Test integration with existing pantheon flow

### Adding AI Providers
1. Create provider class inheriting from `AIProvider`
2. Implement required methods: `__init__`, `initialize()`, `generate_response()`, `cleanup()`
3. Add to `DEFAULT_CONFIG` in `ai_framework.py`
4. Update `.env.example` with new API key
5. Register in `AsyncMessageBus.start()`

### Memory and State Management
- Use `MemoryAgent` for inter-agent communication
- Store events as `{"type": str, "data": dict}` format
- Include timestamps in all data structures
- Use `await memory.store(event)` and `await memory.recall()`

### Security Practices
- Never commit API keys or secrets
- Use environment variables for configuration
- Validate input data before processing
- Handle sensitive data appropriately in logs

## Dependencies

Core dependencies (install via pip):
- `aiohttp` - Async HTTP client
- `aioredis` - Redis async client
- `aiosqlite` - SQLite async client
- `python-dotenv` - Environment variable loading
- `toml` - Configuration file parsing

## Environment Setup

1. Copy `.env.example` to `.env`
2. Add API keys for desired providers
3. Optional: Start Redis server (SQLite fallback available)
4. Run `pip install -e .`

## Common Patterns

### Agent Method Signature
```python
async def {action}(self, input_data) -> dict:
    """Process input and return structured output."""
    # Process input
    # Return dict with timestamp and metadata
```

### Provider Integration
```python
class CustomProvider(AIProvider):
    async def generate_response(self, message: Message, history: List[Message]) -> str:
        # API call logic here
        pass
```

### Configuration Management
- Runtime API keys override environment variables
- TOML config stored in persistence layer
- Environment variables take precedence over defaults

## CLI Usage

- **Chat**: `python ai_framework.py chat provider "message"`
- **Interactive**: `python ai_framework.py interactive provider`
- **Management**: `python ai_framework.py list|status|set-api-key|set-default`

This document should be updated as the codebase evolves. Last updated: 2026-01-16</content>
<parameter name="filePath">C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\AGENTS.md