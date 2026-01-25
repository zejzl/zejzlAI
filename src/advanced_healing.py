"""
Advanced Healing Strategies for ZEJZL.NET Phase 8
Implements component-specific healing logic with pattern recognition and predictive capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger("AdvancedHealing")


class ComponentType(Enum):
    """Types of components that can be healed"""
    AI_PROVIDER = "ai_provider"
    DATABASE = "database"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    AGENT = "agent"
    API_ENDPOINT = "api_endpoint"
    EXTERNAL_SERVICE = "external_service"


class HealingStrategy(Enum):
    """Available healing strategies"""
    RESTART = "restart"
    RECONNECT = "reconnect"
    RETRY = "retry"
    FALLBACK = "fallback"
    SCALE_UP = "scale_up"
    CIRCUIT_BREAK = "circuit_break"
    DATA_REPAIR = "data_repair"
    CONFIG_RESET = "config_reset"
    RESOURCE_BOOST = "resource_boost"


@dataclass
class FailurePattern:
    """Pattern of failures for predictive healing"""
    component: str
    component_type: ComponentType
    error_type: str
    error_message: str
    frequency: int = 0
    last_occurrence: Optional[datetime] = None
    avg_time_between_failures: Optional[float] = None
    success_rate: float = 0.0
    preferred_strategy: Optional[HealingStrategy] = None
    confidence: float = 0.0


@dataclass
class HealingAttempt:
    """Record of a healing attempt"""
    component: str
    component_type: ComponentType
    strategy: HealingStrategy
    error_details: str
    success: bool
    duration: float
    energy_used: float
    timestamp: datetime
    outcome: str
    predictive: bool = False  # Whether this was a predictive heal


@dataclass
class ComponentHealth:
    """Health status of a component"""
    component: str
    component_type: ComponentType
    health_score: float = 100.0  # 0-100
    last_check: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    avg_response_time: Optional[float] = None
    predictive_risk: float = 0.0  # Risk of failure (0-1)
    recommended_actions: List[str] = field(default_factory=list)


class ComponentHealingStrategy:
    """Strategy for healing a specific component type"""

    def __init__(self, component_type: ComponentType):
        self.component_type = component_type
        self.strategies = self._get_strategies_for_type()

    def _get_strategies_for_type(self) -> Dict[str, List[HealingStrategy]]:
        """Get healing strategies for different error types"""
        base_strategies = {
            ComponentType.AI_PROVIDER: {
                "timeout": [HealingStrategy.RETRY, HealingStrategy.RECONNECT, HealingStrategy.CIRCUIT_BREAK],
                "rate_limit": [HealingStrategy.RETRY, HealingStrategy.RESOURCE_BOOST],
                "auth_error": [HealingStrategy.CONFIG_RESET, HealingStrategy.RECONNECT],
                "model_error": [HealingStrategy.FALLBACK, HealingStrategy.RESTART],
                "network_error": [HealingStrategy.RECONNECT, HealingStrategy.RETRY],
            },
            ComponentType.DATABASE: {
                "connection_error": [HealingStrategy.RECONNECT, HealingStrategy.RESTART],
                "timeout": [HealingStrategy.RETRY, HealingStrategy.RESOURCE_BOOST],
                "corruption": [HealingStrategy.DATA_REPAIR, HealingStrategy.RESTART],
                "lock_error": [HealingStrategy.RETRY, HealingStrategy.RESOURCE_BOOST],
            },
            ComponentType.NETWORK: {
                "dns_error": [HealingStrategy.RETRY, HealingStrategy.RECONNECT],
                "timeout": [HealingStrategy.RETRY, HealingStrategy.FALLBACK],
                "connection_refused": [HealingStrategy.RECONNECT, HealingStrategy.RETRY],
            },
            ComponentType.FILESYSTEM: {
                "permission_error": [HealingStrategy.CONFIG_RESET, HealingStrategy.FALLBACK],
                "disk_full": [HealingStrategy.RESOURCE_BOOST, HealingStrategy.DATA_REPAIR],
                "file_not_found": [HealingStrategy.RETRY, HealingStrategy.FALLBACK],
            },
            ComponentType.MEMORY: {
                "out_of_memory": [HealingStrategy.RESOURCE_BOOST, HealingStrategy.RESTART],
                "memory_leak": [HealingStrategy.RESTART, HealingStrategy.RESOURCE_BOOST],
            },
            ComponentType.AGENT: {
                "logic_error": [HealingStrategy.RESTART, HealingStrategy.CONFIG_RESET],
                "timeout": [HealingStrategy.RETRY, HealingStrategy.RESOURCE_BOOST],
                "communication_error": [HealingStrategy.RECONNECT, HealingStrategy.RETRY],
            },
            ComponentType.API_ENDPOINT: {
                "server_error": [HealingStrategy.RETRY, HealingStrategy.FALLBACK],
                "auth_error": [HealingStrategy.CONFIG_RESET, HealingStrategy.RECONNECT],
                "rate_limit": [HealingStrategy.RETRY, HealingStrategy.RESOURCE_BOOST],
            },
            ComponentType.EXTERNAL_SERVICE: {
                "service_unavailable": [HealingStrategy.RETRY, HealingStrategy.FALLBACK],
                "api_error": [HealingStrategy.RETRY, HealingStrategy.RECONNECT],
                "timeout": [HealingStrategy.RETRY, HealingStrategy.CIRCUIT_BREAK],
            }
        }
        return base_strategies.get(self.component_type, {})

    def get_strategies_for_error(self, error_type: str) -> List[HealingStrategy]:
        """Get recommended healing strategies for a specific error type"""
        return self.strategies.get(error_type, [HealingStrategy.RETRY, HealingStrategy.RESTART])


class AdvancedHealingSystem:
    """
    Advanced healing system with component-specific strategies, pattern recognition, and predictive healing.
    """

    def __init__(self, magic_system=None):
        self.magic_system = magic_system
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.healing_history: List[HealingAttempt] = []
        self.component_health: Dict[str, ComponentHealth] = {}
        self.predictive_alerts: List[Dict[str, Any]] = []
        self.component_strategies: Dict[ComponentType, ComponentHealingStrategy] = {}

        # Initialize strategies for all component types
        for comp_type in ComponentType:
            self.component_strategies[comp_type] = ComponentHealingStrategy(comp_type)

        # Start predictive monitoring when event loop is available
        try:
            asyncio.create_task(self._predictive_monitoring_loop())
        except RuntimeError:
            # No event loop running yet - will be started later
            pass

    async def heal_component(self, component: str, component_type: ComponentType,
                           error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Advanced healing with component-specific strategies and pattern recognition.

        Args:
            component: Name of the component (e.g., 'claude_provider', 'sqlite_db')
            component_type: Type of component
            error: The exception that occurred
            context: Additional context about the failure

        Returns:
            bool: True if healing was successful
        """
        error_type = self._classify_error(error)
        error_message = str(error)

        # Update failure patterns
        await self._update_failure_patterns(component, component_type, error_type, error_message)

        # Get component health
        health = self._get_component_health(component, component_type)

        # Get recommended strategies based on patterns and component type
        strategies = self._get_recommended_strategies(component, component_type, error_type, error_message)

        logger.info(f"Attempting to heal {component} ({component_type.value}) with strategies: {[s.value for s in strategies]}")

        # Try strategies in order
        for strategy in strategies:
            success = await self._execute_healing_strategy(
                component, component_type, strategy, error, context
            )

            # Record the attempt
            attempt = HealingAttempt(
                component=component,
                component_type=component_type,
                strategy=strategy,
                error_details=f"{error_type}: {error_message}",
                success=success,
                duration=0.0,  # Would need to time this properly
                energy_used=10.0,  # Base energy cost
                timestamp=datetime.now(),
                outcome="success" if success else "failed"
            )
            self.healing_history.append(attempt)

            if success:
                # Update component health
                health.success_count += 1
                health.last_check = datetime.now()
                health.health_score = min(100.0, health.health_score + 10.0)

                logger.info(f"Successfully healed {component} using {strategy.value}")
                return True
            else:
                health.failure_count += 1
                health.health_score = max(0.0, health.health_score - 5.0)

        logger.warning(f"Failed to heal {component} with any strategy")
        return False

    async def predictive_heal(self, component: str, component_type: ComponentType,
                            risk_factors: Dict[str, Any]) -> bool:
        """
        Attempt predictive healing before a failure occurs.

        Args:
            component: Component to heal preemptively
            component_type: Type of component
            risk_factors: Factors indicating potential failure

        Returns:
            bool: True if preventive healing was successful
        """
        # Check if predictive healing is warranted
        health = self._get_component_health(component, component_type)
        if health.predictive_risk < 0.7:  # Only heal if risk is high
            return False

        logger.info(f"Attempting predictive healing for {component} (risk: {health.predictive_risk:.2f})")

        # Use preventive strategies
        preventive_strategies = [
            HealingStrategy.RESOURCE_BOOST,
            HealingStrategy.CONFIG_RESET,
            HealingStrategy.RECONNECT
        ]

        for strategy in preventive_strategies:
            success = await self._execute_healing_strategy(
                component, component_type, strategy, None, {"predictive": True}
            )

            if success:
                attempt = HealingAttempt(
                    component=component,
                    component_type=component_type,
                    strategy=strategy,
                    error_details="Predictive maintenance",
                    success=True,
                    duration=0.0,
                    energy_used=5.0,  # Lower energy cost for preventive
                    timestamp=datetime.now(),
                    outcome="preventive_success",
                    predictive=True
                )
                self.healing_history.append(attempt)

                health.health_score = min(100.0, health.health_score + 5.0)
                health.predictive_risk = max(0.0, health.predictive_risk - 0.2)

                logger.info(f"Predictive healing successful for {component}")
                return True

        return False

    def _classify_error(self, error: Exception) -> str:
        """Classify an error into a category"""
        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network-related errors
        if any(keyword in error_msg for keyword in ['timeout', 'connection', 'network', 'dns']):
            return 'network_error'

        # Authentication errors
        if any(keyword in error_msg for keyword in ['auth', 'unauthorized', 'forbidden', 'token']):
            return 'auth_error'

        # Rate limiting
        if any(keyword in error_msg for keyword in ['rate', 'limit', 'quota', '429']):
            return 'rate_limit'

        # Database errors
        if any(keyword in error_msg for keyword in ['database', 'sqlite', 'connection', 'lock']):
            return 'database_error'

        # Memory errors
        if any(keyword in error_msg for keyword in ['memory', 'out of memory', 'allocation']):
            return 'memory_error'

        # File system errors
        if any(keyword in error_msg for keyword in ['permission', 'file', 'disk', 'io']):
            return 'filesystem_error'

        # API errors
        if any(keyword in error_msg for keyword in ['api', 'server error', '500', '502', '503']):
            return 'api_error'

        # Timeout errors
        if 'timeout' in error_type or 'timeout' in error_msg:
            return 'timeout'

        return 'generic_error'

    async def _update_failure_patterns(self, component: str, component_type: ComponentType,
                                     error_type: str, error_message: str):
        """Update failure pattern recognition"""
        pattern_key = f"{component}:{error_type}"

        if pattern_key not in self.failure_patterns:
            self.failure_patterns[pattern_key] = FailurePattern(
                component=component,
                component_type=component_type,
                error_type=error_type,
                error_message=error_message
            )

        pattern = self.failure_patterns[pattern_key]
        pattern.frequency += 1
        pattern.last_occurrence = datetime.now()

        # Calculate success rate based on recent healing attempts
        recent_attempts = [
            attempt for attempt in self.healing_history[-20:]  # Last 20 attempts
            if attempt.component == component and attempt.error_details.startswith(error_type)
        ]

        if recent_attempts:
            pattern.success_rate = sum(1 for a in recent_attempts if a.success) / len(recent_attempts)

            # Determine preferred strategy based on success rates
            strategy_success = defaultdict(list)
            for attempt in recent_attempts:
                strategy_success[attempt.strategy].append(attempt.success)

            best_strategy = None
            best_rate = 0.0

            for strategy, successes in strategy_success.items():
                rate = sum(successes) / len(successes)
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy

            if best_strategy and best_rate > 0.6:  # Only use if >60% success rate
                pattern.preferred_strategy = best_strategy
                pattern.confidence = best_rate

    def _get_recommended_strategies(self, component: str, component_type: ComponentType,
                                  error_type: str, error_message: str) -> List[HealingStrategy]:
        """Get recommended healing strategies based on patterns and component type"""
        strategies = []

        # First, check if we have a preferred strategy from pattern learning
        pattern_key = f"{component}:{error_type}"
        if pattern_key in self.failure_patterns:
            pattern = self.failure_patterns[pattern_key]
            if pattern.preferred_strategy and pattern.confidence > 0.6:
                strategies.append(pattern.preferred_strategy)

        # Then add component-type specific strategies
        component_strategy = self.component_strategies.get(component_type)
        if component_strategy:
            type_strategies = component_strategy.get_strategies_for_error(error_type)
            strategies.extend(type_strategies)

        # Remove duplicates while preserving order
        seen = set()
        unique_strategies = []
        for strategy in strategies:
            if strategy not in seen:
                unique_strategies.append(strategy)
                seen.add(strategy)

        # If no strategies found, use defaults
        if not unique_strategies:
            unique_strategies = [HealingStrategy.RETRY, HealingStrategy.RESTART]

        return unique_strategies[:3]  # Limit to top 3 strategies

    async def _execute_healing_strategy(self, component: str, component_type: ComponentType,
                                      strategy: HealingStrategy, error: Exception = None,
                                      context: Dict[str, Any] = None) -> bool:
        """Execute a specific healing strategy"""
        logger.debug(f"Executing {strategy.value} strategy for {component}")

        try:
            if strategy == HealingStrategy.RESTART:
                return await self._restart_component(component, component_type, context)
            elif strategy == HealingStrategy.RECONNECT:
                return await self._reconnect_component(component, component_type, context)
            elif strategy == HealingStrategy.RETRY:
                return await self._retry_operation(component, component_type, error, context)
            elif strategy == HealingStrategy.FALLBACK:
                return await self._use_fallback(component, component_type, context)
            elif strategy == HealingStrategy.RESOURCE_BOOST:
                return await self._boost_resources(component, component_type, context)
            elif strategy == HealingStrategy.CIRCUIT_BREAK:
                return await self._activate_circuit_breaker(component, component_type, context)
            elif strategy == HealingStrategy.DATA_REPAIR:
                return await self._repair_data(component, component_type, context)
            elif strategy == HealingStrategy.CONFIG_RESET:
                return await self._reset_config(component, component_type, context)
            else:
                logger.warning(f"Unknown healing strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Error executing {strategy.value} strategy for {component}: {e}")
            return False

    # Individual healing strategy implementations
    async def _restart_component(self, component: str, component_type: ComponentType,
                               context: Dict[str, Any] = None) -> bool:
        """Restart a component"""
        # This would need component-specific restart logic
        # For now, just simulate with magic system if available
        if self.magic_system:
            return await self.magic_system.blue_spark_heal(component, "restart")
        return True  # Simulate success

    async def _reconnect_component(self, component: str, component_type: ComponentType,
                                 context: Dict[str, Any] = None) -> bool:
        """Reconnect to a component"""
        if self.magic_system:
            return await self.magic_system.blue_spark_heal(component, "reconnection")
        return True

    async def _retry_operation(self, component: str, component_type: ComponentType,
                             error: Exception = None, context: Dict[str, Any] = None) -> bool:
        """Retry a failed operation"""
        # Simple retry logic - in real implementation would retry the actual operation
        await asyncio.sleep(0.1)  # Brief delay
        return True

    async def _use_fallback(self, component: str, component_type: ComponentType,
                          context: Dict[str, Any] = None) -> bool:
        """Switch to fallback mode"""
        if self.magic_system:
            return await self.magic_system.blue_spark_heal(component, "fallback_mode")
        return True

    async def _boost_resources(self, component: str, component_type: ComponentType,
                             context: Dict[str, Any] = None) -> bool:
        """Boost resources for a component"""
        if self.magic_system:
            config = {"component": component, "boost_type": "resources"}
            result = await self.magic_system.acorn_vitality_boost(component, config)
            return result.get("boost", 0) > 0
        return True

    async def _activate_circuit_breaker(self, component: str, component_type: ComponentType,
                                      context: Dict[str, Any] = None) -> bool:
        """Activate circuit breaker protection"""
        # Circuit breaker logic would be handled elsewhere
        return True

    async def _repair_data(self, component: str, component_type: ComponentType,
                         context: Dict[str, Any] = None) -> bool:
        """Repair corrupted data"""
        if self.magic_system:
            return await self.magic_system.blue_spark_heal(component, "data_repair")
        return True

    async def _reset_config(self, component: str, component_type: ComponentType,
                          context: Dict[str, Any] = None) -> bool:
        """Reset component configuration"""
        if self.magic_system:
            return await self.magic_system.blue_spark_heal(component, "config_reset")
        return True

    def _get_component_health(self, component: str, component_type: ComponentType) -> ComponentHealth:
        """Get or create component health tracking"""
        if component not in self.component_health:
            self.component_health[component] = ComponentHealth(
                component=component,
                component_type=component_type
            )
        return self.component_health[component]

    async def _predictive_monitoring_loop(self):
        """Background loop for predictive monitoring and healing"""
        while True:
            try:
                await self._check_predictive_risks()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in predictive monitoring: {e}")
                await asyncio.sleep(60)

    async def _check_predictive_risks(self):
        """Check all components for predictive risk factors"""
        for component_name, health in self.component_health.items():
            # Calculate predictive risk based on various factors
            risk_factors = []

            # Recent failure rate
            if health.failure_count > 0:
                failure_rate = health.failure_count / (health.success_count + health.failure_count + 1)
                if failure_rate > 0.3:  # >30% failure rate
                    risk_factors.append(failure_rate * 0.4)

            # Health score degradation
            if health.health_score < 70:
                risk_factors.append((100 - health.health_score) / 100 * 0.3)

            # Time since last check
            if health.last_check:
                hours_since_check = (datetime.now() - health.last_check).total_seconds() / 3600
                if hours_since_check > 24:  # No check in 24 hours
                    risk_factors.append(min(hours_since_check / 24 * 0.1, 0.2))

            # Pattern-based risk
            pattern_risk = self._calculate_pattern_risk(component_name)
            risk_factors.append(pattern_risk)

            # Overall risk
            health.predictive_risk = min(1.0, sum(risk_factors))

            # Trigger predictive healing if risk is high
            if health.predictive_risk > 0.8:
                logger.warning(f"High predictive risk for {component_name} (risk: {health.predictive_risk:.2f})")
                await self.predictive_heal(component_name, health.component_type, {})

    def _calculate_pattern_risk(self, component: str) -> float:
        """Calculate risk based on failure patterns"""
        risk = 0.0

        for pattern_key, pattern in self.failure_patterns.items():
            if pattern.component == component:
                # Recent failures increase risk
                if pattern.last_occurrence:
                    hours_since_failure = (datetime.now() - pattern.last_occurrence).total_seconds() / 3600
                    if hours_since_failure < 24:  # Within last 24 hours
                        recency_factor = max(0, 1 - (hours_since_failure / 24))
                        risk += pattern.frequency * 0.1 * recency_factor

                # Low success rate increases risk
                if pattern.success_rate < 0.5:
                    risk += (1 - pattern.success_rate) * 0.2

        return min(0.5, risk)  # Cap pattern risk at 0.5

    async def _perform_predictive_maintenance(self):
        """Perform proactive maintenance on components showing early warning signs"""
        maintenance_performed = 0

        for component_name, health in self.component_health.items():
            # Medium risk components get preventive maintenance
            if 0.4 <= health.predictive_risk <= 0.7:
                logger.info(f"Performing preventive maintenance on {component_name} (risk: {health.predictive_risk:.2f})")

                # Light maintenance - resource boost and config check
                success = await self._execute_light_maintenance(component_name, health.component_type)
                if success:
                    health.predictive_risk = max(0.0, health.predictive_risk - 0.1)
                    health.health_score = min(100.0, health.health_score + 1.0)
                    maintenance_performed += 1

                    # Record the maintenance
                    attempt = HealingAttempt(
                        component=component_name,
                        component_type=health.component_type,
                        strategy=HealingStrategy.RESOURCE_BOOST,  # Using resource boost as preventive
                        error_details="Preventive maintenance",
                        success=True,
                        duration=0.0,
                        energy_used=3.0,  # Lower energy cost for preventive
                        timestamp=datetime.now(),
                        outcome="preventive_maintenance",
                        predictive=True
                    )
                    self.healing_history.append(attempt)

            # Generate recommendations for high-risk components
            elif health.predictive_risk > 0.7:
                recommendations = self._generate_maintenance_recommendations(component_name, health)
                health.recommended_actions = recommendations

        if maintenance_performed > 0:
            logger.info(f"Completed preventive maintenance on {maintenance_performed} components")

    async def _execute_light_maintenance(self, component: str, component_type: ComponentType) -> bool:
        """Execute light preventive maintenance"""
        try:
            # Simple resource boost - in a real system this would do actual maintenance
            if self.magic_system:
                config = {"component": component, "maintenance": "light"}
                result = await self.magic_system.acorn_vitality_boost(component, config)
                return result.get("boost", 0) > 0
            return True  # Simulate success
        except Exception as e:
            logger.error(f"Light maintenance failed for {component}: {e}")
            return False

    def _generate_maintenance_recommendations(self, component: str, health: ComponentHealth) -> List[str]:
        """Generate maintenance recommendations for high-risk components"""
        recommendations = []

        # Analyze failure patterns for this component
        component_patterns = [
            pattern for pattern in self.failure_patterns.values()
            if pattern.component == component
        ]

        if health.health_score < 50:
            recommendations.append("Immediate attention required - health critically low")

        if health.failure_count > health.success_count:
            recommendations.append("High failure rate detected - consider component replacement")

        # Pattern-based recommendations
        for pattern in component_patterns:
            if pattern.success_rate < 0.5:
                recommendations.append(f"Address {pattern.error_type} errors - current success rate: {pattern.success_rate:.1%}")

        if not recommendations:
            recommendations.append("Monitor closely - showing early risk indicators")

        return recommendations[:3]  # Limit to top 3 recommendations

    def get_predictive_insights(self) -> Dict[str, Any]:
        """Get predictive analytics and insights"""
        high_risk_components = [
            name for name, health in self.component_health.items()
            if health.predictive_risk > 0.7
        ]

        medium_risk_components = [
            name for name, health in self.component_health.items()
            if 0.4 <= health.predictive_risk <= 0.7
        ]

        # Calculate failure prediction accuracy
        recent_predictions = []
        for attempt in self.healing_history[-50:]:  # Last 50 attempts
            if attempt.predictive:
                recent_predictions.append(attempt.success)

        prediction_accuracy = 0.0
        if recent_predictions:
            prediction_accuracy = sum(recent_predictions) / len(recent_predictions)

        # Component health trends
        health_trends = {}
        for name, health in self.component_health.items():
            # Simple trend calculation based on recent history
            recent_attempts = [
                attempt for attempt in self.healing_history[-20:]
                if attempt.component == name
            ]

            if len(recent_attempts) >= 5:
                early_success_rate = sum(1 for a in recent_attempts[:5] if a.success) / 5
                late_success_rate = sum(1 for a in recent_attempts[-5:] if a.success) / 5
                trend = "improving" if late_success_rate > early_success_rate + 0.1 else \
                       "declining" if early_success_rate > late_success_rate + 0.1 else "stable"
            else:
                trend = "insufficient_data"

            health_trends[name] = {
                "current_risk": health.predictive_risk,
                "trend": trend,
                "recommendations": health.recommended_actions
            }

        return {
            "high_risk_components": high_risk_components,
            "medium_risk_components": medium_risk_components,
            "prediction_accuracy": prediction_accuracy,
            "health_trends": health_trends,
            "preventive_actions_taken": len([h for h in self.healing_history if h.predictive and h.outcome == "preventive_maintenance"]),
            "alerts_generated": len(self.predictive_alerts)
        }

    def analyze_patterns_and_learn(self) -> Dict[str, Any]:
        """Analyze healing patterns and update strategies based on learning"""
        insights = {
            "patterns_learned": 0,
            "strategies_improved": 0,
            "predictive_accuracy": 0.0,
            "component_improvements": []
        }

        # Analyze pattern effectiveness
        for pattern_key, pattern in self.failure_patterns.items():
            if pattern.confidence > 0.8:  # High confidence patterns
                insights["patterns_learned"] += 1

                # Check if we should promote this pattern's strategy
                recent_attempts = [
                    attempt for attempt in self.healing_history[-50:]  # Last 50 attempts
                    if attempt.component == pattern.component and attempt.error_details.startswith(pattern.error_type)
                ]

                if len(recent_attempts) >= 5:  # Enough data
                    current_strategy_rate = sum(1 for a in recent_attempts if a.success) / len(recent_attempts)
                    if current_strategy_rate > pattern.confidence + 0.1:  # Significant improvement
                        pattern.confidence = current_strategy_rate
                        insights["strategies_improved"] += 1

        # Analyze component health trends
        for component_name, health in self.component_health.items():
            if len(self.healing_history) > 10:
                recent_health_attempts = [
                    attempt for attempt in self.healing_history[-20:]
                    if attempt.component == component_name
                ]

                if recent_health_attempts:
                    recent_success_rate = sum(1 for a in recent_health_attempts if a.success) / len(recent_health_attempts)
                    if recent_success_rate > 0.8:  # Good recent performance
                        health.health_score = min(100.0, health.health_score + 2.0)
                        insights["component_improvements"].append({
                            "component": component_name,
                            "improvement": "health_score_boost",
                            "reason": "consistent_success"
                        })
                    elif recent_success_rate < 0.3:  # Poor recent performance
                        health.health_score = max(0.0, health.health_score - 1.0)
                        insights["component_improvements"].append({
                            "component": component_name,
                            "improvement": "health_score_penalty",
                            "reason": "poor_performance"
                        })

        # Calculate predictive accuracy
        if self.healing_history:
            predictive_attempts = [h for h in self.healing_history if h.predictive]
            if predictive_attempts:
                predictive_success_rate = sum(1 for h in predictive_attempts if h.success) / len(predictive_attempts)
                insights["predictive_accuracy"] = predictive_success_rate

        return insights

    def get_healing_analytics(self) -> Dict[str, Any]:
        """Get comprehensive healing analytics"""
        total_attempts = len(self.healing_history)
        successful_attempts = sum(1 for h in self.healing_history if h.success)
        success_rate = successful_attempts / total_attempts if total_attempts > 0 else 0

        # Strategy effectiveness with success rates
        strategy_stats = defaultdict(lambda: {"attempts": 0, "successes": 0, "success_rate": 0.0})
        for attempt in self.healing_history:
            strategy_stats[attempt.strategy.value]["attempts"] += 1
            if attempt.success:
                strategy_stats[attempt.strategy.value]["successes"] += 1

        # Calculate success rates
        for strategy_name, stats in strategy_stats.items():
            if stats["attempts"] > 0:
                stats["success_rate"] = stats["successes"] / stats["attempts"]

        # Component health overview with trends
        component_overview = {}
        for name, health in self.component_health.items():
            # Calculate recent performance
            recent_attempts = [
                attempt for attempt in self.healing_history[-20:]
                if attempt.component == name
            ]
            recent_success_rate = 0.0
            if recent_attempts:
                recent_success_rate = sum(1 for a in recent_attempts if a.success) / len(recent_attempts)

            component_overview[name] = {
                "health_score": health.health_score,
                "predictive_risk": health.predictive_risk,
                "failure_count": health.failure_count,
                "success_count": health.success_count,
                "avg_response_time": health.avg_response_time,
                "recent_success_rate": recent_success_rate,
                "recommended_actions": health.recommended_actions
            }

        # Pattern analysis with detailed metrics
        pattern_analysis = {}
        for pattern_key, pattern in self.failure_patterns.items():
            # Calculate trend (improving/worsening/stable)
            trend = "stable"
            if pattern.frequency > 5:  # Enough data
                recent_occurrences = sum(1 for attempt in self.healing_history[-20:]
                                       if attempt.component == pattern.component and
                                       attempt.error_details.startswith(pattern.error_type))
                if recent_occurrences > pattern.frequency * 0.6:  # Increasing
                    trend = "worsening"
                elif recent_occurrences < pattern.frequency * 0.3:  # Decreasing
                    trend = "improving"

            pattern_analysis[pattern_key] = {
                "component": pattern.component,
                "component_type": pattern.component_type.value,
                "error_type": pattern.error_type,
                "frequency": pattern.frequency,
                "success_rate": pattern.success_rate,
                "preferred_strategy": pattern.preferred_strategy.value if pattern.preferred_strategy else None,
                "confidence": pattern.confidence,
                "last_occurrence": pattern.last_occurrence.isoformat() if pattern.last_occurrence else None,
                "trend": trend
            }

        # Learning insights
        learning_insights = self.analyze_patterns_and_learn()

        return {
            "total_healing_attempts": total_attempts,
            "overall_success_rate": success_rate,
            "strategy_effectiveness": dict(strategy_stats),
            "component_health": component_overview,
            "active_failure_patterns": len(self.failure_patterns),
            "pattern_analysis": pattern_analysis,
            "predictive_alerts": len(self.predictive_alerts),
            "learning_insights": learning_insights,
            "system_health_score": self._calculate_system_health_score()
        }

    def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score"""
        if not self.component_health:
            return 100.0

        health_scores = [health.health_score for health in self.component_health.values()]
        avg_health = sum(health_scores) / len(health_scores)

        # Adjust based on recent failures
        recent_failures = sum(1 for attempt in self.healing_history[-10:] if not attempt.success)
        failure_penalty = min(20.0, recent_failures * 2.0)

        # Adjust based on predictive alerts
        alert_penalty = min(10.0, len(self.predictive_alerts) * 1.0)

        return max(0.0, min(100.0, avg_health - failure_penalty - alert_penalty))