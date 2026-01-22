"""
Learner Agent for ZEJZL.NET Pantheon System.

Implements advanced learning loop optimization that analyzes event patterns,
identifies bottlenecks, and generates optimization suggestions for continuous
improvement of the multi-agent orchestration system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from collections import defaultdict, Counter

from base import PantheonAgent, AgentConfig
from messagebus import Message

logger = logging.getLogger("LearnerAgent")


class LearnerAgent(PantheonAgent):
    """
    Learner Agent for Pantheon 9-Agent System.
    Responsible for learning patterns from memory/events and optimizing the learning loop.

    Specialization: Pattern Recognition & Continuous Optimization
    Responsibilities:
    - Analyze historical data for patterns and trends
    - Identify successful and failed execution patterns
    - Generate optimization suggestions for system improvement
    - Implement continuous learning and adaptation

    Expertise Areas:
    - Pattern recognition and machine learning
    - Performance bottleneck identification
    - Optimization strategy development
    - Continuous improvement methodologies
    """

    def __init__(self, message_bus=None, persistence=None):
        config = AgentConfig(
            name="Learner",
            role="Pattern Recognition & Continuous Optimization",
            channels=["learner_channel"]
        )
        super().__init__(config, message_bus)

        self.specialization = "Pattern Recognition & Continuous Optimization"
        self.responsibilities = [
            "Analyze historical data for patterns and trends",
            "Identify successful and failed execution patterns",
            "Generate optimization suggestions for system improvement",
            "Implement continuous learning and adaptation"
        ]
        self.expertise_areas = [
            "Pattern recognition and machine learning",
            "Performance bottleneck identification",
            "Optimization strategy development",
            "Continuous improvement methodologies"
        ]
        self.learned_patterns: Dict[str, Any] = {}
        self.success_patterns: List[Dict[str, Any]] = []
        self.failure_patterns: List[Dict[str, Any]] = []
        self.optimization_suggestions: List[str] = []
        self.persistence = persistence

        # Load persisted patterns if persistence is available
        if self.persistence:
            asyncio.create_task(self.load_patterns())

    async def save_patterns(self):
        """Save learned patterns to persistence"""
        # Get persistence from AI provider bus if not set
        persistence = self.persistence
        if not persistence:
            try:
                from base import get_ai_provider_bus
                bus = await get_ai_provider_bus()
                persistence = bus.persistence
            except Exception as e:
                logger.debug(f"Could not get persistence for saving patterns: {e}")
                return

        patterns_state = {
            "learned_patterns": self.learned_patterns,
            "success_patterns": self.success_patterns[-50:],  # Keep last 50
            "failure_patterns": self.failure_patterns[-30:],  # Keep last 30
            "optimization_suggestions": self.optimization_suggestions[-20:]  # Keep last 20
        }

        try:
            await persistence.save_learner_patterns(patterns_state)
            logger.debug("Learner patterns saved successfully")
        except Exception as e:
            logger.warning(f"Failed to save learner patterns: {e}")

    async def process(self, message: Message):
        """Process incoming message (not implemented)"""
        pass

    async def load_patterns(self):
        """Load learned patterns from persistence"""
        # Get persistence from AI provider bus if not set
        persistence = self.persistence
        if not persistence:
            try:
                from base import get_ai_provider_bus
                bus = await get_ai_provider_bus()
                persistence = bus.persistence
            except Exception as e:
                logger.debug(f"Could not get persistence for loading patterns: {e}")
                return

        try:
            patterns_state = await persistence.load_learner_patterns()
            if not patterns_state:
                logger.debug("No persisted learner patterns found")
                return

            self.learned_patterns = patterns_state.get("learned_patterns", {})
            self.success_patterns = patterns_state.get("success_patterns", [])
            self.failure_patterns = patterns_state.get("failure_patterns", [])
            self.optimization_suggestions = patterns_state.get("optimization_suggestions", [])

            logger.info("Learner patterns loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load learner patterns: {e}")

    async def learn(self, memory_events: List[Dict[str, Any]],
                   profiling_data: Optional[Dict[str, Any]] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Advanced learning process that analyzes event patterns and optimizes future behavior.
        Now integrates with performance profiling data for data-driven insights.
        Implements learning loop optimization for the Pantheon system.
        """
        logger.debug("[%s] Learning from %d events with profiling data: %s",
                    self.name, len(memory_events), profiling_data is not None)

        try:
            # Analyze event sequences and patterns
            patterns = await self._analyze_patterns(memory_events)
            success_rate = await self._calculate_success_rate(memory_events)
            bottlenecks = await self._identify_bottlenecks(memory_events)

            # Integrate profiling data if available
            if profiling_data:
                enhanced_patterns = await self._integrate_profiling_data(patterns, profiling_data)
                enhanced_bottlenecks = await self._enhance_bottlenecks_with_profiling(bottlenecks, profiling_data)
                optimizations = await self._generate_optimizations(memory_events, enhanced_patterns, enhanced_bottlenecks, profiling_data)
            else:
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
                "profiling_integrated": profiling_data is not None,
                "timestamp": asyncio.get_event_loop().time(),
            }

            logger.info("[%s] Learning complete: %d patterns, %.2f%% success rate, profiling: %s",
                        self.name, len(patterns), success_rate * 100, "integrated" if profiling_data else "not used")

            # Save patterns after successful learning
            asyncio.create_task(self.save_patterns())

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.error("[%s] Learning failed due to data error: %s", self.name, e)
            return {
                "error": str(e),
                "patterns_analyzed": 0,
                "success_rate": 0.0,
                "bottlenecks_identified": 0,
                "optimizations_suggested": 0,
                "profiling_integrated": False,
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

    async def _generate_optimizations(self, events: List[Dict[str, Any]], patterns: Dict[str, Any], bottlenecks: List[Dict[str, Any]], profiling_data: Optional[Dict[str, Any]] = None) -> List[str]:
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

        # Add profiling-based optimizations
        if profiling_data:
            profiling_opts = await self._generate_profiling_optimizations(profiling_data)
            optimizations.extend(profiling_opts)

        return optimizations

    async def _integrate_profiling_data(self, patterns: Dict[str, Any], profiling_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate performance profiling data with pattern analysis.
        """
        enhanced_patterns = patterns.copy()

        # Add performance metrics to patterns
        agent_metrics = profiling_data.get("agent_metrics", {})
        enhanced_patterns["performance_correlations"] = {}

        # Correlate success patterns with high-performing agents
        if patterns.get("success_paths"):
            for pattern in patterns["success_paths"]:
                # Analyze which agents performed well in successful patterns
                pattern_agents = set()
                for event_seq in pattern:
                    if isinstance(event_seq, dict) and "agent" in event_seq:
                        pattern_agents.add(event_seq["agent"])

                # Check performance of agents in this pattern
                high_performers = []
                for agent in pattern_agents:
                    if agent in agent_metrics:
                        metrics = agent_metrics[agent]
                        if metrics.get("efficiency_score", 0) > 0.8:
                            high_performers.append(agent)

                enhanced_patterns["performance_correlations"][str(pattern)] = {
                    "high_performing_agents": high_performers,
                    "correlation_strength": len(high_performers) / len(pattern_agents) if pattern_agents else 0
                }

        return enhanced_patterns

    async def _enhance_bottlenecks_with_profiling(self, bottlenecks: List[Dict[str, Any]], profiling_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enhance bottleneck analysis with profiling data.
        """
        enhanced_bottlenecks = []
        agent_metrics = profiling_data.get("agent_metrics", {})

        for bottleneck in bottlenecks:
            enhanced = bottleneck.copy()

            # Add performance context
            if bottleneck["type"] == "performance_bottleneck":
                # Identify which agents are causing the bottleneck
                slow_agents = []
                for agent_name, metrics in agent_metrics.items():
                    if metrics.get("avg_response_time", 0) > 2.0:  # Slow threshold
                        slow_agents.append({
                            "agent": agent_name,
                            "response_time": metrics["avg_response_time"],
                            "efficiency": metrics.get("efficiency_score", 0)
                        })

                enhanced["slow_agents"] = slow_agents
                enhanced["bottleneck_severity"] = len(slow_agents)

            elif bottleneck["type"] == "execution_error":
                # Correlate with low reliability agents
                unreliable_agents = []
                for agent_name, metrics in agent_metrics.items():
                    if metrics.get("success_rate", 1.0) < 0.8:
                        unreliable_agents.append({
                            "agent": agent_name,
                            "success_rate": metrics["success_rate"],
                            "error_count": metrics.get("failed_calls", 0)
                        })

                enhanced["unreliable_agents"] = unreliable_agents

            enhanced_bottlenecks.append(enhanced)

        return enhanced_bottlenecks

    async def _generate_profiling_optimizations(self, profiling_data: Dict[str, Any]) -> List[str]:
        """
        Generate optimizations based on profiling data.
        """
        optimizations = []
        agent_metrics = profiling_data.get("agent_metrics", {})

        # Agent-specific optimizations
        for agent_name, metrics in agent_metrics.items():
            efficiency = metrics.get("efficiency_score", 1.0)
            reliability = metrics.get("success_rate", 1.0)
            avg_time = metrics.get("avg_response_time", 0)

            if efficiency < 0.7:
                optimizations.append(f"Optimize {agent_name} efficiency (current: {efficiency:.2f})")
            if reliability < 0.8:
                optimizations.append(f"Improve {agent_name} reliability (current: {reliability:.1%})")
            if avg_time > 2.0:
                optimizations.append(f"Reduce {agent_name} response time (current: {avg_time:.2f}s)")

        # System-level optimizations
        system_metrics = profiling_data.get("system_metrics", {})
        if system_metrics.get("system_efficiency", 1.0) < 0.8:
            optimizations.append("Optimize overall system performance")

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
