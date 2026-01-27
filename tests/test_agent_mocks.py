#!/usr/bin/env python3
"""
Mock tests for ZEJZL.NET agents
Verifies integration without requiring real AI providers
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent
from src.agents.validator import ValidatorAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.improver import ImproverAgent
from src.agents.memory import MemoryAgent
from src.agents.executor import ExecutorAgent
from src.agents.learner import LearnerAgent


@pytest.fixture
def mock_ai_bus():
    bus = AsyncMock()
    bus.send_message.return_value = '{"objective": "mocked objective", "requirements": ["req1"]}'
    return bus


@pytest.mark.asyncio
async def test_observer_mock(mock_ai_bus):
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = ObserverAgent()
        result = await agent.observe("test task")

        assert result["ai_generated"] is True
        assert "mocked objective" in str(result)
        mock_ai_bus.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_reasoner_mock(mock_ai_bus):
    mock_ai_bus.send_message.return_value = '{"analysis": "mocked analysis", "subtasks": [{"description": "step 1"}]}'
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = ReasonerAgent()
        result = await agent.reason({"task": "test task"})

        assert result["ai_generated"] is True
        assert "mocked analysis" in str(result)
        mock_ai_bus.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_actor_mock(mock_ai_bus):
    mock_ai_bus.send_message.return_value = '{"execution_steps": ["step 1"], "tools_needed": []}'
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = ActorAgent()
        result = await agent.act({"subtasks": ["subtask 1"]})

        assert result["ai_generated"] is True
        assert len(result["results"]) == 1
        mock_ai_bus.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_validator_mock(mock_ai_bus):
    mock_ai_bus.send_message.return_value = '{"quality_score": 90, "completeness_score": 95, "critical_issues": []}'
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = ValidatorAgent()
        result = await agent.validate({"results": [{"action": "test"}]})

        assert result["ai_generated"] is True
        assert result["quality_score"] == 90
        mock_ai_bus.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_agent_fallback_on_failure():
    # Simulate AI Provider Bus failure
    with patch('base.get_ai_provider_bus', side_effect=Exception("API failure")):
        agent = ObserverAgent()
        result = await agent.observe("test task")

        # Should use fallback logic
        assert result["ai_generated"] is False
        assert "error" in result
        assert "Complete: test task" in result["objective"]


@pytest.mark.asyncio
async def test_memory_agent_instantiation():
    agent = MemoryAgent(persistence=MagicMock())
    assert agent.name == "Memory"
    # Should be able to store and recall
    await agent.store({"type": "test", "data": "foo"})
    events = await agent.recall()
    assert len(events) == 1


@pytest.mark.asyncio
async def test_executor_agent_instantiation():
    agent = ExecutorAgent()
    assert agent.name == "Executor"
    result = await agent.execute({"cmd": "test"})
    assert "success" in result["status"]


@pytest.mark.asyncio
async def test_learner_agent_instantiation():
    agent = LearnerAgent()
    assert agent.name == "Learner"
    result = await agent.learn([])
    assert "patterns_analyzed" in result


@pytest.mark.asyncio
async def test_analyzer_mock(mock_ai_bus):
    mock_ai_bus.send_message.return_value = '{"health_score": 88, "recommendations": ["improve tests"]}'
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = AnalyzerAgent()
        result = await agent.analyze([{"type": "test", "data": {}}])

        assert result["ai_generated"] is True
        assert result["health_score"] == 88
        mock_ai_bus.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_improver_mock(mock_ai_bus):
    mock_ai_bus.send_message.return_value = '{"priority_actions": ["finalize integration"]}'
    with patch('base.get_ai_provider_bus', return_value=mock_ai_bus):
        agent = ImproverAgent()
        result = await agent.improve({"health_score": 80}, {"bottlenecks": []})

        assert result["ai_generated"] is True
        assert "finalize integration" in result["priority_actions"]
        mock_ai_bus.send_message.assert_called_once()
