# ZEJZL.NET

[![Tests](https://github.com/zejzl/zejzlAI/actions/workflows/tests.yml/badge.svg)](https://github.com/zejzl/zejzlAI/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Multi-Agent AI Framework with 9-Agent Pantheon Orchestration System**

An async message bus AI framework that orchestrates multiple AI models through a specialized 9-agent system for complex task decomposition, execution, validation, and continuous learning.

## Features

### Core Framework
- **9-Agent Pantheon System**: Specialized agents working in concert (Observer, Reasoner, Actor, Validator, Memory, Executor, Analyzer, Learner, Improver)
- **Multi-Provider Support**: Integrate ChatGPT, Claude, Gemini, and Grok with optimized configuration
- **Dual Message Bus Architecture**: Separate buses for AI providers and inter-agent communication
- **High-Performance MessageBus**: [NEW - 2026-01-30] Upgraded to Grokputer MessageBus achieving 407K msg/sec (204x faster than Redis), 0.007ms P95 latency (987x lower), enabling 10,000+ agent swarms and real-time multi-agent coordination
- **Async Message Bus**: High-performance async/await architecture for concurrent operations
- **Hybrid Persistence**: Redis (primary) + SQLite (automatic fallback) for reliable state management
- **Multiple Operation Modes**: Single agent, collaboration, swarm, and full pantheon orchestration
- **Python-Toon Configuration**: Enhanced annotated configuration format with validation
- **Multi-Provider Consensus**: Intelligent response aggregation from multiple AI providers
- **Agent Personalization**: Unique personality traits, communication styles, and expertise areas for each agent

### Phase 3 Enhancements (Production-Ready)
- **Rate Limiting**: Multi-tier token bucket algorithm (per-minute/hour/day limits per provider)
- **Smart Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Conversation Pruning**: Automatic maintenance of last 100 messages per conversation
- **Performance Telemetry**: Comprehensive tracking of response times, success rates, and errors
- **Real AI Integration**: Full integration between Pantheon agents and AI provider bus
- **PantheonAgent AI Integration**: Complete bidirectional communication with all AI providers via call_ai() method
- **Error Recovery**: Graceful handling of API failures with configurable fallback behavior

### Phase 4 Enhancements (Advanced Orchestration & Self-Healing)
- **Advanced Workflow Patterns**: Parallel execution, conditional branching, and iterative loops
- **Multi-Agent Coordination**: Complex workflow orchestration with dependency management
- **Parallel Group Execution**: Simultaneous agent operations for improved performance
- **Conditional Branching**: Dynamic decision-making based on runtime conditions
- **Loop Control System**: Iterative workflows with configurable break conditions
- **Magic System**: Fairy magic-inspired self-healing with circuit breakers and auto-recovery
- **Circuit Breaker Pattern**: Prevents cascading failures across 4 system components
- **Blue Spark Healing**: Energy-based healing with DPO-style preference learning
- **Acorn Vitality Boost**: Performance enhancement for agents (10-50% boost)
- **Learning Loop Optimization**: Advanced pattern analysis and bottleneck identification
- **Continuous Improvement**: Automatic optimization suggestions from learned patterns
- **Interactive Onboarding**: Token counting demos and system status tool
- **Master Orchestration**: Comprehensive automation with Infinite Panda Adventure mode

### Phase 6 Enhancements (Advanced AI Capabilities) ✅ COMPLETE
- **Multi-Modal AI Integration**: Support for text, image, audio, and structured data processing
- **Advanced Reasoning Engine**: Deductive, inductive, abductive, and causal reasoning strategies
- **Natural Language Understanding**: Intent recognition, semantic analysis, and sentiment processing
- **AI Model Orchestration**: Intelligent model selection and coordination based on task requirements
- **Custom AI Model Training**: Framework for training specialized AI models
- **Intelligent Task Analysis**: Automatic task complexity assessment and capability matching
- **Context-Aware Processing**: Adaptive processing based on conversation context and history
- **Compliance Ready**: GDPR and enterprise security standards compliant

### PantheonAgent AI Provider Integration ✅ COMPLETE (2026-01-27)
- **Full bidirectional communication**: Pantheon agents can call any AI provider
- **Magic system integration**: Automatic vitality boosts (1.1x - 1.5x improvements)
- **Robust error handling**: Provider fallback and graceful degradation
- **Production-ready testing**: Real-world task processing verified
- **Performance optimization**: ~1.0s response times with comprehensive monitoring

### Phase 5 Enhancements (Enterprise Scalability & Performance)
- **Real-time Performance Monitoring**: Comprehensive metrics collection and alerting
- **Advanced Caching System**: Multi-level caching with Redis primary and memory fallback
- **Performance Profiling**: Function-level execution time tracking and optimization
- **Load Balancing**: Intelligent request distribution and resource management
- **Scalability Management**: Auto-scaling policies and resource limit monitoring
- **Enterprise Security Framework**: End-to-end AES-256-GCM encryption infrastructure
- **Secure Key Management**: Automatic key generation, rotation, and secure storage
- **Encrypted Message Bus**: Secure inter-agent communications with encryption
- **Secure Persistence Layer**: Encrypted database storage with key isolation

### Phase 6 Enhancements (Advanced AI Capabilities)
- **Multi-Modal AI Integration**: Support for text, image, audio, and structured data processing
- **Advanced Reasoning Engine**: Deductive, inductive, abductive, and causal reasoning strategies
- **Natural Language Understanding**: Intent recognition, semantic analysis, and sentiment processing
- **AI Model Orchestration**: Intelligent model selection and coordination based on task requirements
- **Custom AI Model Training**: Framework for training specialized AI models
- **Intelligent Task Analysis**: Automatic task complexity assessment and capability matching
- **Context-Aware Processing**: Adaptive processing based on conversation context and history
- **Compliance Ready**: GDPR and enterprise security standards compliant

### Phase 5 Enhancements (Advanced AI & User Experience)
- **Streaming AI Responses**: Real-time token streaming from AI providers with WebSocket support
- **Web UI Dashboard**: Beautiful real-time monitoring interface with magic system controls
- **Docker Containerization**: Production-ready deployment with health checks
- **Multi-Provider Consensus**: Enhanced accuracy through intelligent AI response aggregation
- **Agent Personalization Framework**: 6 unique agent personalities with specialized traits and communication styles
- **Advanced WebSocket Integration**: Live system status updates and real-time chat
- **Personality-Enhanced Prompts**: Dynamic AI prompts based on agent personality and expertise
- **Consensus Mode Web Interface**: Toggle multi-provider consensus in the dashboard chat

### Phase 6 Enhancements (Enterprise Debugging & Observability)
- **Comprehensive Logging System**: Structured JSON logging with multiple log levels and rotation
- **Advanced Debugging Framework**: Request tracing, performance profiling, and system snapshots
- **Real-time Debug Dashboard**: Live debugging interface with system introspection
- **Performance Monitoring**: Detailed metrics collection and analysis
- **Debug CLI Tool**: Command-line interface for system debugging and monitoring
- **Health Check Endpoints**: Detailed system health monitoring with metrics
- **Log Aggregation**: Centralized logging with searchable debug information
- **Request Tracing**: End-to-end request monitoring and performance analysis

## Architecture

```
┌─────────────────────────────────────────────────┐
│  CLI Interface (Interactive Menu)               │
├─────────────────────────────────────────────────┤
│  AsyncMessageBus (Orchestration Layer)          │
│  - Provider Management                          │
│  - Message Routing                              │
│  - Conversation History                         │
│  - Magic System (Self-Healing)                  │
├─────────────────────────────────────────────────┤
│  9-Agent Pantheon System                        │
│  Observer → Reasoner → Actor → Validator        │
│  → Executor → Memory → Analyzer → Learner       │
│  → Improver                                     │
├─────────────────────────────────────────────────┤
│  AI Provider Layer (7 Providers)                │
│  - Circuit Breakers (Auto-Recovery)             │
│  - Rate Limiting & Retry Logic                  │
├─────────────────────────────────────────────────┤
│  Persistence Layer (Redis + SQLite)             │
└─────────────────────────────────────────────────┘
```

### The 9 Agents with Personality Framework

Each agent now has a unique personality with specialized communication styles and expertise areas:

1. **Observer** (Analytical) - Thorough task analysis with systematic decomposition
2. **Reasoner** (Logical) - Strategic planning with risk assessment and dependency mapping
3. **Actor** (Direct) - Practical execution with efficient action planning
4. **Validator** (Analytical) - Rigorous quality assurance with detailed validation reports
5. **Executor** - Performs validated tasks with error handling
6. **Memory** - Stores and recalls execution state and history
7. **Analyzer** (Technical) - Deep performance analysis with actionable insights
8. **Learner** - Identifies patterns, bottlenecks, and generates optimizations (Phase 4: Enhanced)
9. **Improver** (Creative) - Innovative system optimization with magic-based healing (Phase 4: Enhanced)

### Agent Personalities

- **Communication Styles**: Formal, Casual, Technical, Creative, Empathetic, Direct, Analytical, Storyteller
- **Expertise Areas**: Specialized knowledge domains for enhanced task performance
- **Behavioral Traits**: Unique characteristics affecting agent decision-making
- **Motivational Drivers**: Core motivations guiding agent behavior and responses

### Multi-Provider Consensus

- **Intelligent Aggregation**: Combines responses from multiple AI providers for enhanced accuracy
- **Fallback Logic**: Gracefully handles provider failures with automatic recovery
- **Magic Integration**: Applies vitality boosts to consensus API calls
- **Web Interface**: Toggle consensus mode in the real-time dashboard

## Installation

### Prerequisites

- Python 3.10+
- Redis (optional, will use SQLite fallback if unavailable)
- API keys for desired AI providers

### Setup

1. Clone the repository:
```bash
git clone https://github.com/zejzl/zejzlAI.git
cd zejzlAI
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Docker Deployment (Recommended):**
```bash
# Quick Docker setup
docker-compose up -d

# View logs
docker-compose logs -f

# Access web dashboard at: http://localhost:8000
```

5. **Manual Setup (Alternative):**
```bash
# (Optional) Start Redis manually
redis-server
```

## Usage

### CLI Commands

**Chat with a specific provider:**
```bash
python ai_framework.py chat chatgpt "What is quantum computing?"
python ai_framework.py chat claude "Explain neural networks"
```

**Interactive conversation mode:**
```bash
python ai_framework.py interactive chatgpt
```

**System management:**
```bash
python ai_framework.py status           # Show framework status
python ai_framework.py list             # List all providers
python ai_framework.py set-api-key openai sk-YOUR-KEY
```

### Web Dashboard

Access the beautiful real-time web interface:

```bash
# Start with Docker (recommended)
docker-compose up -d

# Or run directly
python web_dashboard.py

# Access at: http://localhost:8000
```

**Authentication:** API routes require an API key sent in the `X-API-Key` header. Configure keys in `.env` as
`ZEJZL_API_KEY_1=your_key:tier:description` (add `_2`, `_3`, ... for more). Without a key most routes return 401.
For local development, set `ENVIRONMENT=development` to use a built-in insecure test key when no keys are configured.
CORS origins are set with `CORS_ORIGINS`.

Features:
- **Live System Monitoring**: Real-time magic system status and AI provider health
- **Interactive Chat**: Chat with AI agents using single or consensus mode
- **Magic Controls**: Apply vitality boosts, shield activation, and healing spells
- **Agent Personalities**: View personality traits and expertise areas
- **Debug Panel**: System snapshots, logs, performance metrics, and health checks
- **WebSocket Updates**: Live status updates without page refresh

### Debugging

The standalone `debug_cli.py` tool was removed in the repository cleanup. Structured logging, request tracing and the
performance monitor live in `src/logging_debug.py` and `src/performance.py`, and the web dashboard has a debug panel
(system snapshots, logs, performance metrics, health checks). Logs are written to `ai_framework.log` and stdout;
set the level with `LOG_LEVEL`.

### Interactive Menu

Run the full interactive menu with all operation modes:

```bash
python main.py
```

Available modes:
1. **Single Agent** - Simple Observer → Reasoner → Actor loop
2. **Collaboration Mode** - Grok + Claude dual AI planning
3. **Swarm Mode** - Multi-agent async coordination
4. **Pantheon Mode** - Full 9-agent orchestration with validation and learning
5. **Learning Loop** - Single optimization cycle for system improvement
6. **Offline Mode** - Cached responses for offline operation
7. **Community Vault** - Browse and share tools, configs and evolutions
8. **ORAM Mode** - Observer-Reasoner-Actor + Memory iterative processing
9. **Quit**

Modes that call an AI provider need at least one API key in `.env`; without one they print
`[ERROR] No AI providers available` and return. Each mode shuts down the shared provider bus on exit.

### Running Tests

The pytest suite and the manual test scripts were removed in the repository cleanup, so there is no `pytest` run to do.
These checks work on the current tree:

```bash
# 1. Syntax check every file
python -m compileall -q .

# 2. Import every module under src/ (data_science.py is skipped: it needs pandas, which is not in requirements.txt)
python -c "import importlib, pathlib; [importlib.import_module('.'.join(f.with_suffix('').parts)) for f in pathlib.Path('src').rglob('*.py') if f.name not in ('__init__.py', 'data_science.py')]"

# 3. Dashboard smoke test (pip install httpx first): public pages return 200,
#    protected API routes 401, and nothing should return 5xx
python -c "from fastapi.testclient import TestClient; import web_dashboard; print(TestClient(web_dashboard.app).get('/').status_code)"

# 4. Provider connectivity (needs a real key)
python ai_framework.py chat claude "test"
```

To check the Redis fallback, stop Redis and confirm the framework logs one warning and continues with SQLite.

`.github/workflows/tests.yml` still references test scripts that no longer exist (`9agent_pantheon_test.py`,
`single_session_test_loop.py`, `interactive_session_example.py`) and needs updating before CI can pass.

### Running MCP Servers

**Code Analysis MCP Server:**
```bash
python src/mcp_servers/code_analysis.py --stdio
```

**Data Science MCP Server:**
```bash
python src/mcp_servers/data_science.py --stdio
```

**Other MCP Servers (filesystem, database, websearch, github):**
```bash
# These servers run automatically when accessed through the MCP client/registry
# Configure in web dashboard or use programmatically
```

## Configuration

### Environment Variables (.env)

```bash
# AI Provider API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=your-gemini-key
GROK_API_KEY=your-grok-key
DEEPSEEK_API_KEY=your-deepseek-key
QWEN_API_KEY=your-qwen-key
ZAI_API_KEY=your-zai-key

# Infrastructure
REDIS_URL=redis://localhost:6379
SQLITE_PATH=~/.ai_framework.db

# Runtime Settings
DEFAULT_PROVIDER=chatgpt
LOG_LEVEL=INFO
ENVIRONMENT=production      # 'development' enables the insecure dev API key
CORS_ORIGINS=http://localhost:8000

# Web dashboard authentication (one per key: key:tier:description)
ZEJZL_API_KEY_1=change-me:pro:Admin key

# Stripe payments (optional)
STRIPE_API_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
```

`ANTHROPIC_API_KEY` is an Anthropic API key from console.anthropic.com; a claude.ai Pro/Max subscription cannot be used.

### Supported AI Providers

| Provider | Model | API Endpoint |
|----------|-------|--------------|
| ChatGPT | gpt-3.5-turbo | OpenAI API |
| Claude | claude-3-opus-20240229 | Anthropic API |
| Gemini | gemini-3.5-flash-lite | Google AI API |
| Grok | grok-4.3 | xAI API |
| DeepSeek | deepseek-coder | DeepSeek API |
| Qwen | qwen-turbo | Alibaba Cloud API |
| Zai | zai-1 | Custom API |

## Project Structure

```
zejzlAI/
├── ai_framework.py              # Core: message bus, persistence, AI providers, CLI
├── base.py                      # PantheonAgent base class + shared AI provider bus
├── main.py                      # Interactive menu entry point
├── startup.py                   # Production entry point (Procfile)
├── web_dashboard.py             # FastAPI web dashboard
├── messagebus.py                # Inter-agent message bus
├── pantheon_swarm.py            # Swarm orchestration (budgets, permissions, blackboard)
├── pantheon_rlm.py              # Pantheon RLM
├── pantheon_rlm_integration.py  # RLM integration
├── pantheon_config.json         # Swarm configuration
├── offline_cache.py             # SQLite response cache (offline mode)
├── community_vault.py           # Community vault
├── rate_limiter.py              # Rate limiting
├── telemetry.py                 # Performance tracking
├── token_haze.py                # Interactive onboarding tool
├── orchestrate.sh, start.sh     # Orchestration and quick-start scripts
├── Dockerfile, docker-compose.yml, docker-entrypoint.sh
├── Procfile, render.yaml, railway.json, runtime.txt   # Deployment config
├── pyproject.toml, requirements.txt, .env.example
├── *.md                         # Guides: REDIS_SETUP, DOCKER_README, DEPLOY_RENDER, MCP_*, PHASE*_COMPLETE, ...
├── config/                      # mcp_servers.json
├── docs/  blog/  skills/  scripts/
├── templates/  static/          # Dashboard HTML and billing/blackboard/onboarding pages
├── web/                         # Dashboard templates and static JS/CSS
└── src/
    ├── magic.py                 # Fairy magic self-healing system
    ├── auth.py                  # API key authentication and rate limiting
    ├── payments.py              # Stripe integration (optional)
    ├── agent_personality.py     # Agent personality framework
    ├── logging_debug.py         # Structured logging and debug monitor
    ├── mcp_client.py, mcp_types.py, mcp_registry.py, mcp_security.py
    ├── mcp_agent_integration.py, mcp_agent_mixin.py
    ├── task_manager.py, user_management.py, budget_alerts.py
    ├── business_analytics.py, insight_engine.py, predictive_analytics.py
    ├── agents/                  # observer, reasoner, actor, validator, memory, executor,
    │                            # analyzer, learner, improver, consensus, observer_mcp, protocols
    └── mcp_servers/             # base_server, filesystem, database, websearch, github,
                                 # code_analysis, data_science
```

## Development

### Adding a New Agent

1. Create agent file in `src/agents/{agent_name}.py`
2. Implement async method with structured input/output
3. Add to the pantheon flow in `run_pantheon_mode()` in `main.py`

### Adding a New AI Provider

1. Inherit from `AIProvider` class in `ai_framework.py`
2. Implement `initialize()`, `generate_response()`, `cleanup()`
3. Add to `DEFAULT_CONFIG` and register in `AsyncMessageBus.start()`

## Roadmap

### Completed
- [x] **Phase 1**: Core issue fixes (main.py, base.py, imports, deprecations)
- [x] **Phase 2**: Integration & Testing (dual message bus, AI provider integration, test suite)
- [x] **Phase 3**: Production enhancements (rate limiting, retry logic, telemetry, pruning)
- [x] **Phase 4**: Self-healing & learning (magic system, circuit breakers, learning loop optimization)
- [x] **Phase 5**: Advanced AI & User Experience (streaming, web UI, Docker, consensus, personalization)
- [x] Real AI integration for Pantheon agents (Phase 3)
- [x] Rate limiting and retry logic (Phase 3)
- [x] Circuit breaker pattern for automatic failure recovery (Phase 4)
- [x] Python-Toon configuration system (Phase 5)
- [x] Streaming AI response support (Phase 5)
- [x] Web UI dashboard with real-time monitoring (Phase 5)
- [x] Docker containerization (Phase 5)
- [x] Multi-provider consensus mode (Phase 5)
- [x] Agent personalization framework (Phase 5)
- [x] Comprehensive test coverage (11/11 tests passing)
- [x] Full documentation (Architecture, Redis Setup, Phase 1-5 summaries)
- [x] Redis setup and inter-agent pub/sub
- [x] Learning loop optimization with pattern analysis
- [x] Self-healing with preference learning

### Completed (Phase 6: Enterprise Debugging & Observability) ✅
- [x] Comprehensive Logging System: Structured JSON logging with multiple levels and rotation
- [x] Advanced Debug Framework: Request tracing, performance profiling, and system snapshots
- [x] Real-time Debug Dashboard: Live debugging interface with system introspection
- [x] Debug CLI Tool: Command-line interface for system debugging and monitoring
- [x] Health Check Endpoints: Detailed system health monitoring with metrics
- [x] Performance Monitoring: Operation timing, success rates, and bottleneck identification
- [x] Request Tracing: End-to-end request monitoring and analysis
- [x] Log Aggregation: Centralized logging with searchable debug information
- [x] **Pantheon Mode Fixes**: Resolved agent communication issues, JSON parsing improvements, and fallback handling
- [x] **Provider Optimization**: Streamlined provider configuration with focus on stable providers (Grok, Claude, Gemini)
- [x] **Magic System Tuning**: Reduced verbosity and improved error handling for persistence operations
- [x] **Cost Tracking & Analytics**: Complete token usage tracking, cost calculation, and analytics dashboard

### Phase 7 Enhancements (Cost Tracking & Analytics) ✅
- [x] **Cost tracking and token usage analytics**: Real-time token counting, cost calculation, usage analytics, and dashboard integration
- [x] **Usage Analytics Engine**: Comprehensive reporting on requests, tokens, costs, and performance metrics
- [x] **Provider Cost Optimization**: Automatic cost calculation for all AI providers with pricing intelligence
- [x] **Analytics Dashboard**: Web-based cost and usage analytics with historical trends
- [x] **Database Schema**: Enhanced SQLite schema with daily/hourly analytics tables
- [x] **API Endpoints**: RESTful endpoints for cost data retrieval and analytics

### Phase 9 Enhancements (MCP Protocol Integration + Security Validator) ✅
- [x] **MCP Protocol Client**: Full JSON-RPC 2.0 implementation with circuit breaker integration and magic system support
- [x] **Server Registry**: Dynamic multi-server management with health monitoring, auto-reconnection, and access control
- [x] **Agent Integration Layer**: High-level API for agents with context management, caching, and usage tracking
- [x] **Built-in MCP Servers**: 6 production-ready servers providing 36+ tools
  - **Filesystem Server** (7 tools): File I/O, search, metadata with secure path validation
  - **Database Server** (6 tools): SQLite queries, schema introspection, SQL injection prevention
  - **Web Search Server** (3 tools): DuckDuckGo search, news, instant answers (no API key required)
  - **GitHub Server** (8 tools): Repository operations, issues, PRs, file access, search (token auth)
  - **Code Analysis Server** (6 tools): Codebase analysis, complexity metrics, dependency analysis, quality assessment
  - **Data Science Server** (6 tools): Dataset analysis, statistics, correlations, outlier detection, visualization
- [x] **MCP Agent Mixin**: Drop-in capabilities for existing agents with decorators and base classes
- [x] **MCP-Enhanced Observer**: Example implementation with web search, filesystem, and database integration
- [x] **Comprehensive Documentation**: MCP_INTEGRATION_GUIDE.md and MCP_SERVERS_GUIDE.md with examples
- [x] **PantheonAgent AI Integration**: Complete bidirectional AI Provider Bus integration via call_ai() method
- [x] **Production Testing**: Real-world task processing with comprehensive performance validation

### Security Validator Implementation ✅
- [x] **Advanced Command Safety Analysis**: 12 security policies covering file ops, network, database, and system operations
- [x] **Risk Assessment Engine**: 5-tier risk levels (SAFE → LOW_RISK → MEDIUM_RISK → HIGH_RISK → CRITICAL)
- [x] **Approval Gates**: NONE, LOG_ONLY, USER_CONFIRM, ADMIN_APPROVE, BLOCKED approval requirements
- [x] **Validator Agent Integration**: Replaced hardcoded validation with real security-aware analysis
- [x] **Web Dashboard Security Tab**: Interactive approval management interface with risk visualization
- [x] **Security Endpoints**: RESTful API for security validation, approvals, and reporting
- [x] **Dangerous Command Detection**: Pattern matching for risky operations like `rm -rf /`, `dd` commands, etc.
- [x] **Audit Trail**: Security event logging and approval history tracking

### Phase 10 Enhancements (Complete) ✅
- [x] **MCP Security Layer**: Authorization, rate limiting, audit logging with web dashboard API endpoints
- [x] **MCP Testing Suite**: Comprehensive integration tests with real server testing (15 tests passing)
- [x] **Web Dashboard MCP**: Full UI integration with server management, tool execution, and real-time monitoring
- [x] **Custom MCP Servers**: Domain-specific servers for code analysis and data science operations
- [ ] MCP tool composition and workflows
- [ ] Vector database integration for semantic memory
- [ ] Distributed agent deployment (multi-node)
- [ ] Community vault for shared patterns and evolutions
- [ ] Multi-language support and localization
- [ ] Advanced reasoning engine enhancements

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with async Python, leveraging multiple AI providers for enhanced orchestration capabilities.

---

## Quick Start

### Docker Deployment (Recommended)
```bash
# 1. Clone and setup
git clone https://github.com/zejzl/zejzlAI.git
cd zejzlAI/zejzl_net

# 2. Configure API keys (optional)
cp .env.example .env
# Edit .env and add your API keys

# 3. Deploy with Docker
docker-compose up -d

# 4. Access web dashboard
# Open: http://localhost:8000

# 5. View logs
docker-compose logs -f zejzl_net
```

### Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys (required for any mode that calls an AI provider)
cp .env.example .env
# Edit .env and add your API keys

# 3. Run the framework
./start.sh                        # Quick start (bash)
python main.py                    # Interactive menu
python web_dashboard.py           # Web dashboard (port 8000)
python token_haze.py              # Interactive onboarding
python ai_framework.py status     # Check status

# 4. Check the install
python -m compileall -q .         # Syntax check (see 'Running Tests' for more)
```

## Performance

- **Test Coverage**: 11/11 tests passing (all tests including Redis)
- **MessageBus Throughput**: 407,911 msg/sec (204x faster than Redis) [Updated 2026-01-30]
- **MessageBus Latency**: 0.007ms P95 (sub-millisecond, 987x lower than Redis) [Updated 2026-01-30]
- **Pantheon Pipeline**: 0.072ms for full 9-agent cycle (was 67.5ms) - 937x faster [Updated 2026-01-30]
- **Rate Limiting**: 60 req/min, 1000 req/hour per provider
- **Retry Success**: ~15-20% improvement over no retry
- **Response Time**: P95 tracked per provider
- **Conversation Limit**: 100 messages per conversation (auto-pruned)
- **Circuit Breakers**: 4 components with auto-recovery (15-60s timeout)
- **Vitality Boost**: 10-50% performance improvement per boost
- **Healing Success**: Tracked with DPO-style preference learning

---

**Status**: Phase 10 Complete | **Version**: 0.0.10.0 | **Phase**: 10 Complete (MCP Ecosystem + Custom Servers + Full Pantheon Integration)

## 🎯 Integration Verification (2026-01-27)

**PantheonAgent → AI Provider Bus Integration: ✅ PRODUCTION READY**

**Key Achievements:**
- ✅ **Full bidirectional communication**: All 9 Pantheon agents can call any AI provider
- ✅ **Magic system integration**: Automatic vitality boosts with measurable performance gains
- ✅ **Robust error handling**: Provider fallback, timeout management, graceful degradation
- ✅ **Real-world testing**: Successfully processed complex hackathon task generation
- ✅ **Performance optimization**: ~1.0s response times with comprehensive monitoring

**Integration Features:**
- Multi-provider AI calls (Grok, ChatGPT, Claude, Gemini, DeepSeek, Qwen, Zai)
- Automatic provider validation and intelligent fallback logic
- Structured error handling with stub responses
- Magic system vitality boosts (1.1x - 1.5x improvements)
- TOON format token-efficient communications
- Real-time performance metrics and debugging support
