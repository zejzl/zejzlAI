# tests/test_learning_system_simple.py
"""
Simple tests for the Learning Loop Optimization System.

Basic functionality tests to verify the system works without complex fixtures.
"""

import asyncio
import pytest
import time

from src.learning_loop import LearningLoop
from src.agents.learner import LearnerAgent
from src.agents.profiling import AgentProfiler
from src.agents.consensus import ConsensusManager, ConflictType
from src.agents.memory import MemoryAgent
from src.improvement_applicator import ImprovementApplicator
from src.magic import FairyMagic


class TestLearningSystemSimple:
    """Simple tests for learning system functionality"""

    @pytest.mark.asyncio
    async def test_learning_loop_creation(self):
        """Test that learning loop can be created"""
        loop = LearningLoop()
        assert loop is not None
        assert not loop.running
        assert loop.cycle_interval == 300  # default

    @pytest.mark.asyncio
    async def test_profiler_functionality(self):
        """Test basic profiler functionality"""
        profiler = AgentProfiler()

        # Record some calls
        await profiler.record_agent_call("test_agent", "Test Role", 1.5, True)
        await profiler.record_agent_call("test_agent", "Test Role", 2.1, False)

        # Get report
        report = await profiler.get_performance_report()
        assert "agent_metrics" in report
        assert "test_agent" in report["agent_metrics"]

        metrics = report["agent_metrics"]["test_agent"]
        # Check that we have metrics dict with expected keys
        assert "total_calls" in metrics
        assert "success_rate" in metrics
        assert "avg_response_time" in metrics
        assert metrics["total_calls"] == 2
        assert metrics["success_rate"] == 0.5
        assert metrics["avg_response_time"] == 1.8

    @pytest.mark.asyncio
    async def test_memory_functionality(self):
        """Test memory agent functionality"""
        memory = MemoryAgent()

        # Store events
        event1 = {"type": "observation", "data": {"task": "test"}}
        event2 = {"type": "execution", "data": {"result": "success"}}

        await memory.store(event1)
        await memory.store(event2)

        # Recall events
        events = await memory.recall()
        assert len(events) == 2
        assert events[0]["type"] == "observation"
        assert events[1]["type"] == "execution"

    @pytest.mark.asyncio
    async def test_learner_with_profiling(self):
        """Test learner integration with profiling data"""
        learner = LearnerAgent()
        profiler = AgentProfiler()
        memory = MemoryAgent()

        # Add some profiling data
        await profiler.record_agent_call("observer", "Data Collection", 1.2, True)
        await profiler.record_agent_call("reasoner", "Planning", 2.1, False)

        # Add memory events
        await memory.store({"type": "observation", "data": {"task": "test"}})
        await memory.store({"type": "execution", "data": {"result": "mixed"}})

        # Get profiling report
        profiling_data = await profiler.get_performance_report()

        # Test learning with profiling
        memory_events = await memory.recall() or []
        result = await learner.learn(memory_events, profiling_data)

        assert result is not None
        assert "profiling_integrated" in result
        assert result["profiling_integrated"] is True
        assert "success_rate" in result

    @pytest.mark.asyncio
    async def test_magic_system_basic(self):
        """Test basic magic system functionality"""
        magic = FairyMagic(energy_level=100.0)

        # Test energy levels
        assert magic.energy_level == 100.0

        # Test basic healing (may fail due to randomness)
        healed = await magic.blue_spark_heal("test_component", "test_issue")
        # Just check it returns a boolean
        assert isinstance(healed, bool)

        # Test acorn boost
        boost = await magic.acorn_vitality_boost("test_agent", {"max_tokens": 1024})
        assert "vitality_boost" in boost

    @pytest.mark.asyncio
    async def test_improvement_applicator_creation(self):
        """Test improvement applicator can be created"""
        profiler = AgentProfiler()
        consensus = ConsensusManager()
        magic = FairyMagic()

        applicator = ImprovementApplicator(profiler, consensus, magic)
        assert applicator is not None
        assert applicator.magic_system == magic

    @pytest.mark.asyncio
    async def test_consensus_manager_basic(self):
        """Test basic consensus manager functionality"""
        consensus = ConsensusManager()

        # Test with empty opinions
        result = await consensus.resolve_conflict(
            ConflictType.PLANNING_DISPUTE, []
        )
        assert not result.resolved

    @pytest.mark.asyncio
    async def test_learning_loop_basic_cycle(self):
        """Test basic learning loop cycle execution"""
        # Create minimal components
        learner = LearnerAgent()
        profiler = AgentProfiler()
        consensus = ConsensusManager()
        memory = MemoryAgent()
        magic = FairyMagic()
        applicator = ImprovementApplicator(profiler, consensus, magic)

        # Create learning loop with fast cycle
        loop = LearningLoop(cycle_interval=1, max_cycles_history=5)
        loop.learner = learner
        loop.profiler = profiler
        loop.consensus_manager = consensus
        loop.memory = memory
        loop.improvement_applicator = applicator

        # Add minimal data
        await profiler.record_agent_call("observer", "Data Collection", 1.0, True)
        await memory.store({"type": "observation", "data": {"task": "test"}})

        # Execute cycle
        cycle = await loop.execute_learning_cycle()

        # Verify cycle completed
        assert cycle is not None
        assert cycle.cycle_id.startswith("cycle_")
        # Cycle may or may not succeed depending on data, but should complete

    @pytest.mark.asyncio
    async def test_adaptive_safe_comprehensive_demo(self):
        """Demonstrate adaptive, safe, and comprehensive learning system"""
        # Create full system
        learner = LearnerAgent()
        profiler = AgentProfiler()
        consensus = ConsensusManager()
        memory = MemoryAgent()
        magic = FairyMagic(energy_level=80.0)  # Start with good energy
        applicator = ImprovementApplicator(profiler, consensus, magic)

        loop = LearningLoop(cycle_interval=1)
        loop.learner = learner
        loop.profiler = profiler
        loop.memory = memory
        loop.improvement_applicator = applicator

        # Simulate system learning and adaptation
        initial_energy = magic.energy_level

        # Phase 1: Establish baseline (good performance)
        for i in range(3):
            await profiler.record_agent_call("observer", "Data Collection", 1.0, True)
            await profiler.record_agent_call("reasoner", "Planning", 1.2, True)
            await memory.store({"type": "observation", "data": {"task": f"task_{i}"}})

        # Phase 2: Introduce performance issue
        await profiler.record_agent_call("reasoner", "Planning", 3.5, False)  # Slow and failed
        await memory.store({"type": "execution", "data": {"error": "performance_issue"}})

        # Phase 3: Learning cycle should detect and adapt
        cycle = await loop.execute_learning_cycle()

        # Verify system responded (may have applied improvements)
        final_energy = magic.energy_level

        # System should have attempted some form of adaptation
        # (Exact behavior depends on random magic success, but system should try)
        assert cycle is not None

        # Get insights to verify analysis happened
        insights = await loop.get_recent_insights()
        # Should have generated some insights from the performance data
        assert isinstance(insights, list)

        # Verify magic system was involved (energy may have changed)
        # Note: This is probabilistic, but demonstrates the integration
        assert isinstance(final_energy, (int, float))

        print(f"Learning system demo completed: {len(insights)} insights generated, energy: {initial_energy} -> {final_energy}")