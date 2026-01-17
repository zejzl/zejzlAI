# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ZEJZL.NET is an async message bus AI framework implementing a 9-agent "Pantheon" orchestration system for multi-AI collaboration with self-healing capabilities. The framework supports multiple AI providers (ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, Zai), uses a hybrid persistence layer (Redis primary + SQLite fallback), and features a fairy magic-inspired self-healing system with circuit breakers and learning loop optimization.

## Core Architecture

### Message Bus System
The framework is built around `AsyncMessageBus` (ai_framework.py:680-900) which handles:
- Provider registration and lifecycle management
- Async message queuing and routing
- Conversation history caching
- Dual persistence (Redis + SQLite)
- Self-healing with magic system (Phase 4)
- Automatic failure recovery via circuit breakers

Messages flow: User Input → AsyncMessageBus → Magic System (Pre-boost) → AI Provider → Response → Magic System (Auto-heal if needed) → Persistence Layer

### The 9-Agent Pantheon System
Agents communicate through async method calls and shared memory state. The full execution flow is:

1. **Observer** → Gathers observations from task input
2. **Reasoner** → Creates execution plan with subtasks
3. **Actor** → Executes planned subtasks
4. **Validator** → Validates execution correctness
5. **Executor** → Performs validated tasks with error handling
6. **Memory** → Stores all events and state (acts as shared context)
7. **Analyzer** → Generates metrics from stored events
8. **Learner** → Identifies patterns, bottlenecks, and generates optimizations (Phase 4: Enhanced with learning loop)
9. **Improver** → Suggests magic-based healing and system optimizations (Phase 4: Enhanced with magic recommendations)

All agents are located in `src/agents/` and follow the pattern:
```python
async def {agent_action}(input_data) -> dict:
    # Process input
    # Return structured output with timestamp
```

### Persistence Layer Architecture
Located in ai_framework.py:95-405. The `HybridPersistence` class provides intelligent fallback:
- **Primary**: Redis (aioredis) - high-performance, distributed storage
- **Fallback**: SQLite (aiosqlite) - always initialized, handles Redis failures silently
- Dual-writes to both when possible
- Conversation messages limited to 100 per conversation in Redis (LTRIM)
- SQLite schema includes indexed conversation queries for fast retrieval

### AI Provider Integration
All providers implement the `AIProvider` abstract base class (ai_framework.py:406-678):
- Common interface: `initialize()`, `generate_response()`, `cleanup()`
- Each provider handles its own API format and authentication
- Uses aiohttp for async HTTP requests
- Response times and errors are tracked automatically

### Magic System (Phase 4)
Located in `src/magic.py` (447 lines). Provides self-healing capabilities:
- **Circuit Breakers**: 4 components (ai_provider, persistence, agent_coordinator, tool_call) with auto-recovery
- **Blue Spark Healing**: Energy-based healing with DPO-style preference learning
- **Acorn Vitality Boost**: Performance enhancement (10-50% boost)
- **Fairy Shield**: Protection mechanism for critical operations
- **Energy Management**: 0-100% energy level with automatic recharge

**Integration with MessageBus**:
```python
# Auto-initialized in AsyncMessageBus
self.magic = FairyMagic()

# Pre-task vitality boost
boost = await self.magic.acorn_vitality_boost(f"provider_{name}", config)

# Auto-healing on failure
healed = await self.magic.auto_heal("ai_provider", exception)
```

## Running the Framework

### Setup
1. Copy `.env.example` to `.env`
2. Add real API keys for the providers you want to use
3. Optional: Start Redis server (framework will use SQLite fallback if Redis unavailable)

### CLI Commands

**Direct chat with a provider:**
```bash
python ai_framework.py chat chatgpt "Your message here"
python ai_framework.py chat claude "Your message here" --conversation-id my-session
```

**Interactive mode (multi-turn conversation):**
```bash
python ai_framework.py interactive chatgpt
python ai_framework.py interactive claude
```

**System management:**
```bash
python ai_framework.py status          # Show framework status
python ai_framework.py list            # List registered providers
python ai_framework.py set-api-key openai sk-REAL-KEY
python ai_framework.py set-default-provider claude
```

### Running Pantheon Modes

**Interactive menu (all modes):**
```bash
python main.py
```
Then select from:
- Mode 1: Single Agent (Observer → Reasoner → Actor)
- Mode 4: Pantheon Mode (Full 9-agent orchestration)

**Direct pantheon test:**
```bash
python 9agent_pantheon_test.py
```

**Single agent with validation:**
```bash
python single_session_test_loop.py
```

**Simple interactive session:**
```bash
python interactive_session_example.py
```

**Phase 4 tools:**
```bash
python token_haze.py                  # Interactive onboarding
python token_haze.py --interactive    # Interactive demo mode
python test_magic_integration.py      # Test magic system
./start.sh                            # Quick start (bash)
./orchestrate.sh menu                 # Master orchestration
./orchestrate.sh infinite             # Infinite Panda Adventure!
```

## Development Patterns

