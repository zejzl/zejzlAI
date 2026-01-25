# GEMINI.md - ZEJZL.NET Project Guide for Gemini

## ⚠️ CRITICAL CODING STANDARD FOR GEMINI AGENTS

**STRICT PROHIBITION: NO EMOJIS IN PYTHON CODE**

All Gemini AI agents (including Gemini Pro, Gemini Flash, Gemini Ultra) working on this codebase **must comply** with this mandatory rule:

- **NEVER** use emoji characters (🚀, ✅, ❌, 💡, 🔧, 🤖, 🧠, 📊, etc.) in any source files (.py, .sh, .js, .ts)
- **ALWAYS** use text indicators: `[OK]`, `[ERROR]`, `[INFO]`, `[WARNING]`, `[SUCCESS]`, `[AI]`, `[AGENT]`, `[START]`
- **Reason**: Terminal encoding issues, Python logging compatibility, professional standards
- **Emojis allowed ONLY** in documentation files (`.md`)

This follows professional programming best practices for cross-platform compatibility and enterprise-grade code quality.

## Project: ZEJZL.NET AI Framework

ZEJZL.NET is a sophisticated async message bus AI framework with a 9-agent "Pantheon" orchestration system designed for multi-AI collaboration.

### Technology Stack
- **Language**: Python 3.8+
- **Architecture**: Async message bus with event-driven routing
- **AI Providers**: ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, Zai
- **Database**: Redis (primary) + SQLite (fallback)
- **Web**: Flask + Socket.IO
- **Containerization**: Docker + Docker Compose

### Core Components

1. **Message Bus** (`ai_framework.py`)
   - Async event routing
   - Provider lifecycle management
   - Conversation history caching
   - Dual persistence layer

2. **Pantheon System** (9 specialized agents)
   - Each agent handles specific AI tasks
   - Coordinated through message bus
   - Self-healing with circuit breakers

3. **Web Dashboard** (`web_dashboard.py`)
   - Real-time monitoring
   - Agent status tracking
   - Configuration management

4. **Community Vault** (`community_vault.py`)
   - Shared knowledge base
   - Cross-agent learning

### Development Workflow

```bash
# Environment Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Run Framework
python main.py

# Run Web Dashboard
python web_dashboard.py

# Run Tests
python test_comprehensive.py
pytest tests/

# Docker Deployment
docker-compose up -d
./orchestrate.sh start
```

### Testing
- Unit tests: `test_*.py` files
- Integration: `test_integration.py`
- MCP: `test_mcp_*.py` files
- Comprehensive: `test_comprehensive.py`

### Code Style Guidelines

When working with Gemini on this project:

1. **No Emojis in Code** (CRITICAL)
2. **Type Hints**: Use Python type hints for all functions
3. **Docstrings**: Google-style docstrings for all classes/methods
4. **Async/Await**: Proper async handling for message bus operations
5. **Error Handling**: Comprehensive try/except with logging
6. **Logging**: Use Python logging module with text indicators

### Example Code Pattern

```python
import logging

logger = logging.getLogger(__name__)

async def process_message(message: dict) -> dict:
    """Process incoming message through AI provider.

    Args:
        message: Message dictionary with content and metadata

    Returns:
        Processed message response

    Raises:
        AIProviderError: If provider fails to process
    """
    try:
        logger.info("[START] Processing message")
        result = await ai_provider.send(message)
        logger.info("[SUCCESS] Message processed")
        return result
    except Exception as e:
        logger.error(f"[ERROR] Failed to process: {e}")
        raise
```

### File Structure
- Root: Main scripts and configuration
- `src/`: Core framework modules
- `src/agents/`: Pantheon agent implementations
- `tests/`: Test suites
- `config/`: Configuration files
- `web/`: Web dashboard assets

### Important Notes
- All API keys go in `.env` file (never commit)
- Redis must be running for full functionality
- SQLite is automatic fallback if Redis unavailable
- Web dashboard runs on port 5000 by default

### Common Tasks

**Add New AI Provider:**
1. Extend provider class in `ai_framework.py`
2. Add API key to `.env`
3. Register in message bus
4. Add tests

**Modify Pantheon Agent:**
1. Edit agent in `src/agents/`
2. Update message routing
3. Test with `test_pantheon_mode.py`

**Update Web Dashboard:**
1. Modify `web_dashboard.py`
2. Update templates in `web/`
3. Test real-time updates

Remember: **NO EMOJIS IN SOURCE CODE!** Use text indicators like `[OK]`, `[ERROR]`, `[INFO]` instead.
