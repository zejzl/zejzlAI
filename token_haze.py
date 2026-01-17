#!/usr/bin/env python3
"""
Token Haze - Interactive Introduction to ZEJZL.NET

This script provides an interactive onboarding experience for new users,
demonstrating ZEJZL.NET's capabilities including real token counting,
AI provider integration, Pantheon agent orchestration, and live system metrics.

Author: ZEJZL.NET Team
Last Updated: 2026-01-17
"""

import sys
import time
import asyncio
from typing import Optional


def print_header():
    """Print ASCII art header (Windows-compatible, no emojis)."""
    print("=" * 70)
    print("                   Z E J Z L . N E T")
    print("           AI Orchestration Framework v0.0.4")
    print("=" * 70)
    print()


def print_welcome():
    """Print a welcoming message for new users."""
    print("[WELCOME] You're entering the realm of intelligent AI orchestration.")
    print("[INFO] ZEJZL.NET is a multi-agent AI framework with 9 specialized agents.")
    print("[INFO] Here, tokens power the communication between AI providers and agents.")
    print()


def explain_tokens():
    """Explain what tokens are with real counting examples."""
    print("[TOKEN BASICS]")
    print("- Tokens are units of text that AI models process")
    print("- They can be words, subwords, or characters")
    print("- ZEJZL.NET uses tokens to communicate with multiple AI providers")
    print("- Efficient token usage = better performance and cost optimization")
    print()

    # Try to use tiktoken for real token counting
    try:
        import tiktoken
        encoder = tiktoken.encoding_for_model("gpt-4")

        print("[REAL TOKEN COUNTING DEMO]")
        demo_texts = [
            "Hello, world!",
            "The quick brown fox jumps over the lazy dog.",
            "ZEJZL.NET is an AI orchestration framework with 9 agents.",
        ]

        for text in demo_texts:
            tokens = encoder.encode(text)
            print(f"  Text: '{text}'")
            print(f"  Tokens: {len(tokens)} | {tokens[:10]}..." if len(tokens) > 10 else f"  Tokens: {len(tokens)} | {tokens}")
            print()
    except ImportError:
        print("[SIMPLE TOKEN ESTIMATION]")
        text = "Hello, new user! Welcome to the world of AI orchestration."
        token_estimate = len(text.split())
        print(f"  Text: '{text}'")
        print(f"  Estimated tokens: {token_estimate} (rough estimate: ~1 token per word)")
        print(f"  [NOTE] Install tiktoken for accurate counting: pip install tiktoken")
        print()


