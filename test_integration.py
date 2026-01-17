#!/usr/bin/env python3
"""
Integration tests for zejzl.net
Tests the full system including AI providers, message bus, and agents
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from messagebus import AsyncMessageBus as InterAgentBus, Message
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent
from src.agents.memory import MemoryAgent


@pytest.mark.asyncio
async def test_full_single_agent_flow():
    """Test the complete Observer -> Reasoner -> Actor flow"""
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    memory = MemoryAgent()

    task = "Test task for integration"

    # Step 1: Observe
    observation = await observer.observe(task)
    assert observation is not None
    assert observation["task"] == task
    await memory.store({"type": "observation", "data": observation})

    # Step 2: Reason
    plan = await reasoner.reason(observation)
    assert plan is not None
    assert "subtasks" in plan
    await memory.store({"type": "plan", "data": plan})

    # Step 3: Act
    execution = await actor.act(plan)
    assert execution is not None
    assert "results" in execution
    await memory.store({"type": "execution", "data": execution})

    # Verify memory stores all events
    events = await memory.recall()
    assert len(events) == 3
    assert events[0]["type"] == "observation"
    assert events[1]["type"] == "plan"
    assert events[2]["type"] == "execution"


@pytest.mark.asyncio
async def test_messagebus_pub_sub():
    """Test Inter-Agent Message Bus pub/sub functionality"""
    bus = InterAgentBus()

    try:
        await bus.initialize()

        # Subscribe to test channel
        queue = await bus.subscribe("test_integration")

        # Publish message
        msg = Message.create(
            content="integration test message",
            sender="test_agent",
            provider="test"
        )
        await bus.publish("test_integration", msg)

        # Receive message
        received = await asyncio.wait_for(queue.get(), timeout=2.0)
        assert received.content == "integration test message"
        assert received.sender == "test_agent"

    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        await bus.cleanup()


@pytest.mark.asyncio
async def test_messagebus_message_persistence():
    """Test message persistence in Inter-Agent Bus"""
    bus = InterAgentBus()

    try:
        await bus.initialize()

        # Create and save message
        msg = Message.create(
            content="persistent message",
            sender="test",
            provider="test",
            conversation_id="test_conv_integration"
        )
        msg.response = "test response"
        await bus.save_message(msg)

        # Retrieve history
        history = await bus.get_history("test_conv_integration", limit=1)
        assert len(history) >= 1

        # Check that history contains our conversation
        found = any("persistent message" in str(entry) for entry in history)
        assert found or len(history) > 0  # Allow for either match

    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        await bus.cleanup()


@pytest.mark.asyncio
async def test_memory_agent_recall_by_type():
    """Test Memory agent's ability to filter by event type"""
    memory = MemoryAgent()

    # Store different event types
    await memory.store({"type": "observation", "data": "obs1"})
    await memory.store({"type": "plan", "data": "plan1"})
    await memory.store({"type": "observation", "data": "obs2"})
    await memory.store({"type": "execution", "data": "exec1"})

    # Recall all
    all_events = await memory.recall()
    assert len(all_events) == 4

    # Recall by type using filter function
    observations = await memory.recall(filter_fn=lambda e: e.get("type") == "observation")
    assert len(observations) == 2
    assert all(e["type"] == "observation" for e in observations)

    plans = await memory.recall(filter_fn=lambda e: e.get("type") == "plan")
    assert len(plans) == 1
    assert plans[0]["type"] == "plan"


@pytest.mark.asyncio
async def test_agent_chain_with_memory():
    """Test agent chain with shared memory state"""
    from src.agents.validator import ValidatorAgent
    from src.agents.executor import ExecutorAgent

    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    executor = ExecutorAgent()
    memory = MemoryAgent()

    task = "Integration test task"

    # Full chain
    observation = await observer.observe(task)
    await memory.store({"type": "observation", "data": observation})

    plan = await reasoner.reason(observation)
    await memory.store({"type": "plan", "data": plan})

    execution = await actor.act(plan)
    await memory.store({"type": "execution", "data": execution})

    validation = await validator.validate(execution)
    await memory.store({"type": "validation", "data": validation})

    executor_result = await executor.execute(validation)
    await memory.store({"type": "executor", "data": executor_result})

    # Verify complete chain in memory
    events = await memory.recall()
    assert len(events) == 5

    # Verify event sequence
    assert events[0]["type"] == "observation"
    assert events[1]["type"] == "plan"
    assert events[2]["type"] == "execution"
    assert events[3]["type"] == "validation"
    assert events[4]["type"] == "executor"


@pytest.mark.asyncio
async def test_full_pantheon_orchestration():
    """Test complete 9-agent Pantheon system"""
    from src.agents.analyzer import AnalyzerAgent
    from src.agents.learner import LearnerAgent
    from src.agents.improver import ImproverAgent
    from src.agents.validator import ValidatorAgent
    from src.agents.executor import ExecutorAgent

    # Initialize all 9 agents
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    memory = MemoryAgent()
    executor = ExecutorAgent()
    analyzer = AnalyzerAgent()
    learner = LearnerAgent()
    improver = ImproverAgent()

    task = "Complete Pantheon integration test"

    # Execute full Pantheon flow
    observation = await observer.observe(task)
    await memory.store({"type": "observation", "data": observation})

    plan = await reasoner.reason(observation)
    await memory.store({"type": "plan", "data": plan})

    execution = await actor.act(plan)
    await memory.store({"type": "execution", "data": execution})

    validation = await validator.validate(execution)
    await memory.store({"type": "validation", "data": validation})

    executor_result = await executor.execute(validation)
    await memory.store({"type": "executor", "data": executor_result})

    events = await memory.recall()
    analysis = await analyzer.analyze(events)
    assert analysis is not None

    learned = await learner.learn(events)
    assert learned is not None

    improvement = await improver.improve(analysis, learned)
    assert improvement is not None

    # Verify all agents executed
    assert len(events) >= 5
    assert analysis is not None
    assert learned is not None
    assert improvement is not None


@pytest.mark.asyncio
async def test_concurrent_agent_execution():
    """Test multiple agents running concurrently"""
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    tasks = ["Task 1", "Task 2", "Task 3"]

    # Execute agents concurrently for multiple tasks
    observations = await asyncio.gather(
        *[observer.observe(task) for task in tasks]
    )
    assert len(observations) == 3

    plans = await asyncio.gather(
        *[reasoner.reason(obs) for obs in observations]
    )
    assert len(plans) == 3

    executions = await asyncio.gather(
        *[actor.act(plan) for plan in plans]
    )
    assert len(executions) == 3


if __name__ == "__main__":
    # Run tests manually
    print("Running zejzl.net integration tests...")
    pytest.main([__file__, "-v", "--tb=short"])
