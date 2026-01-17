# ZEJZL.NET Commands Reference

## Overview

ZEJZL.NET provides multiple interfaces for interacting with the AI orchestration framework. This document covers all available commands, flags, and options across different entry points.

## 1. Main Interactive Menu (`python main.py`)

The primary interactive interface with menu-driven operation modes.

### Available Modes:
- **1. Single Agent** - Observe-Reason-Act loop with one agent
- **4. Pantheon Mode** - Full 9-agent orchestration with validation & learning
- **9. Quit** - Exit the application

### Usage:
```bash
python main.py
```

## 2. AI Framework CLI (`python ai_framework.py`)

Direct command-line interface for AI provider interactions and framework management.

### Commands:

#### `chat` - Send messages to AI providers
```bash
python ai_framework.py chat <provider> <message> [--conversation-id <id>]
```

**Arguments:**
- `provider` - AI provider (chatgpt, claude, gemini, grok)
- `message` - Message to send to the AI

**Options:**
- `--conversation-id <id>` - Conversation ID (default: "default")

**Examples:**
```bash
python ai_framework.py chat chatgpt "What is quantum computing?"
python ai_framework.py chat claude "Explain neural networks" --conversation-id "science_001"
```

#### `interactive` - Start interactive chat mode
```bash
python ai_framework.py interactive <provider>
```

**Arguments:**
- `provider` - AI provider to use for the session

**Examples:**
```bash
python ai_framework.py interactive grok
```

#### `list` - List all registered providers
```bash
python ai_framework.py list
```

**Description:** Shows all available AI providers and their status.

#### `status` - Show framework status
```bash
python ai_framework.py status
```

**Description:** Displays current framework health, provider status, and system metrics.

#### `set-api-key` - Configure API keys
```bash
python ai_framework.py set-api-key <provider> <api_key>
```

**Arguments:**
- `provider` - AI provider name
- `api_key` - API key for the provider

**Examples:**
```bash
python ai_framework.py set-api-key openai sk-your-key-here
python ai_framework.py set-api-key anthropic sk-ant-your-key-here
```

#### `set-default` - Set default provider
```bash
python ai_framework.py set-default <provider>
```

**Arguments:**
- `provider` - AI provider to set as default

**Examples:**
```bash
python ai_framework.py set-default grok
```

## 3. Debug CLI Tool (`python debug_cli.py`)

Command-line interface for system debugging and monitoring.

### Commands:

#### `status` - Show system status overview
```bash
python debug_cli.py status
```

**Description:** Displays comprehensive system health, agent status, and framework metrics.

#### `logs` - View recent debug logs
```bash
python debug_cli.py logs [--lines <number>]
```

**Options:**
- `--lines, -n <number>` - Number of lines to display (default: 20)

**Examples:**
```bash
python debug_cli.py logs
python debug_cli.py logs --lines 50
```

#### `performance` - Show performance metrics
```bash
python debug_cli.py performance [--level <type>]
```

**Options:**
- `--level <type>` - Performance level to focus on (debug, performance, main) (default: debug)

**Examples:**
```bash
python debug_cli.py performance
python debug_cli.py performance --level performance
```

#### `snapshot` - Create system snapshot
```bash
python debug_cli.py snapshot [--level <type>]
```

**Options:**
- `--level <type>` - Snapshot level (debug, performance, main) (default: debug)

**Description:** Creates a comprehensive snapshot of system state for analysis.

#### `clear-logs` - Clear debug logs
```bash
python debug_cli.py clear-logs
```

**Description:** Rotates and clears old debug log files.

#### `set-level` - Set logging level
```bash
python debug_cli.py set-level --log-level <level>
```

**Options:**
- `--log-level <level>` - Log level (DEBUG, INFO, WARNING, ERROR)

**Examples:**
```bash
python debug_cli.py set-level --log-level DEBUG
python debug_cli.py set-level --log-level INFO
```

## 4. Master Orchestration Script (`./orchestrate.sh`)

Comprehensive automation script for system management and deployment.

