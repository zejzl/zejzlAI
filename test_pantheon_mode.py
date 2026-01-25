#!/usr/bin/env python3
"""
Test ZEJZL.NET Pantheon Mode with sample prompts
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

async def test_pantheon_mode(prompt: str):
    """Test pantheon mode with a given prompt"""
    print(f"\n[TEST] Testing Pantheon Mode with prompt: '{prompt}'")
    print("=" * 60)

    try:
        # Import agents
        from src.agents.observer import ObserverAgent
        from src.agents.reasoner import ReasonerAgent
        from src.agents.actor import ActorAgent
        from src.agents.validator import ValidatorAgent
        from src.agents.memory import MemoryAgent
        from src.agents.executor import ExecutorAgent
        from src.agents.analyzer import AnalyzerAgent
        from src.agents.learner import LearnerAgent
        from src.agents.improver import ImproverAgent

        print("[INIT] Initializing agents...")

        # Initialize agents
        observer = ObserverAgent()
        reasoner = ReasonerAgent()
        actor = ActorAgent()
        validator = ValidatorAgent()
        memory = MemoryAgent()
        executor = ExecutorAgent()
        analyzer = AnalyzerAgent()
        learner = LearnerAgent()
        improver = ImproverAgent()

        print("[OK] All agents initialized")

        # Run the pantheon orchestration
        print("\n[1/9 Observer] Gathering observations...")
        observation = await observer.observe(prompt)
        await memory.store({"type": "observation", "data": observation})
        print(f"[OBSERVATION] {observation.get('objective', 'N/A')[:100]}...")

        print("\n[2/9 Reasoner] Creating execution plan...")
        plan = await reasoner.reason(observation)
        await memory.store({"type": "plan", "data": plan})
        subtasks = plan.get('subtasks', [])
        print(f"[PLAN] Generated with {len(subtasks)} subtasks")

        print("\n[3/9 Actor] Executing planned actions...")
        execution = await actor.act(plan)
        await memory.store({"type": "execution", "data": execution})
        results = execution.get('results', [])
        print(f"[EXECUTION] Completed with {len(results)} action plans")

        print("\n[4/9 Validator] Validating execution...")
        validation = await validator.validate(execution)
        await memory.store({"type": "validation", "data": validation})
        validation_status = validation.get('overall_validation', 'UNKNOWN')
        print(f"[VALIDATION] Status: {validation_status}")

        print("\n[5/9 Executor] Performing validated tasks...")
        execution_result = await executor.execute(validation)
        await memory.store({"type": "executor", "data": execution_result})
        print(f"[EXECUTOR] Completed tasks")

        print("\n[6/9 Memory] Recalling stored events...")
        events = await memory.recall()
        print(f"[MEMORY] {len(events)} events stored")

        print("\n[7/9 Analyzer] Analyzing metrics...")
        analysis = await analyzer.analyze(events)
        health_score = analysis.get('health_score', 0)
        print(f"[ANALYSIS] Health score {health_score}/100")

        print("\n[8/9 Learner] Learning patterns...")
        learned = await learner.learn(events)
        patterns = learned.get('learned_patterns', {})
        print(f"[LEARNER] Identified {len(patterns)} patterns")

        print("\n[9/9 Improver] Generating improvements...")
        improvement = await improver.improve(analysis, learned)
        magic_improvements = improvement.get('magic_improvements', [])
        print(f"[IMPROVER] Generated {len(magic_improvements)} improvement suggestions")

        print("\n" + "=" * 60)
        print("[SUCCESS] Pantheon orchestration completed successfully!")
        print(f"[TASK] Processed: '{prompt}'")
        print(f"[AGENTS] Coordinated: 9/9")
        print(f"[STORAGE] Events stored: {len(events)}")
        print(f"[VALIDATION] Status: {validation_status}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n[ERROR] Error during pantheon execution: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run multiple test prompts"""
    test_prompts = [
        "Create a Python function to calculate fibonacci numbers recursively"
    ]

    print("[TEST] ZEJZL.NET Pantheon Mode Testing")
    print("=" * 50)

    successful_tests = 0
    total_tests = len(test_prompts)

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n[TEST {i}/{total_tests}]")
        success = await test_pantheon_mode(prompt)
        if success:
            successful_tests += 1

    print("\n" + "=" * 50)
    print(f"[RESULTS] Test Results: {successful_tests}/{total_tests} successful")
    if successful_tests == total_tests:
        print("[SUCCESS] All tests passed! Pantheon mode is working correctly.")
    else:
        print(f"[WARNING] {total_tests - successful_tests} tests failed. Check the errors above.")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())