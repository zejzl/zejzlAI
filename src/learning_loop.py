# src/learning_loop.py
"""
Learning Loop Optimization for ZEJZL.NET Pantheon System.

Implements continuous learning cycles that optimize the multi-agent orchestration
through data-driven insights, pattern recognition, and automated improvements.
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.agents.learner import LearnerAgent
from src.agents.profiling import AgentProfiler
from src.agents.consensus import ConsensusManager, AgentOpinion
from src.agents.memory import MemoryAgent
from src.improvement_applicator import ImprovementApplicator

logger = logging.getLogger("LearningLoop")


class LearningPhase(Enum):
    """Phases of the learning loop"""
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    IMPLEMENTATION = "implementation"
    EVALUATION = "evaluation"
    ADAPTATION = "adaptation"


@dataclass
class LearningCycle:
    """A single learning cycle"""
    cycle_id: str
    start_time: datetime
    phase: LearningPhase = LearningPhase.OBSERVATION
    performance_data: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    optimization_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    implementation_actions: List[Dict[str, Any]] = field(default_factory=list)
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    end_time: Optional[datetime] = None
    success: bool = False

    def complete_phase(self, phase_data: Optional[Dict[str, Any]] = None):
        """Complete current phase and move to next"""
        if phase_data:
            if self.phase == LearningPhase.OBSERVATION:
                self.performance_data.update(phase_data)
            elif self.phase == LearningPhase.ANALYSIS:
                self.analysis_results.update(phase_data)
            elif self.phase == LearningPhase.OPTIMIZATION:
                self.optimization_recommendations.extend(phase_data.get('recommendations', []))
            elif self.phase == LearningPhase.IMPLEMENTATION:
                self.implementation_actions.extend(phase_data.get('actions', []))
            elif self.phase == LearningPhase.EVALUATION:
                self.evaluation_metrics.update(phase_data)

        # Move to next phase
        phase_order = list(LearningPhase)
        current_index = phase_order.index(self.phase)
        if current_index < len(phase_order) - 1:
            self.phase = phase_order[current_index + 1]
        else:
            self.end_time = datetime.now()
            self.success = True

    def get_duration(self) -> Optional[float]:
        """Get cycle duration in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class LearningInsight:
    """A learning insight generated from analysis"""
    insight_id: str
    insight_type: str  # "pattern", "bottleneck", "optimization", "anomaly"
    description: str
    confidence: float
    impact_potential: str  # "high", "medium", "low"
    related_agents: List[str]
    recommended_actions: List[str]
    generated_at: datetime
    applied: bool = False
    applied_at: Optional[datetime] = None
    impact_measured: Optional[Dict[str, Any]] = None


