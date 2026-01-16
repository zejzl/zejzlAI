# ZEJZL.NET

[![Tests](https://github.com/zejzl/zejzlAI/actions/workflows/tests.yml/badge.svg)](https://github.com/zejzl/zejzlAI/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Multi-Agent AI Framework with 9-Agent Pantheon Orchestration System**

An async message bus AI framework that orchestrates multiple AI models through a specialized 9-agent system for complex task decomposition, execution, validation, and continuous learning.

## Features

- **9-Agent Pantheon System**: Specialized agents working in concert (Observer, Reasoner, Actor, Validator, Memory, Executor, Analyzer, Learner, Improver)
- **Multi-Provider Support**: Integrate ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, and Zai
- **Async Message Bus**: High-performance async/await architecture for concurrent operations
- **Hybrid Persistence**: Redis (primary) + SQLite (automatic fallback) for reliable state management
- **Multiple Operation Modes**: Single agent, collaboration, swarm, and full pantheon orchestration
- **Flexible Configuration**: TOML-based config with environment variable support

## Architecture

```
┌─────────────────────────────────────────────────┐
│  CLI Interface (Interactive Menu)               │
├─────────────────────────────────────────────────┤
│  AsyncMessageBus (Orchestration Layer)          │
│  - Provider Management                          │
│  - Message Routing                              │
│  - Conversation History                         │
├─────────────────────────────────────────────────┤
│  9-Agent Pantheon System                        │
│  Observer → Reasoner → Actor → Validator        │
│  → Executor → Memory → Analyzer → Learner       │
│  → Improver                                     │
├─────────────────────────────────────────────────┤
│  AI Provider Layer (7 Providers)                │
├─────────────────────────────────────────────────┤
│  Persistence Layer (Redis + SQLite)             │
└─────────────────────────────────────────────────┘
```

### The 9 Agents

1. **Observer** - Perceives and analyzes task requirements
2. **Reasoner** - Plans and decomposes tasks into subtasks
3. **Actor** - Executes planned actions
4. **Validator** - Validates execution correctness and safety
5. **Executor** - Performs validated tasks with error handling
6. **Memory** - Stores and recalls execution state and history
7. **Analyzer** - Generates performance metrics and telemetry
8. **Learner** - Identifies patterns from execution traces
9. **Improver** - Suggests system optimizations based on learned patterns

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

4. (Optional) Start Redis:
```bash
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

### Interactive Menu

Run the full interactive menu with all operation modes:

```bash
python main.py
```

Available modes:
1. **Single Agent** - Simple Observer → Reasoner → Actor loop
2. **Collaboration Mode** - Grok + Claude dual AI planning
3. **Swarm Mode** - Multi-agent async coordination
4. **Pantheon Mode** - Full 9-agent orchestration
5. **Improver Manual** - Self-improvement on sessions
6. **Offline Mode** - Cached/local fallback
7. **Community Vault Sync** - Share evolutions and tools
8. **Save Game** - Persist session progress

### Running Tests

**Full 9-agent pantheon test:**
```bash
python -c "import asyncio; exec(open('9agent_pantheon_test.py').read()); asyncio.run(run_pantheon_demo('Build a REST API'))"
```

**Single agent with validation:**
```bash
echo "Create a calculator" | python -c "import asyncio; exec(open('single_session_test_loop.py').read()); asyncio.run(run_single_agent_with_validation())"
```

**Simple interactive session:**
```bash
echo "Write a hello world" | python -c "import asyncio; exec(open('interactive_session_example.py').read()); asyncio.run(run_single_agent_demo())"
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
```

### Supported AI Providers

| Provider | Model | API Endpoint |
|----------|-------|--------------|
| ChatGPT | gpt-3.5-turbo | OpenAI API |
| Claude | claude-3-opus-20240229 | Anthropic API |
| Gemini | gemini-pro | Google AI API |
| Grok | grok-1 | xAI API |
| DeepSeek | deepseek-coder | DeepSeek API |
| Qwen | qwen-turbo | Alibaba Cloud API |
| Zai | zai-1 | Custom API |

## Project Structure

```
zejzl_net/
├── ai_framework.py              # Core framework (970 lines)
├── main.py                      # Interactive CLI entry point
├── 9agent_pantheon_test.py      # Full orchestration test
├── single_session_test_loop.py  # Single agent test
├── interactive_session_example.py # Basic example
├── CLAUDE.md                    # Claude Code documentation
├── AGENTS.md                    # Agent system documentation
├── pyproject.toml               # Build configuration
├── .env.example                 # Environment template
└── src/
    └── agents/                  # 9 agent implementations
        ├── observer.py
        ├── reasoner.py
        ├── actor.py
        ├── validator.py
        ├── memory.py
        ├── executor.py
        ├── analyzer.py
        ├── learner.py
        └── improver.py
```

## Development

### Adding a New Agent

1. Create agent file in `src/agents/{agent_name}.py`
2. Implement async method with structured input/output
3. Add to pantheon flow in `9agent_pantheon_test.py`

### Adding a New AI Provider

1. Inherit from `AIProvider` class in `ai_framework.py`
2. Implement `initialize()`, `generate_response()`, `cleanup()`
3. Add to `DEFAULT_CONFIG` and register in `AsyncMessageBus.start()`

## Roadmap

- [ ] Real AI implementation for agents (currently stubs)
- [ ] Streaming response support
- [ ] Rate limiting and retry logic
- [ ] Persistent memory across sessions
- [ ] Community vault for shared patterns
- [ ] Web UI dashboard
- [ ] Docker containerization
- [ ] Multi-language support

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with async Python, leveraging multiple AI providers for enhanced orchestration capabilities.

---

**Status**: Active Development | **Version**: 0.0.1
