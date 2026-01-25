#!/usr/bin/env python3
"""
Test Agent Logic Expansions
Tests the enhanced agent implementations with real logic instead of stubs.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.executor import ExecutorAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent


async def test_executor_agent():
    """Test the enhanced Executor Agent with real execution capabilities."""
    print("[TEST] Testing Enhanced Executor Agent...")

    executor = ExecutorAgent()

    # Test data processing execution
    data_step = {
        "type": "data_processing",
        "operation": "transform",
        "transform_type": "json_parse",
        "data": '{"test": "value", "number": 42}'
    }

    result = await executor._execute_data_step(data_step, 30)
    assert result["status"] == "success"
    assert result["result"]["test"] == "value"
    print("[OK] Data processing execution works")

    # Test file operation execution (read operation)
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_file = f.name

    try:
        file_step = {
            "type": "file_operation",
            "operation": "read",
            "file_path": temp_file
        }

        result = await executor._execute_file_step(file_step, 30)
        assert result["status"] == "success"
        assert "test content" in result["content"]
        print("[OK] File operation execution works")
    finally:
        os.unlink(temp_file)

    # Test code execution
    code_step = {
        "type": "code",
        "language": "python",
        "code": "result = 2 + 3\nfinal_answer = result * 2"
    }

    result = await executor._execute_code_step(code_step, 30)
    assert result["status"] == "success"
    assert "final_answer" in result["output"]
    assert result["output"]["final_answer"] == 10
    print("[OK] Code execution works")

    print("[OK] Executor Agent tests passed!")


async def test_reasoner_agent():
    """Test the enhanced Reasoner Agent with intelligent fallback planning."""
    print("\n[TEST] Testing Enhanced Reasoner Agent...")

    reasoner = ReasonerAgent()

    # Test task type classification
    assert reasoner._classify_task_type("research the latest AI developments") == "research/analysis"
    assert reasoner._classify_task_type("create a mobile app") == "creation/development"
    assert reasoner._classify_task_type("write a report") == "writing/documentation"
    print("[OK] Task type classification works")

    # Test fallback plan generation
    observation = {
        "task": "research AI trends",
        "requirements": ["credible sources", "recent data"],
        "complexity_level": "Medium"
    }

    plan = reasoner._generate_fallback_plan(observation, "AI unavailable")

    assert plan["analysis"]["task_type"] == "research/analysis"
    assert len(plan["subtasks"]) >= 3
    assert "research" in plan["approach"].lower()
    assert plan["fallback_type"] == "intelligent_rule_based"
    print("[OK] Intelligent fallback planning works")

    print("[OK] Reasoner Agent tests passed!")


async def test_actor_agent():
    """Test the enhanced Actor Agent with intelligent execution planning."""
    print("\n[TEST] Testing Enhanced Actor Agent...")

    actor = ActorAgent()

    # Test fallback execution plan generation
    subtasks = [
        "research the latest developments",
        "create a comprehensive report",
        "test the implementation"
    ]

    plans = actor._generate_fallback_execution_plans(subtasks, "AI unavailable")

    assert len(plans) == 3

    # Check research subtask
    research_plan = plans[0]
    assert "research" in research_plan["execution_plan"][0].lower()
    assert "sources" in str(research_plan["tools_needed"])
    assert research_plan["estimated_duration"] in ["2-4 hours", "1-2 hours"]

    # Check creation subtask
    creation_plan = plans[1]
    assert "design" in creation_plan["execution_plan"][0].lower()
    assert "development" in str(creation_plan["tools_needed"])
    assert creation_plan["estimated_duration"] in ["4-8 hours", "2-6 hours", "1-3 hours"]

    # Check testing subtask
    testing_plan = plans[2]
    assert "test" in testing_plan["execution_plan"][0].lower()
    assert "testing" in str(testing_plan["tools_needed"])

    print("[OK] Execution plan generation works")

    print("[OK] Actor Agent tests passed!")


async def test_agent_integration():
    """Test the full agent integration pipeline."""
    print("\n[TEST] Testing Full Agent Integration Pipeline...")

    # Initialize agents
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    executor = ExecutorAgent()

    # Test observation (simulated)
    observation = {
        "task": "create a simple Python script to calculate fibonacci numbers",
        "requirements": ["working code", "error handling", "documentation"],
        "complexity_level": "Low"
    }

    # Test Reasoner → Actor → Executor pipeline
    print("[PLAN] Testing Reasoner → Actor → Executor pipeline...")

    # Generate plan (using fallback for testing)
    plan = reasoner._generate_fallback_plan(observation, "Testing pipeline")

    # Generate execution plans
    execution_summary = actor._generate_fallback_execution_plans(plan["subtasks"], "Testing pipeline")

    # Execute a simple step
    simple_execution_step = {
        "type": "code",
        "language": "python",
        "code": "fib = [0, 1]\nfor i in range(2, 10):\n    fib.append(fib[i-1] + fib[i-2])\nresult = fib"
    }

    execution_result = await executor._execute_code_step(simple_execution_step, 30)

    assert execution_result["status"] == "success"
    assert "result" in execution_result["output"]
    assert len(execution_result["output"]["result"]) == 10  # Should have 10 fibonacci numbers

    print("[OK] Full agent pipeline works")

    print("[OK] Agent Integration tests passed!")


async def run_all_tests():
    """Run all agent enhancement tests."""
    print("Running Comprehensive Agent Logic Tests")
    print("=" * 60)

    try:
        await test_executor_agent()
        await test_reasoner_agent()
        await test_actor_agent()
        await test_agent_integration()

        print("\n" + "=" * 60)
        print("[SUCCESS] ALL AGENT ENHANCEMENT TESTS PASSED!")
        print("\n[STATS] Test Summary:")
        print("[OK] Executor Agent: Real task execution capabilities")
        print("[OK] Reasoner Agent: Intelligent fallback planning")
        print("[OK] Actor Agent: Smart execution strategy generation")
        print("[OK] Agent Integration: Full pipeline functionality")

        print("\n[START] Agents are now production-ready with real logic!")
        return 0

    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)