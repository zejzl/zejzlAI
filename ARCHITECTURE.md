# ZEJZL.NET Architecture Documentation

## Overview

ZEJZL.NET implements a dual-layer architecture with two distinct message bus systems, each serving a specific purpose.

## Two Message Bus Systems

### 1. AI Provider Message Bus (`ai_framework.py`)

**Purpose**: Manages communication with external AI providers (ChatGPT, Claude, Gemini, etc.)

**Location**: `ai_framework.py:680-829`

**Key Features**:
- Provider registration and lifecycle management
- Conversation history management with caching
- Hybrid persistence layer (Redis primary + SQLite fallback)
- Request/response pattern for AI API calls
- Configuration management (API keys, default providers)
- Response time tracking and error handling
- **Self-healing with magic system (Phase 4)**
- **Circuit breakers for automatic failure recovery (Phase 4)**
- **Pre-task vitality boosts and auto-healing (Phase 4)**

**Use Case**: When you need to send a prompt to an AI provider and get a response
```python
bus = AsyncMessageBus()
await bus.start()
response = await bus.send_message("Hello, AI!", provider_name="chatgpt")
```

**CLI Interface**: `python ai_framework.py chat chatgpt "your message"`

---

### 2. Inter-Agent Message Bus (`messagebus.py`)

**Purpose**: Enables pub/sub communication between Pantheon agents

**Location**: `messagebus.py:46-154`

**Key Features**:
- Channel-based publish/subscribe pattern
- Redis-backed message persistence
- Async queue management for local subscribers
- Message history retrieval with caching
- 100-message limit per conversation with 30-day expiration

**Use Case**: When agents need to communicate with each other asynchronously
```python
bus = AsyncMessageBus()
await bus.initialize()
queue = await bus.subscribe("task_channel")
await bus.publish("task_channel", message)
received = await queue.get()
```

**Integration**: Used by `base.py` PantheonAgent class for inter-agent coordination

---

## Why Two Separate Systems?

### Different Communication Patterns

1. **AI Provider Bus** (Request/Response)
   - Synchronous: Send request → Wait → Get response
   - One-to-one communication
   - Stateful (conversation history)
   - Provider-specific logic

2. **Inter-Agent Bus** (Pub/Sub)
   - Asynchronous: Publish → Multiple subscribers receive
   - One-to-many or many-to-many communication
   - Stateless message passing
   - Generic, protocol-agnostic

### Separation of Concerns

- **AI Provider Bus**: External API integration, authentication, rate limiting, error handling
- **Inter-Agent Bus**: Internal message routing, event distribution, agent coordination

### Performance & Scalability

- AI Provider Bus: Optimized for conversation caching and API quota management
- Inter-Agent Bus: Optimized for low-latency message passing between agents

---

## The 9-Agent Pantheon System

The Pantheon system uses the **Inter-Agent Bus** for coordination:

```
User Input → Observer → Reasoner → Actor → Validator → Executor
                ↓          ↓         ↓         ↓          ↓
              Memory Agent (shared state)
                ↓          ↓         ↓
            Analyzer → Learner → Improver
```

Each agent can:
1. Subscribe to specific channels
2. Publish messages to channels
3. Access shared Memory state
4. Optionally call AI providers via the AI Provider Bus

---

## Integration Point: base.py PantheonAgent

The `base.py` file defines the `PantheonAgent` base class that:

1. **Uses Inter-Agent Bus** for agent-to-agent communication
   - `self.bus.subscribe(channel)` - Listen to other agents
   - `self.bus.publish(channel, message)` - Broadcast to other agents

2. **Calls AI Providers** via the integrated `call_ai()` method
   - Fully integrated with the AI Provider Bus in `ai_framework.py`
   - Supports fallback stub responses on failure

---

## Current Implementation Status

### ✓ Complete
- AI Provider Bus with 7 providers
- SQLite fallback persistence
- CLI interface (chat, interactive, list, status)
- Inter-Agent Bus (Redis pub/sub)
- Message persistence and history
- Pantheon 9-Agent System with unique personalities
- PantheonAgent AI provider integration
- Full Pantheon orchestration with real AI reasoning
- Error recovery and retry logic (exponential backoff)
- Rate limiting for AI providers (multi-tier token bucket)
- Streaming AI responses
- Multi-provider consensus mode
- Agent performance metrics and telemetry
- Self-healing with magic system and circuit breakers
- Enterprise security and encryption
- MCP Protocol integration with 24 tools
- Cost tracking and token usage analytics

### ⚠ In Progress
- MCP Security Layer (Authorization, rate limiting)
- Distributed agent deployment
- Community vault for shared patterns

---

## Data Flow Examples

### Example 1: User Chat with AI Provider

```
User → CLI → AI Provider Bus → ChatGPT API → Response → SQLite → User
```

### Example 2: Pantheon Task Execution

```
User Task → Observer (pub) → reasoner_channel
                ↓
            Reasoner (sub) → AI Provider Bus → Grok API
                ↓
            Reasoner (pub) → actor_channel
                ↓
            Actor (sub) → ... → Validation → Execution
```

### Example 3: Memory-Backed Learning

```
All Agents → Memory.store() → Analyzer → Learner → Improver
                ↓
          Shared State → Future Agent Decisions
```

---

## File Organization

```
zejzl_net/
├── ai_framework.py         # AI Provider Bus + CLI
├── messagebus.py           # Inter-Agent Bus
├── base.py                 # PantheonAgent base class
├── main.py                 # Interactive Pantheon UI
├── src/agents/             # 9 Agent implementations
│   ├── observer.py
│   ├── reasoner.py
│   ├── actor.py
│   ├── validator.py
│   ├── memory.py
│   ├── executor.py
│   ├── analyzer.py
│   ├── learner.py
│   └── improver.py
├── test_basic.py           # Unit tests
└── requirements.txt        # Dependencies
```

---

## Next Steps

1. **Enable Redis for Inter-Agent Bus**
   - Currently requires Redis for full pub/sub functionality
   - Add fallback for local-only operation

2. **Add Integration Tests**
   - Test full Pantheon flow with real AI providers
   - Test message bus under load
   - Test persistence failover scenarios

3. **Performance Optimization**
   - Add message batching
   - Implement connection pooling
   - Add circuit breakers for failing providers

---

## Design Philosophy

**Modularity**: Each system can be used independently
**Resilience**: Multiple fallback layers (Redis → SQLite, multiple providers)
**Flexibility**: Easy to add new providers or agents
**Observability**: Comprehensive logging at every layer

---

*Last Updated: 2026-01-17*
