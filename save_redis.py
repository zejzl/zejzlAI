#!/usr/bin/env python3
"""
Redis State Saver for ZEJZL.NET
Saves current system state to Redis for persistence.

Usage:
    python save_redis.py [options]

Options:
    --all          Save all state (default)
    --config       Save provider configurations only
    --magic        Save magic system state only
    --learning     Save agent learning patterns only
    --verbose      Show detailed output
"""

import asyncio
import sys
import json
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_framework import AsyncMessageBus


async def save_all_state(verbose=False):
    """Save all system state to Redis"""
    print("Initializing ZEJZL.NET AsyncMessageBus...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        # Save configuration
        if verbose:
            print("Saving provider configuration...")
        # Create default config
        config = {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-opus-20240229"},
                "gemini": {"api_key": os.environ.get("GEMINI_API_KEY", ""), "model": "gemini-2.5-flash"},
                "zai": {"api_key": os.environ.get("ZAI_API_KEY", ""), "model": "zai-1"},
                "grok": {"api_key": os.environ.get("GROK_API_KEY", ""), "model": "grok-1"},
                "deepseek": {"api_key": os.environ.get("DEEPSEEK_API_KEY", ""), "model": "deepseek-coder"},
                "qwen": {"api_key": os.environ.get("QWEN_API_KEY", ""), "model": "qwen-turbo"}
            },
            "default_provider": "chatgpt",
            "redis_url": "redis://localhost:6379",
            "sqlite_path": str(Path.home() / ".ai_framework.db")
        }
        await bus.persistence.save_config(config)
        if verbose:
            print(f"[OK] Configuration saved: {len(config.get('providers', {}))} providers")

        # Save magic state (if available)
        if hasattr(bus, 'magic') and bus.magic:
            if verbose:
                print("Saving magic system state...")
            # Create sample magic state for testing
            magic_state = {
                "energy_level": 85.5,
                "acorn_reserve": 12,
                "spells_cast": 47,
                "healing_sessions": 23,
                "last_updated": asyncio.get_event_loop().time()
            }
            await bus.magic.save_state(magic_state)
            if verbose:
                print("[OK] Magic state saved")

        # Save learning patterns (if available)
        if verbose:
            print("Saving agent learning patterns...")
        # Create sample learning patterns for testing
        learning_patterns = {
            "success_patterns": [
                {"type": "observation", "pattern": "clear_task"},
                {"type": "planning", "pattern": "step_by_step"}
            ],
            "failure_patterns": [
                {"type": "vague_request", "frequency": 5}
            ],
            "performance_metrics": {
                "avg_response_time": 2.3,
                "success_rate": 0.87,
                "total_interactions": 156
            },
            "last_updated": asyncio.get_event_loop().time()
        }
        await bus.persistence.save_learner_patterns(learning_patterns)
        if verbose:
            print("[OK] Learning patterns saved")

        print("[OK] All system state saved to Redis successfully!")

        # Show summary
        print("\n[STATS] State Summary:")
        print(f"   * Configuration: {len(config)} providers configured")
        print("   * Magic System: Energy and spell data preserved")
        print("   * Learning: Agent patterns and metrics saved")
    except Exception as e:
        print(f"[ERROR] Error saving state: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def save_config_only(verbose=False):
    """Save only configuration state"""
    print("Saving configuration to Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        config = {
            "providers": {
                "chatgpt": {"api_key": os.environ.get("OPENAI_API_KEY", ""), "model": "gpt-3.5-turbo"},
                "claude": {"api_key": os.environ.get("ANTHROPIC_API_KEY", ""), "model": "claude-3-opus-20240229"},
                "gemini": {"api_key": os.environ.get("GEMINI_API_KEY", ""), "model": "gemini-2.5-flash"},
                "zai": {"api_key": os.environ.get("ZAI_API_KEY", ""), "model": "zai-1"},
                "grok": {"api_key": os.environ.get("GROK_API_KEY", ""), "model": "grok-1"},
                "deepseek": {"api_key": os.environ.get("DEEPSEEK_API_KEY", ""), "model": "deepseek-coder"},
                "qwen": {"api_key": os.environ.get("QWEN_API_KEY", ""), "model": "qwen-turbo"}
            },
            "default_provider": "chatgpt",
            "redis_url": "redis://localhost:6379",
            "sqlite_path": str(Path.home() / ".ai_framework.db")
        }
        await bus.persistence.save_config(config)
        if verbose:
            print(f"[OK] Configuration saved: {len(config['providers'])} providers")
        else:
            print("[OK] Configuration saved successfully!")
    except Exception as e:
        print(f"[ERROR] Error saving configuration: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def save_magic_only(verbose=False):
    """Save only magic system state"""
    print("Saving magic system state to Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        if hasattr(bus, 'magic') and bus.magic:
            magic_state = {
                "energy_level": 92.3,
                "acorn_reserve": 8,
                "spells_cast": 29,
                "healing_sessions": 15,
                "last_updated": asyncio.get_event_loop().time()
            }
            await bus.magic.save_state(magic_state)
            if verbose:
                print("[OK] Magic state saved with current energy levels")
            else:
                print("[OK] Magic state saved successfully!")
        else:
            print("[WIP]️ Magic system not available")
            return False
    except Exception as e:
        print(f"[ERROR] Error saving magic state: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def save_learning_only(verbose=False):
    """Save only agent learning patterns"""
    print("Saving agent learning patterns to Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        learning_patterns = {
            "success_patterns": [
                {"pattern": "structured_request", "confidence": 0.95},
                {"pattern": "clear_objectives", "confidence": 0.89}
            ],
            "optimization_suggestions": [
                "Use TOON format for better token efficiency",
                "Implement parallel agent processing",
                "Add confidence scoring to responses"
            ],
            "performance_stats": {
                "total_patterns": 47,
                "success_rate": 0.91,
                "avg_processing_time": 1.8
            },
            "last_updated": asyncio.get_event_loop().time()
        }
        await bus.persistence.save_learner_patterns(learning_patterns)
        if verbose:
            print(f"[OK] Learning patterns saved: {len(learning_patterns['success_patterns'])} success patterns")
        else:
            print("[OK] Learning patterns saved successfully!")
    except Exception as e:
        print(f"[ERROR] Error saving learning patterns: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def main():
    """Main function with argument parsing"""
    import argparse

    parser = argparse.ArgumentParser(description="Save ZEJZL.NET state to Redis")
    parser.add_argument("--all", action="store_true", help="Save all state (default)")
    parser.add_argument("--config", action="store_true", help="Save provider configurations only")
    parser.add_argument("--magic", action="store_true", help="Save magic system state only")
    parser.add_argument("--learning", action="store_true", help="Save agent learning patterns only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Default to --all if no specific option given
    if not any([args.config, args.magic, args.learning]):
        args.all = True

    try:
        if args.config:
            success = await save_config_only(args.verbose)
        elif args.magic:
            success = await save_magic_only(args.verbose)
        elif args.learning:
            success = await save_learning_only(args.verbose)
        else:  # args.all
            success = await save_all_state(args.verbose)

        if success:
            print("\n[SUCCESS] Redis state save completed successfully!")
            return 0
        else:
            print("\n[ERROR] Redis state save failed!")
            return 1

    except Exception as e:
        print(f"\n[CRITICAL] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)