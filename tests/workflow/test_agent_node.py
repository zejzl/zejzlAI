"""AgentNode and ORAMNode: zejzlAI's own workflow nodes. No network: the provider bus and execute_oram are faked."""
import asyncio
from types import SimpleNamespace

import pytest

import base
from src import oram
from src.workflow import NODE_TYPES, WorkflowDefinitionError, WorkflowEngine, build_workflow
from src.workflow.nodes import AgentNode, NodeContext, ORAMNode
from src.workflow.nodes.agent_node import interpolate


class FakeBus:
    def __init__(self, reply=None, error=None):
        self.reply, self.error, self.calls = reply, error, []

    async def send_message(self, content, provider_name, conversation_id=None):
        self.calls.append({"content": content, "provider": provider_name, "conversation": conversation_id})
        if self.error:
            raise self.error
        return self.reply


def use_bus(monkeypatch, bus):
    async def get_bus():
        return bus

    monkeypatch.setattr(base, "get_ai_provider_bus", get_bus)
    return bus


def run(coro):
    return asyncio.run(coro)


DOWN = ValueError("Provider grok not registered")


# --- configuration ------------------------------------------------------------------------------

class TestConfig:
    def test_agent_or_prompt_exactly_one(self):
        with pytest.raises(ValueError, match="exactly one"):
            AgentNode("a", config={})
        with pytest.raises(ValueError, match="exactly one"):
            AgentNode("a", config={"agent": "observer", "prompt": "hi"})

    def test_unknown_agent_and_bad_format_are_rejected(self):
        with pytest.raises(ValueError, match="unknown agent"):
            AgentNode("a", config={"agent": "oracle"})
        with pytest.raises(ValueError, match="output_format"):
            AgentNode("a", config={"prompt": "hi", "output_format": "xml"})

    def test_defaults(self):
        node = AgentNode("classify", config={"prompt": "hi"})
        assert node.config["output"] == "classify" and node.config["provider"] is None
        assert node.config["output_format"] == "text" and node.config["require_ai"] is False

    def test_oram_defaults_and_validation(self):
        node = ORAMNode("o", config={})
        assert node.config == {"input": "task", "iteration_type": "basic", "max_iterations": 3, "output": "o"}
        with pytest.raises(ValueError, match="iteration_type"):
            ORAMNode("o", config={"iteration_type": "wild"})
        with pytest.raises(ValueError, match="positive integer"):
            ORAMNode("o", config={"max_iterations": 0})

    def test_loader_knows_both_types_and_reports_bad_config(self):
        assert NODE_TYPES["agent"] is AgentNode and NODE_TYPES["oram"] is ORAMNode
        with pytest.raises(WorkflowDefinitionError, match="unknown agent"):
            build_workflow({"nodes": [{"id": "a", "type": "agent", "config": {"agent": "oracle"}}]})


# --- interpolation -----------------------------------------------------------------------------

def test_interpolate_fills_from_data_then_state_and_leaves_unknowns():
    ctx = NodeContext(data={"name": "Zej", "plan": {"steps": 2}}, state={"mood": "calm"})
    assert interpolate("hi {{name}}, {{ mood }}", ctx) == "hi Zej, calm"
    assert '"steps": 2' in interpolate("{{plan}}", ctx)
    assert interpolate("{{missing}}", ctx) == "{{missing}}"
    assert interpolate(42, ctx) == 42


# --- agent form --------------------------------------------------------------------------------

class TestAgentForm:
    def test_observer_reads_task_and_writes_under_its_id(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(error=DOWN))
        node = AgentNode("observe", config={"agent": "observer"})
        ctx = run(node.run(NodeContext(data={"task": "tidy the downloads folder"})))
        out = ctx.get("observe")
        assert out["ai_generated"] is False and out["task"] == "tidy the downloads folder"
        assert ctx.get_state("observe_response") is out

    def test_missing_input_is_an_error(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(error=DOWN))
        node = AgentNode("observe", config={"agent": "observer"})
        with pytest.raises(ValueError, match="no 'task'"):
            run(node.execute(NodeContext(data={})))

    def test_require_ai_fails_the_node_on_fallback(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(error=DOWN))
        node = AgentNode("observe", config={"agent": "observer", "require_ai": True})
        with pytest.raises(RuntimeError, match="fell back to rules"):
            run(node.execute(NodeContext(data={"task": "x"})))

    def test_provider_is_passed_to_the_agent(self, monkeypatch):
        bus = use_bus(monkeypatch, FakeBus(error=DOWN))
        node = AgentNode("observe", config={"agent": "observer", "provider": "claude"})
        run(node.execute(NodeContext(data={"task": "x"})))
        assert bus.calls and bus.calls[0]["provider"] == "claude"

    @pytest.mark.asyncio
    async def test_observe_reason_act_chain_runs_offline(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(error=DOWN))
        wf = build_workflow({
            "name": "ora",
            "nodes": [
                {"id": "observe", "type": "agent", "config": {"agent": "observer"}},
                {"id": "reason", "type": "agent", "config": {"agent": "reasoner", "input": "observe"}},
                {"id": "act", "type": "agent", "config": {"agent": "actor", "input": "reason"}},
            ],
            "edges": [["observe", "reason"], ["reason", "act"]],
        })
        result = await WorkflowEngine("ora").execute(wf, {"task": "tidy the downloads folder"})
        assert result["status"] == "success" and result["nodes_executed"] == 3
        data = result["data"]
        assert data["reason"]["subtasks"] and "results" in data["act"]
        assert data["act"]["ai_generated"] is False


