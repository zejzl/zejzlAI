#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Swarm Wrapper for zejzl.net - Multi-Agent Orchestration with Budget & Security

Integrates Network-AI Swarm Orchestrator with zejzl.net's 9-Agent Pantheon:
- Budget Tracking: Prevent runaway token costs (30-50% savings)
- Permission Gates: Secure access to sensitive APIs (DB, payments, email)
- Shared Blackboard: Coordinate state across agents
- Failure Detection: No more silent agent failures

Usage:
    from src.swarm_wrapper import SwarmCoordinator
    
    coordinator = SwarmCoordinator(message_bus)
    result = await coordinator.execute_task(
        task_id="task_001",
        task_description="Deploy new feature",
        budget=10000
    )
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging

# Import budget alert system
try:
    from src.budget_alerts import BudgetAlertManager
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    logging.warning("BudgetAlertManager not available - alerts disabled")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cost_calculator import TokenUsage
from src.logging_debug import logger

# Windows UTF-8 console fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

# ============================================================================
# Configuration
# ============================================================================

# Swarm orchestrator data directory
SWARM_DATA_DIR = Path(__file__).parent.parent / "skills" / "swarm-orchestrator" / "data"
SWARM_SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "swarm-orchestrator" / "scripts"

# Budget thresholds
BUDGET_WARNING_THRESHOLD = 0.8  # Warn at 80% usage
BUDGET_CRITICAL_THRESHOLD = 0.9  # Critical at 90% usage

# Permission resource types
SENSITIVE_RESOURCES = {
    "DATABASE": 0.7,      # Risk score
    "PAYMENTS": 0.9,
    "EMAIL": 0.6,
    "FILE_EXPORT": 0.5
}

# Trusted agents (higher trust = more permissions)
AGENT_TRUST_LEVELS = {
    "observer": 0.6,
    "reasoner": 0.7,
    "actor": 0.5,
    "analyzer": 0.8,
    "executor": 0.5,
    "improver": 0.7,
    "learner": 0.8,
    "memory": 0.9,
    "validator": 0.8,
    "pantheon": 0.95,      # High trust - coordinates all agents
    "orchestrator": 0.9    # High trust - coordination role
}

# ============================================================================
# Exceptions
# ============================================================================

class BudgetExhaustedError(Exception):
    """Raised when token budget is exhausted"""
    pass

class PermissionDeniedError(Exception):
    """Raised when permission check fails"""
    pass

class SwarmCoordinationError(Exception):
    """Raised when agent coordination fails"""
    pass

# ============================================================================
# Budget Tracker
# ============================================================================