### Commands:

#### `setup` - Complete system setup
```bash
./orchestrate.sh setup
```

**Description:** Performs complete ZEJZL.NET system initialization, including dependencies, environment, and git setup.

#### `dev` - Development workflow
```bash
./orchestrate.sh dev
```

**Description:** Runs tests, checks code quality, and commits changes.

#### `deploy-staging` - Deploy to staging
```bash
./orchestrate.sh deploy-staging
```

**Description:** Deploys the system to staging environment with Docker.

#### `deploy-production` - Deploy to production
```bash
./orchestrate.sh deploy-production
```

**Description:** Deploys the system to production environment with Docker.

#### `maintenance` - Run maintenance tasks
```bash
./orchestrate.sh maintenance
```

**Description:** Performs Docker cleanup, Python cache clearing, and dependency updates.

#### `monitor` - Show monitoring dashboard
```bash
./orchestrate.sh monitor
```

**Description:** Displays system status, service health, and performance metrics.

#### `optimize` - Performance optimization
```bash
./orchestrate.sh optimize
```

**Description:** Runs performance tests and optimization routines.

#### `security` - Security audit
```bash
./orchestrate.sh security
```

**Description:** Performs security checks on dependencies and environment.

#### `docs` - Documentation check
```bash
./orchestrate.sh docs
```

**Description:** Validates documentation and checks for updates.

#### `health` - System health check
```bash
./orchestrate.sh health
```

**Description:** Comprehensive health check of all system components.

#### `recovery` - Emergency recovery
```bash
./orchestrate.sh recovery
```

**Description:** Emergency recovery mode - stops all services and resets to clean state.

#### `demo` - Start ZEJZL.NET demo
```bash
./orchestrate.sh demo
```

**Description:** Starts full demo with web dashboard and all services.

#### `tools` - Show available tools
```bash
./orchestrate.sh tools
```

**Description:** Lists all available development and deployment tools.

#### `menu` - Interactive menu (default)
```bash
./orchestrate.sh menu
# or just:
./orchestrate.sh
```

**Description:** Launches interactive menu for all orchestration options.

## 5. Quick Start Script (`./start.sh`)

Simplified startup script for basic operation.

### Usage:
```bash
./start.sh
```

**Description:** Performs basic setup checks and launches the main interactive menu.

## 6. Interactive Onboarding (`python token_haze.py`)

Educational tool demonstrating token usage and system capabilities.

### Usage:
```bash
python token_haze.py [--interactive]
```

**Options:**
- `--interactive` - Run in interactive mode

**Description:** Provides hands-on introduction to ZEJZL.NET with real token counting examples.

## 7. Web Dashboard (`python web_dashboard.py`)

Web-based monitoring and control interface.

### Usage:
```bash
python web_dashboard.py
```

**Description:** Starts web server on http://localhost:8000 with real-time monitoring, chat interface, and security management.

## 8. Test Commands

### Basic Tests (`python -m pytest test_basic.py test_integration.py`)
```bash
# Run all tests
python -m pytest test_basic.py test_integration.py -v

# Run specific tests
python -m pytest test_integration.py::test_full_pantheon_orchestration -v

# With coverage
python -m pytest --cov=. --cov-report=html
```

### Magic System Tests (`python test_magic_integration.py`)
```bash
python test_magic_integration.py
```

### Phase 5 Enhanced Tests (`python example_enhanced.py`)
```bash
python example_enhanced.py
python example_enhanced.py --interactive
```

### Security Integration Tests (`python test_security_integration.py`)
```bash
python test_security_integration.py
```

### Full Pantheon Test (`python 9agent_pantheon_test.py`)
```bash
python 9agent_pantheon_test.py
```

### Single Agent Test (`python single_session_test_loop.py`)
```bash
python single_session_test_loop.py
```

### Interactive Example (`python interactive_session_example.py`)
```bash
python interactive_session_example.py
```

## 9. Docker Commands

