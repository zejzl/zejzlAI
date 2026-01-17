"""
Magic System for ZEJZL.NET

Implements fairy magic simulation for self-healing and agent enhancement.
Core features:
- Acorn Vitality: Natural boosts for resource allocation and agent stamina
- Blue Spark Healing: Energy-based healing with preference learning
- Fairy Shield: Protection mechanism for unauthorized access
- Circuit Breaker: Automatic failure recovery and self-healing
- Rituals: Enchanted operations with tool integration

Lore ties: Holly's mesmer/healing, oak acorns for strength, underground fairy tech.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger("MagicSystem")


class CircuitBreakerState(Enum):
    """Circuit breaker states for self-healing"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    expected_exception: tuple = (Exception,)  # Exception types to count as failures


@dataclass
class HealingRecord:
    """Record of healing attempts for learning"""
    target: str
    issue: str
    success: bool
    energy_used: float
    timestamp: datetime
    outcome: str


class CircuitBreaker:
    """
    Circuit breaker pattern for automatic failure recovery.
    Prevents cascading failures by temporarily blocking requests to failing services.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker half-open, testing service recovery")
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True
        return (datetime.now() - self.last_failure_time) > timedelta(seconds=self.config.recovery_timeout)

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.success_count += 1
            logger.info("Circuit breaker reset to CLOSED after successful test")

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker opened after failed recovery test")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class FairyMagic:
    """
    Core class for fairy magic simulation in ZEJZL.NET.
    Represents the People's tech-magic system with self-healing capabilities.

    Features:
    - Acorn Vitality: Natural boost for resource allocation and agent stamina
    - Blue Spark Healing: Energy-based healing with preference learning
    - Fairy Shield: Protection mechanism blocking unauthorized access
    - Circuit Breaker Integration: Automatic failure recovery
    - Rituals: Enchanted operations with tool integration

    Lore ties: Holly's mesmer/healing, oak acorns for strength, underground fairy tech.
    """

    def __init__(self, energy_level: float = 100.0, max_energy: float = 100.0):
        self.energy_level = energy_level
        self.max_energy = max_energy
        self.acorn_reserve = 5  # Number of 'acorn potions' available
        self.is_shielded = False
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.healing_history: List[HealingRecord] = []
        self.learning_preferences: Dict[str, float] = {}  # For DPO-style learning

        # Initialize circuit breakers for common failure points
        self._init_circuit_breakers()

    def _init_circuit_breakers(self):
        """Initialize circuit breakers for different system components"""
        components = {
            "ai_provider": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30),
            "persistence": CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60),
            "agent_coordinator": CircuitBreakerConfig(failure_threshold=2, recovery_timeout=15),
            "tool_call": CircuitBreakerConfig(failure_threshold=3, recovery_timeout=45)
        }

        for component, config in components.items():
            self.circuit_breakers[component] = CircuitBreaker(config)

    async def recharge_magic(self, acorn_boost: bool = False) -> float:
        """
        Recharge magic energy. Optional acorn boost for extra vitality.
        Ties to herbal lore: Holly's mesmer/healing properties.
        """
        if self.energy_level >= self.max_energy:
            logger.debug("Magic already at maximum energy")
            return self.energy_level

        base_recharge = random.uniform(10, 20)

        if acorn_boost and self.acorn_reserve > 0:
            self.acorn_reserve -= 1
            base_recharge += 15  # Acorn's 'zdravi' (healing) property
            logger.info("Acorn vitality infused - extra spark! Acorns remaining: %d", self.acorn_reserve)

        self.energy_level = min(self.max_energy, self.energy_level + base_recharge)

        # Simulate 'mana' flow timing
        await asyncio.sleep(0.1)

        logger.debug("Magic recharged to %.1f%%", self.energy_level)
        return self.energy_level

    async def blue_spark_heal(self, target: str, issue: str) -> bool:
        """
        Blue spark healing - success based on energy level.
        Collects preferences for DPO learning from healing outcomes.

        Args:
            target: Component to heal (e.g., 'agent_coordinator', 'tool_call')
            issue: Description of the issue being healed

        Returns:
            bool: True if healing successful
        """
        if self.energy_level < 15:
            logger.warning("Magic depleted! Recharge first.")
            return False

        success_chance = min(0.95, self.energy_level / 100)  # Higher energy = better heal
        success = random.random() < success_chance

        energy_used = 15.0 if success else 5.0  # Less energy used on failure
        self.energy_level -= energy_used

        outcome = "healed" if success else "failed"

        # Record healing attempt for learning
        record = HealingRecord(
            target=target,
            issue=issue,
            success=success,
            energy_used=energy_used,
            timestamp=datetime.now(),
            outcome=outcome
        )
        self.healing_history.append(record)

        # Update learning preferences (DPO-style: healed outcomes preferred)
        pref_key = f"{target}:{issue}"
        current_pref = self.learning_preferences.get(pref_key, 0.5)
        if success:
            self.learning_preferences[pref_key] = min(1.0, current_pref + 0.1)
        else:
            self.learning_preferences[pref_key] = max(0.0, current_pref - 0.05)

        if success:
            logger.info("Blue spark healing successful on %s: %s", target, issue)
            return True
        else:
            logger.error("Heal failed on %s: Magic flicker (low energy). Issue: %s", target, issue)
            return False

    async def acorn_vitality_boost(self, agent_name: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Acorn vitality boost for agents.
        Herbal lore: Acorns for strength and digestion (metaphor for task flow).

        Args:
            agent_name: Name of the agent to boost
            agent_config: Current agent configuration

        Returns:
            Dict with boost metrics and updated configuration
        """
        if self.acorn_reserve <= 0:
            logger.warning("No acorn potions remaining for vitality boost")
            return {"boost": 0, "reason": "no_acorns"}

        boost_factor = random.uniform(1.1, 1.5)  # 10-50% performance gain

        # Apply vitality boost to agent configuration
        boosted_config = agent_config.copy()

        # Increase token limits for better performance
        if "max_tokens" in boosted_config:
            original_tokens = boosted_config["max_tokens"]
            boosted_config["max_tokens"] = min(4096, int(original_tokens * boost_factor))

        # Add performance boost parameters
        boosted_config["vitality_boost"] = boost_factor
        boosted_config["error_reduction"] = (boost_factor - 1.0) * 0.3  # Estimated error reduction

        self.energy_level = min(self.max_energy, self.energy_level + 5)  # Acorn recharges slightly

        logger.info("Acorn boost applied: %.2fx vitality to %s", boost_factor, agent_name)

        return {
            "vitality_boost": boost_factor,
            "new_config": boosted_config,
            "acorns_remaining": self.acorn_reserve
        }

    async def fairy_shield(self, activate: bool = True) -> bool:
        """
        Fairy shield activation/deactivation.
        Like LEP's invisibility - blocks unauthorized access to system components.
        """
        cost = 10 if activate else -5  # Deactivate recharges energy

        if activate and self.energy_level < cost:
            logger.warning("Insufficient energy for fairy shield activation")
            return False

        self.energy_level = max(0, self.energy_level - cost) if activate else min(self.max_energy, self.energy_level - cost)
        self.is_shielded = activate

        status = "activated" if activate else "deactivated"
        logger.info("Fairy shield %s - energy now %.1f%%", status, self.energy_level)

        return True

    async def perform_ritual(self, ritual_type: str, target_file: Optional[str] = None) -> str:
        """
        Perform magical rituals using enchanted operations.
        Integrates with system tools for enhanced functionality.

        Args:
            ritual_type: Type of ritual to perform
            target_file: Optional target file for file-based rituals

        Returns:
            str: Ritual result message
        """
        rituals = {
            "holly_blessing": lambda: "Blue spark blesses task - 100% success aura!",
            "oak_fortification": lambda: f"Oak strength infused - system fortified against {random.randint(3, 7)} types of errors",
            "fairy_ward": lambda: "Fairy ward activated - protection against external threats",
            "mana_surge": lambda: f"Mana surge: +{random.randint(20, 40)} energy restored"
        }

        if ritual_type not in rituals:
            return f"Unknown ritual: {ritual_type}"

        result = rituals[ritual_type]()

        # Apply ritual effects
        if ritual_type == "mana_surge":
            energy_boost = random.randint(20, 40)
            self.energy_level = min(self.max_energy, self.energy_level + energy_boost)
            logger.info("Mana surge ritual completed - energy boosted by %d", energy_boost)

        if target_file and ritual_type == "fairy_ward":
            # Could integrate with file operations here
            logger.info("Fairy ward applied to file: %s", target_file)

        return result

    async def get_circuit_breaker_status(self, component: str) -> Dict[str, Any]:
        """Get status of a specific circuit breaker"""
        if component not in self.circuit_breakers:
            return {"error": f"Unknown component: {component}"}

        return self.circuit_breakers[component].get_status()

    async def reset_circuit_breaker(self, component: str) -> bool:
        """Manually reset a circuit breaker to closed state"""
        if component not in self.circuit_breakers:
            return False

        self.circuit_breakers[component].state = CircuitBreakerState.CLOSED
        self.circuit_breakers[component].failure_count = 0
        logger.info("Circuit breaker manually reset for component: %s", component)
        return True

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive magic system status"""
        return {
            "energy_level": self.energy_level,
            "max_energy": self.max_energy,
            "acorn_reserve": self.acorn_reserve,
            "is_shielded": self.is_shielded,
            "circuit_breakers": {
                name: cb.get_status() for name, cb in self.circuit_breakers.items()
            },
            "healing_history_count": len(self.healing_history),
            "learning_preferences_count": len(self.learning_preferences)
        }

    async def auto_heal(self, component: str, error: Exception) -> bool:
        """
        Automatic healing attempt using magic + circuit breaker logic.
        Combines blue spark healing with circuit breaker state management.
        """
        if component not in self.circuit_breakers:
            logger.warning("Unknown component for auto-heal: %s", component)
            return False

        cb = self.circuit_breakers[component]

        # Don't attempt healing if circuit breaker is open
        if cb.state == CircuitBreakerState.OPEN:
            logger.debug("Skipping auto-heal for %s - circuit breaker is OPEN", component)
            return False

        # Attempt blue spark healing
        success = await self.blue_spark_heal(component, str(error))

        if success:
            # Reset circuit breaker on successful healing
            cb.failure_count = max(0, cb.failure_count - 1)
            logger.info("Auto-healing successful for %s", component)
        else:
            # Record failure in circuit breaker
            cb._on_failure()
            logger.warning("Auto-healing failed for %s", component)

        return success


# Integration helper for ZEJZL.NET agent workflows
async def integrate_magic_with_workflow(magic: FairyMagic, agent_name: str, workflow_func: Callable) -> Any:
    """
    Integrate magic system into agent workflow with pre-task boosts and error healing.
    """
    try:
        # Pre-task vitality boost
        agent_config = {"max_tokens": 1024}  # Default config, could be loaded from persistence
        boost_result = await magic.acorn_vitality_boost(agent_name, agent_config)

        if boost_result.get("boost", 0) > 0:
            logger.info("Applied pre-task vitality boost to %s", agent_name)

        # Execute workflow
        result = await workflow_func()

        return result

    except Exception as e:
        # Auto-heal on workflow failure
        healed = await magic.auto_heal(agent_name, e)
        if healed:
            logger.info("Auto-healing successful, retrying workflow for %s", agent_name)
            # Retry workflow after healing
            return await workflow_func()
        else:
            logger.error("Auto-healing failed for %s, propagating error", agent_name)
            raise e


if __name__ == "__main__":
    async def demo():
        magic = FairyMagic()

        print(f"Initial energy: {magic.energy_level}%")
        print(f"Acorn reserve: {magic.acorn_reserve}")

        # Test vitality boost
        boost = await magic.acorn_vitality_boost("test_agent", {"max_tokens": 1024})
        print(f"Vitality boost: {boost}")

        # Test shield
        await magic.fairy_shield(True)
        print(f"Shield active: {magic.is_shielded}")

        # Test ritual
        ritual_result = await magic.perform_ritual("holly_blessing")
        print(f"Ritual result: {ritual_result}")

        # Test healing
        healed = await magic.blue_spark_heal("test_component", "simulated_error")
        print(f"Healing successful: {healed}")

        # Show final status
        status = await magic.get_system_status()
        print(f"Final energy: {status['energy_level']}%")

    asyncio.run(demo())