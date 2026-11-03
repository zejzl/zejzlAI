"""
Workflow nodes that use zejzlAI's own agents and ORAM loop.

AgentNode has two forms:

  agent form   config {"agent": "observer" | "reasoner" | "actor", "input": <context key>, "provider": <name>}
               runs one Pantheon agent step: observer.observe(task), reasoner.reason(observation), actor.act(plan).
               `input` names the context key holding the step's input (default: the step's natural key, see AGENTS).
               The agents degrade to a rule-based answer when the provider is down (`ai_generated: False`);
               set "require_ai": true to fail the node instead.
  prompt form  config {"prompt": "... {{var}} ...", "provider": <name>, "output_format": "text" | "json" | "decision"}
               sends one prompt through the shared provider bus (`base.get_ai_provider_bus().send_message`),
               {{var}} placeholders are filled from the context data and state.

Both forms store their result under config "output" (default: the node id) and in state as "<node_id>_response".

ORAMNode runs one `execute_oram` loop: config {"task": "... {{var}} ..." or "input": <context key>,
"iteration_type": "basic", "max_iterations": 3}. The default cap of 3 iterations is Zejzl's ORAM decision of 2026-11-03.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from .base import BaseNode, NodeContext

# agent name -> (module, class, method, natural input key)
AGENTS: Dict[str, tuple] = {
    "observer": ("src.agents.observer", "ObserverAgent", "observe", "task"),
    "reasoner": ("src.agents.reasoner", "ReasonerAgent", "reason", "observation"),
    "actor": ("src.agents.actor", "ActorAgent", "act", "plan"),
}
OUTPUT_FORMATS = ("text", "json", "decision")
ORAM_TYPES = ("basic", "deep_analysis", "creative", "problem_solving", "optimization")
DEFAULT_ORAM_ITERATIONS = 3


def interpolate(value: Any, context: NodeContext) -> Any:
    """Replace {{key}} placeholders with values from the context data, then state. Non-strings pass through."""
    if not isinstance(value, str) or "{{" not in value:
        return value

    def repl(match: "re.Match[str]") -> str:
        key = match.group(1).strip()
        if key in context.data:
            val = context.data[key]
        elif key in context.state:
            val = context.state[key]
        else:
            return match.group(0)
        return json.dumps(val, indent=2, default=str) if isinstance(val, (dict, list)) else str(val)

    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, value)


class AgentNode(BaseNode):
    """One Pantheon agent step, or one prompt, through the provider bus. See the module docstring."""

    def __init__(self, node_id: str, name: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(node_id, name, config)
        agent = self.config.get("agent")
        prompt = self.config.get("prompt")
        if bool(agent) == bool(prompt):
            raise ValueError(f"AgentNode {node_id}: give exactly one of 'agent' or 'prompt'")
        if agent and agent not in AGENTS:
            raise ValueError(f"AgentNode {node_id}: unknown agent {agent!r}; choose from {', '.join(AGENTS)}")
        fmt = self.config.setdefault("output_format", "text")
        if fmt not in OUTPUT_FORMATS:
            raise ValueError(f"AgentNode {node_id}: output_format must be one of {', '.join(OUTPUT_FORMATS)}")
        self.config.setdefault("provider", None)
        self.config.setdefault("output", node_id)
        self.config.setdefault("require_ai", False)

    async def execute(self, context: NodeContext) -> NodeContext:
        if self.config.get("agent"):
            result = await self._run_agent(context)
        else:
            result = await self._run_prompt(context)
        context.set(self.config["output"], result)
        context.set_state(f"{self.node_id}_response", result)
        return context

    async def _run_agent(self, context: NodeContext) -> Dict[str, Any]:
        import importlib

        module_name, class_name, method, natural_key = AGENTS[self.config["agent"]]
        input_key = self.config.get("input", natural_key)
        if input_key not in context.data:
            raise ValueError(
                f"AgentNode {self.node_id}: no {input_key!r} in the workflow data for agent {self.config['agent']}"
            )
        payload = interpolate(context.get(input_key), context)
        agent = getattr(importlib.import_module(module_name), class_name)()
        result = await getattr(agent, method)(payload, provider=self.config["provider"])
        if self.config["require_ai"] and isinstance(result, dict) and result.get("ai_generated") is False:
            reason = result.get("fallback_reason") or result.get("error") or "provider unavailable"
            raise RuntimeError(f"AgentNode {self.node_id}: {self.config['agent']} fell back to rules: {reason}")
        return result

    async def _run_prompt(self, context: NodeContext) -> Any:
        from base import get_ai_provider_bus

        prompt = interpolate(self.config["prompt"], context)
        conversation_id = self.config.get("conversation_id") or f"workflow:{self.node_id}"
        bus = await get_ai_provider_bus()
        reply = await bus.send_message(prompt, self.config["provider"], conversation_id)
        if reply is None:
            raise RuntimeError(f"AgentNode {self.node_id}: the provider returned no content")
        return self._parse(str(reply), self.config["output_format"])

    def _parse(self, text: str, output_format: str) -> Any:
        if output_format == "text":
            return text.strip()
        if output_format == "json":
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise ValueError(f"AgentNode {self.node_id}: no JSON object in the reply: {text[:100]!r}")
            return json.loads(match.group())
        lowered = text.lower()
        if any(word in lowered for word in ("yes", "true", "proceed")):
            return True
        if any(word in lowered for word in ("no", "false", "stop")):
            return False
        raise ValueError(f"AgentNode {self.node_id}: no yes/no decision in the reply: {text[:100]!r}")


class ORAMNode(BaseNode):
    """One ORAM loop (Observe, Reason, Act, Memory) on a task, capped at `max_iterations` (default 3)."""

    def __init__(self, node_id: str, name: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(node_id, name, config)
        if not self.config.get("task") and not self.config.get("input"):
            self.config["input"] = "task"
        kind = self.config.setdefault("iteration_type", "basic")
        if kind not in ORAM_TYPES:
            raise ValueError(f"ORAMNode {node_id}: iteration_type must be one of {', '.join(ORAM_TYPES)}")
        cap = self.config.setdefault("max_iterations", DEFAULT_ORAM_ITERATIONS)
        if not isinstance(cap, int) or cap < 1:
            raise ValueError(f"ORAMNode {node_id}: max_iterations must be a positive integer")
        self.config.setdefault("output", node_id)

    async def execute(self, context: NodeContext) -> NodeContext:
        from src import oram

        if self.config.get("task"):
            task = interpolate(self.config["task"], context)
        else:
            task = context.get(self.config["input"])
            if not task:
                raise ValueError(f"ORAMNode {self.node_id}: no {self.config['input']!r} in the workflow data")
        iterations = await oram.execute_oram(
            str(task),
            iteration_type=oram.ORAMIterationType(self.config["iteration_type"]),
            max_iterations=self.config["max_iterations"],
        )
        scores = [it.quality_score for it in iterations]
        insights = [i for it in iterations for i in (it.insights or [])]
        last = iterations[-1] if iterations else None
        result = {
            "task": str(task),
            "iteration_type": self.config["iteration_type"],
            "iterations": len(iterations),
            "best_quality": max(scores) if scores else 0.0,
            "average_quality": sum(scores) / len(scores) if scores else 0.0,
            "insights": insights,
            "result": (last.action or {}).get("results") if last else None,
            "ai_generated": all((it.action or {}).get("ai_generated", True) for it in iterations) if iterations else False,
        }
        context.set(self.config["output"], result)
        context.set_state(f"{self.node_id}_response", result)
        return context
