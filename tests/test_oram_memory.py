"""ORAM file memory backend (src/agents/memory.py + the hooks in src/oram.py).

Off unless ORAM_MEMORY_DIR is set: then one JSONL line per completed run under that directory, and the Reason step
gets the earlier runs of the same task as `prior_runs`. No provider is ever called: the agents are stubs, and the
reasoner test fakes the bus like tests/test_agent_fallbacks.py.
"""

import asyncio
import json

import pytest

import base
from src.agents.memory import MemoryAgent, format_prior_runs, scrub_secrets, task_key
from src.agents.reasoner import ReasonerAgent
from src.oram import ORAMConfig, ORAMIterationType, ORAMSystem, execute_oram
from tests.test_oram import StubActor, StubObserver, StubReasoner, make_system


def run(coro):
    return asyncio.run(coro)


def real_memory_system(**kw):
    """Stub agents, but the real MemoryAgent (which reads ORAM_MEMORY_DIR at construction)."""
    system = make_system(reasoner=StubReasoner("a" * 80), actor=StubActor(["step"]), **kw)
    system.memory = MemoryAgent()
    return system


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    path = tmp_path / "oram-memory"
    monkeypatch.setenv("ORAM_MEMORY_DIR", str(path))
    return path


@pytest.fixture
def no_memory_dir(monkeypatch):
    monkeypatch.delenv("ORAM_MEMORY_DIR", raising=False)


# --- backend off -------------------------------------------------------------------------------

def test_without_the_env_var_nothing_is_written_and_reasoning_has_no_prior_runs(no_memory_dir, tmp_path):
    system = real_memory_system()
    assert system.memory.file_backend_enabled is False
    iterations = run(system.execute_oram_loop("task"))
    run(system.execute_oram_loop("task"))
    assert list(tmp_path.iterdir()) == []
    assert "prior_runs" not in iterations[0].reasoning
    assert system.memory.recall_runs("task") == []
    assert run(system.memory.recall("task")) == []


def test_without_the_env_var_execute_oram_keeps_the_type_default(no_memory_dir, monkeypatch):
    seen = {}

    async def fake_loop(self, task, iteration_type, context=None):
        self.config.set_iteration_type(iteration_type)
        seen["limit"] = self.config.max_iterations
        return []

    monkeypatch.setattr(ORAMSystem, "execute_oram_loop", fake_loop)
    run(execute_oram("task", ORAMIterationType.PROBLEM_SOLVING))
    assert seen["limit"] == 8


def test_the_event_list_api_is_unchanged(no_memory_dir):
    memory = MemoryAgent()
    run(memory.store({"type": "a"}))
    run(memory.store({"type": "b"}))
    assert run(memory.recall()) == [{"type": "a"}, {"type": "b"}]
    assert run(memory.recall(lambda e: e["type"] == "b")) == [{"type": "b"}]


# --- backend on --------------------------------------------------------------------------------

def test_a_run_writes_one_line_per_task_file(memory_dir):
    system = real_memory_system()
    assert system.memory.file_backend_enabled is True
    run(system.execute_oram_loop("Summarise the board", ORAMIterationType.DEEP_ANALYSIS))
    files = list(memory_dir.glob("*.jsonl"))
    assert len(files) == 1 and files[0].stem == task_key("Summarise the board")
    lines = files[0].read_text().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["task"] == "Summarise the board"
    assert record["iterations"] == 1 and record["calls"] == 3
    assert record["iteration_type"] == "deep_analysis"
    assert record["best_quality"] == pytest.approx(0.95) and record["convergence_achieved"] is True
    assert record["ts"].endswith("+00:00")
    assert "1 iterations" in record["summary"] and "step" in record["result"]
    assert any(i.startswith("Reasoning:") for i in record["insights"])


def test_a_second_run_of_the_same_task_sees_the_first_as_prior_runs(memory_dir):
    run(real_memory_system().execute_oram_loop("same task"))
    second = run(real_memory_system().execute_oram_loop("same task"))
    prior = second[0].reasoning["prior_runs"]
    assert len(prior) == 1 and "quality 0.95" in prior[0] and "1 iterations" in prior[0]
    assert second[0].observation["prior_runs"] == prior
    assert len(next(memory_dir.glob("*.jsonl")).read_text().splitlines()) == 2


def test_a_different_task_does_not_see_the_other_tasks_runs(memory_dir):
    run(real_memory_system().execute_oram_loop("same task"))
    other = run(real_memory_system().execute_oram_loop("other task"))
    assert "prior_runs" not in other[0].reasoning
    assert len(list(memory_dir.glob("*.jsonl"))) == 2


def test_the_task_key_ignores_case_and_spacing_but_not_wording():
    assert task_key("Summarise the board") == task_key("  summarise   THE board ")
    assert task_key("Summarise the board") != task_key("Summarise the boards")
    assert task_key("x" * 500).count("/") == 0 and len(task_key("x" * 500)) < 60
    assert task_key("???").startswith("task-")


def test_recall_returns_newest_first_and_respects_the_limit(memory_dir):
    memory = MemoryAgent()
    for n in range(7):
        memory.store_run("t", {"iterations": n})
    runs = memory.recall_runs("t")
    assert [r["iterations"] for r in runs] == [6, 5, 4, 3, 2]
    assert [r["iterations"] for r in run(memory.recall("t", limit=2))] == [6, 5]
    assert memory.recall_runs("t", limit=0) == []


def test_a_corrupt_line_is_skipped_not_fatal(memory_dir):
    memory = MemoryAgent()
    path = memory.store_run("t", {"iterations": 1})
    with path.open("a") as handle:
        handle.write("{not json\n\n[1, 2]\n")
    memory.store_run("t", {"iterations": 2})
    assert [r["iterations"] for r in memory.recall_runs("t")] == [2, 1]


def test_secret_looking_text_is_scrubbed_before_writing(memory_dir):
    fake_key = "sk-" + "A1b2" * 8                        # key-shaped, not a real key
    memory = MemoryAgent()
    path = memory.store_run(f"use {fake_key} to call the api", {
        "summary": f"GROK_API_KEY={fake_key} worked; Bearer {'x' * 24} too",
        "insights": [f"token: {fake_key}", "plain insight"],
        "iterations": 1,
    })
    text = path.read_text()
    assert fake_key not in text and "x" * 24 not in text
    assert "[REDACTED]" in text and "plain insight" in text
    record = json.loads(text)
    assert record["task"] == "use [REDACTED] to call the api"
    assert record["summary"].startswith("GROK_API_KEY [REDACTED]")


def test_scrub_leaves_ordinary_text_alone():
    text = "Review PR #10, the sk-token idea, and password: short"
    assert scrub_secrets(text) == text                    # "sk-token" is too short to be a key; value under 8 chars


def test_stored_text_is_capped_at_two_kilobytes(memory_dir):
    memory = MemoryAgent()
    path = memory.store_run("t", {"summary": "s" * 5000, "result": "r" * 5000})
    record = json.loads(path.read_text())
    assert len(record["summary"]) == 2000 and len(record["result"]) == 2000


def test_execute_oram_defaults_to_three_iterations_with_the_backend_on(memory_dir, monkeypatch):
    seen = {}

    async def fake_loop(self, task, iteration_type, context=None):
        self.config.set_iteration_type(iteration_type)
        seen["limit"] = self.config.max_iterations
        return []

    monkeypatch.setattr(ORAMSystem, "execute_oram_loop", fake_loop)
    run(execute_oram("task", ORAMIterationType.PROBLEM_SOLVING))
    assert seen["limit"] == 3
    run(execute_oram("task", ORAMIterationType.PROBLEM_SOLVING, max_iterations=5))
    assert seen["limit"] == 5


def test_a_stub_memory_without_the_backend_is_tolerated(memory_dir):
    # tests/test_oram.py's StubMemory has no store_run/recall_runs; the hooks must stay no-ops for it.
    system = make_system(reasoner=StubReasoner("a" * 80), actor=StubActor(["step"]))
    iterations = run(system.execute_oram_loop("task"))
    assert len(iterations) == 1 and "prior_runs" not in iterations[0].reasoning
    assert not memory_dir.exists() or list(memory_dir.glob("*.jsonl")) == []


def test_a_failing_recall_does_not_break_the_iteration(memory_dir):
    system = real_memory_system()

    def boom(task, limit=5):
        raise OSError("disk gone")

    system.memory.recall_runs = boom
    iterations = run(system.execute_oram_loop("task"))
    assert len(iterations) == 1 and "error" not in iterations[0].reasoning


# --- the reasoner prompt -----------------------------------------------------------------------

class FakeBus:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    async def send_message(self, content, provider_name, conversation_id=None):
        self.calls.append(content)
        return self.reply


def test_the_reasoner_puts_prior_runs_into_its_prompt(monkeypatch):
    bus = FakeBus('{"analysis": "ok", "subtasks": [], "risks": [], "approach": "a"}')

    async def get_bus():
        return bus

    monkeypatch.setattr(base, "get_ai_provider_bus", get_bus)
    reasoner = ReasonerAgent()
    run(reasoner.reason({"task": "t"}))
    assert "Earlier runs" not in bus.calls[0]
    run(reasoner.reason({"task": "t", "prior_runs": ["2026-11-03 10:00 quality 0.95, 1 iterations: did x"]}))
    assert "Earlier runs of this task" in bus.calls[1] and "did x" in bus.calls[1]


def test_format_prior_runs_is_short_and_newest_first_as_given():
    lines = format_prior_runs([
        {"ts": "2026-11-03T10:00:00+00:00", "best_quality": 0.95, "iterations": 1, "summary": "s" * 1000},
        {"ts": "bad", "iterations": 2},
    ])
    assert lines[0].startswith("2026-11-03 10:00 quality 0.95, 1 iterations: s") and len(lines[0]) <= 240
    assert lines[1] == "bad quality ?, 2 iterations: "