### Adding a New Agent
1. Create agent file in `src/agents/{agent_name}.py`
2. Implement async method with typed input/output
3. Return dict with timestamp and metadata
4. Add import to `src/agents/__init__.py`
5. Integrate into pantheon flow in `9agent_pantheon_test.py`

### Adding a New AI Provider
1. Create provider class inheriting from `AIProvider` in ai_framework.py
2. Implement required methods:
   - `__init__(self, api_key: str, model: str = "default-model")`
   - `async def initialize(self)`
   - `async def generate_response(self, message: Message, history: List[Message]) -> str`
   - `async def cleanup(self)`
3. Add provider to `DEFAULT_CONFIG` in ai_framework.py
4. Add API key to `.env.example`
5. Register provider in `AsyncMessageBus.start()` method

### Memory and State Management
- Use `MemoryAgent` for inter-agent state sharing
- Store events as dicts with `type` and `data` fields
- Call `await memory.store(event)` after each agent step
- Retrieve with `await memory.recall()` or `await memory.recall(event_type="plan")`

### Error Handling
- Redis connection failures are handled silently with SQLite fallback
- API errors are logged with full stack traces to `ai_framework.log`
- Each provider has try/except around HTTP requests
- Conversation history is preserved even if provider calls fail

## Project Structure

```
zejzl_net/
├── ai_framework.py              # Core: MessageBus, Persistence, Providers + Magic (950 lines)
├── main.py                      # Interactive CLI menu entry point
├── 9agent_pantheon_test.py      # Full 9-agent orchestration demo
├── single_session_test_loop.py  # Single agent + validation test
├── interactive_session_example.py # Simple single agent example
├── token_haze.py                # Interactive onboarding (Phase 4)
├── test_magic_integration.py    # Magic system tests (Phase 4)
├── orchestrate.sh               # Master orchestration (Phase 4)
├── start.sh                     # Quick start script (Phase 4)
├── pyproject.toml               # Build config (setuptools)
├── .env                         # API keys (git-ignored, copy from .env.example)
├── .env.example                 # Template with all required env vars
└── src/
    ├── __init__.py              # Package init
    ├── magic.py                 # Self-healing magic system (Phase 4)
    └── agents/
        ├── __init__.py          # Agent subpackage init
        ├── observer.py          # Observation & perception
        ├── reasoner.py          # Planning & task decomposition
        ├── actor.py             # Action execution
        ├── validator.py         # Safety & correctness checks
        ├── memory.py            # State storage & recall
        ├── executor.py          # Reliable task execution
        ├── analyzer.py          # Telemetry & metrics
        ├── learner.py           # Pattern learning + optimization (Phase 4: Enhanced)
        └── improver.py          # Self-optimization + magic (Phase 4: Enhanced)
```

## Important Implementation Details

### Import Paths
The project uses absolute imports from project root:
```python
from src.agents.observer import ObserverAgent
```
NOT relative imports. The `sys.path` is adjusted in ai_framework.py:36-38.

### Async Patterns
All core operations are async/await:
- Agent methods are `async def`
- Provider API calls use aiohttp
- Persistence layer uses aioredis and aiosqlite
- Always use `await` when calling agent or provider methods

### Configuration Priority
1. Runtime API keys (set via CLI `set-api-key`)
2. Environment variables from `.env`
3. TOML config stored in persistence layer
4. DEFAULT_CONFIG hardcoded in ai_framework.py

### Logging
- All framework logs go to `ai_framework.log` and stdout
- Level set via `LOG_LEVEL` env var (default: INFO)
- Each agent and provider logs at INFO level
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Message Format
Every message processed by the bus has:
- `id`: Unique identifier (hash-based)
- `content`: User input text
- `sender`: Always "user"
- `provider`: Target AI provider name
- `conversation_id`: Thread identifier (default: "default")
- `response`: AI response text (filled after processing)
- `response_time`: Latency in seconds
- `error`: Error message if API call failed

## Testing the System

The current implementation uses stub agents (placeholder implementations). To test:

1. **Test provider integration**: Use `python ai_framework.py chat chatgpt "test"` to verify API connectivity
2. **Test full pantheon flow**: Run `python 9agent_pantheon_test.py` - all agents should execute and return stub data
3. **Test persistence**: Check that messages persist by querying conversation history in subsequent sessions
4. **Test fallback**: Stop Redis and verify SQLite fallback engages automatically

## Phase 4 Features (Self-Healing)

**Completed Enhancements:**
- ✅ Rate limiting on provider API calls (Phase 3)
- ✅ Conversation pruning (Phase 3: 100 message limit)
- ✅ Automatic retries with exponential backoff (Phase 3)
- ✅ Circuit breaker pattern for failure recovery (Phase 4)
- ✅ Auto-healing with preference learning (Phase 4)
- ✅ Performance vitality boosts (10-50% improvement) (Phase 4)
- ✅ Learning loop optimization with bottleneck detection (Phase 4)

**Known Limitations (Current State):**
- Agent implementations are stubs (return mock data, not real AI reasoning)
- No streaming response support
- Memory agent uses in-process storage (not persistent across runs)
- Magic system state not persistent (lost on restart)
- Learning patterns not saved to database
