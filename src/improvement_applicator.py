# src/improvement_applicator.py
"""
Improvement Applicator for ZEJZL.NET Learning Loop.

Applies learning insights and optimization recommendations to improve system performance,
providing feedback loops for continuous optimization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from src.agents.profiling import AgentProfiler
from src.learning_loop import LearningInsight
from src.agents.consensus import ConsensusManager
from src.magic import FairyMagic

logger = logging.getLogger("ImprovementApplicator")


@dataclass
class AppliedImprovement:
    """Record of an applied improvement"""
    improvement_id: str
    insight_id: str
    improvement_type: str
    description: str
    applied_at: datetime
    expected_impact: str
    actual_impact: Optional[Dict[str, Any]] = None
    success: bool = False
    rollback_possible: bool = False
    rollback_data: Optional[Dict[str, Any]] = None


@dataclass
class ImprovementAction:
    """An improvement action that can be applied"""
    action_id: str
    action_type: str
    description: str
    apply_function: Callable
    rollback_function: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)


class ImprovementApplicator:
    """
    Applies learning insights to improve system performance
    """

    def __init__(self, profiler: AgentProfiler, consensus_manager: ConsensusManager, magic_system: Optional[FairyMagic] = None):
        self.profiler = profiler
        self.consensus_manager = consensus_manager
        self.magic_system = magic_system or FairyMagic()
        self.applied_improvements: List[AppliedImprovement] = []
        self.improvement_actions: Dict[str, ImprovementAction] = {}
        self.active_improvements: Dict[str, AppliedImprovement] = {}

        # Register available improvement actions
        self._register_improvement_actions()

    # Magic-based improvement actions
    async def _apply_blue_spark_healing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply blue spark healing to failing components"""
        insight_data = parameters.get("insight_data", {})
        related_agents = insight_data.get("related_agents", [])

        healed_components = []
        for agent in related_agents:
            # Map agent names to magic system components
            component_map = {
                "observer": "ai_provider",
                "reasoner": "agent_coordinator",
                "actor": "tool_call",
                "executor": "tool_call",
                "analyzer": "persistence",
                "learner": "agent_coordinator",
                "improver": "agent_coordinator",
                "memory": "persistence"
            }

            component = component_map.get(agent.lower(), "agent_coordinator")
            issue = f"Performance issues detected for {agent}"

            healed = await self.magic_system.blue_spark_heal(component, issue)
            if healed:
                healed_components.append(agent)

        return {
            "action": "blue_spark_healing_applied",
            "healed_components": healed_components,
            "rollback_data": {}
        }

    async def _apply_acorn_vitality_boost(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Apply acorn vitality boost to underperforming agents"""
        insight_data = parameters.get("insight_data", {})
        related_agents = insight_data.get("related_agents", [])

        boosted_agents = []
        for agent in related_agents:
            agent_config = {"max_tokens": 1024}  # Could load actual config
            boost_result = await self.magic_system.acorn_vitality_boost(agent, agent_config)

            if boost_result.get("vitality_boost", 0) > 0:
                boosted_agents.append({
                    "agent": agent,
                    "boost_factor": boost_result["vitality_boost"],
                    "new_config": boost_result.get("new_config", {})
                })

        return {
            "action": "acorn_vitality_boost_applied",
            "boosted_agents": boosted_agents,
            "acorns_remaining": self.magic_system.acorn_reserve,
            "rollback_data": {}
        }

    async def _apply_fairy_shield_activation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Activate fairy shield for protection"""
        activated = await self.magic_system.fairy_shield(True)

        return {
            "action": "fairy_shield_activated",
            "success": activated,
            "current_energy": self.magic_system.energy_level,
            "rollback_data": {"was_shielded": self.magic_system.is_shielded}
        }

    async def _rollback_fairy_shield_activation(self, rollback_data: Dict[str, Any]):
        """Rollback fairy shield activation"""
        was_shielded = rollback_data.get("was_shielded", False)
        await self.magic_system.fairy_shield(was_shielded)

    async def _apply_circuit_breaker_reset(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Reset circuit breaker for components with transient failures"""
        insight_data = parameters.get("insight_data", {})
        related_agents = insight_data.get("related_agents", [])

        reset_components = []
        for agent in related_agents:
            component_map = {
                "observer": "ai_provider",
                "reasoner": "agent_coordinator",
                "actor": "tool_call",
                "executor": "tool_call",
                "analyzer": "persistence",
                "learner": "agent_coordinator",
                "improver": "agent_coordinator",
                "memory": "persistence"
            }

            component = component_map.get(agent.lower(), "agent_coordinator")
            reset = await self.magic_system.reset_circuit_breaker(component)
            if reset:
                reset_components.append(component)

        return {
            "action": "circuit_breakers_reset",
            "reset_components": reset_components,
            "rollback_data": {}
        }

    async def _apply_holly_blessing_ritual(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform holly blessing ritual for task success enhancement"""
        ritual_result = await self.magic_system.perform_ritual("holly_blessing")

        return {
            "action": "holly_blessing_ritual_performed",
            "ritual_result": ritual_result,
            "current_energy": self.magic_system.energy_level,
            "rollback_data": {}
        }

    def _register_improvement_actions(self):
        """Register all available improvement actions"""
        self.improvement_actions = {
            "rate_limit_adjustment": ImprovementAction(
                action_id="rate_limit_adjustment",
                action_type="performance",
                description="Adjust rate limits based on performance analysis",
                apply_function=self._apply_rate_limit_adjustment,
                rollback_function=self._rollback_rate_limit_adjustment,
                required_permissions=["rate_limit_management"]
            ),
            "agent_weight_rebalancing": ImprovementAction(
                action_id="agent_weight_rebalancing",
                action_type="coordination",
                description="Rebalance agent consensus weights for better coordination",
                apply_function=self._apply_agent_weight_rebalancing,
                rollback_function=self._rollback_agent_weight_rebalancing,
                required_permissions=["consensus_management"]
            ),
            "caching_optimization": ImprovementAction(
                action_id="caching_optimization",
                action_type="performance",
                description="Implement intelligent caching for frequent operations",
                apply_function=self._apply_caching_optimization,
                required_permissions=["cache_management"]
            ),
            "parallel_processing": ImprovementAction(
                action_id="parallel_processing",
                action_type="performance",
                description="Enable parallel processing for independent tasks",
                apply_function=self._apply_parallel_processing,
                required_permissions=["execution_management"]
            ),
            "error_handling_enhancement": ImprovementAction(
                action_id="error_handling_enhancement",
                action_type="reliability",
                description="Enhance error handling and recovery mechanisms",
                apply_function=self._apply_error_handling_enhancement,
                required_permissions=["error_handling"]
            ),
            "resource_allocation": ImprovementAction(
                action_id="resource_allocation",
                action_type="performance",
                description="Optimize resource allocation based on usage patterns",
                apply_function=self._apply_resource_allocation,
                required_permissions=["resource_management"]
            ),
            # Magic-based self-healing actions
            "blue_spark_healing": ImprovementAction(
                action_id="blue_spark_healing",
                action_type="reliability",
                description="Apply blue spark healing to failing components",
                apply_function=self._apply_blue_spark_healing,
                required_permissions=["magic_system"]
            ),
            "acorn_vitality_boost": ImprovementAction(
                action_id="acorn_vitality_boost",
                action_type="performance",
                description="Apply acorn vitality boost to underperforming agents",
                apply_function=self._apply_acorn_vitality_boost,
                required_permissions=["magic_system"]
            ),
            "fairy_shield_activation": ImprovementAction(
                action_id="fairy_shield_activation",
                action_type="reliability",
                description="Activate fairy shield for protection during high-risk operations",
                apply_function=self._apply_fairy_shield_activation,
                rollback_function=self._rollback_fairy_shield_activation,
                required_permissions=["magic_system"]
            ),
            "circuit_breaker_reset": ImprovementAction(
                action_id="circuit_breaker_reset",
                action_type="reliability",
                description="Reset circuit breaker for components with transient failures",
                apply_function=self._apply_circuit_breaker_reset,
                required_permissions=["magic_system"]
            ),
            "holly_blessing_ritual": ImprovementAction(
                action_id="holly_blessing_ritual",
                action_type="performance",
                description="Perform holly blessing ritual for task success enhancement",
                apply_function=self._apply_holly_blessing_ritual,
                required_permissions=["magic_system"]
            )
        }

    async def apply_learning_insights(self, insights: List[LearningInsight],
                                    auto_apply: bool = False,
                                    confidence_threshold: float = 0.7) -> List[AppliedImprovement]:
        """
        Apply learning insights to improve the system
        """
        applied_improvements = []

        for insight in insights:
            if insight.applied:
                continue  # Already applied

            if insight.confidence < confidence_threshold:
                logger.debug(f"Skipping insight {insight.insight_id}: confidence {insight.confidence} below threshold {confidence_threshold}")
                continue

            # Determine appropriate action based on insight
            action = await self._select_action_for_insight(insight)
            if not action:
                logger.debug(f"No suitable action found for insight {insight.insight_id}")
                continue

            # Apply the improvement if auto-apply is enabled
            if auto_apply:
                applied = await self._apply_improvement_action(insight, action)
                if applied:
                    applied_improvements.append(applied)
                    insight.applied = True
                    insight.applied_at = datetime.now()
            else:
                # Just mark as available for manual application
                logger.info(f"Improvement available for insight {insight.insight_id}: {action.description}")

        return applied_improvements

    async def _select_action_for_insight(self, insight: LearningInsight) -> Optional[ImprovementAction]:
        """Select the most appropriate action for a given insight"""
        insight_type = insight.insight_type
        recommended_actions = insight.recommended_actions

        # Map insight types to actions
        type_action_map = {
            "bottleneck": "performance",
            "pattern": "coordination",
            "anomaly": "reliability",
            "optimization": "performance"
        }

        target_action_type = type_action_map.get(insight_type, "performance")

        # Find actions that match the insight's recommendations
        for action in self.improvement_actions.values():
            if action.action_type == target_action_type:
                # Check if action description matches any recommendation
                for rec_action in recommended_actions:
                    if any(keyword in rec_action.lower() for keyword in action.action_id.split("_")):
                        return action

        # Fallback: return first action of matching type
        for action in self.improvement_actions.values():
            if action.action_type == target_action_type:
                return action

        return None

    async def _apply_improvement_action(self, insight: LearningInsight,
                                      action: ImprovementAction) -> Optional[AppliedImprovement]:
        """Apply a specific improvement action"""
        try:
            logger.info(f"Applying improvement action: {action.action_id} for insight {insight.insight_id}")

            # Prepare parameters for the action
            parameters = action.parameters.copy()
            parameters.update({
                "insight": insight,
                "insight_data": {
                    "type": insight.insight_type,
                    "confidence": insight.confidence,
                    "impact_potential": insight.impact_potential,
                    "related_agents": insight.related_agents
                }
            })

            # Apply the improvement
            result = await action.apply_function(parameters)

            # Create applied improvement record
            applied = AppliedImprovement(
                improvement_id=f"imp_{datetime.now().timestamp()}",
                insight_id=insight.insight_id,
                improvement_type=action.action_type,
                description=action.description,
                applied_at=datetime.now(),
                expected_impact=insight.impact_potential,
                success=True,
                rollback_possible=action.rollback_function is not None,
                rollback_data=result.get("rollback_data") if isinstance(result, dict) else None
            )

            self.applied_improvements.append(applied)
            self.active_improvements[applied.improvement_id] = applied

            logger.info(f"Successfully applied improvement: {applied.improvement_id}")
            return applied

        except Exception as e:
            logger.error(f"Failed to apply improvement action {action.action_id}: {e}")
            return None

    async def measure_improvement_impact(self, improvement_id: str) -> Dict[str, Any]:
        """Measure the actual impact of an applied improvement"""
        if improvement_id not in self.active_improvements:
            return {"error": "Improvement not found"}

        improvement = self.active_improvements[improvement_id]

        # Get current performance metrics
        current_report = await self.profiler.get_performance_report()

        # Compare with baseline (would need to store baseline when improvement is applied)
        # For now, just report current state
        impact = {
            "improvement_id": improvement_id,
            "measured_at": datetime.now(),
            "current_performance": current_report,
            "impact_assessment": "measured",
            "baseline_comparison": "not_available"  # Would compare with pre-improvement metrics
        }

        improvement.actual_impact = impact
        return impact

    async def rollback_improvement(self, improvement_id: str) -> bool:
        """Rollback an applied improvement"""
        if improvement_id not in self.active_improvements:
            return False

        improvement = self.active_improvements[improvement_id]
        if not improvement.rollback_possible:
            logger.warning(f"Improvement {improvement_id} cannot be rolled back")
            return False

        # Find the corresponding action
        action = None
        for act in self.improvement_actions.values():
            if act.action_id in improvement.description.lower().replace(" ", "_"):
                action = act
                break

        if not action or not action.rollback_function:
            return False

        try:
            await action.rollback_function(improvement.rollback_data or {})
            improvement.success = False
            del self.active_improvements[improvement_id]
            logger.info(f"Successfully rolled back improvement: {improvement_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback improvement {improvement_id}: {e}")
            return False

    # Improvement Action Implementations
    async def _apply_rate_limit_adjustment(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust rate limits based on performance analysis"""
        # This would integrate with the rate limiter
        # For now, simulate the adjustment
        return {
            "action": "rate_limits_adjusted",
            "rollback_data": {"original_limits": {}}
        }

    async def _rollback_rate_limit_adjustment(self, rollback_data: Dict[str, Any]):
        """Rollback rate limit adjustments"""
        # Restore original limits
        pass

    async def _apply_agent_weight_rebalancing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Rebalance agent consensus weights"""
        insight_data = parameters.get("insight_data", {})
        related_agents = insight_data.get("related_agents", [])

        # Adjust weights for related agents
        original_weights = {}
        for agent in related_agents:
            # This would modify consensus manager weights
            original_weights[agent] = 1.0  # Placeholder

        return {
            "action": "agent_weights_rebalanced",
            "rollback_data": {"original_weights": original_weights}
        }

    async def _rollback_agent_weight_rebalancing(self, rollback_data: Dict[str, Any]):
        """Rollback agent weight changes"""
        # Restore original weights
        pass

    async def _apply_caching_optimization(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Implement intelligent caching"""
        # This would enable caching for frequent operations
        return {
            "action": "caching_optimized",
            "rollback_data": {}
        }

    async def _apply_parallel_processing(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enable parallel processing for independent tasks"""
        # This would modify execution to allow parallelism
        return {
            "action": "parallel_processing_enabled",
            "rollback_data": {}
        }

    async def _apply_error_handling_enhancement(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance error handling mechanisms"""
        # This would improve error recovery
        return {
            "action": "error_handling_enhanced",
            "rollback_data": {}
        }

    async def _apply_resource_allocation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resource allocation"""
        # This would adjust resource distribution
        return {
            "action": "resources_reallocated",
            "rollback_data": {}
        }

    # Public interface methods
    async def get_applied_improvements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of applied improvements"""
        recent = self.applied_improvements[-limit:]
        return [{
            "id": imp.improvement_id,
            "type": imp.improvement_type,
            "description": imp.description,
            "applied_at": imp.applied_at.isoformat(),
            "success": imp.success,
            "expected_impact": imp.expected_impact
        } for imp in recent]

    async def get_improvement_status(self) -> Dict[str, Any]:
        """Get overall improvement status"""
        total_applied = len(self.applied_improvements)
        active_count = len(self.active_improvements)
        successful_count = len([imp for imp in self.applied_improvements if imp.success])

        return {
            "total_improvements_applied": total_applied,
            "active_improvements": active_count,
            "successful_improvements": successful_count,
            "success_rate": successful_count / total_applied if total_applied > 0 else 0,
            "available_actions": len(self.improvement_actions)
        }

    def set_auto_apply_threshold(self, threshold: float):
        """Set confidence threshold for auto-applying improvements"""
        # This would be used by the learning loop
        pass