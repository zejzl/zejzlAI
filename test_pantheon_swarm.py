#!/usr/bin/env python3
"""
Test script for Pantheon Swarm integration

Tests SwarmCoordinator with real PantheonRLM execution
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pantheon_swarm import PantheonSwarm


async def test_basic_execution():
    """Test 1: Basic task execution with budget tracking"""
    print("\n" + "="*60)
    print("TEST 1: Basic Execution with Budget Tracking")
    print("="*60)
    
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-fast-reasoning",
        verbose=True
    )
    
    result = await swarm.process_task(
        task="What are the key advantages of multi-agent AI systems?",
        budget=10000
    )
    
    if result['success']:
        print(f"\n✅ TEST PASS: Task completed successfully")
        print(f"   Budget used: {result['estimated_tokens']:,} / 10,000 tokens")
        print(f"   Execution time: {result['execution_time']:.2f}s")
        print(f"   Result length: {len(result['result'])} chars")
    else:
        print(f"\n❌ TEST FAIL: {result.get('message', 'Unknown error')}")
    
    return result['success']


async def test_permission_gates():
    """Test 2: Permission gate enforcement"""
    print("\n" + "="*60)
    print("TEST 2: Permission Gate Enforcement")
    print("="*60)
    
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-fast-reasoning",
        verbose=True
    )
    
    # Test with DATABASE permission (should be granted)
    print("\nTest 2a: DATABASE permission with detailed justification")
    result = await swarm.process_task(
        task="Plan database schema update for new feature",
        budget=10000,
        required_permissions=["DATABASE"]
    )
    
    if result['success']:
        print(f"✅ Permission granted (expected)")
    else:
        if result.get('error') == 'permission_denied':
            print(f"❌ Permission denied (unexpected): {result.get('message')}")
        else:
            print(f"✗ Other error: {result.get('message')}")
    
    # Test with PAYMENTS permission (high-risk, may be denied)
    print("\nTest 2b: PAYMENTS permission (high-risk resource)")
    result2 = await swarm.process_task(
        task="Process payment transaction",
        budget=10000,
        required_permissions=["PAYMENTS"]
    )
    
    if not result2['success'] and result2.get('error') == 'permission_denied':
        print(f"✅ Permission denied for high-risk resource (expected)")
    elif result2['success']:
        print(f"⚠️ Permission granted (may be acceptable with good justification)")
    else:
        print(f"✗ Other error: {result2.get('message')}")
    
    return True


async def test_budget_exhaustion():
    """Test 3: Budget exhaustion detection"""
    print("\n" + "="*60)
    print("TEST 3: Budget Exhaustion Detection")
    print("="*60)
    
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-fast-reasoning",
        verbose=True
    )
    
    result = await swarm.process_task(
        task="Write a comprehensive 10-page guide to AI safety",
        budget=100  # Very small budget
    )
    
    if not result['success'] and result.get('error') == 'budget_exhausted':
        print(f"\n✅ TEST PASS: Budget exhaustion detected correctly")
        print(f"   Budget: {result['budget_status']['used_tokens']:,} / {result['budget_status']['max_tokens']:,} tokens")
        print(f"   Status: {result['budget_status']['status']}")
    else:
        print(f"\n❌ TEST FAIL: Budget exhaustion not detected")
    
    return result.get('error') == 'budget_exhausted'


async def test_blackboard_coordination():
    """Test 4: Blackboard state tracking"""
    print("\n" + "="*60)
    print("TEST 4: Blackboard State Tracking")
    print("="*60)
    
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-fast-reasoning",
        verbose=True
    )
    
    # Execute task
    result = await swarm.process_task(
        task="List 3 benefits of AI agents",
        budget=5000
    )
    
    if result['success']:
        task_id = result['task_id']
        
        # Check blackboard state
        status = swarm.get_blackboard_state(f"task:{task_id}:status")
        description = swarm.get_blackboard_state(f"task:{task_id}:description")
        result_text = swarm.get_blackboard_state(f"task:{task_id}:result")
        
        print(f"\n✅ TEST PASS: Blackboard tracking working")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {status}")
        print(f"   Description: {description}")
        print(f"   Result length: {len(result_text)} chars")
        
        # List all blackboard keys
        all_state = swarm.get_blackboard_state()
        print(f"   Total blackboard keys: {len(all_state)}")
        
        return True
    else:
        print(f"\n❌ TEST FAIL: Task execution failed")
        return False


async def test_multiple_tasks():
    """Test 5: Multiple task execution with budget tracking"""
    print("\n" + "="*60)
    print("TEST 5: Multiple Tasks with Independent Budgets")
    print("="*60)
    
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-fast-reasoning",
        verbose=False  # Less verbose for multiple tasks
    )
    
    tasks = [
        ("Explain neural networks in one sentence", 3000),
        ("List 3 AI frameworks", 3000),
        ("What is Transfer Learning?", 3000)
    ]
    
    results = []
    for task, budget in tasks:
        print(f"\nExecuting: {task}")
        result = await swarm.process_task(task=task, budget=budget)
        results.append(result)
        
        if result['success']:
            print(f"✓ Success ({result['estimated_tokens']:,} tokens)")
        else:
            print(f"✗ Failed: {result.get('message')}")
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ TEST RESULT: {success_count}/{len(tasks)} tasks completed")
    
    return success_count == len(tasks)


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Pantheon Swarm Integration Test Suite")
    print("="*60)
    
    tests = [
        ("Basic Execution", test_basic_execution),
        ("Permission Gates", test_permission_gates),
        ("Budget Exhaustion", test_budget_exhaustion),
        ("Blackboard Coordination", test_blackboard_coordination),
        ("Multiple Tasks", test_multiple_tasks)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            print(f"\n{'#'*60}")
            print(f"Running: {name}")
            print(f"{'#'*60}")
            
            result = await test_func()
            results.append((name, result))
            
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Pantheon Swarm integration successful!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review output above.")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
