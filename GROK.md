# GROK.md - ZEJZL.NET Project Context for Grok

## ⚠️ MANDATORY CODING RULE FOR GROK AGENTS

**ZERO TOLERANCE: NO EMOJIS IN SOURCE CODE**

This is a **non-negotiable coding standard** that all Grok agents must follow when working on this repository:

🚫 **FORBIDDEN in source code files (.py, .sh, .js, .ts):**
- Emoji characters: 🚀, ✅, ❌, 💡, 🔧, 🤖, 🧠, 📊, 💬, 🎯, 🔍, etc.
- Unicode decorative characters

✅ **REQUIRED instead:**
- Text indicators: `[OK]`, `[ERROR]`, `[INFO]`, `[SUCCESS]`, `[START]`, `[AI]`, `[AGENT]`, `[DATA]`, `[CHAT]`, `[GOAL]`, `[SEARCH]`

**Rationale:**
- Terminal encoding compatibility across Windows/Linux
- Python logging system compatibility
- Log file parsing and monitoring tools
- Professional coding standards
- Accessibility and screen reader support

✅ **Emojis allowed ONLY in `.md` documentation files** (like this one)

All Grok agents must audit their code changes before committing to ensure zero emoji usage in source files.

## Project Overview

ZEJZL.NET is an async message bus AI framework implementing a 9-agent "Pantheon" orchestration system for multi-AI collaboration with self-healing capabilities.

### Key Features
- **Multi-AI Support**: ChatGPT, Claude, Gemini, Grok, DeepSeek, Qwen, Zai
- **Message Bus Architecture**: Async event-driven message routing
- **9-Agent Pantheon**: Specialized agents for different AI tasks
- **Self-Healing**: Automatic failure recovery with circuit breakers
- **Dual Persistence**: Redis (primary) + SQLite (fallback)
- **Advanced AI**: Multi-modal, reasoning, natural language understanding

### Architecture
- **Message Bus**: `AsyncMessageBus` handles provider orchestration
- **Pantheon System**: 9 specialized agents working in harmony
- **Persistence**: Hybrid Redis/SQLite for conversation history
- **Self-Healing**: "Magic" system with circuit breakers and learning loops
- **Web Dashboard**: Flask-based monitoring and control interface

### Status
Phase 6 Complete - All development phases finished with advanced AI capabilities fully implemented.

## Development Commands

```bash
# Setup
pip install -r requirements.txt

# Run main framework
python main.py

# Run web dashboard
python web_dashboard.py

# Run tests
python test_comprehensive.py
python test_pantheon_mode.py

# Docker
docker-compose up -d
./orchestrate.sh start
```

## Important Files
- `ai_framework.py` - Core framework and message bus
- `main.py` - Main entry point
- `web_dashboard.py` - Web interface
- `community_vault.py` - Community knowledge system
- `src/agents/` - Pantheon agent implementations

## Coding Guidelines

All Grok agents working on this project must:
1. Follow the NO EMOJIS IN CODE rule
2. Use proper Python type hints
3. Add comprehensive docstrings
4. Write tests for new features
5. Update relevant documentation
6. Check logs for any issues before committing