### Build and Start Services
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access Running Services
```bash
# Web dashboard
open http://localhost:8000

# Check container status
docker-compose ps

# Execute commands in containers
docker-compose exec zejzl_net bash
```

## 10. Security Validator Commands

### Test Security Validation
```bash
# Run security integration test
python test_security_integration.py

# Validate specific command via web API
curl -X POST http://localhost:8000/api/security/validate \
  -H "Content-Type: application/json" \
  -d '{"operation": "rm -rf /", "user": "test"}'
```

### Security Dashboard (Web Interface)
- **Security Tab**: Real-time validation stats and risk monitoring
- **Approval Management**: Interactive approval/deny interface for dangerous operations
- **Risk Visualization**: Charts showing security risk distribution
- **Audit Log**: Security event history and compliance tracking

## 11. MCP (Model Context Protocol) Commands

### Server Testing
```bash
# Test filesystem MCP server
python test_mcp_servers.py filesystem

# Test database MCP server
python test_mcp_servers.py database

# Test web search MCP server
python test_mcp_servers.py websearch

# Test GitHub MCP server
python test_mcp_servers.py github
```

### MCP Agent Integration Tests
```bash
# Test MCP-enhanced observer
python test_mcp_agent_integration.py

# Test MCP client functionality
python test_mcp_client.py

# Test MCP security layer
python test_mcp_security.py
```

### MCP Registry Management
```bash
# Test MCP server registry
python test_mcp_registry.py

# Test MCP integration
python test_mcp_integration.py
```

## 12. Cost Tracking & Analytics

### Usage Analytics
```bash
# Run cost calculation tests
python test_cost_calculation.py

# Run analytics tests
python test_analytics.py
```

### Analytics Endpoints (Web Dashboard)
- **Cost Analytics**: Token usage and cost tracking
- **Provider Performance**: AI provider metrics and efficiency
- **Usage Trends**: Historical usage patterns and optimization insights

## 13. Multi-Modal AI Commands

### Image Processing Tests
```bash
# Test PDF reading capabilities
python test_pdf_reading.py

# Test multi-modal AI processing
python advanced_ai_test.py
```

### Multi-Modal Endpoints (Web Dashboard)
- **Image Analysis**: Upload and analyze images with AI
- **PDF Processing**: Extract text and analyze PDF documents
- **Multi-Modal Chat**: Combine text, images, and structured data

## 14. Development & Maintenance

### Git Operations
```bash
# Status and commit
git status
git add .
git commit -m "Development update"

# Push changes
git push origin main
```

### Code Quality
```bash
# Run tests with coverage
python -m pytest --cov=. --cov-report=term-missing

# Check dependencies
pip check

# Update dependencies
pip install --upgrade -r requirements.txt
```

## 15. Configuration & Environment

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
# Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, GROK_API_KEY
```

### Supported AI Providers
- **ChatGPT**: OpenAI GPT models
- **Claude**: Anthropic Claude models
- **Gemini**: Google Gemini models
- **Grok**: xAI Grok models
- **DeepSeek**: DeepSeek Coder models
- **Qwen**: Alibaba Cloud Qwen models
- **ZAI**: Custom ZAI models

## Quick Reference

### Most Common Commands:
```bash
# Start interactive system
python main.py

# Quick setup and start
./start.sh

# Full orchestration menu
./orchestrate.sh

# Start web dashboard
python web_dashboard.py

# Debug and monitoring
python debug_cli.py status
python debug_cli.py logs

# Run tests
python -m pytest test_basic.py test_integration.py -v

# Chat with AI
python ai_framework.py chat grok "Hello, AI!"

# Docker deployment
docker-compose up -d
```

### Emergency Commands:
```bash
# Emergency recovery
./orchestrate.sh recovery

# Clear all logs
python debug_cli.py clear-logs

# Force restart services
docker-compose down && docker-compose up -d
```

---

**Version**: 0.0.9.1 | **Status**: Security Validator Complete
**Last Updated**: 2026-01-17 | **Framework**: ZEJZL.NET AI Orchestration</content>
<parameter name="filePath">zejzl_net/commands.md