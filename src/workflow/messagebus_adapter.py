"""
Workflows on the in-process message bus.

MessageBusAdapter gives a workflow an identity on the bus (`workflow:<id>`) and three operations:
publish (fire and forget), request (send_and_wait for the reply) and broadcast. MessageBusNode exposes
them to workflow files as node type `bus`. A process-wide default bus is created on first use; tests
and embedders can pass their own bus. The idea comes from grokputer's messagebus_adapter.py; the code
is new, written against this bus's real API (grokputer's version used a Message shape and a `publish`
method the bus never had, and simulated subscriptions).

The other end of a request is a BusAgent (src/core/bus_agent.py). `start_default_agents` starts the
ProviderBusAgent as `provider`, so `{operation: request, to: provider, content: {prompt: ...}}` asks a
model through the shared provider bus.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from src.core.bus_agent import BusAgent, ProviderBusAgent
from src.core.message_bus import Message, MessageBus, MessagePriority

from .nodes.agent_node import interpolate
from .nodes.base import BaseNode, NodeContext

PRIORITIES = {"high": MessagePriority.HIGH, "normal": MessagePriority.NORMAL, "low": MessagePriority.LOW}
OPERATIONS = ("publish", "request", "broadcast")
DEFAULT_AGENTS = ("provider",)

_default_bus: Optional[MessageBus] = None
_adapters: Dict[str, "MessageBusAdapter"] = {}


def get_default_bus() -> MessageBus:
    """The process-wide bus, created on first use."""
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus


def reset_default_bus() -> None:
    """Forget the default bus and its adapters (tests, or after a shutdown)."""
    global _default_bus
    _default_bus = None
    _adapters.clear()


def interpolate_deep(value: Any, context: NodeContext) -> Any:
    """interpolate() through dicts and lists."""
    if isinstance(value, dict):
        return {k: interpolate_deep(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate_deep(v, context) for v in value]
    return interpolate(value, context)


class MessageBusAdapter:
    """A workflow's identity and operations on the bus."""

    def __init__(self, workflow_id: str, bus: Optional[MessageBus] = None):
        self.workflow_id = workflow_id
        self.bus = bus or get_default_bus()
        self.participant_id = f"workflow:{workflow_id}"
        if self.participant_id not in self.bus.queues:
            self.bus.register_agent(self.participant_id)

    def _message(self, to_agent: str, content: Dict[str, Any], message_type: str, priority: str) -> Message:
        if priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {', '.join(PRIORITIES)}")
        return Message(
            from_agent=self.participant_id,
            to_agent=to_agent,
            message_type=message_type,
            content={**content, "workflow_id": self.workflow_id},
            priority=PRIORITIES[priority],
        )

    async def publish(self, to_agent: str, content: Dict[str, Any], message_type: str = "workflow", priority: str = "normal") -> Message:
        """Send one message; raises MessageBusError when nobody with that id is registered."""
        message = self._message(to_agent, content, message_type, priority)
        await self.bus.send(message)
        return message

    async def request(self, to_agent: str, content: Dict[str, Any], timeout: float = 30.0, message_type: str = "request") -> Dict[str, Any]:
        """Send and wait for the agent's reply (MessageBus.send_and_wait)."""
        message = self._message(to_agent, content, message_type, "high")
        return await self.bus.send_and_wait(to_agent, message, timeout=timeout)

    async def broadcast(self, content: Dict[str, Any], message_type: str = "workflow_status") -> int:
        """Send to every other registered agent; returns how many."""
        message = self._message("*", content, message_type, "low")
        await self.bus.broadcast(message)
        return sum(1 for agent_id in self.bus.queues if agent_id != self.participant_id)

    def received(self) -> List[Message]:
        """Drain messages addressed to this workflow (non-blocking)."""
        queue = self.bus.queues.get(self.participant_id)
        out: List[Message] = []
        while queue is not None:
            try:
                out.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return out

    def shutdown(self) -> None:
        if self.participant_id in self.bus.queues:
            self.bus.unregister_agent(self.participant_id)
        _adapters.pop(self.workflow_id, None)


