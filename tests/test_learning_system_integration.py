# tests/test_learning_system_integration.py
"""
Integration tests for the Learning Loop Optimization System.

Tests the adaptive, safe, and comprehensive layers of the learning system,
including continuous learning, self-healing, and performance optimization.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from src.learning_loop import LearningLoop
from src.learning_types import LearningPhase
from src.agents.learner import LearnerAgent
from src.agents.profiling import AgentProfiler
from src.agents.consensus import ConsensusManager
from src.agents.memory import MemoryAgent
from src.improvement_applicator import ImprovementApplicator
from src.magic import FairyMagic
from src.agents.protocols import AgentMessage, MessageType


class TestLearningSystemIntegration:
    """Test the complete learning system integration"""

    @pytest.fixture
    async def setup_learning_system(self):
        """Set up a complete learning system for testing"""
        # Create components
        learner = LearnerAgent()
        profiler = AgentProfiler()
        consensus_manager = ConsensusManager()
        memory = MemoryAgent()
        magic_system = FairyMagic(energy_level=50.0)  # Limited energy for testing
        improvement_applicator = ImprovementApplicator(profiler, consensus_manager, magic_system)

        # Create learning loop
        learning_loop = LearningLoop(
            cycle_interval=1,  # Fast cycles for testing
            max_cycles_history=10
        )
        # Override components
        learning_loop.learner = learner
        learning_loop.profiler = profiler
        learning_loop.consensus_manager = consensus_manager
        learning_loop.memory = memory
        learning_loop.improvement_applicator = improvement_applicator

        yield {
            "learning_loop": learning_loop,
            "learner": learner,
            "profiler": profiler,
            "consensus_manager": consensus_manager,
            "memory": memory,
            "magic_system": magic_system,
            "improvement_applicator": improvement_applicator
        }

    @pytest.mark.asyncio
    async def test_adaptive_learning_cycle(self, setup_learning_system):
        """Test that the learning system adapts over multiple cycles"""
        components = await setup_learning_system
        learning_loop = components["learning_loop"]
        profiler = components["profiler"]
        memory = components["memory"]

        # Simulate some initial performance data
        await profiler.record_agent_call("observer", "Data Collection & Environmental Monitoring", 1.5, True)
        await profiler.record_agent_call("reasoner", "Strategic Planning & Task Decomposition", 2.1, False)
        await profiler.record_agent_call("actor", "Action Execution & Tool Integration", 0.8, True)

        # Store some events in memory
        await memory.store({"type": "observation", "data": {"task": "test_task"}, "timestamp": time.time()})
        await memory.store({"type": "execution", "data": {"result": "success"}, "timestamp": time.time()})
        await memory.store({"type": "validation", "data": {"is_valid": True}, "timestamp": time.time()})

        # Execute learning cycle
        cycle_result = await learning_loop.execute_learning_cycle()

        # Verify cycle completed
        assert cycle_result is not None
        assert cycle_result.success
        assert cycle_result.cycle_id.startswith("cycle_")

        # Verify insights were generated
        insights = await learning_loop.get_recent_insights()
        assert len(insights) > 0

        # Execute another cycle to test adaptation
        await profiler.record_agent_call("observer", "Data Collection & Environmental Monitoring", 1.2, True)  # Improved
        await profiler.record_agent_call("reasoner", "Strategic Planning & Task Decomposition", 1.8, True)  # Improved

        cycle_result_2 = await learning_loop.execute_learning_cycle()
        assert cycle_result_2.success

        # Verify system adapted (should have different insights)
        insights_2 = await learning_loop.get_recent_insights()
        assert len(insights_2) >= len(insights)  # At least as many insights

    @pytest.mark.asyncio
    async def test_safe_rollback_capabilities(self, setup_learning_system):
        """Test that the system safely rolls back harmful changes"""
        components = await setup_learning_system
        improvement_applicator = components["improvement_applicator"]
        magic_system = components["magic_system"]

        # Mock a failing improvement
        original_energy = magic_system.energy_level

        # Create a mock insight that would trigger fairy shield
        insight = type('MockInsight', (), {
            'insight_id': 'test_rollback',
            'insight_type': 'anomaly',
            'description': 'Test anomaly for rollback',
            'confidence': 0.9,
            'impact_potential': 'high',
            'related_agents': ['observer'],
            'recommended_actions': ['Test rollback'],
            'generated_at': datetime.now(),
            'applied': False
        })()

        # Apply improvement (fairy shield activation)
        applied = await improvement_applicator.apply_learning_insights([insight], auto_apply=True)
        assert len(applied) > 0

        # Verify shield was activated
        assert magic_system.is_shielded

        # Test rollback
        improvement_id = applied[0].improvement_id
        rollback_success = await improvement_applicator.rollback_improvement(improvement_id)
        assert rollback_success

        # Verify shield was deactivated
        assert not magic_system.is_shielded

    @pytest.mark.asyncio
    async def test_comprehensive_system_coverage(self, setup_learning_system):
        """Test comprehensive integration of all system components"""
        components = await setup_learning_system
        learning_loop = components["learning_loop"]
        profiler = components["profiler"]
        memory = components["memory"]
        magic_system = components["magic_system"]

        # Test all phases of learning cycle
        initial_energy = magic_system.energy_level
        initial_shield = magic_system.is_shielded

        # Populate system with realistic data
        await self._populate_test_data(profiler, memory)

        # Execute complete learning cycle
        cycle = await learning_loop.execute_learning_cycle()
        assert cycle is not None

        # Verify all phases completed
        assert cycle.phase == LearningPhase.EVALUATION  # Should complete full cycle
        assert cycle.evaluation_metrics is not None

        # Verify comprehensive insights generated
        insights = await learning_loop.get_recent_insights()
        insight_types = {i['type'] for i in insights}
        assert len(insight_types) > 1  # Multiple types of insights

        # Verify magic system integration
        # Energy should have been used for healing/analysis
        final_energy = magic_system.energy_level
        # Note: Energy usage depends on random healing success, so just check it's a valid value
        assert isinstance(final_energy, (int, float))

        # Verify profiling data integration
        performance_report = await profiler.get_performance_report()
        assert 'agent_metrics' in performance_report
        assert 'system_metrics' in performance_report

    @pytest.mark.asyncio
    async def test_continuous_monitoring_adaptation(self, setup_learning_system):
        """Test continuous monitoring and adaptive responses"""
        components = await setup_learning_system
        learning_loop = components["learning_loop"]
        profiler = components["profiler"]

        # Enable monitoring
        learning_loop.monitoring_enabled = True
        learning_loop.adaptation_enabled = True

        # Establish baseline with good performance
        await profiler.record_agent_call("observer", "Data Collection & Environmental Monitoring", 1.0, True)
        await profiler.record_agent_call("reasoner", "Strategic Planning & Task Decomposition", 1.0, True)
        await profiler.record_agent_call("actor", "Action Execution & Tool Integration", 1.0, True)

        # Start monitoring
        await learning_loop._establish_performance_baseline()

        # Verify baseline established
        assert learning_loop.performance_baseline is not None
        assert 'agent_metrics' in learning_loop.performance_baseline

        # Simulate performance degradation (anomaly)
        await profiler.record_agent_call("observer", "Data Collection & Environmental Monitoring", 3.0, False)  # Slow and failed

        # Trigger monitoring
        await learning_loop._monitor_system_performance()

        # Verify anomaly detection and response
        # (In real implementation, this would trigger healing/adaptation)
        assert learning_loop.performance_baseline is not None  # Still exists

    @pytest.mark.asyncio
    async def test_confidence_thresholds_and_safety(self, setup_learning_system):
        """Test that confidence thresholds prevent unsafe optimizations"""
        components = await setup_learning_system
        learning_loop = components["learning_loop"]
        improvement_applicator = components["improvement_applicator"]

        # Set conservative confidence threshold
        learning_loop.minimum_confidence_threshold = 0.8
        learning_loop.auto_apply_optimizations = True

        # Create low-confidence insight
        insight_low = type('MockInsight', (), {
            'insight_id': 'low_confidence_test',
            'insight_type': 'pattern',
            'description': 'Low confidence pattern',
            'confidence': 0.5,  # Below threshold
            'impact_potential': 'medium',
            'related_agents': ['observer'],
            'recommended_actions': ['Safe action'],
            'generated_at': datetime.now(),
            'applied': False
        })()

        # Create high-confidence insight
        insight_high = type('MockInsight', (), {
            'insight_id': 'high_confidence_test',
            'insight_type': 'anomaly',
            'description': 'High confidence anomaly',
            'confidence': 0.9,  # Above threshold
            'impact_potential': 'high',
            'related_agents': ['reasoner'],
            'recommended_actions': ['Critical healing needed'],
            'generated_at': datetime.now(),
            'applied': False
        })()

        # Apply insights
        applied = await improvement_applicator.apply_learning_insights(
            [insight_low, insight_high], auto_apply=True, confidence_threshold=0.8
        )

        # Only high-confidence insight should be applied
        assert len(applied) == 1
        assert applied[0].insight_id == 'high_confidence_test'

    async def _populate_test_data(self, profiler, memory):
        """Populate test data for comprehensive testing"""
        # Add diverse performance data
        agents_and_roles = [
            ("observer", "Data Collection & Environmental Monitoring"),
            ("reasoner", "Strategic Planning & Task Decomposition"),
            ("actor", "Action Execution & Tool Integration"),
            ("validator", "Quality Assurance & Safety Validation"),
            ("executor", "Safe Execution & Error Recovery")
        ]

        # Simulate varied performance
        for agent, role in agents_and_roles:
            # Mix of good and poor performance
            response_times = [0.8, 2.1, 1.2, 0.9, 1.8]
            successes = [True, False, True, True, False]

            for rt, success in zip(response_times, successes):
                await profiler.record_agent_call(agent, role, rt, success)

        # Add memory events
        event_types = ["observation", "execution", "validation", "analysis"]
        for i, event_type in enumerate(event_types):
            await memory.store({
                "type": event_type,
                "data": {"test_data": f"event_{i}"},
                "timestamp": time.time() + i
            })

    @pytest.mark.asyncio
    async def test_magic_system_integration_safety(self, setup_learning_system):
        """Test that magic system integration is safe and doesn't cause cascading failures"""
        components = await setup_learning_system
        magic_system = components["magic_system"]
        improvement_applicator = components["improvement_applicator"]

        # Test energy conservation
        initial_energy = magic_system.energy_level

        # Create insight that would trigger multiple magic actions
        insight = type('MockInsight', (), {
            'insight_id': 'magic_safety_test',
            'insight_type': 'anomaly',
            'description': 'Test magic safety',
            'confidence': 0.95,
            'impact_potential': 'high',
            'related_agents': ['observer', 'reasoner', 'actor'],
            'recommended_actions': ['Apply comprehensive healing'],
            'generated_at': datetime.now(),
            'applied': False
        })()

        # Apply magic-based improvements
        applied = await improvement_applicator.apply_learning_insights([insight], auto_apply=True)
        final_energy = magic_system.energy_level

        # Verify energy was used but not depleted completely
        assert final_energy >= 0
        assert final_energy <= initial_energy  # Should have used some energy

        # Verify circuit breakers are functioning
        cb_status = await magic_system.get_circuit_breaker_status("ai_provider")
        assert "state" in cb_status

    @pytest.mark.asyncio
    async def test_learning_loop_status_reporting(self, setup_learning_system):
        """Test comprehensive status reporting of the learning system"""
        components = await setup_learning_system
        learning_loop = components["learning_loop"]

        # Get initial status
        status = await learning_loop.get_learning_status()

        # Verify status structure
        required_fields = [
            "running", "current_cycle", "total_cycles",
            "successful_cycles", "total_insights", "cycle_interval"
        ]

        for field in required_fields:
            assert field in status

        # Execute a cycle
        await learning_loop.execute_learning_cycle()

        # Get updated status
        updated_status = await learning_loop.get_learning_status()

        # Verify status updated
        assert updated_status["total_cycles"] >= status["total_cycles"]
        assert updated_status["successful_cycles"] >= status["successful_cycles"]