# AGENTS.md - Coding Guidelines for ZEJZL.NET

This document provides essential information for agentic coding assistants working in the ZEJZL.NET repository. It includes build/test commands, code style guidelines, and development practices.

IMPORTANT NOTICE: Emojis are forbidden in this repo!

## Project Overview

ZEJZL.NET is an async message bus AI framework implementing a 9-agent "Pantheon" orchestration system for multi-AI collaboration. The framework supports multiple AI providers (ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, Zai) and uses a hybrid persistence layer (Redis primary + SQLite fallback).

**Status**: Phase 6 Complete - Advanced AI Capabilities implemented. All ZEJZL.NET development phases completed: Multi-modal AI, advanced reasoning, natural language understanding, and AI model orchestration now active.

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

## Learning Loop Optimization System

ZEJZL.NET features a sophisticated continuous learning and self-healing system that adapts and improves system performance over time.

### Components

- **LearningLoop**: Orchestrates continuous learning cycles with 6-phase optimization
- **LearnerAgent**: Advanced pattern recognition and bottleneck analysis
- **AgentProfiler**: Comprehensive performance monitoring and metrics collection
- **ImprovementApplicator**: Automated application of optimization recommendations
- **ConsensusManager**: Conflict resolution and decision consensus building

### Learning Cycle Phases

1. **Observation**: Collect system performance metrics and environmental data
2. **Analysis**: Analyze patterns, identify bottlenecks, and detect anomalies
3. **Optimization**: Generate improvement recommendations from multiple data sources
4. **Implementation**: Apply selected optimizations with rollback capabilities
5. **Evaluation**: Measure impact and effectiveness of applied changes
6. **Adaptation**: Update system behavior based on learning results

### Self-Healing Integration

The learning loop integrates with the FairyMagic system for automatic self-healing:

- **Blue Spark Healing**: Applied to failing components detected by learning analysis
- **Acorn Vitality Boost**: Performance enhancement for underperforming agents
- **Fairy Shield**: Protection during high-risk operations
- **Circuit Breaker Reset**: Recovery from transient failures
- **Holly Blessing Rituals**: Success enhancement for critical tasks

### Continuous Monitoring

Real-time monitoring runs parallel to learning cycles:
- Anomaly detection compared to performance baselines
- Proactive adaptation based on performance patterns
- Emergency healing for critical system issues
- Load balancing and resource optimization

### Usage

```python
from src.learning_loop import LearningLoop
from src.agents.profiling import AgentProfiler
from src.improvement_applicator import ImprovementApplicator

# Initialize components
profiler = AgentProfiler()
learning_loop = LearningLoop()
improvement_applicator = ImprovementApplicator(profiler)

# Start continuous learning and monitoring
await learning_loop.start_continuous_learning()

# Manual learning cycle
result = await learning_loop.execute_learning_cycle()

# Get learning insights
insights = await learning_loop.get_recent_insights()

# Check applied improvements
improvements = await improvement_applicator.get_applied_improvements()
```

## Advanced Workflow Patterns

ZEJZL.NET includes an advanced workflow orchestration system supporting:

### Features
- **Parallel Execution**: Multiple agents running simultaneously with `ParallelGroupStep`
- **Conditional Branching**: Decision-based workflow paths with `ConditionalBranchStep`
- **Loop Control**: Iterative execution with break conditions using `LoopControlStep`
- **Dependency Management**: Step execution ordering and prerequisite checking
- **Agent Integration**: Seamless integration with the Pantheon 9-agent system

### Components
- **WorkflowDefinition**: Complete workflow specification with steps and context
- **WorkflowExecutor**: Execution engine for complex workflow patterns
- **WorkflowStep Types**: Agent execution, conditional branches, parallel groups, loop controls

### Usage
```python
from src.workflows import execute_advanced_workflow

# Execute predefined workflow patterns
result = await execute_advanced_workflow("parallel", "analyze sales data")
result = await execute_advanced_workflow("conditional", "complex task")
result = await execute_advanced_workflow("loop", "iterative improvement")
```

### Predefined Workflows
- **parallel**: Parallel observation and analysis with sequential reasoning
- **conditional**: Branching workflow based on task complexity
- **loop**: Iterative improvement with validation loops

## Enterprise Security & Encryption

ZEJZL.NET includes enterprise-grade security and encryption features:

### Components
- **KeyManager**: Secure key generation, storage, and rotation system
- **EncryptionEngine**: AES-256-GCM encryption/decryption for data at rest
- **EnterpriseSecurity**: Main security coordinator with compliance features
- **SecureMessageBus**: Encrypted wrapper for inter-agent communications
- **SecurePersistence**: Encrypted persistence layer with key isolation

### Security Features
- **AES-256-GCM Encryption**: Industry-standard encryption for all sensitive data
- **Automatic Key Rotation**: Regular key updates with secure key lifecycle management
- **End-to-End Encryption**: All communications encrypted from source to destination
- **Secure Key Storage**: Encrypted key store with system fingerprint protection
- **Compliance Ready**: Enterprise security standards and GDPR compliance

### Usage
```python
from src.security import EnterpriseSecurity

# Initialize enterprise security
security = EnterpriseSecurity(enable_encryption=True)
await security.initialize_security()

# Encrypt sensitive data
encrypted = security.encryption_engine.encrypt_json({"secret": "data"})
decrypted = security.encryption_engine.decrypt_json(encrypted)

# Check security status
status = security.get_security_status()
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

  Modified:
  - readme.md - Updated with Phase 9 information

  Phase 9 MCP Integration Summary

  Completed Tasks (4 of 7):
  - Task 1: MCP Protocol Client Foundation
  - Task 2: Server Registry & Discovery
  - Task 3: Agent Integration Layer
  - Task 4: Built-in MCP Servers

  What Was Built:
  - 24 Production-Ready Tools across 4 MCP servers
  - Full JSON-RPC 2.0 protocol implementation
  - Security Features: Path traversal prevention, SQL injection protection, token authentication
  - Integration: Seamless agent mixin, global interface, context management
  - Documentation: 2 comprehensive guides with examples

  Remaining Tasks:
  - Task 5: Security & Authorization layer
  - Task 6: Integration testing with real servers
  - Task 7: Web dashboard MCP integration

  Repository Status

  - Branch: main
  - Remote: https://github.com/zejzl/zejzlAI.git
  - Status: Clean working tree, all changes pushed

  All Phase 9 code is now live on GitHub and ready for use! 🎉


This document should be updated as the codebase evolves. Last updated: 2026-01-17</content>
<parameter name="filePath">C:\Users\Administrator\Desktop\ZejzlAI\zejzl_net\AGENTS.md