# --- prompt form -------------------------------------------------------------------------------

class TestPromptForm:
    def test_prompt_is_interpolated_and_sent_once(self, monkeypatch):
        bus = use_bus(monkeypatch, FakeBus(reply="  low  "))
        node = AgentNode("urgency", config={"prompt": "Urgency of: {{message}}", "provider": "grok"})
        ctx = run(node.execute(NodeContext(data={"message": "the build is red"})))
        assert ctx.get("urgency") == "low"
        assert bus.calls == [{"content": "Urgency of: the build is red", "provider": "grok", "conversation": "workflow:urgency"}]

    def test_json_and_decision_formats(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(reply='Sure: {"ok": true, "n": 2} done'))
        ctx = run(AgentNode("j", config={"prompt": "p", "output_format": "json"}).execute(NodeContext()))
        assert ctx.get("j") == {"ok": True, "n": 2}
        use_bus(monkeypatch, FakeBus(reply="Yes, proceed."))
        ctx = run(AgentNode("d", config={"prompt": "p", "output_format": "decision"}).execute(NodeContext()))
        assert ctx.get("d") is True

    def test_unparseable_replies_and_provider_errors_fail_the_node(self, monkeypatch):
        use_bus(monkeypatch, FakeBus(reply="maybe"))
        with pytest.raises(ValueError, match="no yes/no decision"):
            run(AgentNode("d", config={"prompt": "p", "output_format": "decision"}).execute(NodeContext()))
        use_bus(monkeypatch, FakeBus(reply="no braces here"))
        with pytest.raises(ValueError, match="no JSON object"):
            run(AgentNode("j", config={"prompt": "p", "output_format": "json"}).execute(NodeContext()))
        use_bus(monkeypatch, FakeBus(error=DOWN))
        with pytest.raises(ValueError, match="not registered"):
            run(AgentNode("t", config={"prompt": "p"}).execute(NodeContext()))


# --- ORAM node ---------------------------------------------------------------------------------

def _iteration(i, score, insights, results, ai=True):
    return SimpleNamespace(
        iteration_id=i, quality_score=score, insights=insights,
        action={"results": results, "ai_generated": ai}, observation={}, reasoning={},
    )


class TestORAMNode:
    def test_runs_execute_oram_with_the_cap_and_summarises(self, monkeypatch):
        calls = []

        async def fake_execute_oram(task, iteration_type, max_iterations):
            calls.append((task, iteration_type, max_iterations))
            return [_iteration(1, 0.6, ["a"], {"draft": 1}), _iteration(2, 0.9, ["b", "c"], {"draft": 2})]

        monkeypatch.setattr(oram, "execute_oram", fake_execute_oram)
        node = ORAMNode("oram", config={"iteration_type": "creative"})
        ctx = run(node.execute(NodeContext(data={"task": "plan a post"})))
        assert calls == [("plan a post", oram.ORAMIterationType.CREATIVE, 3)]
        out = ctx.get("oram")
        assert out["iterations"] == 2 and out["best_quality"] == 0.9 and out["average_quality"] == 0.75
        assert out["insights"] == ["a", "b", "c"] and out["result"] == {"draft": 2} and out["ai_generated"] is True

    def test_task_template_and_missing_task(self, monkeypatch):
        seen = {}

        async def fake_execute_oram(task, iteration_type, max_iterations):
            seen["task"] = task
            return []

        monkeypatch.setattr(oram, "execute_oram", fake_execute_oram)
        ctx = run(ORAMNode("o", config={"task": "summarise {{topic}}"}).execute(NodeContext(data={"topic": "agents"})))
        assert seen["task"] == "summarise agents" and ctx.get("o")["iterations"] == 0
        with pytest.raises(ValueError, match="no 'task'"):
            run(ORAMNode("o", config={}).execute(NodeContext(data={})))
