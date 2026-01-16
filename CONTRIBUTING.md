# Contributing to ZEJZL.NET

Thank you for your interest in contributing to ZEJZL.NET! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Add your API keys to .env
```

3. Run tests:
```bash
python -c "import asyncio; exec(open('9agent_pantheon_test.py').read()); asyncio.run(run_pantheon_demo('test task'))"
```

## Code Style

- Follow PEP 8 style guidelines
- Use async/await for all I/O operations
- Add type hints where appropriate
- Keep functions focused and single-purpose
- Document complex logic with comments

## Agent Development

When adding a new agent:

1. Create a new file in `src/agents/{agent_name}.py`
2. Implement the agent class with async methods
3. Return structured dictionaries with timestamps
4. Add comprehensive docstrings
5. Update the pantheon flow if needed
6. Add tests for the new agent

Example agent structure:
```python
import time

class NewAgent:
    def __init__(self, name: str = "NewAgent"):
        self.name = name

    async def process(self, input_data: dict) -> dict:
        """
        Process input and return structured output.

        Args:
            input_data: Dictionary with task information

        Returns:
            Dictionary with results and metadata
        """
        # Your implementation here
        return {
            "result": "processed data",
            "timestamp": time.perf_counter()
        }
```

## Provider Development

When adding a new AI provider:

1. Inherit from the `AIProvider` abstract base class
2. Implement required methods:
   - `__init__(self, api_key: str, model: str)`
   - `async def initialize(self)`
   - `async def generate_response(self, message: Message, history: List[Message]) -> str`
   - `async def cleanup(self)`
3. Add provider to `DEFAULT_CONFIG` in `ai_framework.py`
4. Update `.env.example` with the new API key variable
5. Register the provider in `AsyncMessageBus.start()`

## Testing

- Test your changes thoroughly before submitting
- Run all existing tests to ensure nothing breaks
- Add new tests for new features
- Test with and without Redis running (to verify SQLite fallback)
- Test with different AI providers if applicable

## Documentation

- Update CLAUDE.md if you change architecture or add major features
- Update README.md with new usage examples or features
- Add docstrings to all new functions and classes
- Comment complex algorithms or non-obvious logic

## Pull Request Process

1. Update documentation to reflect your changes
2. Ensure all tests pass
3. Update the README.md if needed
4. Write a clear PR description explaining:
   - What changes you made
   - Why you made them
   - How to test them
5. Link any related issues

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
Add feature: Brief description

- Detailed point 1
- Detailed point 2
- Detailed point 3
```

Examples:
- `Add streaming response support for ChatGPT provider`
- `Fix memory leak in Redis persistence layer`
- `Update observer agent to handle complex tasks`

## Areas for Contribution

We welcome contributions in these areas:

### High Priority
- Real AI implementation for agents (replace stubs)
- Rate limiting and retry logic for providers
- Persistent memory across sessions
- Comprehensive test suite

### Medium Priority
- Streaming response support
- Web UI dashboard
- Additional AI provider integrations
- Performance optimizations

### Documentation
- More usage examples
- Video tutorials
- API reference documentation
- Architecture deep-dives

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions about architecture or implementation
- Check existing issues and PRs before creating new ones

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
