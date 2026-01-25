#!/usr/bin/env python3
"""
Docker demo script for ZEJZL.NET
Runs a sample pantheon orchestration
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/app')

async def main():
    try:
        print("[DOCKER] ZEJZL.NET Docker Demo Starting")
        print("=" * 40)

        from src.agents.observer import ObserverAgent
        from src.agents.reasoner import ReasonerAgent
        from src.agents.actor import ActorAgent

        print("[OK] AI Agents initialized")

        # Run a simple demo
        observer = ObserverAgent()
        reasoner = ReasonerAgent()
        actor = ActorAgent()

        task = "Create a Python function to calculate fibonacci numbers"
        print(f"\n[TARGET] Task: {task}")

        print("\n[AI] Observer analyzing task...")
        observation = await observer.observe(task)
        print(f"[DATA] Observation: {observation.get('complexity_level', 'Unknown')} complexity")

        print("\n[BRAIN] Reasoner creating plan...")
        plan = await reasoner.reason(observation)
        print(f"[PLAN] Plan generated with {len(plan.get('subtasks', []))} subtasks")

        print("\n[ACTION] Actor planning execution...")
        execution = await actor.act(plan)
        print(f"[EXEC] Execution plan ready for {execution.get('total_subtasks', 0)} subtasks")

        print("\n[SUCCESS] Demo completed successfully!")
        print("ZEJZL.NET is running with AI-powered agents!")

    except Exception as e:
        print(f"[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())