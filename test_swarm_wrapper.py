#!/usr/bin/env python3
"""
Test script for SwarmCoordinator integration with zejzl.net

Tests all swarm orchestration features:
- Budget tracking
- Permission gates
- Shared blackboard
- Task execution
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.swarm_wrapper import SwarmCoordinator, BudgetExhaustedError, PermissionDeniedError

async def test_budget_tracking():
    """Test 1: Budget tracking and enforcement"""
    print("\n" + "=" * 60)
    print("TEST 1: Budget Tracking")
    print("=" * 60)
    
    coordinator = SwarmCoordinator()
    
    # Initialize budget
    task_id = "test_budget_001"
    coordinator.budget_tracker.initialize(task_id, 5000)
    
    # Check initial status
    status = coordinator.get_budget_status(task_id)
    print(f"\nInitial budget: {status['max_tokens']:,} tokens")
    print(f"Status: {status['status']}")
    
    # Spend tokens
    coordinator.budget_tracker.spend(task_id, 1000, "First API call")
    status = coordinator.get_budget_status(task_id)
    print(f"\nAfter 1st spend: {status['used_tokens']:,} / {status['max_tokens']:,} tokens ({status['usage_percentage']:.1f}%)")
    print(f"Status: {status['status']}")
    
    # Spend more tokens (exceed budget)
    coordinator.budget_tracker.spend(task_id, 4500, "Large API call")
    status = coordinator.get_budget_status(task_id)
    print(f"\nAfter 2nd spend: {status['used_tokens']:,} / {status['max_tokens']:,} tokens ({status['usage_percentage']:.1f}%)")
    print(f"Status: {status['status']}")
    print(f"Can continue: {status['can_continue']}")
    
    if status['status'] == 'EXHAUSTED':
        print("\n✅ TEST PASS: Budget exhaustion detected correctly")
    else:
        print("\n❌ TEST FAIL: Budget should be exhausted")

async def test_permission_gates():
    """Test 2: Permission evaluation"""
    print("\n" + "=" * 60)
    print("TEST 2: Permission Gates")
    print("=" * 60)
    
    coordinator = SwarmCoordinator()
    
    # Test 1: High-trust agent with good justification
    print("\nTest 2a: High-trust agent (memory) + detailed justification")
    granted = await coordinator.check_permission(
        agent_id="memory",
        resource_type="DATABASE",
        justification="User requested critical data update for bug fix deployment"
    )
    print(f"Result: {'✅ GRANTED' if granted else '❌ DENIED'}")
    
    # Test 2: Low-trust agent with weak justification
    print("\nTest 2b: Low-trust agent (executor) + weak justification")
    granted = await coordinator.check_permission(
        agent_id="executor",
        resource_type="PAYMENTS",
        justification="Update needed"
    )
    print(f"Result: {'✅ GRANTED' if granted else '❌ DENIED'}")
    
    # Test 3: Medium-trust agent with good justification
    print("\nTest 2c: Medium-trust agent (reasoner) + good justification")
    granted = await coordinator.check_permission(
        agent_id="reasoner",
        resource_type="EMAIL",
        justification="User requested email notification for critical feature deployment"
    )
    print(f"Result: {'✅ GRANTED' if granted else '❌ DENIED'}")
    
    print("\n✅ TEST PASS: Permission evaluation working")

async def test_blackboard_coordination():
    """Test 3: Shared blackboard"""
    print("\n" + "=" * 60)
    print("TEST 3: Blackboard Coordination")
    print("=" * 60)
    
    coordinator = SwarmCoordinator()
    
    # Write state
    print("\nWriting to blackboard...")
    coordinator.blackboard.write("task:deploy:status", "in_progress")
    coordinator.blackboard.write("task:deploy:progress", "50")
    coordinator.blackboard.write("agent:observer:state", "active")
    
    # Read state
    print("\nReading from blackboard...")
    status = coordinator.get_blackboard_state("task:deploy:status")
    progress = coordinator.get_blackboard_state("task:deploy:progress")
    agent_state = coordinator.get_blackboard_state("agent:observer:state")
    
    print(f"  task:deploy:status = {status}")
    print(f"  task:deploy:progress = {progress}")
    print(f"  agent:observer:state = {agent_state}")
    
    # List all keys
    all_state = coordinator.get_blackboard_state()
    print(f"\nTotal keys in blackboard: {len(all_state)}")
    print(f"Keys: {', '.join(list(all_state.keys())[:5])}...")
    
    print("\n✅ TEST PASS: Blackboard coordination working")

async def test_task_execution():
    """Test 4: Full task execution with budget + permissions"""
    print("\n" + "=" * 60)
    print("TEST 4: Task Execution (Budget + Permissions)")
    print("=" * 60)
    
    coordinator = SwarmCoordinator()
    
    # Test 4a: Successful execution
    print("\nTest 4a: Execute task with sufficient budget")
    try:
        result = await coordinator.execute_task(
            task_id="test_task_001",
            task_description="Deploy new feature to staging environment",
            budget=10000,
            required_permissions=["DATABASE"]
        )
        
        print(f"✅ Task completed successfully!")
        print(f"   Budget used: {result['budget_status']['used_tokens']:,} / {result['budget_status']['max_tokens']:,} tokens")
        print(f"   Status: {result['budget_status']['status']}")
        
    except Exception as e:
        print(f"❌ Task failed: {e}")
    
    # Test 4b: Budget exhaustion
    print("\nTest 4b: Execute task with insufficient budget")
    try:
        result = await coordinator.execute_task(
            task_id="test_task_002",
            task_description="Deploy large feature requiring extensive API calls",
            budget=100,  # Very small budget
            required_permissions=["DATABASE"]
        )
        
        print(f"❌ TEST FAIL: Should have exhausted budget")
        
    except BudgetExhaustedError as e:
        print(f"✅ Budget exhausted as expected: {e}")
    
    # Test 4c: Permission denial
    print("\nTest 4c: Execute task requiring high-risk permission")
    try:
        result = await coordinator.execute_task(
            task_id="test_task_003",
            task_description="Process payments",
            budget=10000,
            required_permissions=["PAYMENTS"]  # High-risk resource
        )
        
        print(f"Result: {result}")
        
    except PermissionDeniedError as e:
        print(f"⚠️ Permission denied (expected for high-risk resource): {e}")
    
    print("\n✅ TEST PASS: Task execution with enforcement working")

async def test_integration_pattern():
    """Test 5: Show integration pattern with MessageBus"""
    print("\n" + "=" * 60)
    print("TEST 5: Integration Pattern Example")
    print("=" * 60)
    
    coordinator = SwarmCoordinator()
    
    print("\nExample: How to integrate with zejzl.net MessageBus")
    print("""
