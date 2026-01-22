#!/usr/bin/env python3
"""
Simple Agent Enhancement Test
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.executor import ExecutorAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent

async def test_agents():
    print("Testing Enhanced Agent Logic...")

    # Test Executor
    executor = ExecutorAgent()
    code_step = {
        "type": "code",
        "language": "python",
        "code": "result = 42"
    }
    result = await executor._execute_code_step(code_step, 30)
    assert result["status"] == "success"
    assert result["output"]["result"] == 42
    print("[PASS] Executor Agent: Code execution works")

    # Test Reasoner
    reasoner = ReasonerAgent()
    observation = {"task": "research AI", "complexity_level": "Low"}
    plan = reasoner._generate_fallback_plan(observation, "test")
    assert len(plan["subtasks"]) > 0
    assert plan["fallback_type"] == "intelligent_rule_based"
    print("[PASS] Reasoner Agent: Intelligent fallback planning works")

    # Test Actor
    actor = ActorAgent()
    subtasks = ["research topic"]
    plans = actor._generate_fallback_execution_plans(subtasks, "test")
    assert len(plans) == 1
    assert "research" in plans[0]["execution_plan"][0].lower()
    print("[PASS] Actor Agent: Smart execution planning works")

    print("\n[SUCCESS] All agent enhancements working correctly!")
    print("Agents now have REAL logic instead of stubs!")

if __name__ == "__main__":
    asyncio.run(test_agents())