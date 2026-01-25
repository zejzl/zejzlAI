#!/usr/bin/env python3
"""
Test ORAM (Observer-Reasoner-Actor + Memory) iterative processing system
"""
import asyncio
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ORAM_Test")

async def test_oram():
    """Test ORAM system functionality."""
    try:
        from src.oram import ORAMSystem, ORAMIterationType, ORAMConfig, execute_oram
        
        print("[TEST] Starting ORAM system tests")
        
        # Test 1: Basic ORAM functionality
        print("\n[TEST 1] Basic ORAM iteration")
        config = ORAMConfig()
        config.max_iterations = 3  # Short test
        
        oram = ORAMSystem(config)
        
        # Simple test task
        iterations = await oram.execute_oram_loop(
            "Analyze the benefits of iterative processing",
            ORAMIterationType.BASIC
        )
        
        print(f"[OK] Basic test complete: {len(iterations)} iterations")
        
        # Test 2: Convenience function
        print("\n[TEST 2] Convenience function")
        quick_iterations = await execute_oram(
            "Test task for convenience function",
            ORAMIterationType.DEEP_ANALYSIS,
            max_iterations=2
        )
        
        print(f"[OK] Convenience function test complete: {len(quick_iterations)} iterations")
        
        # Test 3: Status and insights
        print("\n[TEST 3] Status and insights")
        status = oram.get_status()
        insights = oram.get_insights()
        
        print(f"[OK] Status retrieved: {status}")
        print(f"[OK] Insights retrieved: {len(insights)} insights")
        
        # Show summary
        if iterations:
            best_iteration = max(iterations, key=lambda x: x.quality_score)
            print(f"\n[SUMMARY]")
            print(f"  Total iterations: {len(iterations)}")
            print(f"  Best quality score: {best_iteration.quality_score:.3f}")
            print(f"  Convergence achieved: {best_iteration.quality_score >= config.convergence_threshold}")
            print(f"  Total insights generated: {len(insights)}")
            
            if insights:
                print(f"\n[TOP INSIGHTS]")
                for i, insight in enumerate(insights[:3], 1):
                    print(f"  {i}. {insight}")
        
        print("\n[SUCCESS] ORAM system tests completed successfully!")
        
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False
    
    return True

async def test_oram_integration():
    """Test ORAM integration with existing agents."""
    try:
        print("\n[TEST 4] ORAM agent integration")
        
        # Test that ORAM can access existing agents
        from src.oram import ORAMSystem
        from src.agents.observer import ObserverAgent
        from src.agents.reasoner import ReasonerAgent
        from src.agents.actor import ActorAgent
        from src.agents.memory import MemoryAgent
        
        # Verify agents can be instantiated
        observer = ObserverAgent()
        reasoner = ReasonerAgent()
        actor = ActorAgent()
        memory = MemoryAgent()
        
        print("[OK] All agents instantiated successfully")
        
        # Test ORAM with these agents
        from src.oram import ORAMConfig
        config = ORAMConfig()
        config.max_iterations = 2
        
        oram = ORAMSystem(config)
        
        # Simple iteration test
        iterations = await oram.execute_oram_loop(
            "Test agent integration",
            ORAMIterationType.BASIC
        )
        
        print(f"[OK] Integration test complete: {len(iterations)} iterations")
        return True
        
    except Exception as e:
        print(f"[ERROR] Integration test failed: {e}")
        return False

async def main():
    """Run all ORAM tests."""
    print("=" * 60)
    print("ORAM SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Run tests
    test1_passed = await test_oram()
    test2_passed = await test_oram_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Basic ORAM Functionality", test1_passed),
        ("Agent Integration", test2_passed)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("[SUCCESS] All ORAM tests passed! System ready for use.")
    else:
        print("[WARNING] Some tests failed. Check implementation.")
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())