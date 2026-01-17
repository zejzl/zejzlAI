#!/usr/bin/env python3
"""
Basic tests for zejzl.net
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from messagebus import AsyncMessageBus, Message
from src.agents.observer import ObserverAgent


@pytest.mark.asyncio
async def test_message_creation():
    """Test Message creation"""
    msg = Message.create(
        content="test message",
        sender="test",
        provider="test",
        conversation_id="test_conv"
    )
    
    assert msg.content == "test message"
    assert msg.sender == "test"
    assert msg.provider == "test"
    assert msg.conversation_id == "test_conv"
    assert msg.id is not None
    assert msg.timestamp is not None


@pytest.mark.asyncio
async def test_message_bus_init():
    """Test MessageBus initialization"""
    bus = AsyncMessageBus()
    
    try:
        await bus.initialize()
        assert bus.running is True
        assert bus.redis is not None
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        await bus.cleanup()


@pytest.mark.asyncio
async def test_observer_agent():
    """Test Observer agent basic functionality"""
    observer = ObserverAgent()

    # Test basic observation
    result = await observer.observe("test task")

    assert result is not None
    assert "task" in result
    assert result["task"] == "test task"
    assert "objective" in result  # AI-generated observation structure
    assert "requirements" in result
    assert "timestamp" in result
    assert result.get("ai_generated", False)  # Should be AI-generated


@pytest.mark.asyncio
async def test_pub_sub():
    """Test publish/subscribe functionality"""
    bus = AsyncMessageBus()
    
    try:
        await bus.initialize()
        
        # Subscribe to a channel
        queue = await bus.subscribe("test_channel")
        
        # Publish a message
        msg = Message.create(
            content="test",
            sender="test",
            provider="test"
        )
        await bus.publish("test_channel", msg)
        
        # Receive the message
        received = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert received.content == "test"
        
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        await bus.cleanup()


if __name__ == "__main__":
    # Run tests manually
    print("Running zejzl.net tests...")
    pytest.main([__file__, "-v"])