def check_redis_status() -> tuple[bool, Optional[str]]:
    """Check Redis connection and return status."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True, socket_connect_timeout=2)
        r.ping()

        # Try to get some stats
        info = r.info('stats')
        total_commands = info.get('total_commands_processed', 0)
        return True, f"Redis: CONNECTED | Commands processed: {total_commands:,}"
    except Exception as e:
        return False, f"Redis: OFFLINE ({str(e)[:50]})"


def check_messagebus_performance():
    """Display AsyncMessageBus performance metrics."""
    print("[ASYNCMESSAGEBUS PERFORMANCE]")
    try:
        # Try to import and test AsyncMessageBus
        from ai_framework import AsyncMessageBus

        print("  Status: AsyncMessageBus module available")
        print("  Architecture: Dual-bus system (AI provider + inter-agent)")
        print("  Features: Rate limiting, consensus mode, magic self-healing")
        print("  Providers: ChatGPT, Claude, Grok, Gemini, DeepSeek, Qwen, Zai")
        print("  Persistence: Redis primary + SQLite fallback")
        print()
    except ImportError as e:
        print(f"  Status: AsyncMessageBus not available ({str(e)})")
        print("  [NOTE] Run from ZEJZL.NET root directory to access modules")
        print()


def show_pantheon_status():
    """Display Pantheon agent information."""
    print("[PANTHEON STATUS - 9 Agent Orchestration System]")
    agents = [
        ("Observer", "Task perception, requirement analysis, complexity assessment"),
        ("Reasoner", "Strategic planning, logical reasoning, risk evaluation"),
        ("Actor", "Execution planning, tool integration, practical implementation"),
        ("Validator", "Quality assurance, safety validation, compliance checking"),
        ("Analyzer", "Performance insights, metrics analysis, system optimization"),
        ("Improver", "Self-healing, continuous improvement, magic system integration"),
        ("Learner", "Pattern recognition, learning algorithms, adaptive behavior"),
        ("Memory", "State persistence, conversation history, data management"),
        ("Executor", "Workflow orchestration, task coordination, progress monitoring"),
    ]

    for name, description in agents:
        print(f"  [{name:<10}] {description}")
    print()
    print("  Usage: python main.py (interactive menu)")
    print("  Direct: python 9agent_pantheon_test.py")
    print("  Web UI: http://localhost:8000 (after docker-compose up)")
    print()


def show_system_metrics():
    """Display system metrics and status."""
    print("[ZEJZL.NET SYSTEM METRICS]")

    # Redis status
    redis_connected, redis_msg = check_redis_status()
    print(f"  {redis_msg}")

    # Python version
    print(f"  Python: {sys.version.split()[0]}")

    # Check for key ZEJZL.NET dependencies
    dependencies = [
        ("fastapi", "Web dashboard framework"),
        ("uvicorn", "ASGI web server"),
        ("jinja2", "Template engine"),
        ("psutil", "System monitoring"),
        ("redis", "Message persistence"),
        ("aiosqlite", "Database fallback"),
        ("tiktoken", "Token counting"),
    ]

    print("\n  [DEPENDENCIES]")
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"    [{module_name:<12}] INSTALLED - {description}")
        except ImportError:
            print(f"    [{module_name:<12}] MISSING   - {description}")
    print()

    # Check for AI providers
    ai_providers = ["openai", "anthropic", "google", "xai"]
    available_providers = []
    for provider in ai_providers:
        try:
            __import__(provider)
            available_providers.append(provider)
        except ImportError:
            pass

    print(f"  AI Providers Available: {len(available_providers)}")
    if available_providers:
        print(f"  Available: {', '.join(available_providers)}")
    print()


def show_quick_start():
    """Show quick start commands."""
    print("[ZEJZL.NET QUICK START GUIDE]")
    print("  1. Interactive menu (recommended):")
    print("     python main.py")
    print()
    print("  2. Direct 9-agent orchestration:")
    print("     python 9agent_pantheon_test.py")
    print()
    print("  3. Web dashboard:")
    print("     docker-compose up -d")
    print("     # Visit: http://localhost:8000")
    print()
    print("  4. Debug CLI:")
    print("     python debug_cli.py status")
    print()
    print("  5. Run tests:")
    print("     python -m pytest test_basic.py test_integration.py -v")
    print()
    print("  6. Master orchestration:")
    print("     ./orchestrate.sh menu")
    print()
    print("  7. Token counting demo:")
    print("     python token_haze.py --interactive")
    print()


def interactive_demo():
    """Run interactive demo with user choices."""
    print("[ZEJZL.NET INTERACTIVE DEMO]")
    print()
    print("What would you like to learn about?")
    print()
    print("  1. Token counting demonstration")
    print("  2. AsyncMessageBus architecture")
    print("  3. Pantheon agent orchestration")
    print("  4. System metrics and dependencies")
    print("  5. Quick start commands")
    print("  6. All of the above")
    print("  0. Exit")
    print()

    try:
        choice = input("Enter your choice (0-6): ").strip()
        print()

        if choice == "1":
            explain_tokens()
        elif choice == "2":
            check_messagebus_performance()
        elif choice == "3":
            show_pantheon_status()
        elif choice == "4":
            show_system_metrics()
        elif choice == "5":
            show_quick_start()
        elif choice == "6":
            explain_tokens()
            check_messagebus_performance()
            show_pantheon_status()
            show_system_metrics()
            show_quick_start()
        elif choice == "0":
            print("[EXIT] Goodbye!")
            return
        else:
            print("[ERROR] Invalid choice. Please enter a number between 0-6.")
            return

        # Ask if user wants to continue
        print()
        cont = input("Continue exploring? (y/n): ").strip().lower()
        if cont == 'y':
            interactive_demo()

    except (KeyboardInterrupt, EOFError):
        print("\n[EXIT] Goodbye!")


def show_next_steps():
    """Show what new users should do next."""
    print("[NEXT STEPS]")
    print("  1. Read README.md for complete project overview")
    print("  2. Explore the web dashboard: docker-compose up -d")
    print("  3. Try the interactive menu: python main.py")
    print("  4. Run the 9-agent demo: python 9agent_pantheon_test.py")
    print("  5. Use the debug CLI: python debug_cli.py status")
    print("  6. Master orchestration: ./orchestrate.sh menu")
    print("  7. Join the community: https://github.com/zejzl/zejzlAI")
    print()


def main():
    """Main function to run the interactive introduction."""
    print_header()
    print_welcome()

    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
    else:
        # Default non-interactive tour
        explain_tokens()
        check_messagebus_performance()
        show_pantheon_status()
        show_system_metrics()
        show_quick_start()
        show_next_steps()

        print("=" * 70)
        print("[SUCCESS] ZEJZL.NET introduction tour complete!")
        print("[TIP] Run with --interactive for interactive demo:")
        print("      python token_haze.py --interactive")
        print("[WEB] Launch web dashboard: docker-compose up -d")
        print("=" * 70)


if __name__ == "__main__":
    main()
