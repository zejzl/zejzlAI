#!/usr/bin/env python3
"""
Pantheon Swarm - SwarmCoordinator integrated with PantheonRLM

Combines zejzl.net's 9-Agent Pantheon with swarm orchestration:
- Budget tracking for token usage control
- Permission gates for sensitive operations
- Shared blackboard for agent coordination
- Failure detection and recovery

Usage:
    from pantheon_swarm import PantheonSwarm
    
    swarm = PantheonSwarm("pantheon_config.json")
    result = await swarm.process_task(
        task="Deploy new feature",
        budget=10000,
        required_permissions=["DATABASE"]
    )
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import Pantheon RLM
from pantheon_rlm import PantheonRLM

# Import SwarmCoordinator
sys.path.insert(0, str(Path(__file__).parent))
from src.swarm_wrapper import SwarmCoordinator, BudgetExhaustedError, PermissionDeniedError
from src.cost_calculator import TokenUsage


class PantheonSwarm:
    """
    SwarmCoordinator-integrated Pantheon for zejzl.net
    
    Wraps PantheonRLM with:
    - Budget tracking (prevent runaway costs)
    - Permission gates (secure DB/payment/email access)
    - Shared blackboard (agent coordination state)
    - Failure detection (budget exhaustion, permission denial)
    """
    
    def __init__(
        self,
        pantheon_config_path: str = "pantheon_config.json",
        model: str = "claude-sonnet-4-5",
        api_key: Optional[str] = None,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize Pantheon Swarm.
        
        Args:
            pantheon_config_path: Path to Pantheon configuration
            model: LLM model to use
            api_key: API key (optional, reads from env)
            max_iterations: Max RLM iterations
            verbose: Print debug output
        """
        # Initialize Pantheon RLM
        self.pantheon = PantheonRLM(
            pantheon_config_path=pantheon_config_path,
            model=model,
            api_key=api_key,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        # Initialize SwarmCoordinator
        self.coordinator = SwarmCoordinator()
        
        # Task counter for unique IDs
        self.task_counter = 0
        
        self.verbose = verbose
    
    async def process_task(
        self,
        task: str,
        budget: int = 10000,
        required_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process task with budget tracking and permission gates.
        
        Args:
            task: Task description
            budget: Maximum tokens allowed (default 10,000)
            required_permissions: Resources needed (e.g., ["DATABASE", "EMAIL"])
        
        Returns:
            Dict with result, token_usage, and budget_status
        """
        
        # Generate task ID
        self.task_counter += 1
        task_id = f"pantheon_{self.task_counter}_{int(datetime.now().timestamp())}"
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Pantheon Swarm - Task {task_id}")
            print(f"{'='*60}")
            print(f"Task: {task}")
            print(f"Budget: {budget:,} tokens")
            if required_permissions:
                print(f"Permissions: {', '.join(required_permissions)}")
            print(f"{'='*60}\n")
        
        # Initialize budget
        self.coordinator.budget_tracker.initialize(task_id, budget)
        
        # Write initial state to blackboard
        self.coordinator.blackboard.write(f"task:{task_id}:status", "started")
        self.coordinator.blackboard.write(f"task:{task_id}:description", task)
        
        try:
            # Check permissions if required
            if required_permissions:
                for resource in required_permissions:
                    if self.verbose:
                        print(f"[PERMISSION CHECK] Checking access to {resource}...")
                    
                    permission = self.coordinator.permission_manager.evaluate(
                        agent_id="pantheon",
                        resource_type=resource,
                        justification=f"Pantheon task {task_id}: {task}"
                    )
                    
                    if not permission['granted']:
                        raise PermissionDeniedError(
                            f"Permission denied for {resource}: {permission['reason']}"
                        )
                    
                    if self.verbose:
                        print(f"[PERMISSION CHECK] ✓ Access granted to {resource}")
            
            # Execute task with Pantheon RLM
            if self.verbose:
                print(f"\n[PANTHEON] Executing with 9-Agent Pantheon...")
            
            # Track start time
            start_time = asyncio.get_event_loop().time()
            
            # Execute (PantheonRLM is synchronous, so run in executor)
            result = await asyncio.to_thread(self.pantheon.process_task, task)
            
            # Calculate execution time
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Estimate token usage (rough approximation)
            # TODO: Replace with actual token tracking from PantheonRLM
            estimated_tokens = len(task) * 4 + len(result) * 4
            
            # Track token usage
            budget_status = self.coordinator.budget_tracker.spend(
                task_id,
                estimated_tokens,
                f"Pantheon execution: {task[:50]}..."
            )
            
            if self.verbose:
                print(f"\n[BUDGET] Used {estimated_tokens:,} / {budget:,} tokens ({budget_status['usage_percentage']:.1f}%)")
                print(f"[BUDGET] Status: {budget_status['status']}")
            
            # Check if budget exhausted
            if budget_status['status'] == 'EXHAUSTED':
                raise BudgetExhaustedError(
                    f"Token budget exhausted: {budget_status['used_tokens']:,} / {budget_status['max_tokens']:,}"
                )
            
            # Update blackboard
            self.coordinator.blackboard.write(f"task:{task_id}:status", "completed")
            self.coordinator.blackboard.write(f"task:{task_id}:result", result)
            self.coordinator.blackboard.write(f"task:{task_id}:execution_time", str(execution_time))
            
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"[SUCCESS] Task completed in {execution_time:.2f}s")
                print(f"{'='*60}\n")
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "budget_status": budget_status,
                "execution_time": execution_time,
                "estimated_tokens": estimated_tokens
            }
            
        except BudgetExhaustedError as e:
            if self.verbose:
                print(f"\n[ERROR] Budget exhausted: {e}")
            
            self.coordinator.blackboard.write(f"task:{task_id}:status", "failed_budget")
            
            return {
                "success": False,
                "task_id": task_id,
                "error": "budget_exhausted",
                "message": str(e),
                "budget_status": self.coordinator.budget_tracker.check(task_id)
            }
        
        except PermissionDeniedError as e:
            if self.verbose:
                print(f"\n[ERROR] Permission denied: {e}")
            
            self.coordinator.blackboard.write(f"task:{task_id}:status", "failed_permission")
            
            return {
                "success": False,
                "task_id": task_id,
                "error": "permission_denied",
                "message": str(e)
            }
        
        except Exception as e:
            if self.verbose:
                print(f"\n[ERROR] Task execution failed: {e}")
                import traceback
                traceback.print_exc()
            
            self.coordinator.blackboard.write(f"task:{task_id}:status", "failed_error")
            self.coordinator.blackboard.write(f"task:{task_id}:error", str(e))
            
            return {
                "success": False,
                "task_id": task_id,
                "error": "execution_failed",
                "message": str(e)
            }
    
    def get_budget_status(self, task_id: str) -> Dict[str, Any]:
        """Get budget status for a task"""
        return self.coordinator.get_budget_status(task_id)
    
    def get_blackboard_state(self, key: Optional[str] = None) -> Any:
        """Get blackboard state (all or specific key)"""
        return self.coordinator.get_blackboard_state(key)
    
    async def check_permission(
        self,
        agent_id: str,
        resource_type: str,
        justification: str
    ) -> bool:
        """Check if an agent has permission to access a resource"""
        return await self.coordinator.check_permission(
            agent_id=agent_id,
            resource_type=resource_type,
            justification=justification
        )


async def example_usage():
    """Example: Using PantheonSwarm for zadecs with budget and permissions"""
    
    print("\n" + "="*60)
    print("Pantheon Swarm - Example Usage")
    print("="*60)
    
    # Initialize swarm
    swarm = PantheonSwarm(
        pantheon_config_path="pantheon_config.json",
        model="grok-4-1-fast-reasoning",  # Use Grok (fast + reasoning)
        verbose=True
    )
    
    # Example 1: Simple task (no permissions needed)
    print("\n[EXAMPLE 1] Simple research task (no permissions)")
    result1 = await swarm.process_task(
        task="Summarize the key benefits of Training-Free GRPO",
        budget=5000
    )
    
    if result1['success']:
        print(f"\n✓ Result: {result1['result'][:200]}...")
        print(f"✓ Budget used: {result1['estimated_tokens']:,} / 5,000 tokens")
    else:
        print(f"\n✗ Failed: {result1.get('message', 'Unknown error')}")
    
    # Example 2: Deployment task (requires DATABASE permission)
    print("\n[EXAMPLE 2] Deployment task (DATABASE permission required)")
    result2 = await swarm.process_task(
        task="Plan deployment of new chat feature to production",
        budget=10000,
        required_permissions=["DATABASE"]
    )
    
    if result2['success']:
        print(f"\n✓ Result: {result2['result'][:200]}...")
        print(f"✓ Budget used: {result2['estimated_tokens']:,} / 10,000 tokens")
    else:
        print(f"\n✗ Failed: {result2.get('message', 'Unknown error')}")
    
    # Example 3: Budget exhaustion test
    print("\n[EXAMPLE 3] Budget exhaustion test (very small budget)")
    result3 = await swarm.process_task(
        task="Write a comprehensive guide to multi-agent AI systems",
        budget=100  # Very small budget
    )
    
    if result3['success']:
        print(f"\n✓ Result: {result3['result'][:200]}...")
    else:
        print(f"\n✗ Failed (expected): {result3.get('message', 'Unknown error')}")
        print(f"   Error type: {result3.get('error', 'unknown')}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