def get_message_bus_adapter(workflow_id: str, bus: Optional[MessageBus] = None) -> MessageBusAdapter:
    """One adapter per workflow id on the default bus (or the given bus)."""
    adapter = _adapters.get(workflow_id)
    if adapter is None or (bus is not None and adapter.bus is not bus):
        adapter = MessageBusAdapter(workflow_id, bus)
        _adapters[workflow_id] = adapter
    return adapter


async def start_default_agents(bus: Optional[MessageBus] = None, names=DEFAULT_AGENTS) -> List[BusAgent]:
    """Start the built-in bus agents (today: `provider`). Returns them; stop with stop_agents()."""
    bus = bus or get_default_bus()
    agents: List[BusAgent] = []
    for name in names:
        if name == "provider":
            agent = ProviderBusAgent(name, bus)
        else:
            raise ValueError(f"unknown built-in bus agent {name!r}")
        agent.start()
        agents.append(agent)
    await asyncio.sleep(0)  # let the loops start
    return agents


async def stop_agents(agents: List[BusAgent]) -> None:
    for agent in agents:
        await agent.stop()


class MessageBusNode(BaseNode):
    """
    Node type `bus`: talk to agents on the in-process bus.

    Config:
        operation: publish | request | broadcast
        to: agent id (publish, request)
        content: dict, {{var}} placeholders filled from the context (default {})
        message_type: default "workflow" / "request" / "workflow_status" by operation
        timeout: seconds to wait for a reply (request, default 30)
        priority: high | normal | low (publish, default normal)
        output: context key for the result (default: the node id)
    The adapter is the one for the running workflow (context metadata `workflow_id`), or `set_adapter()`.
    """

    def __init__(self, node_id: str, name: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(node_id, name, config)
        operation = self.config.get("operation")
        if operation not in OPERATIONS:
            raise ValueError(f"MessageBusNode {node_id}: operation must be one of {', '.join(OPERATIONS)}")
        if operation in ("publish", "request") and not self.config.get("to"):
            raise ValueError(f"MessageBusNode {node_id}: {operation} needs 'to' (an agent id)")
        self.config.setdefault("content", {})
        self.config.setdefault("timeout", 30.0)
        self.config.setdefault("priority", "normal")
        self.config.setdefault("output", node_id)
        self.adapter: Optional[MessageBusAdapter] = None

    def set_adapter(self, adapter: MessageBusAdapter) -> None:
        self.adapter = adapter

    def _adapter_for(self, context: NodeContext) -> MessageBusAdapter:
        if self.adapter is not None:
            return self.adapter
        workflow_id = context.metadata.get("workflow_id") or context.metadata.get("workflow_name") or "workflow"
        return get_message_bus_adapter(str(workflow_id))

    async def execute(self, context: NodeContext) -> NodeContext:
        adapter = self._adapter_for(context)
        operation = self.config["operation"]
        content = interpolate_deep(self.config["content"], context)
        if not isinstance(content, dict):
            raise ValueError(f"MessageBusNode {self.node_id}: content must be a dict")
        to_agent = interpolate(self.config.get("to"), context)
        if operation == "publish":
            message = await adapter.publish(to_agent, content, self.config.get("message_type", "workflow"), self.config["priority"])
            result: Dict[str, Any] = {"status": "published", "to": to_agent, "correlation_id": message.correlation_id}
        elif operation == "request":
            reply = await adapter.request(to_agent, content, timeout=float(self.config["timeout"]), message_type=self.config.get("message_type", "request"))
            result = {"status": "replied", "to": to_agent, "reply": reply}
        else:
            count = await adapter.broadcast(content, self.config.get("message_type", "workflow_status"))
            result = {"status": "broadcast", "recipients": count}
        context.set(self.config["output"], result)
        context.set_state(f"{self.node_id}_response", result)
        return context
