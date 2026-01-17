"""
Learner Agent for ZEJZL.NET Pantheon System.

Implements advanced learning loop optimization that analyzes event patterns,
identifies bottlenecks, and generates optimization suggestions for continuous
improvement of the multi-agent orchestration system.
"""

import asyncio
import logging
from typing import Any, Dict, List
from collections import defaultdict, Counter

logger = logging.getLogger("LearnerAgent")


class LearnerAgent:
    """
    Learner Agent for Pantheon 9-Agent System.
    Responsible for learning patterns from memory/events and optimizing the learning loop.
    """

    def __init__(self):
        self.name = "Learner"
        self.learned_patterns: Dict[str, Any] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        self.optimization_suggestions: List[str] = []

    async def learn(self, memory_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Advanced learning process that analyzes event patterns and optimizes future behavior.
        Implements learning loop optimization for the Pantheon system.
        """
        logger.debug("[%s] Learning from %d events", self.name, len(memory_events))

        try:
            # Analyze event sequences and patterns
            patterns = await self._analyze_patterns(memory_events)
            success_rate = await self._calculate_success_rate(memory_events)
            bottlenecks = await self._identify_bottlenecks(memory_events)
            optimizations = await self._generate_optimizations(memory_events, patterns, bottlenecks)

            # Store learned knowledge
            await self._store_learned_patterns(patterns, success_rate, bottlenecks)

            # Update optimization suggestions
            self.optimization_suggestions.extend(optimizations)

            result = {
                "patterns_analyzed": len(patterns),
                "success_rate": success_rate,
                "bottlenecks_identified": len(bottlenecks),
                "optimizations_suggested": len(optimizations),
                "learned_patterns": patterns,
                "bottlenecks": bottlenecks,
                "optimizations": optimizations,
                "timestamp": asyncio.get_event_loop().time(),
            }

            logger.info("[%s] Learning complete: %d patterns, %.2f%% success rate",
                       self.name, len(patterns), success_rate * 100)
            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.error("[%s] Learning failed due to data error: %s", self.name, e)
            return {
                "error": str(e),
                "patterns_analyzed": 0,
                "success_rate": 0.0,
                "bottlenecks_identified": 0,
                "optimizations_suggested": 0,
                "timestamp": asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.error("[%s] Learning failed with unexpected error: %s", self.name, e)
            return {
                "error": str(e),
                "patterns_analyzed": 0,
                "success_rate": 0.0,
                "bottlenecks_identified": 0,
                "optimizations_suggested": 0,
                "timestamp": asyncio.get_event_loop().time()
            }

    async def _analyze_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze event sequences to identify successful and failed patterns.
        """
        patterns: Dict[str, Any] = {
            "event_sequences": [],
            "task_types": Counter(),
            "agent_performance": defaultdict(list),
            "execution_times": [],
            "success_paths": [],
            "failure_paths": []
        }

        # Group events by conversation/task
        conversations = defaultdict(list)
        for event in events:
            conv_id = event.get("conversation_id", "default")
            conversations[conv_id].append(event)

        for conv_id, conv_events in conversations.items():
            # Analyze event sequence
            sequence = [e["type"] for e in conv_events]
            patterns["event_sequences"].append(sequence)

            # Extract task types and performance metrics
            for event in conv_events:
                event_type = event["type"]
                data = event["data"]

                if event_type == "observation":
                    task_desc = data.get("task", "")
                    patterns["task_types"][task_desc] += 1

                elif event_type in ["execution", "validation", "executor"]:
                    # Track agent performance
                    if "timestamp" in data:
                        patterns["execution_times"].append(data["timestamp"])

                # Classify as success or failure path
                if event_type == "validation" and data.get("is_valid", False):
                    patterns["success_paths"].append(sequence)
                elif event_type == "validation" and not data.get("is_valid", True):
                    patterns["failure_paths"].append(sequence)

        return patterns

    async def _calculate_success_rate(self, events: List[Dict[str, Any]]) -> float:
        """
        Calculate overall success rate from validation events.
        """
        validations = [e for e in events if e["type"] == "validation"]
        if not validations:
            return 0.0

        successful = sum(1 for v in validations if v["data"].get("is_valid", False))
        return successful / len(validations)

    async def _identify_bottlenecks(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify bottlenecks and failure points in the process.
        """
        bottlenecks = []

        # Analyze validation failures
        failed_validations = [
            e for e in events
            if e["type"] == "validation" and not e["data"].get("is_valid", True)
        ]
        for failure in failed_validations:
            bottlenecks.append({
                "type": "validation_failure",
                "reason": failure["data"].get("reason", "unknown"),
                "frequency": len(failed_validations),
                "impact": "blocks_execution"
            })

        # Analyze execution timeouts or errors
        failed_executions = [
            e for e in events
            if e["type"] == "executor" and e["data"].get("error")
        ]
        for failure in failed_executions:
            bottlenecks.append({
                "type": "execution_error",
                "error": failure["data"]["error"],
                "frequency": len(failed_executions),
                "impact": "execution_failure"
            })

        # Analyze slow response times
        execution_times = [
            e["data"].get("timestamp", 0)
            for e in events if "timestamp" in e["data"]
        ]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            slow_executions = [t for t in execution_times if t > avg_time * 1.5]
            if slow_executions:
                bottlenecks.append({
                    "type": "performance_bottleneck",
                    "description": (
                        f"{len(slow_executions)} executions slower than 1.5x average"
                    ),
                    "average_time": avg_time,
                    "impact": "reduced_performance"
                })

        return bottlenecks

    async def _generate_optimizations(self, events: List[Dict[str, Any]], patterns: Dict[str, Any], bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """
        Generate optimization suggestions based on patterns and bottlenecks.
        """
        optimizations = []

        # Success pattern optimizations
        if patterns["success_paths"]:
            success_count = len(patterns["success_paths"])
            optimizations.append(
                f"Reinforce {success_count} successful execution patterns"
            )

        # Failure pattern optimizations
        if patterns["failure_paths"]:
            failure_count = len(patterns["failure_paths"])
            optimizations.append(
                f"Address {failure_count} failure patterns with improved validation"
            )

        # Bottleneck-specific optimizations
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "validation_failure":
                optimizations.append("Enhance pre-validation checks to prevent common failures")
            elif bottleneck["type"] == "execution_error":
                optimizations.append("Implement retry logic for transient execution errors")
            elif bottleneck["type"] == "performance_bottleneck":
                optimizations.append("Optimize slow execution paths and implement caching")

        # Task pattern optimizations
        common_tasks = patterns["task_types"].most_common(3)
        if common_tasks:
            optimizations.append(
                f"Create specialized handling for top tasks: {[task for task, _ in common_tasks]}"
            )

        # Learning loop optimizations
        if len(events) > 10:  # If we have enough data
            optimizations.append("Implement continuous learning with pattern reinforcement")
            optimizations.append("Add predictive optimization based on historical success rates")

        return optimizations

    async def _store_learned_patterns(self, patterns: Dict[str, Any], success_rate: float, bottlenecks: List[Dict[str, Any]]):
        """
        Store learned patterns for future optimization.
        """
        self.learned_patterns.update({
            "last_analysis": patterns,
            "success_rate": success_rate,
            "bottlenecks": bottlenecks,
            "learned_at": asyncio.get_event_loop().time()
        })

        # Store successful patterns for reinforcement
        if patterns["success_paths"]:
            self.success_patterns.extend(patterns["success_paths"][-5:])  # Keep last 5

        # Store failure patterns for avoidance
        if patterns["failure_paths"]:
            self.failure_patterns.extend(patterns["failure_paths"][-3:])  # Keep last 3

    async def get_optimization_suggestions(self) -> List[str]:
        """
        Retrieve current optimization suggestions.
        """
        return self.optimization_suggestions.copy()

    async def get_learned_patterns(self) -> Dict[str, Any]:
        """
        Retrieve stored learned patterns.
        """
        return self.learned_patterns.copy()