class LearningLoop:
    """
    Orchestrates continuous learning cycles for system optimization
    """

    def __init__(self, cycle_interval: int = 300,  # 5 minutes
                 max_cycles_history: int = 100):
        self.cycle_interval = cycle_interval  # seconds
        self.max_cycles_history = max_cycles_history

        # Core components
        self.learner = LearnerAgent()
        self.profiler = AgentProfiler()
        self.consensus_manager = ConsensusManager()
        self.memory = MemoryAgent()
        self.improvement_applicator = ImprovementApplicator(self.profiler, self.consensus_manager)

        # Learning state
        self.current_cycle: Optional[LearningCycle] = None
        self.learning_cycles: List[LearningCycle] = []
        self.learning_insights: List[LearningInsight] = []
        self.optimization_actions: Dict[str, Callable] = {}

        # Continuous learning
        self.running = False
        self.learning_task: Optional[asyncio.Task] = None

        # Configuration
        self.learning_enabled = True
        self.auto_apply_optimizations = False  # Start conservative
        self.minimum_confidence_threshold = 0.7

        # Continuous monitoring
        self.monitoring_enabled = True
        self.adaptation_enabled = True
        self.monitoring_interval = 60  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        self.performance_baseline: Dict[str, Any] = {}
        self.anomaly_threshold = 0.2  # 20% deviation triggers monitoring

        # Register optimization actions
        self._register_optimization_actions()

    def _register_optimization_actions(self):
        """Register available optimization actions"""
        self.optimization_actions = {
            "adjust_agent_weights": self._adjust_agent_weights,
            "rebalance_workload": self._rebalance_workload,
            "optimize_execution_order": self._optimize_execution_order,
            "enable_circuit_breaker": self._enable_circuit_breaker,
            "adjust_rate_limits": self._adjust_rate_limits,
            "update_consensus_weights": self._update_consensus_weights,
            "cache_frequent_patterns": self._cache_frequent_patterns,
            "parallelize_independent_tasks": self._parallelize_independent_tasks
        }

    async def start_continuous_learning(self):
        """Start the continuous learning loop"""
        if self.running:
            logger.warning("Learning loop already running")
            return

        self.running = True
        self.learning_task = asyncio.create_task(self._continuous_learning_loop())

        # Start continuous monitoring if enabled
        if self.monitoring_enabled:
            self.monitoring_task = asyncio.create_task(self._continuous_monitoring_loop())
            logger.info("Continuous monitoring started")

        logger.info("Continuous learning loop started")

    async def stop_continuous_learning(self):
        """Stop the continuous learning loop"""
        self.running = False
        if self.learning_task:
            self.learning_task.cancel()
            try:
                await self.learning_task
            except asyncio.CancelledError:
                pass

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Continuous learning and monitoring loops stopped")

    async def _continuous_learning_loop(self):
        """Main continuous learning loop"""
        while self.running:
            try:
                await self.execute_learning_cycle()
                await asyncio.sleep(self.cycle_interval)
            except Exception as e:
                logger.error(f"Error in learning cycle: {e}")
                await asyncio.sleep(self.cycle_interval)

    async def _continuous_monitoring_loop(self):
        """Continuous monitoring loop for real-time adaptation"""
        logger.info("Starting continuous monitoring loop")

        # Establish baseline performance
        await self._establish_performance_baseline()

        while self.running and self.monitoring_enabled:
            try:
                await self._monitor_system_performance()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def execute_learning_cycle(self) -> Optional[LearningCycle]:
        """Execute a single learning cycle"""
        cycle = LearningCycle(
            cycle_id=f"cycle_{datetime.now().timestamp()}",
            start_time=datetime.now()
        )
        self.current_cycle = cycle

        try:
            logger.info(f"Starting learning cycle {cycle.cycle_id}")

            # Phase 1: Observation - Collect performance data
            performance_data = await self._observe_performance()
            cycle.complete_phase({"performance_data": performance_data})

            # Phase 2: Analysis - Analyze patterns and identify issues
            analysis_results = await self._analyze_patterns(cycle.performance_data)
            cycle.complete_phase({"analysis_results": analysis_results})

            # Phase 3: Optimization - Generate improvement recommendations
            recommendations = await self._generate_optimizations(cycle.analysis_results)
            cycle.complete_phase({"recommendations": recommendations})

            # Phase 4: Implementation - Apply selected optimizations
            actions = await self._implement_optimizations(cycle.optimization_recommendations)
            cycle.complete_phase({"actions": actions})

            # Phase 5: Evaluation - Measure impact of changes
            evaluation = await self._evaluate_impact(cycle.implementation_actions)
            cycle.complete_phase({"evaluation": evaluation})

            # Phase 6: Adaptation - Learn from results and adapt
            await self._adapt_based_on_learning(cycle.evaluation_metrics)

            cycle.success = True
            logger.info(f"Learning cycle {cycle.cycle_id} completed successfully")

        except Exception as e:
            logger.error(f"Learning cycle {cycle.cycle_id} failed: {e}")
            cycle.success = False

        cycle.end_time = datetime.now()
        self.learning_cycles.append(cycle)

        # Maintain history limit
        if len(self.learning_cycles) > self.max_cycles_history:
            self.learning_cycles.pop(0)

        self.current_cycle = None
        return cycle

    async def _observe_performance(self) -> Dict[str, Any]:
        """Collect current system performance data"""
        logger.debug("Observing system performance")

        # Get profiling data
        performance_report = await self.profiler.get_performance_report()

        # Get memory events for pattern analysis
        memory_events = await self.memory.recall()

        # Get current system state
        system_state = {
            "timestamp": datetime.now(),
            "performance_report": performance_report,
            "memory_events_count": len(memory_events),
            "active_cycles": len([c for c in self.learning_cycles if not c.end_time]),
            "total_insights": len(self.learning_insights)
        }

        return system_state

    async def _analyze_patterns(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance patterns and identify issues"""
        logger.debug("Analyzing performance patterns")

        memory_events = (await self.memory.recall()) or []

        # Get current profiling data
        profiling_report = await self.profiler.get_performance_report()

        # Use LearnerAgent for pattern analysis with profiling integration
        analysis = await self.learner.learn(memory_events, profiling_report)

        # Combine with additional profiling insights
        performance_report = performance_data.get("performance_report", {})

        analysis_results = {
            "learner_analysis": analysis,
            "performance_metrics": performance_report,
            "profiling_data": profiling_report,
            "patterns_identified": len(analysis.get("learned_patterns", {}).get("event_sequences", [])),
            "bottlenecks_found": len(analysis.get("bottlenecks", [])),
            "success_rate": analysis.get("success_rate", 0.0),
            "optimization_suggestions": analysis.get("optimizations", []),
            "profiling_integrated": analysis.get("profiling_integrated", False)
        }

        return analysis_results

    async def _generate_optimizations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        logger.debug("Generating optimization recommendations")

        recommendations = []

        # Get learner suggestions
        learner_opts = analysis_results.get("optimization_suggestions", [])
        recommendations.extend([{
            "type": "learner_suggestion",
            "action": opt,
            "confidence": 0.8,
            "source": "pattern_analysis"
        } for opt in learner_opts])

        # Get profiling recommendations
        profiling_opts = await self.profiler.analyze_performance()
        recommendations.extend([{
            "type": "profiling_recommendation",
            "action": opt.description,
            "confidence": 0.9,
            "priority": opt.priority,
            "source": "performance_analysis",
            "agent": opt.agent_name,
            "expected_impact": opt.expected_impact
        } for opt in profiling_opts])

        # Generate learning insights
        insights = await self._generate_insights(analysis_results)
        self.learning_insights.extend(insights)

        # Convert insights to recommendations
        for insight in insights:
            if insight.confidence >= self.minimum_confidence_threshold:
                recommendations.append({
                    "type": "learning_insight",
                    "action": insight.description,
                    "confidence": insight.confidence,
                    "priority": insight.impact_potential,
                    "source": "insight_generation",
                    "insight_id": insight.insight_id,
                    "recommended_actions": insight.recommended_actions
                })

        return recommendations

    async def _generate_insights(self, analysis_results: Dict[str, Any]) -> List[LearningInsight]:
        """Generate learning insights from analysis"""
        insights = []

        # Pattern-based insights
        patterns = analysis_results.get("learner_analysis", {}).get("learned_patterns", {})
        if patterns.get("success_paths"):
            insights.append(LearningInsight(
                insight_id=f"insight_{datetime.now().timestamp()}_success_patterns",
                insight_type="pattern",
                description=f"Identified {len(patterns['success_paths'])} successful execution patterns",
                confidence=0.85,
                impact_potential="high",
                related_agents=["all"],
                recommended_actions=["Reinforce successful patterns", "Create templates for common success paths"],
                generated_at=datetime.now()
            ))

        # Bottleneck insights
        bottlenecks = analysis_results.get("learner_analysis", {}).get("bottlenecks", [])
        for bottleneck in bottlenecks:
            insights.append(LearningInsight(
                insight_id=f"insight_{datetime.now().timestamp()}_bottleneck_{bottleneck['type']}",
                insight_type="bottleneck",
                description=f"Detected {bottleneck['type']} affecting {bottleneck.get('frequency', 0)} operations",
                confidence=0.9,
                impact_potential="high",
                related_agents=["analyzer", "improver"],
                recommended_actions=bottleneck.get("impact", "").split(", "),
                generated_at=datetime.now()
            ))

        # Performance insights
        perf_metrics = analysis_results.get("performance_metrics", {})
        agent_metrics = perf_metrics.get("agent_metrics", {})

        # Find efficiency leaders and laggards
        if agent_metrics:
            efficiencies = {name: metrics.get("efficiency_score", 0)
                          for name, metrics in agent_metrics.items()}

            if efficiencies:
                best_agent = max(efficiencies.items(), key=lambda x: x[1])
                worst_agent = min(efficiencies.items(), key=lambda x: x[1])

                if best_agent[1] > worst_agent[1] * 1.5:  # Significant difference
                    insights.append(LearningInsight(
                        insight_id=f"insight_{datetime.now().timestamp()}_efficiency_gap",
                        insight_type="optimization",
                        description=f"Performance gap between {best_agent[0]} ({best_agent[1]:.2f}) and {worst_agent[0]} ({worst_agent[1]:.2f})",
                        confidence=0.8,
                        impact_potential="medium",
                        related_agents=[best_agent[0], worst_agent[0]],
                        recommended_actions=["Analyze best practices from top performer", "Apply optimizations to underperformer"],
                        generated_at=datetime.now()
                    ))

        return insights

    async def _implement_optimizations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Implement selected optimizations using the improvement applicator"""
        actions_taken = []

        if not self.auto_apply_optimizations:
            logger.info(f"Auto-apply disabled. Generated {len(recommendations)} recommendations for manual review")
            return actions_taken

        # Convert recommendations to learning insights for the applicator
        insights = []
        for rec in recommendations:
            if rec.get("confidence", 0) >= self.minimum_confidence_threshold:
                insight = LearningInsight(
                    insight_id=rec.get("insight_id", f"rec_{datetime.now().timestamp()}"),
                    insight_type=rec.get("source", "optimization"),
                    description=rec.get("action", "Optimization recommendation"),
                    confidence=rec.get("confidence", 0.5),
                    impact_potential=rec.get("priority", "medium"),
                    related_agents=[rec.get("agent", "system")] if rec.get("agent") != "system" else ["all"],
                    recommended_actions=[rec.get("action", "")],
                    generated_at=datetime.now()
                )
                insights.append(insight)

        # Apply insights using the improvement applicator
        applied_improvements = await self.improvement_applicator.apply_learning_insights(
            insights, auto_apply=True, confidence_threshold=self.minimum_confidence_threshold
        )

        # Convert applied improvements to actions_taken format
        for applied in applied_improvements:
            actions_taken.append({
                "recommendation": {
                    "action": applied.description,
                    "confidence": 0.8,  # Would come from insight
                    "type": applied.improvement_type
                },
                "action_taken": applied.improvement_type,
                "result": {"improvement_id": applied.improvement_id},
                "timestamp": applied.applied_at
            })
            logger.info(f"Applied improvement: {applied.improvement_id} - {applied.description}")

        return actions_taken

    async def _evaluate_impact(self, implementation_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate the impact of implemented optimizations"""
        if not implementation_actions:
            return {"impact": "none", "measurements": {}}

        # Wait a bit for changes to take effect
        await asyncio.sleep(10)

        # Measure current performance
        current_performance = await self._observe_performance()

        # Use improvement applicator to measure impact of applied improvements
        impact_measurements = []
        for action in implementation_actions:
            result = action.get("result", {})
            improvement_id = result.get("improvement_id")
            if improvement_id:
                impact = await self.improvement_applicator.measure_improvement_impact(improvement_id)
                impact_measurements.append(impact)

        evaluation = {
            "actions_evaluated": len(implementation_actions),
            "current_performance": current_performance,
            "impact_measurements": impact_measurements,
            "improvements_with_impact": len(impact_measurements),
            "impact": "measured",
            "timestamp": datetime.now()
        }

        return evaluation

    async def _establish_performance_baseline(self):
        """Establish baseline performance metrics for anomaly detection"""
        logger.info("Establishing performance baseline")

        # Collect metrics over a short period to establish baseline
        baseline_samples = []
        for _ in range(3):  # Take 3 samples
            performance_data = await self._observe_performance()
            baseline_samples.append(performance_data)
            await asyncio.sleep(10)  # Wait between samples

        # Calculate baseline averages
        if baseline_samples:
            agent_metrics_samples = [s.get("performance_report", {}).get("agent_metrics", {}) for s in baseline_samples]
            system_metrics_samples = [s.get("performance_report", {}).get("system_metrics", {}) for s in baseline_samples]

            # Average agent metrics
            agent_baseline = {}
            if agent_metrics_samples:
                all_agents = set()
                for sample in agent_metrics_samples:
                    all_agents.update(sample.keys())

                for agent in all_agents:
                    agent_samples = [s.get(agent, {}) for s in agent_metrics_samples if agent in s]
                    if agent_samples:
                        agent_baseline[agent] = {
                            "avg_response_time": statistics.mean([s.get("avg_response_time", 0) for s in agent_samples]),
                            "success_rate": statistics.mean([s.get("success_rate", 1.0) for s in agent_samples]),
                            "efficiency_score": statistics.mean([s.get("efficiency_score", 1.0) for s in agent_samples])
                        }

            # Average system metrics
            system_baseline = {}
            if system_metrics_samples:
                system_baseline = {
                    "system_efficiency": statistics.mean([s.get("system_efficiency", 1.0) for s in system_metrics_samples]),
                    "total_agent_calls": statistics.mean([s.get("total_agent_calls", 0) for s in system_metrics_samples])
                }

            self.performance_baseline = {
                "agent_metrics": agent_baseline,
                "system_metrics": system_baseline,
                "established_at": datetime.now()
            }

            logger.info(f"Performance baseline established with {len(agent_baseline)} agents")

    async def _monitor_system_performance(self):
        """Monitor system performance for anomalies and trigger adaptations"""
        current_performance = await self._observe_performance()

        if not self.performance_baseline:
            return  # No baseline established yet

        # Check for anomalies
        anomalies = await self._detect_performance_anomalies(current_performance)

        if anomalies:
            logger.info(f"Detected {len(anomalies)} performance anomalies")
            await self._handle_performance_anomalies(anomalies, current_performance)

        # Check for adaptation opportunities
        if self.adaptation_enabled:
            adaptations = await self._identify_adaptation_opportunities(current_performance)
            if adaptations:
                await self._apply_adaptations(adaptations)

    async def _detect_performance_anomalies(self, current_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect performance anomalies compared to baseline"""
        anomalies = []

        current_report = current_performance.get("performance_report", {})
        current_agent_metrics = current_report.get("agent_metrics", {})
        current_system_metrics = current_report.get("system_metrics", {})

        baseline_agent_metrics = self.performance_baseline.get("agent_metrics", {})
        baseline_system_metrics = self.performance_baseline.get("system_metrics", {})

        # Check agent-level anomalies
        for agent_name, current_metrics in current_agent_metrics.items():
            baseline_metrics = baseline_agent_metrics.get(agent_name)
            if not baseline_metrics:
                continue

            # Check response time anomaly
            current_time = current_metrics.get("avg_response_time", 0)
            baseline_time = baseline_metrics.get("avg_response_time", 0)
            if baseline_time > 0:
                time_deviation = abs(current_time - baseline_time) / baseline_time
                if time_deviation > self.anomaly_threshold:
                    anomalies.append({
                        "type": "response_time_anomaly",
                        "agent": agent_name,
                        "severity": "high" if time_deviation > 0.5 else "medium",
                        "current_value": current_time,
                        "baseline_value": baseline_time,
                        "deviation": time_deviation
                    })

            # Check success rate anomaly
            current_success = current_metrics.get("success_rate", 1.0)
            baseline_success = baseline_metrics.get("success_rate", 1.0)
            success_deviation = abs(current_success - baseline_success)
            if success_deviation > self.anomaly_threshold:
                anomalies.append({
                    "type": "success_rate_anomaly",
                    "agent": agent_name,
                    "severity": "high" if success_deviation > 0.3 else "medium",
                    "current_value": current_success,
                    "baseline_value": baseline_success,
                    "deviation": success_deviation
                })

        # Check system-level anomalies
        current_efficiency = current_system_metrics.get("system_efficiency", 1.0)
        baseline_efficiency = baseline_system_metrics.get("system_efficiency", 1.0)
        efficiency_deviation = abs(current_efficiency - baseline_efficiency)
        if efficiency_deviation > self.anomaly_threshold:
            anomalies.append({
                "type": "system_efficiency_anomaly",
                "severity": "high" if efficiency_deviation > 0.3 else "medium",
                "current_value": current_efficiency,
                "baseline_value": baseline_efficiency,
                "deviation": efficiency_deviation
            })

        return anomalies

    async def _handle_performance_anomalies(self, anomalies: List[Dict[str, Any]], current_performance: Dict[str, Any]):
        """Handle detected performance anomalies"""
        for anomaly in anomalies:
            logger.warning(f"Handling anomaly: {anomaly['type']} for {anomaly.get('agent', 'system')}")

            # Create emergency insights for critical anomalies
            if anomaly["severity"] == "high":
                insight = LearningInsight(
                    insight_id=f"anomaly_{datetime.now().timestamp()}_{anomaly['type']}",
                    insight_type="anomaly",
                    description=f"Critical performance anomaly detected: {anomaly['type']}",
                    confidence=0.9,
                    impact_potential="high",
                    related_agents=[anomaly["agent"]] if "agent" in anomaly else ["system"],
                    recommended_actions=["Apply immediate healing", "Trigger emergency optimization"],
                    generated_at=datetime.now()
                )

                # Apply immediate healing for critical anomalies
                if self.auto_apply_optimizations:
                    healing_applied = await self.improvement_applicator.apply_learning_insights([insight], auto_apply=True)
                    if healing_applied:
                        logger.info(f"Applied emergency healing for anomaly: {anomaly['type']}")

    async def _identify_adaptation_opportunities(self, current_performance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify opportunities for proactive adaptation"""
        adaptations = []

        # Check for underutilized agents that could take more load
        agent_metrics = current_performance.get("performance_report", {}).get("agent_metrics", {})

        high_performers = []
        low_performers = []

        for agent_name, metrics in agent_metrics.items():
            efficiency = metrics.get("efficiency_score", 1.0)
            if efficiency > 0.9:
                high_performers.append(agent_name)
            elif efficiency < 0.7:
                low_performers.append(agent_name)

        # Suggest load balancing if there's imbalance
        if high_performers and low_performers:
            adaptations.append({
                "type": "load_balancing",
                "description": f"Balance load between high performers {high_performers} and low performers {low_performers}",
                "high_performers": high_performers,
                "low_performers": low_performers
            })

        return adaptations

    async def _apply_adaptations(self, adaptations: List[Dict[str, Any]]):
        """Apply identified adaptations"""
        for adaptation in adaptations:
            logger.info(f"Applying adaptation: {adaptation['type']}")

            if adaptation["type"] == "load_balancing":
                # Implement load balancing logic
                await self._apply_load_balancing(adaptation)

    async def _apply_load_balancing(self, adaptation: Dict[str, Any]):
        """Apply load balancing adaptation"""
        # This would adjust task routing to balance load
        logger.info(f"Load balancing applied between {adaptation['high_performers']} and {adaptation['low_performers']}")

    async def _adapt_based_on_learning(self, evaluation_metrics: Dict[str, Any]):
        """Adapt system behavior based on learning results"""
        # Store learning results in memory for future reference
        learning_event = {
            "type": "learning_cycle_complete",
            "cycle_id": self.current_cycle.cycle_id if self.current_cycle else "unknown",
            "evaluation": evaluation_metrics,
            "timestamp": datetime.now()
        }

        await self.memory.store(learning_event)

        # Update learner with new insights
        if self.learning_insights:
            recent_insights = self.learning_insights[-5:]  # Last 5 insights
            await self.learner._store_learned_patterns(
                {"recent_insights": [i.description for i in recent_insights]},
                evaluation_metrics.get("current_performance", {}).get("performance_report", {}).get("system_metrics", {}).get("system_efficiency", 1.0),
                []  # No bottlenecks in this context
            )

    # Optimization action implementations
    async def _adjust_agent_weights(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust agent consensus weights based on performance"""
        # Implementation would modify consensus weights
        return {"action": "agent_weights_adjusted", "status": "simulated"}

    async def _rebalance_workload(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Rebalance workload distribution"""
        return {"action": "workload_rebalanced", "status": "simulated"}

    async def _optimize_execution_order(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize task execution order"""
        return {"action": "execution_order_optimized", "status": "simulated"}

    async def _enable_circuit_breaker(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Enable circuit breaker for failing components"""
        return {"action": "circuit_breaker_enabled", "status": "simulated"}

    async def _adjust_rate_limits(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust rate limits based on performance"""
        return {"action": "rate_limits_adjusted", "status": "simulated"}

    async def _update_consensus_weights(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Update consensus algorithm weights"""
        return {"action": "consensus_weights_updated", "status": "simulated"}

    async def _cache_frequent_patterns(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Cache frequently used patterns"""
        return {"action": "patterns_cached", "status": "simulated"}

    async def _parallelize_independent_tasks(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Parallelize independent tasks"""
        return {"action": "tasks_parallelized", "status": "simulated"}

    # Public interface methods
    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current learning loop status"""
        return {
            "running": self.running,
            "current_cycle": self.current_cycle.cycle_id if self.current_cycle else None,
            "total_cycles": len(self.learning_cycles),
            "successful_cycles": len([c for c in self.learning_cycles if c.success]),
            "total_insights": len(self.learning_insights),
            "applied_insights": len([i for i in self.learning_insights if i.applied]),
            "cycle_interval": self.cycle_interval,
            "auto_apply_enabled": self.auto_apply_optimizations
        }

    async def get_recent_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent learning insights"""
        recent = self.learning_insights[-limit:]
        return [{
            "id": i.insight_id,
            "type": i.insight_type,
            "description": i.description,
            "confidence": i.confidence,
            "impact": i.impact_potential,
            "applied": i.applied,
            "generated_at": i.generated_at.isoformat()
        } for i in recent]

    async def get_cycle_history(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent learning cycle history"""
        recent = self.learning_cycles[-limit:]
        return [{
            "id": c.cycle_id,
            "start_time": c.start_time.isoformat(),
            "end_time": c.end_time.isoformat() if c.end_time else None,
            "duration": c.get_duration(),
            "success": c.success,
            "phase": c.phase.value,
            "recommendations_count": len(c.optimization_recommendations),
            "actions_count": len(c.implementation_actions)
        } for c in recent]

    async def trigger_manual_cycle(self) -> Dict[str, Any]:
        """Manually trigger a learning cycle"""
        cycle = await self.execute_learning_cycle()
        return {
            "cycle_id": cycle.cycle_id,
            "success": cycle.success,
            "duration": cycle.get_duration(),
            "recommendations": len(cycle.optimization_recommendations)
        } if cycle else {"error": "Failed to execute cycle"}

    def set_auto_apply(self, enabled: bool):
        """Enable or disable automatic optimization application"""
        self.auto_apply_optimizations = enabled
        logger.info(f"Auto-apply optimizations: {'enabled' if enabled else 'disabled'}")

    def set_confidence_threshold(self, threshold: float):
        """Set minimum confidence threshold for optimizations"""
        self.minimum_confidence_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Confidence threshold set to {self.minimum_confidence_threshold}")