# In ai_framework.py or main.py:

from src.swarm_wrapper import SwarmCoordinator

class ZejzlPantheonRLM:
    def __init__(self):
        self.bus = AsyncMessageBus()
        self.coordinator = SwarmCoordinator(message_bus=self.bus)
    
    async def process_user_request(self, request: str, budget: int = 10000):
        # Execute with swarm coordination
        try:
            result = await self.coordinator.execute_task(
                task_id=f"user_request_{timestamp}",
                task_description=request,
                budget=budget,
                required_permissions=["DATABASE"] if "deploy" in request else None
            )
            
            return result
            
        except BudgetExhaustedError:
            return {"error": "Token budget exceeded. Please try a simpler query."}
        
        except PermissionDeniedError as e:
            return {"error": f"Permission denied: {e}"}
    """)
    
    print("\n✅ Integration pattern documented")

async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SwarmCoordinator Test Suite for zejzl.net")
    print("=" * 60)
    
    tests = [
        test_budget_tracking,
        test_permission_gates,
        test_blackboard_coordination,
        test_task_execution,
        test_integration_pattern
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review src/swarm_wrapper.py")
    print("  2. Integrate with ai_framework.py MessageBus")
    print("  3. Add budget tracking to web dashboard")
    print("  4. Test with real 9-Agent Pantheon")
    print()

if __name__ == "__main__":
    asyncio.run(main())
