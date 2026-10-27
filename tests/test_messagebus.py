"""Message bus round-trips: the Redis-backed bus (with an in-memory fake Redis)
and the in-process agent bus in src/core."""

import asyncio

import pytest

import messagebus
from src.core import message_bus as core_bus


class FakeRedis:
    """Just enough of redis.asyncio.Redis for messagebus.AsyncMessageBus."""

    def __init__(self):
        self.published = []
        self.lists = {}
        self.expiry = {}
        self.closed = False

    async def ping(self):
        return True

    async def publish(self, channel, data):
        self.published.append((channel, data))
        return 1

    async def lpush(self, key, value):
        self.lists.setdefault(key, []).insert(0, value)

    async def ltrim(self, key, start, end):
        self.lists[key] = self.lists.get(key, [])[start:end + 1]

    async def expire(self, key, seconds):
        self.expiry[key] = seconds

    async def lrange(self, key, start, end):
        return self.lists.get(key, [])[start:end + 1]

    async def aclose(self):
        self.closed = True


@pytest.fixture
def fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setattr(messagebus.aioredis, "from_url", lambda *a, **k: fake)
    return fake


def test_publish_reaches_subscriber(fake_redis):
    async def scenario():
        bus = messagebus.AsyncMessageBus("redis://example.invalid:6379")
        await bus.initialize()
        queue = await bus.subscribe("chat")
        msg = messagebus.Message.create("hello", sender="tester", provider="grok")
        await bus.publish("chat", msg)
        received = await asyncio.wait_for(queue.get(), timeout=1)
        await bus.unsubscribe("chat", queue)
        await bus.cleanup()
        return bus, msg, received

    bus, msg, received = asyncio.run(scenario())
    assert received is msg
    assert received.content == "hello"
    assert fake_redis.published and fake_redis.published[0][0] == "chat"
    assert "chat" not in bus.subscribers
    assert fake_redis.closed
    assert bus.running is False


def test_publish_requires_initialize():
    async def scenario():
        bus = messagebus.AsyncMessageBus()
        msg = messagebus.Message.create("x", sender="s", provider="p")
        await bus.publish("chat", msg)

    with pytest.raises(RuntimeError):
        asyncio.run(scenario())


def test_history_round_trip(fake_redis):
    async def scenario():
        bus = messagebus.AsyncMessageBus()
        await bus.initialize()
        for i in range(3):
            msg = messagebus.Message.create(f"q{i}", sender="u", provider="p", conversation_id="c1")
            msg.response = f"a{i}"
            await bus.save_message(msg)
        unanswered = messagebus.Message.create("no answer", sender="u", provider="p", conversation_id="c1")
        await bus.save_message(unanswered)
        return await bus.get_history("c1", limit=10)

    history = asyncio.run(scenario())
    assert history == [
        {"role": "user", "content": "q0"},
        {"role": "assistant", "content": "a0"},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
    ]
    assert fake_redis.expiry["conversation:c1"] == 30 * 24 * 3600


def _msg(frm, to, kind="task", priority=core_bus.MessagePriority.NORMAL, **content):
    return core_bus.Message(
        from_agent=frm, to_agent=to, message_type=kind, content=content, priority=priority
    )


def test_core_bus_send_receive():
    async def scenario():
        bus = core_bus.MessageBus(default_timeout=1)
        bus.register_agent("observer")
        bus.register_agent("reasoner")
        await bus.send(_msg("observer", "reasoner", text="look"))
        got = await bus.receive("reasoner", timeout=1)
        return bus, got

    bus, got = asyncio.run(scenario())
    assert got.from_agent == "observer"
    assert got.content == {"text": "look"}
    assert bus.get_stats() is not None


def test_core_bus_priority_order():
    async def scenario():
        bus = core_bus.MessageBus(default_timeout=1)
        bus.register_agent("a")
        bus.register_agent("b")
        await bus.send(_msg("a", "b", priority=core_bus.MessagePriority.LOW, n=1))
        await bus.send(_msg("a", "b", priority=core_bus.MessagePriority.HIGH, n=2))
        first = await bus.receive("b", timeout=1)
        second = await bus.receive("b", timeout=1)
        return first, second

    first, second = asyncio.run(scenario())
    assert first.content["n"] == 2
    assert second.content["n"] == 1


def test_core_bus_broadcast_skips_sender():
    async def scenario():
        bus = core_bus.MessageBus(default_timeout=1)
        for name in ("a", "b", "c"):
            bus.register_agent(name)
        await bus.broadcast(_msg("a", "*", kind="announce", v=1))
        return bus

    bus = asyncio.run(scenario())
    assert bus.get_queue_size("a") == 0
    assert bus.get_queue_size("b") == 1
    assert bus.get_queue_size("c") == 1


def test_core_bus_unknown_agent():
    async def scenario():
        bus = core_bus.MessageBus(default_timeout=1)
        await bus.send(_msg("a", "nobody"))

    with pytest.raises(Exception):
        asyncio.run(scenario())
