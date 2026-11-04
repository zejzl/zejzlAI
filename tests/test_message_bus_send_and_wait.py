"""MessageBus.send_and_wait and BusAgent: request/response by correlation_id, without touching the caller's queue.
Ported from grokputer tests/core/test_send_and_wait.py; the agent is this repo's BusAgent."""
import asyncio
from typing import Any, Dict, Optional

import pytest

from src.core.bus_agent import BusAgent
from src.core.message_bus import Message, MessageBus
from src.exceptions import MessageBusError


class EchoAgent(BusAgent):
    def __init__(self, agent_id, bus):
        super().__init__(agent_id, bus, receive_timeout=0.05)

    async def process_message(self, message: Message) -> Optional[Dict[str, Any]]:
        if message.message_type == "silent":
            return None
        if message.message_type == "boom":
            raise RuntimeError("bad message")
        return {"echo": message.content.get("n")}


def _request(n=1, message_type="ask"):
    return Message(from_agent="caller", to_agent="ignored", message_type=message_type, content={"n": n})


@pytest.mark.asyncio
async def test_returns_the_replys_content():
    bus = MessageBus()
    bus.register_agent("caller")
    agent = EchoAgent("echo", bus)
    agent.start()
    try:
        assert await bus.send_and_wait("echo", _request(7), timeout=3) == {"echo": 7}
    finally:
        await agent.stop()
    assert bus._awaiting_reply == {} and "echo" not in bus.queues


@pytest.mark.asyncio
async def test_concurrent_requests_get_their_own_replies():
    bus = MessageBus()
    bus.register_agent("caller")
    agent = EchoAgent("echo", bus)
    agent.start()
    try:
        results = await asyncio.gather(*(bus.send_and_wait("echo", _request(n), timeout=3) for n in range(5)))
    finally:
        await agent.stop()
    assert [r["echo"] for r in results] == [0, 1, 2, 3, 4]


@pytest.mark.asyncio
async def test_timeout_raises_and_cleans_up():
    bus = MessageBus()
    bus.register_agent("caller")
    EchoAgent("echo", bus)  # registered but not running: nobody answers
    with pytest.raises(asyncio.TimeoutError):
        await bus.send_and_wait("echo", _request(), timeout=0.1)
    assert bus._awaiting_reply == {}


@pytest.mark.asyncio
async def test_unknown_target_raises_bus_error():
    bus = MessageBus()
    with pytest.raises(MessageBusError):
        await bus.send_and_wait("nobody", _request(), timeout=0.1)
    assert bus._awaiting_reply == {}


@pytest.mark.asyncio
async def test_reply_from_a_different_agent_does_not_resolve_the_request():
    bus = MessageBus()
    bus.register_agent("caller")
    bus.register_agent("echo")
    bus.register_agent("other")

    async def impostor():
        await asyncio.sleep(0.05)
        (corr,) = bus._awaiting_reply.keys()
        await bus.send(Message("other", "caller", "reply", {"echo": "wrong"}, correlation_id=corr))

    asyncio.create_task(impostor())
    with pytest.raises(asyncio.TimeoutError):
        await bus.send_and_wait("echo", _request(), timeout=0.3)


@pytest.mark.asyncio
async def test_reply_to_an_unregistered_sender_is_dropped_and_the_agent_keeps_serving():
    bus = MessageBus()
    agent = EchoAgent("echo", bus)
    agent.start()
    try:
        await bus.send(Message(from_agent="ghost", to_agent="echo", message_type="ask", content={"n": 1}))
        await asyncio.sleep(0.2)
        assert agent.running and agent.processed == 1

        bus.register_agent("caller")
        assert await bus.send_and_wait("echo", _request(5), timeout=3) == {"echo": 5}
    finally:
        await agent.stop()


@pytest.mark.asyncio
async def test_a_failing_handler_answers_with_an_error_and_a_silent_one_with_nothing():
    bus = MessageBus()
    bus.register_agent("caller")
    agent = EchoAgent("echo", bus)
    agent.start()
    try:
        reply = await bus.send_and_wait("echo", _request(1, "boom"), timeout=3)
        assert reply["error"].startswith("RuntimeError")
        with pytest.raises(asyncio.TimeoutError):
            await bus.send_and_wait("echo", _request(1, "silent"), timeout=0.2)
    finally:
        await agent.stop()
