# src/agents/profiling.py
"""
Agent Performance Profiling and Optimization for ZEJZL.NET Pantheon System.

Tracks agent performance metrics, identifies bottlenecks, and provides optimization
recommendations for improved multi-agent coordination and execution.
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger("AgentProfiler")


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent"""
    agent_name: str
    agent_role: str

    # Timing metrics
    total_calls: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    response_times: List[float] = field(default_factory=list)

    # Success metrics
    successful_calls: int = 0
    failed_calls: int = 0
    success_rate: float = 0.0

    # Resource metrics
    memory_usage: float = 0.0
    cpu_usage: float = 0.0

    # Coordination metrics
    messages_sent: int = 0
    messages_received: int = 0
    conflicts_participated: int = 0
    consensus_reached: int = 0

    # Performance scores
    efficiency_score: float = 1.0  # 0.0 to 1.0
    reliability_score: float = 1.0  # 0.0 to 1.0
    coordination_score: float = 1.0  # 0.0 to 1.0

    def update_response_time(self, response_time: float, success: bool = True):
        """Update timing metrics"""
        self.total_calls += 1
        self.total_response_time += response_time
        self.avg_response_time = self.total_response_time / self.total_calls
        self.min_response_time = min(self.min_response_time, response_time)
        self.max_response_time = max(self.max_response_time, response_time)

        # Keep last 100 response times for analysis
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)

        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1

        total_attempts = self.successful_calls + self.failed_calls
        if total_attempts > 0:
            self.success_rate = self.successful_calls / total_attempts

    def calculate_scores(self):
        """Calculate performance scores"""
        # Efficiency: inverse of normalized response time (lower is better)
        if self.response_times:
            avg_time = statistics.mean(self.response_times)
            # Normalize against expected response time (assume 1 second baseline)
            self.efficiency_score = max(0.1, min(1.0, 1.0 / (1.0 + avg_time)))

        # Reliability: success rate
        self.reliability_score = self.success_rate

        # Coordination: consensus reached vs conflicts participated
        total_coordination = self.conflicts_participated + self.consensus_reached
        if total_coordination > 0:
            self.coordination_score = self.consensus_reached / total_coordination
        else:
            self.coordination_score = 1.0

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        self.calculate_scores()
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "total_calls": self.total_calls,
            "avg_response_time": round(self.avg_response_time, 3),
            "success_rate": round(self.success_rate, 3),
            "efficiency_score": round(self.efficiency_score, 3),
            "reliability_score": round(self.reliability_score, 3),
            "coordination_score": round(self.coordination_score, 3),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "conflicts_participated": self.conflicts_participated,
            "consensus_reached": self.consensus_reached
        }


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation for an agent"""
    agent_name: str
    recommendation_type: str  # "performance", "reliability", "coordination"
    priority: str  # "high", "medium", "low"
    description: str
    expected_impact: str
    implementation_effort: str  # "low", "medium", "high"
    metrics: Dict[str, Any] = field(default_factory=dict)


class AgentProfiler:
    """
    Profiles agent performance and provides optimization recommendations
    """

    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.optimization_history: List[OptimizationRecommendation] = []
        self.max_history = max_history
        self.system_metrics = {
            "total_agent_calls": 0,
            "total_response_time": 0.0,
            "system_efficiency": 1.0,
            "bottlenecks_identified": 0,
            "optimizations_applied": 0
        }

    def get_or_create_metrics(self, agent_name: str, agent_role: str) -> PerformanceMetrics:
        """Get or create performance metrics for an agent"""
        if agent_name not in self.metrics:
            self.metrics[agent_name] = PerformanceMetrics(agent_name, agent_role)
        return self.metrics[agent_name]

    async def record_agent_call(self, agent_name: str, agent_role: str,
                               response_time: float, success: bool = True):
        """Record an agent method call"""
        metrics = self.get_or_create_metrics(agent_name, agent_role)
        metrics.update_response_time(response_time, success)

        # Update system metrics
        self.system_metrics["total_agent_calls"] += 1
        self.system_metrics["total_response_time"] += response_time

    async def record_message_sent(self, agent_name: str, agent_role: str):
        """Record a message sent by an agent"""
        metrics = self.get_or_create_metrics(agent_name, agent_role)
        metrics.messages_sent += 1

    async def record_message_received(self, agent_name: str, agent_role: str):
        """Record a message received by an agent"""
        metrics = self.get_or_create_metrics(agent_name, agent_role)
        metrics.messages_received += 1

    async def record_conflict_participation(self, agent_name: str, agent_role: str,
                                          consensus_reached: bool = True):
        """Record participation in conflict resolution"""
        metrics = self.get_or_create_metrics(agent_name, agent_role)
        metrics.conflicts_participated += 1
        if consensus_reached:
            metrics.consensus_reached += 1

    async def analyze_performance(self) -> List[OptimizationRecommendation]:
        """Analyze all agent performance and generate optimization recommendations"""
        recommendations = []

        # Calculate system-wide metrics
        if self.system_metrics["total_agent_calls"] > 0:
            avg_system_time = (self.system_metrics["total_response_time"] /
                             self.system_metrics["total_agent_calls"])
            self.system_metrics["system_efficiency"] = max(0.1, min(1.0, 1.0 / (1.0 + avg_system_time)))

        # Analyze individual agents
        for agent_name, metrics in self.metrics.items():
            recs = await self._analyze_agent_performance(metrics)
            recommendations.extend(recs)

        # Analyze system-wide bottlenecks
        system_recs = await self._analyze_system_bottlenecks()
        recommendations.extend(system_recs)

        # Sort by priority
        priority_order = {"high": 3, "medium": 2, "low": 1}
        recommendations.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)

        # Store recommendations
        self.optimization_history.extend(recommendations)
        if len(self.optimization_history) > self.max_history:
            self.optimization_history = self.optimization_history[-self.max_history:]

        return recommendations

    async def _analyze_agent_performance(self, metrics: PerformanceMetrics) -> List[OptimizationRecommendation]:
        """Analyze individual agent performance"""
        recommendations = []

        # Performance analysis
        if metrics.avg_response_time > 2.0:  # Slow response
            recommendations.append(OptimizationRecommendation(
                agent_name=metrics.agent_name,
                recommendation_type="performance",
                priority="high",
                description=f"Optimize {metrics.agent_name} response time (currently {metrics.avg_response_time:.2f}s)",
                expected_impact="Reduce response time by 30-50%",
                implementation_effort="medium",
                metrics={"current_avg_time": metrics.avg_response_time}
            ))

        if metrics.success_rate < 0.8:  # Low success rate
            recommendations.append(OptimizationRecommendation(
                agent_name=metrics.agent_name,
                recommendation_type="reliability",
                priority="high",
                description=f"Improve {metrics.agent_name} success rate (currently {metrics.success_rate:.1%})",
                expected_impact="Increase success rate by 20-30%",
                implementation_effort="medium",
                metrics={"current_success_rate": metrics.success_rate}
            ))

        if metrics.efficiency_score < 0.7:
            recommendations.append(OptimizationRecommendation(
                agent_name=metrics.agent_name,
                recommendation_type="performance",
                priority="medium",
                description=f"Enhance {metrics.agent_name} efficiency (score: {metrics.efficiency_score:.2f})",
                expected_impact="Improve efficiency by 15-25%",
                implementation_effort="low",
                metrics={"efficiency_score": metrics.efficiency_score}
            ))

        # Coordination analysis
        if metrics.coordination_score < 0.8 and metrics.conflicts_participated > 0:
            recommendations.append(OptimizationRecommendation(
                agent_name=metrics.agent_name,
                recommendation_type="coordination",
                priority="medium",
                description=f"Improve {metrics.agent_name} consensus participation (score: {metrics.coordination_score:.2f})",
                expected_impact="Better conflict resolution outcomes",
                implementation_effort="low",
                metrics={"coordination_score": metrics.coordination_score}
            ))

        return recommendations

    async def _analyze_system_bottlenecks(self) -> List[OptimizationRecommendation]:
        """Analyze system-wide bottlenecks"""
        recommendations = []

        # Find slowest agents
        if len(self.metrics) >= 3:
            sorted_by_time = sorted(self.metrics.values(),
                                  key=lambda m: m.avg_response_time,
                                  reverse=True)
            slowest_agent = sorted_by_time[0]

            if slowest_agent.avg_response_time > 1.5 * sorted_by_time[-1].avg_response_time:
                recommendations.append(OptimizationRecommendation(
                    agent_name="system",
                    recommendation_type="performance",
                    priority="high",
                    description=f"Address system bottleneck: {slowest_agent.agent_name} is significantly slower",
                    expected_impact="Balance system performance",
                    implementation_effort="high",
                    metrics={"bottleneck_agent": slowest_agent.agent_name,
                           "bottleneck_time": slowest_agent.avg_response_time}
                ))

        # Low success rate agents
        low_success_agents = [m for m in self.metrics.values() if m.success_rate < 0.7]
        if len(low_success_agents) > len(self.metrics) * 0.3:  # More than 30% have low success
            recommendations.append(OptimizationRecommendation(
                agent_name="system",
                recommendation_type="reliability",
                priority="high",
                description="Multiple agents have low success rates - review error handling",
                expected_impact="Improve overall system reliability",
                implementation_effort="medium",
                metrics={"low_success_count": len(low_success_agents)}
            ))

        return recommendations

    async def get_performance_report(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if agent_name:
            metrics = self.metrics.get(agent_name)
            if not metrics:
                return {"error": f"No metrics found for agent {agent_name}"}
            return {
                "agent_metrics": metrics.get_performance_report(),
                "recent_recommendations": [
                    r for r in self.optimization_history[-5:]
                    if r.agent_name == agent_name
                ]
            }

        # System-wide report
        agent_reports = {name: metrics.get_performance_report()
                        for name, metrics in self.metrics.items()}

        return {
            "system_metrics": self.system_metrics,
            "agent_count": len(self.metrics),
            "agent_metrics": agent_reports,
            "total_recommendations": len(self.optimization_history),
            "recent_recommendations": self.optimization_history[-10:]
        }

    async def apply_optimization(self, recommendation: OptimizationRecommendation):
        """Mark an optimization as applied"""
        self.system_metrics["optimizations_applied"] += 1
        logger.info(f"Applied optimization: {recommendation.description}")

    def get_top_performing_agents(self, metric: str = "efficiency_score",
                                top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top performing agents by metric"""
        sorted_agents = sorted(
            self.metrics.values(),
            key=lambda m: getattr(m, metric, 0),
            reverse=True
        )
        return [agent.get_performance_report() for agent in sorted_agents[:top_n]]

    def get_underperforming_agents(self, threshold: float = 0.7,
                                 metric: str = "efficiency_score") -> List[Dict[str, Any]]:
        """Get agents performing below threshold"""
        underperformers = [
            agent.get_performance_report()
            for agent in self.metrics.values()
            if getattr(agent, metric, 1.0) < threshold
        ]
        return underperformers