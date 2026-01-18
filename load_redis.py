#!/usr/bin/env python3
"""
Redis State Loader for ZEJZL.NET
Loads and displays current system state from Redis.

Usage:
    python load_redis.py [options]

Options:
    --all          Load and display all state (default)
    --config       Load provider configurations only
    --magic        Load magic system state only
    --learning     Load agent learning patterns only
    --json         Output in JSON format instead of formatted text
    --verbose      Show detailed output
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_framework import AsyncMessageBus


def format_json_output(data, title=""):
    """Format data as readable JSON"""
    if title:
        print(f"\n{title}")
        print("=" * len(title))

    if isinstance(data, dict):
        # Pretty print with sorted keys
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, indent=2))


def format_text_output(data, title="", indent=0):
    """Format data as readable text"""
    indent_str = "  " * indent

    if title:
        print(f"\n{title}")
        print("=" * len(title))

    if isinstance(data, dict):
        for key, value in sorted(data.items()):
            if isinstance(value, (dict, list)):
                print(f"{indent_str}{key}:")
                format_text_output(value, indent=indent+1)
            else:
                print(f"{indent_str}{key}: {value}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                print(f"{indent_str}[{i}]:")
                format_text_output(item, indent=indent+1)
            else:
                print(f"{indent_str}[{i}]: {item}")
    else:
        print(f"{indent_str}{data}")


async def load_all_state(json_output=False, verbose=False):
    """Load and display all system state from Redis"""
    print("Loading ZEJZL.NET state from Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        state_loaded = []

        # Load configuration
        if verbose:
            print("Loading provider configuration...")
        try:
            config = await bus.load_config()
            if config:
                state_loaded.append("config")
                if json_output:
                    format_json_output(config, "Provider Configuration")
                else:
                    print("\n[CONFIG] Provider Configuration:")
                    print(f"   • Total providers: {len(config.get('providers', {}))}")
                    for provider_name, provider_config in config.get('providers', {}).items():
                        api_key_status = "[OK] Configured" if provider_config.get('api_key') else "[NOT SET] Not configured"
                        model = provider_config.get('model', 'default')
                        print(f"   • {provider_name}: {model} - {api_key_status}")
            else:
                print("   [WARNING] No configuration found")
        except Exception as e:
            print(f"   [ERROR] Error loading configuration: {e}")

        # Load magic state
        if verbose:
            print("Loading magic system state...")
        try:
            # Try to load magic state from persistence
            magic_key = "zejzl:magic_state"
            magic_data = await bus.redis.get(magic_key) if bus.redis else None

            if magic_data:
                magic_state = json.loads(magic_data)
                state_loaded.append("magic")
                if json_output:
                    format_json_output(magic_state, "Magic System State")
                else:
                    print("\n[MAGIC] Magic System State:")
                    energy = magic_state.get('energy_level', 'Unknown')
                    acorns = magic_state.get('acorn_reserve', 'Unknown')
                    spells = magic_state.get('spells_cast', 'Unknown')
                    healings = magic_state.get('healing_sessions', 'Unknown')
                    print(f"   • Energy Level: {energy}%")
                    print(f"   • Acorn Reserve: {acorns}")
                    print(f"   • Spells Cast: {spells}")
                    print(f"   • Healing Sessions: {healings}")
            else:
                print("   [WARNING] No magic state found")
        except Exception as e:
            print(f"   [ERROR] Error loading magic state: {e}")

        # Load learning patterns
        if verbose:
            print("Loading agent learning patterns...")
        try:
            learning_patterns = await bus.persistence.load_learner_patterns()
            if learning_patterns:
                state_loaded.append("learning")
                if json_output:
                    format_json_output(learning_patterns, "Agent Learning Patterns")
                else:
                    print("\n[LEARNING] Agent Learning Patterns:")
                    success_patterns = learning_patterns.get('success_patterns', [])
                    failure_patterns = learning_patterns.get('failure_patterns', [])
                    suggestions = learning_patterns.get('optimization_suggestions', [])
                    stats = learning_patterns.get('performance_stats', {})

                    print(f"   • Success Patterns: {len(success_patterns)}")
                    print(f"   • Failure Patterns: {len(failure_patterns)}")
                    print(f"   • Optimization Suggestions: {len(suggestions)}")
                    print(f"   • Total Patterns Analyzed: {stats.get('total_patterns', 'Unknown')}")
                    print(f"   • Success Rate: {stats.get('success_rate', 'Unknown')}")
            else:
                print("   [WARNING] No learning patterns found")
        except Exception as e:
            print(f"   [ERROR] Error loading learning patterns: {e}")

        # Summary
        if state_loaded:
            print(f"\n[SUCCESS] Successfully loaded: {', '.join(state_loaded)}")
        else:
            print("\n[WARNING] No state data found in Redis")

    except Exception as e:
        print(f"[ERROR] Error loading state: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def load_config_only(json_output=False, verbose=False):
    """Load and display configuration only"""
    print("Loading configuration from Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        config = await bus.load_config()
        if config:
            if json_output:
                format_json_output(config, "Provider Configuration")
            else:
                print("[SUCCESS] Configuration loaded successfully!")
                print(f"   • Default provider: {config.get('default_provider', 'Unknown')}")
                print(f"   • Total providers: {len(config.get('providers', {}))}")
                for provider_name, provider_config in config.get('providers', {}).items():
                    status = "[OK] Configured" if provider_config.get('api_key') else "[NOT SET] Not configured"
                    print(f"   • {provider_name}: {status}")
        else:
            print("[WARNING] No configuration found")
            return False
    except Exception as e:
        print(f"[ERROR] Error loading configuration: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def load_magic_only(json_output=False, verbose=False):
    """Load and display magic state only"""
    print("Loading magic system state from Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        magic_key = "zejzl:magic_state"
        magic_data = await bus.redis.get(magic_key) if bus.redis else None

        if magic_data:
            magic_state = json.loads(magic_data)
            if json_output:
                format_json_output(magic_state, "Magic System State")
            else:
                print("[SUCCESS] Magic state loaded successfully!")
                format_text_output(magic_state, "Magic System Details")
        else:
            print("[WARNING] No magic state found")
            return False
    except Exception as e:
        print(f"[ERROR] Error loading magic state: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def load_learning_only(json_output=False, verbose=False):
    """Load and display learning patterns only"""
    print("Loading agent learning patterns from Redis...")

    bus = AsyncMessageBus()
    await bus.start()

    try:
        learning_patterns = await bus.persistence.load_learner_patterns()
        if learning_patterns:
            if json_output:
                format_json_output(learning_patterns, "Agent Learning Patterns")
            else:
                print("[SUCCESS] Learning patterns loaded successfully!")
                format_text_output(learning_patterns, "Learning Patterns Details")
        else:
            print("[WARNING] No learning patterns found")
            return False
    except Exception as e:
        print(f"[ERROR] Error loading learning patterns: {e}")
        return False
    finally:
        await bus.stop()

    return True


async def main():
    """Main function with argument parsing"""
    import argparse

    parser = argparse.ArgumentParser(description="Load ZEJZL.NET state from Redis")
    parser.add_argument("--all", action="store_true", help="Load all state (default)")
    parser.add_argument("--config", action="store_true", help="Load provider configurations only")
    parser.add_argument("--magic", action="store_true", help="Load magic system state only")
    parser.add_argument("--learning", action="store_true", help="Load agent learning patterns only")
    parser.add_argument("--json", action="store_true", help="Output in JSON format instead of formatted text")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    # Default to --all if no specific option given
    if not any([args.config, args.magic, args.learning]):
        args.all = True

    try:
        if args.config:
            success = await load_config_only(args.json, args.verbose)
        elif args.magic:
            success = await load_magic_only(args.json, args.verbose)
        elif args.learning:
            success = await load_learning_only(args.json, args.verbose)
        else:  # args.all
            success = await load_all_state(args.json, args.verbose)

        if success:
            print("\n[SUCCESS] Redis state load completed successfully!")
            return 0
        else:
            print("\n[ERROR] Redis state load failed!")
            return 1

    except Exception as e:
        print(f"\n[CRITICAL] Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)