"""base.PantheonAgent on the inter-agent bus (messagebus.AsyncMessageBus, Redis faked).

Until now base.py imported MessageBus and Message from src.core.message_bus, whose `subscribe(agent_id)` is an async
generator and whose Message has no `create`, so `start()` and `send()` could never have worked; nothing constructs a
PantheonAgent today, which is why it went unnoticed. These tests pin the class to the bus it was written for.
"""
import asyncio

import pytest

import base
import messagebus
from tests.test_messagebus import FakeRedis


class Echo(base.PantheonAgent):
    def __init__(self, bus, fail_on=None):
        super().__init__(base.AgentConfig(name="Echo", role="test", channels=["tasks"]), bus)
        self.seen = []
        self.fail_on = fail_on

    async def process(self, message):
        self.seen.append(message.content)
        if message.content == self.fail_on:
            raise RuntimeError("cannot process that")
        await self.send("replies", f"got {message.content}", conversation_id=message.conversation_id)


@pytest.fixture
def fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(messagebus.aioredis, "from_url", lambda *a, **k: fake)
    return fake


def test_agent_receives_published_messages_and_replies_on_the_bus(fake_redis):
    async def scenario():
        bus = messagebus.AsyncMessageBus("redis://example.invalid:6379")
        await bus.initialize()
        agent = Echo(bus)
        await agent.start()
        replies = await bus.subscribe("replies")
        await bus.publish("tasks", messagebus.Message.create("hi", sender="tester", provider="grok", conversation_id="c1"))
        reply = await asyncio.wait_for(replies.get(), timeout=2)
        await agent.stop()
        await bus.cleanup()
        return agent, reply, bus

    agent, reply, bus = asyncio.run(scenario())
    assert agent.seen == ["hi"]
    assert reply.content == "got hi" and reply.sender == "Echo" and reply.provider == "grok" and reply.conversation_id == "c1"
    assert agent.running is False and agent.subscriptions == [] and agent._tasks == []
    assert not bus.subscribers.get("tasks")  # unsubscribed on stop


def test_a_failing_process_does_not_stop_the_listener(fake_redis):
    async def scenario():
        bus = messagebus.AsyncMessageBus("redis://example.invalid:6379")
        await bus.initialize()
        agent = Echo(bus, fail_on="bad")
        await agent.start()
        replies = await bus.subscribe("replies")
        for text in ("bad", "good"):
            await bus.publish("tasks", messagebus.Message.create(text, sender="tester", provider="grok"))
        reply = await asyncio.wait_for(replies.get(), timeout=2)
        await agent.stop()
        await bus.cleanup()
        return agent, reply

    agent, reply = asyncio.run(scenario())
    assert agent.seen == ["bad", "good"] and reply.content == "got good"


def test_start_twice_does_not_double_subscribe(fake_redis):
    async def scenario():
        bus = messagebus.AsyncMessageBus("redis://example.invalid:6379")
        await bus.initialize()
        agent = Echo(bus)
        await agent.start()
        await agent.start()
        count = len(bus.subscribers["tasks"])
        await agent.stop()
        await bus.cleanup()
        return count

    assert asyncio.run(scenario()) == 1
