import asyncio
from src.advanced_healing import AdvancedHealingSystem, ComponentType, HealingStrategy

async def test_advanced_healing():
    """Test the advanced healing system"""
    print("[TEST] Testing Advanced Healing System (Phase 8)")

    # Create healing system
    healing = AdvancedHealingSystem()
    print("[OK] Advanced healing system initialized")

    # Test component healing
    test_error = Exception("Connection timeout")

    print("\n[FIX] Testing AI Provider healing...")
    success = await healing.heal_component(
        "test_claude_provider",
        ComponentType.AI_PROVIDER,
        test_error,
        {"endpoint": "api.anthropic.com"}
    )
    print(f"AI Provider healing result: {'[OK] SUCCESS' if success else '[FAILED] FAILED'}")

    print("\n[FIX] Testing Database healing...")
    db_error = Exception("Connection refused")
    success = await healing.heal_component(
        "test_sqlite_db",
        ComponentType.DATABASE,
        db_error,
        {"db_path": "/tmp/test.db"}
    )
    print(f"Database healing result: {'[OK] SUCCESS' if success else '[FAILED] FAILED'}")

    print("\n[FIX] Testing Network healing...")
    net_error = Exception("DNS resolution failed")
    success = await healing.heal_component(
        "test_network",
        ComponentType.NETWORK,
        net_error,
        {"host": "api.example.com"}
    )
    print(f"Network healing result: {'[OK] SUCCESS' if success else '[FAILED] FAILED'}")

    # Test analytics
    print("\n[STATS] Healing Analytics:")
    analytics = healing.get_healing_analytics()
    print(f"Total healing attempts: {analytics['total_healing_attempts']}")
    print(f"Overall success rate: {analytics['overall_success_rate']:.1%}")
    print(f"Active failure patterns: {analytics['active_failure_patterns']}")
    print(f"Component health tracking: {len(analytics['component_health'])} components")

    print("\n[COMPLETE] Advanced Healing System test completed!")

if __name__ == "__main__":
    asyncio.run(test_advanced_healing())