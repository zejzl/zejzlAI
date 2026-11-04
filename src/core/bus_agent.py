"""
Agents that live on the in-process message bus (src/core/message_bus.py).

BusAgent is the receive-process-reply loop: register on the bus, take messages from the own queue,
hand each to `process_message`, and send the reply back to the sender with the request's
correlation_id, which is what `MessageBus.send_and_wait` waits for. The loop follows grokputer's
BaseAgent.run (src/core/base_agent.py) without its heartbeat, task client and session logging.

ProviderBusAgent is the first real agent on this bus: it answers {"prompt", "provider",
"conversation_id"} requests through the shared AI provider bus (`base.get_ai_provider_bus`), so a
workflow (or anything else on the bus) can ask a model without importing ai_framework itself.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Union

from src.exceptions import MessageBusError

from .message_bus import Message, MessageBus, MessagePriority

logger = logging.getLogger(__name__)

Reply = Union[Dict[str, Any], Message, None]


class BusAgent:
    """Receive-process-reply loop on the in-process bus. Subclasses implement `process_message`."""

    def __init__(self, agent_id: str, bus: MessageBus, receive_timeout: float = 1.0):
        self.agent_id = agent_id
        self.bus = bus
        self.receive_timeout = receive_timeout
        self.running = False
        self.processed = 0
        self._task: Optional[asyncio.Task] = None
        if agent_id not in bus.queues:
            bus.register_agent(agent_id)

    async def process_message(self, message: Message) -> Reply:
        """Return a reply: a dict ({"content": ..., "to": ..., "type": ...} or just the content), a Message, or None."""
        raise NotImplementedError

    def start(self) -> asyncio.Task:
        """Start the loop as a task on the running event loop."""
        self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None
        if self.agent_id in self.bus.queues:
            self.bus.unregister_agent(self.agent_id)

    async def run(self) -> None:
        self.running = True
        while self.running:
            try:
                message = await self.bus.receive(self.agent_id, timeout=self.receive_timeout)
            except asyncio.TimeoutError:
                continue
            except ValueError:
                break  # unregistered while running
            try:
                response = await self.process_message(message)
            except Exception as e:  # one bad message must not stop the agent
                logger.error(f"[{self.agent_id}] process_message failed: {e}")
                response = {"content": {"error": f"{type(e).__name__}: {e}"}, "type": "error"}
            self.processed += 1
            if response is None:
                continue
            reply = self._reply_message(message, response)
            try:
                await self.bus.send(reply)
            except MessageBusError:
                # Nobody is registered to read this reply (a one-off sender); not this agent's failure.
                logger.warning(f"[{self.agent_id}] Dropped reply to unregistered agent {reply.to_agent!r} ({reply.message_type})")

    def _reply_message(self, request: Message, response: Union[Dict[str, Any], Message]) -> Message:
        if isinstance(response, Message):
            response.correlation_id = response.correlation_id or request.correlation_id
            return response
        content = response.get("content", response)
        return Message(
            from_agent=self.agent_id,
            to_agent=response.get("to", request.from_agent),
            message_type=response.get("type", "response"),
            content=content if isinstance(content, dict) else {"content": content},
            priority=response.get("priority", MessagePriority.NORMAL),
            correlation_id=response.get("correlation_id") or request.correlation_id,
        )


class ProviderBusAgent(BusAgent):
    """Answers prompt requests through the shared AI provider bus. Errors come back as {"error": ...}."""

    async def process_message(self, message: Message) -> Reply:
        content = message.content if isinstance(message.content, dict) else {}
        prompt = content.get("prompt")
        if not prompt:
            return {"content": {"error": "request needs a 'prompt'"}, "type": "reply"}
        provider = content.get("provider")
        conversation_id = content.get("conversation_id") or f"bus:{message.from_agent}"
        try:
            from base import get_ai_provider_bus

            ai_bus = await get_ai_provider_bus()
            reply = await ai_bus.send_message(prompt, provider, conversation_id)
        except Exception as e:
            return {"content": {"error": str(e), "provider": provider}, "type": "reply"}
        return {"content": {"reply": reply, "provider": provider}, "type": "reply"}
