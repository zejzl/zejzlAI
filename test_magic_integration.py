#!/usr/bin/env python3
"""
Test script for magic system integration with ZEJZL.NET
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_framework import AsyncMessageBus

async def test_magic_integration():
    """Test magic system integration with message bus"""
    print("Testing Magic System Integration with ZEJZL.NET")
    print("=" * 60)

    # Initialize message bus
    bus = AsyncMessageBus()

    try:
        # Start the bus
        await bus.start()
        print("+ Message bus started with magic system")

        # Test magic system status
        magic_status = await bus.magic.get_system_status()
        print("\nMagic System Status:")
        print(f"  Energy Level: {magic_status['energy_level']}%")
        print(f"  Acorn Reserve: {magic_status['acorn_reserve']}")
        print(f"  Fairy Shield: {magic_status['is_shielded']}")
        print(f"  Circuit Breakers: {len(magic_status['circuit_breakers'])} active")

        # Test vitality boost
        print("\nTesting Acorn Vitality Boost...")
        boost = await bus.magic.acorn_vitality_boost("test_agent", {"max_tokens": 1024})
        print(f"  Boost Factor: {boost['vitality_boost']:.2f}x")
        print(f"  New Max Tokens: {boost['new_config']['max_tokens']}")

        # Test fairy shield
        print("\nTesting Fairy Shield...")
        shield_activated = await bus.magic.fairy_shield(True)
        print(f"  Shield Activated: {shield_activated}")

        # Test blue spark healing
        print("\nTesting Blue Spark Healing...")
        healed = await bus.magic.blue_spark_heal("test_component", "simulated_error")
        print(f"  Healing Successful: {healed}")

        # Test ritual
        print("\nTesting Magical Rituals...")
        ritual_result = await bus.magic.perform_ritual("holly_blessing")
        print(f"  Ritual Result: {ritual_result}")

        # Test circuit breaker status
        print("\nTesting Circuit Breaker Status...")
        cb_status = await bus.magic.get_circuit_breaker_status("ai_provider")
        print(f"  AI Provider Circuit Breaker: {cb_status['state']}")

        # Final status
        final_status = await bus.magic.get_system_status()
        print("\nFinal Magic System Status:")
        print(f"  Energy Level: {final_status['energy_level']}%")
        print(f"  Healing History: {final_status['healing_history_count']} records")
        print(f"  Learning Preferences: {final_status['learning_preferences_count']} patterns")

        print("\nMagic system integration test completed successfully!")
        print("The self-healing system with circuit breakers is now active in ZEJZL.NET!")

    except Exception as e:
        print(f"ERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await bus.stop()

if __name__ == "__main__":
    asyncio.run(test_magic_integration())