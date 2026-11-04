"""The workflow side of the bus: MessageBusAdapter, node type `bus`, ProviderBusAgent, and the runner starting agents."""
import asyncio

import pytest

import base
from src.core.bus_agent import BusAgent, ProviderBusAgent
from src.core.message_bus import MessageBus
from src.exceptions import MessageBusError
from src.workflow import (
    NODE_TYPES,
    WorkflowEngine,
    build_workflow,
    get_message_bus_adapter,
    messagebus_adapter,
)
from src.workflow.messagebus_adapter import MessageBusAdapter, MessageBusNode, reset_default_bus
from src.workflow.nodes import NodeContext


class EchoAgent(BusAgent):
    def __init__(self, agent_id, bus):
        super().__init__(agent_id, bus, receive_timeout=0.05)

    async def process_message(self, message):
        return {"echo": message.content, "type": message.message_type}


class FakeProviderBus:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    async def send_message(self, content, provider_name, conversation_id=None):
        self.calls.append((content, provider_name, conversation_id))
        if self.error:
            raise self.error
        return self.reply


def use_provider_bus(monkeypatch, fake):
    async def get_bus():
        return fake

    monkeypatch.setattr(base, "get_ai_provider_bus", get_bus)
    return fake


@pytest.fixture(autouse=True)
def fresh_default_bus():
    reset_default_bus()
    yield
    reset_default_bus()


class TestAdapter:
    @pytest.mark.asyncio
    async def test_publish_request_broadcast_and_received(self):
        bus = MessageBus()
        echo = EchoAgent("echo", bus)
        echo.start()
        adapter = MessageBusAdapter("wf1", bus)
        try:
            msg = await adapter.publish("echo", {"hello": 1}, priority="high")
            assert msg.from_agent == "workflow:wf1" and msg.content == {"hello": 1, "workflow_id": "wf1"}
            await asyncio.sleep(0.1)
            got = adapter.received()  # the echo agent replied to the publisher's own queue
            assert len(got) == 1 and got[0].content["echo"]["hello"] == 1

            reply = await adapter.request("echo", {"q": 2}, timeout=3)
            assert reply == {"echo": {"q": 2, "workflow_id": "wf1"}, "type": "request"}

            assert await adapter.broadcast({"status": "done"}) == 1
            await asyncio.sleep(0.1)
            assert adapter.received()[0].content["echo"]["status"] == "done"
        finally:
            await echo.stop()
        adapter.shutdown()
        assert "workflow:wf1" not in bus.queues

    @pytest.mark.asyncio
    async def test_publish_to_nobody_raises_and_bad_priority_is_rejected(self):
        adapter = MessageBusAdapter("wf2", MessageBus())
        with pytest.raises(MessageBusError):
            await adapter.publish("nobody", {})
        with pytest.raises(ValueError, match="priority"):
            await adapter.publish("nobody", {}, priority="urgent")

    def test_one_adapter_per_workflow_on_the_default_bus(self):
        a = get_message_bus_adapter("same")
        assert get_message_bus_adapter("same") is a and a.bus is messagebus_adapter.get_default_bus()
        other = MessageBus()
        b = get_message_bus_adapter("same", other)
        assert b is not a and b.bus is other


class TestNode:
    def test_config_validation_and_loader(self):
        assert NODE_TYPES["bus"] is MessageBusNode
        with pytest.raises(ValueError, match="operation"):
            MessageBusNode("b", config={})
        with pytest.raises(ValueError, match="needs 'to'"):
            MessageBusNode("b", config={"operation": "request"})
        node = MessageBusNode("b", config={"operation": "broadcast"})
        assert node.config["output"] == "b" and node.config["timeout"] == 30.0

    @pytest.mark.asyncio
    async def test_request_node_in_a_workflow_uses_the_workflow_adapter(self):
        bus = messagebus_adapter.get_default_bus()
        echo = EchoAgent("echo", bus)
        echo.start()
        try:
            wf = build_workflow({
                "name": "ask-echo",
                "nodes": [
                    {"id": "ask", "type": "bus", "config": {"operation": "request", "to": "echo", "content": {"n": "{{n}}"}}},
                    {"id": "tell", "type": "bus", "config": {"operation": "publish", "to": "echo", "content": {"done": True}}},
                    {"id": "all", "type": "bus", "config": {"operation": "broadcast", "content": {"s": "end"}}},
                ],
                "edges": [["ask", "tell"], ["tell", "all"]],
            })
            result = await WorkflowEngine("ask-echo").execute(wf, {"n": 3})
        finally:
            await echo.stop()
        assert result["status"] == "success"
        data = result["data"]
        assert data["ask"]["reply"]["echo"] == {"n": "3", "workflow_id": "ask-echo"}
        assert data["tell"]["status"] == "published" and data["all"]["status"] == "broadcast"

    @pytest.mark.asyncio
    async def test_request_without_an_agent_times_out_as_a_node_failure(self):
        bus = MessageBus()
        bus.register_agent("mute")
        node = MessageBusNode("ask", config={"operation": "request", "to": "mute", "timeout": 0.1})
        node.set_adapter(MessageBusAdapter("wf", bus))
        with pytest.raises(asyncio.TimeoutError):
            await node.execute(NodeContext(data={}, metadata={"workflow_id": "wf"}))


class TestProviderBusAgent:
    @pytest.mark.asyncio
    async def test_answers_prompts_through_the_provider_bus(self, monkeypatch):
        fake = use_provider_bus(monkeypatch, FakeProviderBus(reply="forty-two"))
        bus = MessageBus()
        agent = ProviderBusAgent("provider", bus)
        agent.start()
        adapter = MessageBusAdapter("wf", bus)
        try:
            reply = await adapter.request("provider", {"prompt": "the answer?", "provider": "grok"}, timeout=3)
            assert reply == {"reply": "forty-two", "provider": "grok"}
            assert fake.calls == [("the answer?", "grok", "bus:workflow:wf")]
            reply = await adapter.request("provider", {"nothing": 1}, timeout=3)
            assert reply["error"] == "request needs a 'prompt'"
        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_provider_errors_come_back_as_error_replies(self, monkeypatch):
        use_provider_bus(monkeypatch, FakeProviderBus(error=ValueError("Provider grok not registered")))
        bus = MessageBus()
        agent = ProviderBusAgent("provider", bus)
        agent.start()
        try:
            reply = await MessageBusAdapter("wf", bus).request("provider", {"prompt": "hi"}, timeout=3)
            assert "not registered" in reply["error"]
        finally:
            await agent.stop()


class TestRunner:
    def test_runner_starts_the_provider_agent_for_bus_workflows(self, monkeypatch, tmp_path, capsys):
        use_provider_bus(monkeypatch, FakeProviderBus(reply="pong"))
        from src.workflow import run as workflow_run

        wf = tmp_path / "ping.yaml"
        wf.write_text(
            "name: ping\nnodes:\n  - id: ask\n    type: bus\n"
            "    config: {operation: request, to: provider, content: {prompt: ping}}\n",
            encoding="utf-8",
        )
        code = workflow_run.main([str(wf)])
        out = capsys.readouterr().out
        assert code == 0, out
        assert "Bus agents started: provider" in out and '"reply": "pong"' in out
        assert "provider" not in messagebus_adapter.get_default_bus().queues  # stopped afterwards
