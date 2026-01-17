#!/usr/bin/env python3
"""
Enhanced Example for ZEJZL.NET with Phase 3 Features
Demonstrates:
- Rate limiting
- Retry logic
- Conversation pruning
- Performance tracking
- Real AI provider integration (when API keys available)
"""

import asyncio
import logging
from ai_framework import AsyncMessageBus
from rate_limiter import get_rate_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EnhancedExample")


async def demo_rate_limiting():
    """Demonstrate rate limiting in action"""
    print("\n" + "="*70)
    print("DEMO 1: Rate Limiting")
    print("="*70)

    rate_limiter = get_rate_limiter()

    # Simulate rapid requests
    print("\nAttempting 5 rapid requests...")
    for i in range(5):
        allowed = await rate_limiter.acquire("chatgpt", timeout=2.0)
        if allowed:
            print(f"  Request {i+1}: [OK] Allowed")
        else:
            print(f"  Request {i+1}: [FAIL] Rate limited")

    # Show stats
    stats = await rate_limiter.get_all_stats()
    if "chatgpt" in stats:
        print(f"\nRate Limiter Stats for ChatGPT:")
        print(f"  Requests in last minute: {stats['chatgpt']['requests_last_minute']}")
        print(f"  Tokens available: {stats['chatgpt']['minute_tokens_available']}")
        print(f"  Minute limit: {stats['chatgpt']['minute_limit']}")


async def demo_retry_logic():
    """Demonstrate retry logic with AI framework"""
    print("\n" + "="*70)
    print("DEMO 2: Retry Logic & Error Handling")
    print("="*70)

    bus = AsyncMessageBus()

    try:
        await bus.start()
        print("\n[OK] Message bus started with retry logic enabled")
        print("  - Max retries: 3")
        print("  - Exponential backoff: 1s, 2s, 4s")
        print("  - Retries transient errors: timeout, 50x, connection issues")

    except Exception as e:
        print(f"\n[FAIL] Error starting message bus: {e}")

    finally:
        await bus.stop()


async def demo_conversation_pruning():
    """Demonstrate automatic conversation pruning"""
    print("\n" + "="*70)
    print("DEMO 3: Conversation Pruning")
    print("="*70)

    bus = AsyncMessageBus()

    try:
        await bus.start()

        print("\n[OK] SQLite persistence with automatic pruning")
        print("  - Keeps last 100 messages per conversation")
        print("  - Automatically removes older messages")
        print("  - Matches Redis behavior for consistency")

        # Show pruning in action (simulated)
        print("\nSimulating conversation pruning...")
        print("  [Message 1-100]: Kept in database")
        print("  [Message 101]: New message added")
        print("  [Message 1]: Automatically pruned (oldest)")
        print("  Result: Database maintains 100 most recent messages")

    finally:
        await bus.stop()


async def demo_real_ai_call():
    """Demonstrate real AI provider call (if API key available)"""
    print("\n" + "="*70)
    print("DEMO 4: Real AI Provider Call")
    print("="*70)

    bus = AsyncMessageBus()

    try:
        await bus.start()

        # Check which providers are registered
        if bus.providers:
            print(f"\n[OK] {len(bus.providers)} AI provider(s) registered:")
            for provider_name in bus.providers.keys():
                print(f"  - {provider_name}")

            print("\nNote: To make real AI calls, add API keys to .env file:")
            print("  OPENAI_API_KEY=your-key-here")
            print("  ANTHROPIC_API_KEY=your-key-here")
            print("  # etc...")

            # Try a simple call if provider available
            if bus.providers:
                provider_name = list(bus.providers.keys())[0]
                print(f"\nAttempting call to {provider_name}...")

                try:
                    response = await bus.send_message(
                        content="Say 'hello' in exactly 3 words",
                        provider_name=provider_name,
                        conversation_id="demo"
                    )
                    print(f"[OK] Response: {response}")
                except Exception as e:
                    print(f"[FAIL] Call failed (expected if no API key): {e}")

        else:
            print("\n[WARN] No AI providers registered")
            print("  Add API keys to .env file to enable providers")

    finally:
        await bus.stop()


async def demo_performance_tracking():
    """Demonstrate performance tracking capabilities"""
    print("\n" + "="*70)
    print("DEMO 5: Performance Tracking")
    print("="*70)

    print("\n[OK] Performance metrics tracked:")
    print("  - Response time per request (seconds)")
    print("  - Rate limiter statistics (requests/min/hour/day)")
    print("  - Conversation history size")
    print("  - Provider availability")
    print("  - Retry attempts and success rate")

    print("\nPerformance data is logged to:")
    print("  - Console (INFO level)")
    print("  - ai_framework.log file")
    print("  - SQLite database (message timestamps)")


async def run_all_demos():
    """Run all enhancement demos"""
    print("\n" + "="*70)
    print("ZEJZL.NET - Phase 3 Enhancement Demos")
    print("="*70)

    await demo_rate_limiting()
    await demo_retry_logic()
    await demo_conversation_pruning()
    await demo_real_ai_call()
    await demo_performance_tracking()

    print("\n" + "="*70)
    print("All Demos Complete!")
    print("="*70)

    print("\nPhase 3 Enhancements Summary:")
    print("  [OK] Rate limiting (prevents API quota exhaustion)")
    print("  [OK] Retry logic (handles transient failures)")
    print("  [OK] Conversation pruning (maintains 100-message limit)")
    print("  [OK] Performance tracking (logs metrics)")
    print("  [OK] Real AI integration (ready with API keys)")


async def interactive_mode():
    """Interactive mode to test with real AI"""
    print("\n" + "="*70)
    print("ZEJZL.NET - Interactive AI Testing")
    print("="*70)

    bus = AsyncMessageBus()

    try:
        await bus.start()

        if not bus.providers:
            print("\n[WARN] No AI providers available. Add API keys to .env file.")
            print("Example .env:")
            print("  OPENAI_API_KEY=sk-...")
            print("  ANTHROPIC_API_KEY=sk-ant-...")
            return

        providers = list(bus.providers.keys())
        print(f"\nAvailable providers: {', '.join(providers)}")
        print("Type 'quit' to exit\n")

        while True:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            try:
                # Use first available provider
                response = await bus.send_message(
                    content=user_input,
                    provider_name=providers[0],
                    conversation_id="interactive"
                )
                print(f"AI: {response}\n")

            except Exception as e:
                print(f"Error: {e}\n")

    finally:
        await bus.stop()
        print("\nGoodbye!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(run_all_demos())
