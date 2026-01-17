#!/usr/bin/env python3
"""
Test script for Advanced Workflow Patterns in ZEJZL.NET

Demonstrates parallel execution, conditional branching, and loops
in the Pantheon 9-agent system.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.workflows import execute_advanced_workflow

async def demo():
    """Demonstrate advanced workflow patterns"""
    print("Advanced Workflow Patterns Demo")
    print("=" * 50)

    try:
        # Test parallel workflow
        print("\nTesting Parallel Workflow...")
        result = await execute_advanced_workflow("parallel", "analyze sales data")
        print(f"Status: {result['status']}")
        print(f"Executed steps: {result['executed_steps_count']}")

        # Test conditional workflow
        print("\nTesting Conditional Workflow...")
        result = await execute_advanced_workflow("conditional", "complex analysis task")
        print(f"Status: {result['status']}")
        print(f"Executed steps: {result['executed_steps_count']}")

        # Test loop workflow
        print("\nTesting Loop Workflow...")
        result = await execute_advanced_workflow("loop", "iterative improvement task")
        print(f"Status: {result['status']}")
        print(f"Executed steps: {result['executed_steps_count']}")

        print("\nAdvanced workflow patterns demonstration complete!")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo())