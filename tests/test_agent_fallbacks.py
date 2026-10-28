"""What the ORAM agents do when the AI provider works, fails or answers badly. No network: the provider bus is faked.

The agents fetch the shared bus with `base.get_ai_provider_bus()` and call `send_message(content, provider_name,
conversation_id)`. A provider that is not registered raises ValueError, exactly as the real bus does.
"""

import asyncio
import json
from types import SimpleNamespace

import pytest

import base
from src.agents.actor import ActorAgent
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent


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
OBSERVATION = {"task": "tidy the downloads folder", "context": "test"}
PLAN = {"subtasks": [{"description": "list files"}, "sort them"]}


# --- provider unavailable: every agent degrades to a rule-based answer ----------------------------

def test_observer_falls_back_when_the_provider_is_missing(monkeypatch):
    use_bus(monkeypatch, FakeBus(error=DOWN))
    out = run(ObserverAgent().observe("tidy the downloads folder"))
    assert out["ai_generated"] is False
    assert "not registered" in out["error"]
    assert out["task"] == "tidy the downloads folder" and out["requirements"]


def test_reasoner_falls_back_with_a_usable_plan(monkeypatch):
    use_bus(monkeypatch, FakeBus(error=DOWN))
    out = run(ReasonerAgent().reason(OBSERVATION))
    assert out["ai_generated"] is False and "not registered" in out["fallback_reason"]
    assert out["subtasks"] and out["approach"] and out["risks"]


def test_actor_falls_back_with_one_result_per_subtask(monkeypatch):
    use_bus(monkeypatch, FakeBus(error=DOWN))
    out = run(ActorAgent().act(PLAN))
    assert out["ai_generated"] is False and out["total_subtasks"] == 2 and len(out["results"]) == 2
    assert all(r["ai_generated"] is False and r["execution_plan"] for r in out["results"])


@pytest.mark.parametrize("error", [ValueError("Provider grok not registered"), TimeoutError("timed out"), RuntimeError("500")])
def test_no_agent_raises_whatever_the_provider_error(monkeypatch, error):
    use_bus(monkeypatch, FakeBus(error=error))
    run(ObserverAgent().observe("t"))
    run(ReasonerAgent().reason(OBSERVATION))
    run(ActorAgent().act(PLAN))


# --- provider works -------------------------------------------------------------------------------

def test_observer_uses_the_ai_answer(monkeypatch):
    reply = json.dumps({"objective": "clean up", "requirements": ["list", "sort"], "complexity_level": "Low",
                        "estimated_effort": "Low"})
    use_bus(monkeypatch, FakeBus(reply=reply))
    out = run(ObserverAgent().observe("tidy the downloads folder"))
    assert out["ai_generated"] is True and out["objective"] == "clean up" and out["requirements"] == ["list", "sort"]


def test_reasoner_parses_a_json_plan_and_stringified_lists(monkeypatch):
    reply = json.dumps({"analysis": "two steps", "subtasks": json.dumps([{"id": "1", "description": "a"}]),
                        "risks": "[\"r1\"]", "approach": "sequential"})
    use_bus(monkeypatch, FakeBus(reply=reply))
    out = run(ReasonerAgent().reason(OBSERVATION))
    assert out["ai_generated"] is True and out["analysis"] == "two steps"
    assert out["subtasks"] == [{"id": "1", "description": "a"}] and out["risks"] == ["r1"]


def test_reasoner_keeps_a_non_json_answer_instead_of_failing(monkeypatch):
    use_bus(monkeypatch, FakeBus(reply="Sure! First list the files, then sort them."))
    out = run(ReasonerAgent().reason(OBSERVATION))
    assert out["analysis"] == "AI response parsing failed" and out["raw_response"].startswith("Sure!")
    assert out["subtasks"][0]["id"] == "fallback"


def test_actor_asks_once_per_subtask_and_uses_the_answers(monkeypatch):
    reply = json.dumps({"execution_steps": ["ls", "sort"], "tools_needed": ["shell"], "expected_outcome": "sorted",
                        "risk_mitigation": "dry run", "estimated_duration": "1 min"})
    bus = use_bus(monkeypatch, FakeBus(reply=reply))
    out = run(ActorAgent().act(PLAN))
    assert len(bus.calls) == 2 and out["ai_generated"] is True and out["total_subtasks"] == 2


# --- which provider is asked ----------------------------------------------------------------------

@pytest.mark.parametrize("call, expected", [
    (lambda: ObserverAgent().observe("t"), "grok"),
    (lambda: ReasonerAgent().reason(OBSERVATION), "grok"),
    (lambda: ActorAgent().act(PLAN), "grok"),
    (lambda: ObserverAgent().observe("t", provider="claude"), "claude"),
    (lambda: ReasonerAgent().reason(OBSERVATION, provider="gemini"), "gemini"),
    (lambda: ActorAgent().act(PLAN, provider="chatgpt"), "chatgpt"),
])
def test_default_provider_is_grok_and_an_explicit_one_is_used(monkeypatch, call, expected):
    bus = use_bus(monkeypatch, FakeBus(error=DOWN))
    run(call())
    assert bus.calls and {c["provider"] for c in bus.calls} == {expected}


# --- picking a provider in main.py ----------------------------------------------------------------

def test_get_available_provider_prefers_the_requested_one_then_any():
    import main

    bus = SimpleNamespace(providers={"claude": object(), "gemini": object()})
    assert main.get_available_provider(bus, "gemini") == "gemini"
    assert main.get_available_provider(bus, "grok") == "claude"                  # first registered
    assert main.get_available_provider(SimpleNamespace(providers={}), "grok") is None
    assert main.get_available_provider(None) is None
    assert main.get_available_provider(SimpleNamespace(), "grok") is None        # no providers attribute