class BudgetTracker:
    """Tracks token usage and enforces budget limits"""
    
    def __init__(self, data_dir: Path = SWARM_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.budget_file = self.data_dir / "budget_tracking.json"
        self.budgets = self._load_budgets()
        
        # Initialize budget alert manager
        if ALERTS_AVAILABLE:
            self.alert_manager = BudgetAlertManager(data_dir=data_dir)
        else:
            self.alert_manager = None
    
    def _load_budgets(self) -> Dict[str, Any]:
        """Load budgets from file"""
        if self.budget_file.exists():
            with open(self.budget_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_budgets(self):
        """Save budgets to file"""
        with open(self.budget_file, 'w') as f:
            json.dump(self.budgets, f, indent=2)
    
    def initialize(self, task_id: str, max_tokens: int) -> Dict[str, Any]:
        """Initialize budget for a task"""
        self.budgets[task_id] = {
            "max_tokens": max_tokens,
            "used_tokens": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "OK"
        }
        self._save_budgets()
        
        logger.info(f"Budget initialized for {task_id}: {max_tokens:,} tokens")
        
        return {
            "task_id": task_id,
            "max_tokens": max_tokens,
            "initialized": True
        }
    
    def spend(self, task_id: str, tokens: int, reason: str = "API call") -> Dict[str, Any]:
        """Record token usage"""
        if task_id not in self.budgets:
            raise ValueError(f"Budget not initialized for task {task_id}")
        
        budget = self.budgets[task_id]
        budget["used_tokens"] += tokens
        budget["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Calculate usage percentage
        usage_pct = (budget["used_tokens"] / budget["max_tokens"]) * 100
        
        # Update status
        if budget["used_tokens"] >= budget["max_tokens"]:
            budget["status"] = "EXHAUSTED"
        elif usage_pct >= BUDGET_CRITICAL_THRESHOLD * 100:
            budget["status"] = "CRITICAL"
        elif usage_pct >= BUDGET_WARNING_THRESHOLD * 100:
            budget["status"] = "WARNING"
        else:
            budget["status"] = "OK"
        
        self._save_budgets()
        
        logger.info(f"Budget spend for {task_id}: {tokens:,} tokens ({reason})")
        
        # Trigger budget alert check (async, non-blocking)
        if self.alert_manager:
            asyncio.create_task(
                self.alert_manager.check_and_notify(
                    task_id,
                    budget["used_tokens"],
                    budget["max_tokens"]
                )
            )
        
        return self.check(task_id)
    
    def check(self, task_id: str) -> Dict[str, Any]:
        """Check budget status"""
        if task_id not in self.budgets:
            return {
                "initialized": False,
                "error": f"No budget found for task {task_id}"
            }
        
        budget = self.budgets[task_id]
        remaining = budget["max_tokens"] - budget["used_tokens"]
        usage_pct = (budget["used_tokens"] / budget["max_tokens"]) * 100
        
        return {
            "initialized": True,
            "task_id": task_id,
            "max_tokens": budget["max_tokens"],
            "used_tokens": budget["used_tokens"],
            "remaining_tokens": remaining,
            "usage_percentage": usage_pct,
            "status": budget["status"],
            "can_continue": remaining > 0
        }

# ============================================================================
# Permission Manager
# ============================================================================

class PermissionManager:
    """Manages permission grants for sensitive resources"""
    
    def __init__(self, data_dir: Path = SWARM_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.grants_file = self.data_dir / "active_grants.json"
        self.audit_file = self.data_dir / "audit_log.jsonl"
        self.grants = self._load_grants()
    
    def _load_grants(self) -> Dict[str, Any]:
        """Load active grants from file"""
        if self.grants_file.exists():
            with open(self.grants_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_grants(self):
        """Save grants to file"""
        with open(self.grants_file, 'w') as f:
            json.dump(self.grants, f, indent=2)
    
    def _audit_log(self, event: str, data: Dict[str, Any]):
        """Append to audit log"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            **data
        }
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def evaluate(
        self,
        agent_id: str,
        resource_type: str,
        justification: str,
        scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """Evaluate permission request"""
        
        # Get trust level
        trust_level = AGENT_TRUST_LEVELS.get(agent_id, 0.5)
        
        # Get resource risk
        risk_score = SENSITIVE_RESOURCES.get(resource_type, 0.5)
        
        # Evaluate justification (simple keyword scoring)
        justification_score = self._score_justification(justification)
        
        # Weighted evaluation
        weighted_score = (
            trust_level * 0.4 +
            justification_score * 0.4 +
            (1.0 - risk_score) * 0.2
        )
        
        granted = weighted_score >= 0.5
        
        result = {
            "granted": granted,
            "agent_id": agent_id,
            "resource_type": resource_type,
            "justification": justification,
            "scope": scope,
            "scores": {
                "trust": trust_level,
                "justification": justification_score,
                "risk": risk_score,
                "weighted": weighted_score
            },
            "reason": "Approved" if granted else f"Combined evaluation score ({weighted_score:.2f}) below threshold (0.5).",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Audit log
        self._audit_log(
            "permission_granted" if granted else "permission_denied",
            result
        )
        
        if granted:
            logger.info(f"Permission GRANTED: {agent_id} -> {resource_type} (score: {weighted_score:.2f})")
        else:
            logger.warning(f"Permission DENIED: {agent_id} -> {resource_type} (score: {weighted_score:.2f})")
        
        return result
    
    def _score_justification(self, justification: str) -> float:
        """Score justification text (0.0-1.0)"""
        # Simple keyword-based scoring
        keywords = {
            "user": 0.2,
            "request": 0.2,
            "required": 0.2,
            "critical": 0.3,
            "urgent": 0.2,
            "deploy": 0.3,
            "update": 0.2,
            "fix": 0.2,
            "bug": 0.2,
            "feature": 0.2
        }
        
        score = 0.0
        justification_lower = justification.lower()
        
        for keyword, weight in keywords.items():
            if keyword in justification_lower:
                score += weight
        
        # Length bonus (detailed justifications score higher)
        if len(justification) > 50:
            score += 0.1
        if len(justification) > 100:
            score += 0.1
        
        return min(score, 1.0)

# ============================================================================
# Blackboard Coordinator
# ============================================================================

class BlackboardCoordinator:
    """Shared state coordination for agents"""
    
    def __init__(self, data_dir: Path = SWARM_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.blackboard_file = self.data_dir / "blackboard.md"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load blackboard state from markdown file"""
        if not self.blackboard_file.exists():
            return {}
        
        # Simple parser: extract key-value pairs from markdown
        state = {}
        with open(self.blackboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse markdown sections
        import re
        sections = re.findall(r'## (.*?)\n- \*\*Value:\*\* "(.*?)"', content)
        for key, value in sections:
            state[key] = value
        
        return state
    
    def _save_state(self):
        """Save blackboard state to markdown file"""
        lines = ["# Swarm Blackboard\n"]
        
        for key, value in self.state.items():
            lines.append(f"\n## {key}")
            lines.append(f"- **Value:** \"{value}\"")
            lines.append(f"- **Timestamp:** {datetime.now(timezone.utc).isoformat()}")
        
        with open(self.blackboard_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def write(self, key: str, value: str):
        """Write value to blackboard"""
        self.state[key] = value
        self._save_state()
        logger.debug(f"Blackboard write: {key} = {value}")
    
    def read(self, key: str) -> Optional[str]:
        """Read value from blackboard"""
        value = self.state.get(key)
        logger.debug(f"Blackboard read: {key} = {value}")
        return value
    
    def delete(self, key: str):
        """Delete value from blackboard"""
        if key in self.state:
            del self.state[key]
            self._save_state()
            logger.debug(f"Blackboard delete: {key}")
    
    def list_keys(self) -> List[str]:
        """List all keys in blackboard"""
        return list(self.state.keys())

# ============================================================================
# Swarm Coordinator (Main Class)
# ============================================================================

class SwarmCoordinator:
    """
    Main coordinator for zejzl.net's 9-Agent Pantheon with swarm orchestration
    
    Features:
    - Budget tracking and enforcement
    - Permission gates for sensitive operations
    - Shared blackboard for agent coordination
    - Failure detection and recovery
    """
    
    def __init__(self, message_bus=None):
        self.message_bus = message_bus
        self.budget_tracker = BudgetTracker()
        self.permission_manager = PermissionManager()
        self.blackboard = BlackboardCoordinator()
        
        logger.info("SwarmCoordinator initialized")
    
    @property
    def data_dir(self):
        """Get data directory from budget tracker"""
        return self.budget_tracker.data_dir
    
    async def execute_task(
        self,
        task_id: str,
        task_description: str,
        budget: int = 10000,
        required_permissions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a task with budget tracking and permission checks
        
        Args:
            task_id: Unique task identifier
            task_description: Task description
            budget: Maximum tokens allowed
            required_permissions: List of resources needed (e.g., ["DATABASE", "EMAIL"])
        
        Returns:
            Dict with result, token_usage, and status
        """
        
        # Initialize budget
        self.budget_tracker.initialize(task_id, budget)
        
        # Write initial state to blackboard
        self.blackboard.write(f"task:{task_id}:status", "started")
        self.blackboard.write(f"task:{task_id}:description", task_description)
        
        try:
            # Check permissions if needed
            if required_permissions:
                for resource in required_permissions:
                    permission = self.permission_manager.evaluate(
                        agent_id="orchestrator",
                        resource_type=resource,
                        justification=f"Task {task_id}: {task_description}"
                    )
                    
                    if not permission['granted']:
                        raise PermissionDeniedError(
                            f"Permission denied for {resource}: {permission['reason']}"
                        )
            
            # Execute task (placeholder - integrate with actual MessageBus)
            result = await self._execute_with_pantheon(task_id, task_description)
            
            # Track token usage
            if 'token_usage' in result:
                budget_status = self.budget_tracker.spend(
                    task_id,
                    result['token_usage'].total_tokens,
                    f"Task execution: {task_description[:50]}"
                )
                
                # Check if budget exhausted
                if budget_status['status'] == 'EXHAUSTED':
                    raise BudgetExhaustedError(
                        f"Token budget exhausted: {budget_status['used_tokens']:,} / {budget_status['max_tokens']:,}"
                    )
            
            # Update blackboard
            self.blackboard.write(f"task:{task_id}:status", "completed")
            self.blackboard.write(f"task:{task_id}:result", str(result.get('response', '')))
            
            logger.info(f"Task {task_id} completed successfully")
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "budget_status": self.budget_tracker.check(task_id)
            }
            
        except BudgetExhaustedError as e:
            logger.error(f"Task {task_id} failed: Budget exhausted")
            self.blackboard.write(f"task:{task_id}:status", "failed_budget")
            raise
        
        except PermissionDeniedError as e:
            logger.error(f"Task {task_id} failed: Permission denied")
            self.blackboard.write(f"task:{task_id}:status", "failed_permission")
            raise
        
        except Exception as e:
            logger.error(f"Task {task_id} failed: {str(e)}")
            self.blackboard.write(f"task:{task_id}:status", "failed_error")
            raise SwarmCoordinationError(f"Task execution failed: {str(e)}")
    
    async def _execute_with_pantheon(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """
        Execute task with 9-Agent Pantheon
        (Placeholder - integrate with actual ai_framework.py MessageBus)
        """
        
        # TODO: Replace with actual MessageBus integration
        # For now, return mock result
        
        logger.info(f"Executing task {task_id} with Pantheon: {task_description}")
        
        # Simulate token usage
        token_usage = TokenUsage(
            provider="Grok",
            model="grok-4-fast-reasoning",
            prompt_tokens=len(task_description) * 4,
            completion_tokens=100,
            total_tokens=len(task_description) * 4 + 100
        )
        
        return {
            "response": f"Pantheon result for: {task_description}",
            "token_usage": token_usage,
            "agents_used": ["observer", "reasoner", "actor"]
        }
    
    async def check_permission(
        self,
        agent_id: str,
        resource_type: str,
        justification: str,
        scope: Optional[str] = None
    ) -> bool:
        """
        Check if an agent has permission to access a resource
        
        Args:
            agent_id: Agent requesting access
            resource_type: Resource type (DATABASE, PAYMENTS, EMAIL, etc.)
            justification: Reason for access
            scope: Optional scope (e.g., "read:orders")
        
        Returns:
            True if granted, False otherwise
        """
        
        result = self.permission_manager.evaluate(
            agent_id=agent_id,
            resource_type=resource_type,
            justification=justification,
            scope=scope
        )
        
        return result['granted']
    
    def get_budget_status(self, task_id: str) -> Dict[str, Any]:
        """Get current budget status for a task"""
        return self.budget_tracker.check(task_id)
    
    def get_blackboard_state(self, key: Optional[str] = None) -> Any:
        """Get blackboard state (all or specific key)"""
        if key:
            return self.blackboard.read(key)
        return self.blackboard.state

# ============================================================================
# Usage Example
# ============================================================================

async def example_usage():
    """Example integration with zejzl.net"""
    
    # Initialize coordinator
    coordinator = SwarmCoordinator()
    
    # Execute task with budget and permissions
    try:
        result = await coordinator.execute_task(
            task_id="deploy_feature_001",
            task_description="Deploy new chat feature to production",
            budget=15000,
            required_permissions=["DATABASE"]
        )
        
        print("Task completed successfully!")
        print(f"Budget used: {result['budget_status']['used_tokens']:,} / {result['budget_status']['max_tokens']:,} tokens")
        print(f"Result: {result['result']}")
        
    except BudgetExhaustedError as e:
        print(f"Budget exhausted: {e}")
    
    except PermissionDeniedError as e:
        print(f"Permission denied: {e}")

if __name__ == "__main__":
    asyncio.run(example_usage())
