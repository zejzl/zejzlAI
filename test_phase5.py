#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 5 features:
- Learning Loop
- Improvement Applicator
- Consensus Agents
- Profiling System
- Security System
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 70)
print("ZEJZL.NET Phase 5 Feature Testing")
print("=" * 70)
print()

# Test 1: Learning Loop
print("[TEST 1] Learning Loop System")
print("-" * 70)
try:
    from src.learning_loop import LearningLoop, LearningCycle, LearningPhase

    async def test_learning_loop():
        loop = LearningLoop(cycle_interval_seconds=60)

        # Test cycle creation
        cycle = LearningCycle(
            cycle_id="test-cycle-1",
            start_time=asyncio.get_event_loop().time()
        )

        print(f"✓ Learning cycle created: {cycle.cycle_id}")
        print(f"  Phase: {cycle.phase.value}")

        # Test phase progression
        cycle.complete_phase({"metric": "test"})
        print(f"✓ Phase progressed to: {cycle.phase.value}")

        return True

    result = asyncio.run(test_learning_loop())
    print("[OK] Learning Loop: Working")

except Exception as e:
    print(f"[FAIL] Learning Loop: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Improvement Applicator
print("[TEST 2] Improvement Applicator")
print("-" * 70)
try:
    from src.improvement_applicator import ImprovementApplicator, ImprovementType

    async def test_improvement_applicator():
        applicator = ImprovementApplicator()

        # Test suggestion evaluation
        suggestion = {
            "type": "performance",
            "description": "Optimize query performance",
            "impact": "medium"
        }

        result = await applicator.evaluate_suggestion(suggestion)
        print(f"✓ Suggestion evaluated: feasibility={result['feasibility']:.2f}")

        return True

    result = asyncio.run(test_improvement_applicator())
    print("[OK] Improvement Applicator: Working")

except Exception as e:
    print(f"[FAIL] Improvement Applicator: {e}")

print()

# Test 3: Consensus Agents
print("[TEST 3] Consensus Manager")
print("-" * 70)
try:
    from src.agents.consensus import ConsensusManager, AgentOpinion, ConsensusStrategy

    async def test_consensus():
        manager = ConsensusManager(strategy=ConsensusStrategy.WEIGHTED_VOTING)

        # Test opinion collection
        opinions = [
            AgentOpinion(agent_id="agent1", opinion="approve", confidence=0.9, reasoning="Good approach"),
            AgentOpinion(agent_id="agent2", opinion="approve", confidence=0.8, reasoning="Agreed"),
            AgentOpinion(agent_id="agent3", opinion="reject", confidence=0.6, reasoning="Concerns")
        ]

        consensus = await manager.reach_consensus(opinions)
        print(f"✓ Consensus reached: {consensus.decision}")
        print(f"  Confidence: {consensus.confidence:.2f}")
        print(f"  Participating agents: {len(consensus.participating_agents)}")

        return True

    result = asyncio.run(test_consensus())
    print("[OK] Consensus Manager: Working")

except Exception as e:
    print(f"[FAIL] Consensus Manager: {e}")

print()

# Test 4: Profiling System
print("[TEST 4] Agent Profiler")
print("-" * 70)
try:
    from src.agents.profiling import AgentProfiler

    async def test_profiling():
        profiler = AgentProfiler()

        # Start profiling
        profiler.start_profiling("test_agent", "test_operation")

        # Simulate some work
        await asyncio.sleep(0.1)

        # End profiling
        result = profiler.end_profiling("test_agent", "test_operation")

        if result:
            print(f"✓ Profiling completed: {result['duration_ms']:.2f}ms")

        # Get metrics
        metrics = await profiler.get_agent_metrics("test_agent")
        print(f"✓ Agent metrics retrieved: {metrics['total_operations']} operations")

        return True

    result = asyncio.run(test_profiling())
    print("[OK] Agent Profiler: Working")

except Exception as e:
    print(f"[FAIL] Agent Profiler: {e}")

print()

# Test 5: Security System
print("[TEST 5] Security System")
print("-" * 70)
try:
    from src.security import SecurityManager, SecurityLevel

    async def test_security():
        security = SecurityManager()

        # Test validation
        result = await security.validate_action(
            action_type="file_read",
            parameters={"path": "test.txt"},
            agent_id="test_agent"
        )

        print(f"✓ Action validated: allowed={result['allowed']}")
        print(f"  Risk level: {result['risk_level']}")

        return True

    result = asyncio.run(test_security())
    print("[OK] Security System: Working")

except Exception as e:
    print(f"[FAIL] Security System: {e}")

print()

# Test 6: Communication Protocols
print("[TEST 6] Agent Communication Protocols")
print("-" * 70)
try:
    from src.agents.protocols import AgentProtocol, MessagePriority

    async def test_protocols():
        protocol = AgentProtocol()

        # Create test message
        message = protocol.create_message(
            sender_id="agent1",
            recipient_id="agent2",
            message_type="task_request",
            content={"task": "test"},
            priority=MessagePriority.NORMAL
        )

        print(f"✓ Protocol message created: {message.message_id}")
        print(f"  Priority: {message.priority.value}")

        return True

    result = asyncio.run(test_protocols())
    print("[OK] Communication Protocols: Working")

except Exception as e:
    print(f"[FAIL] Communication Protocols: {e}")

print()

# Summary
print("=" * 70)
print("Phase 5 Testing Complete!")
print("=" * 70)
print()
print("Next step: Run full test suite")
print("  python -m pytest test_basic.py test_integration.py -v")
print()
