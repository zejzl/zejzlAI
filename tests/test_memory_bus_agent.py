"""MemoryBusAgent: the ORAM file memory on the in-process bus (src/core/bus_agent.py).

Everything offline and under a temporary ORAM_MEMORY_DIR. The agent shares its files with ORAM's own MemoryAgent, so a
run stored by one side is recalled by the other.
"""
import asyncio

import pytest

import base  # noqa: F401
from src.agents.memory import MemoryAgent
from src.core.bus_agent import MemoryBusAgent
from src.core.message_bus import MessageBus
from src.workflow import messagebus_adapter
from src.workflow.messagebus_adapter import MessageBusAdapter, reset_default_bus, start_default_agents, stop_agents
from tests.test_oram_memory import real_memory_system


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    path = tmp_path / "oram-memory"
    monkeypatch.setenv("ORAM_MEMORY_DIR", str(path))
    monkeypatch.delenv("ORAM_MEMORY_RANKED", raising=False)
    return path


@pytest.fixture
def no_memory_dir(monkeypatch):
    monkeypatch.delenv("ORAM_MEMORY_DIR", raising=False)
    monkeypatch.delenv("ORAM_MEMORY_RANKED", raising=False)


@pytest.fixture(autouse=True)
def fresh_default_bus():
    reset_default_bus()
    yield
    reset_default_bus()


async def with_agent(coro_fn, memory=None):
    bus = MessageBus()
    agent = MemoryBusAgent("memory", bus, memory=memory, receive_timeout=0.05)
    agent.start()
    adapter = MessageBusAdapter("wf", bus)
    try:
        return await coro_fn(adapter, agent)
    finally:
        await agent.stop()


def ask(content, memory=None):
    async def go(adapter, agent):
        return await adapter.request("memory", content, timeout=3)

    return asyncio.run(with_agent(go, memory))


# --- the three operations ---------------------------------------------------------------------------

def test_store_then_exact_recall_through_the_bus(memory_dir):
    stored = ask({"op": "store", "task": "summarise the README", "record": {"iterations": 1, "summary": "three bullets"}})
    assert stored["backend"] is True and stored["stored"].endswith(".jsonl")
    reply = ask({"op": "recall", "task": "summarise the README"})
    assert reply["count"] == 1 and reply["ranked"] is False and reply["backend"] is True
    assert reply["runs"][0]["summary"] == "three bullets" and reply["runs"][0]["task"] == "summarise the README"
    assert reply["lines"][0].startswith("three bullets (") and reply["lines"][0].endswith("quality ?, 1 iterations)")
    assert ask({"op": "recall", "task": "write a README summary"})["count"] == 0


def test_ranked_recall_by_flag_or_by_request(memory_dir, monkeypatch):
    ask({"op": "store", "task": "summarise the README", "record": {"iterations": 1, "summary": "s"}})
    forced = ask({"op": "recall", "task": "write a README summary", "ranked": True})
    assert forced["count"] == 1 and forced["ranked"] is True and forced["lines"][0].startswith("[task: summarise the README] ")
    monkeypatch.setenv("ORAM_MEMORY_RANKED", "1")
    assert ask({"op": "recall", "task": "write a README summary"})["count"] == 1
    assert ask({"op": "recall", "task": "write a README summary", "ranked": False})["count"] == 0
    assert ask({"op": "recall", "task": "write a README summary", "limit": 0})["count"] == 0


def test_status_reports_the_backend_and_the_flag(memory_dir, monkeypatch):
    status = ask({"op": "status"})
    assert status == {"backend": True, "dir": str(memory_dir), "ranked": False}
    monkeypatch.setenv("ORAM_MEMORY_RANKED", "yes")
    assert ask({"op": "status"})["ranked"] is True


def test_backend_off_answers_empty_and_stores_nothing(no_memory_dir):
    assert ask({"op": "status"}) == {"backend": False, "dir": None, "ranked": False}
    assert ask({"op": "store", "task": "t", "record": {"x": 1}}) == {"stored": None, "backend": False}
    reply = ask({"op": "recall", "task": "t"})
    assert reply == {"runs": [], "lines": [], "count": 0, "ranked": False, "backend": False}


def test_bad_requests_get_an_error_not_a_dead_agent(memory_dir):
    async def go(adapter, agent):
        answers = [
            await adapter.request("memory", {"op": "forget", "task": "t"}, timeout=3),
            await adapter.request("memory", {"op": "recall"}, timeout=3),
            await adapter.request("memory", {"op": "recall", "task": "   "}, timeout=3),
            await adapter.request("memory", {"op": "recall", "task": "t", "limit": "many"}, timeout=3),
            await adapter.request("memory", {"op": "store", "task": "t", "record": "not a dict"}, timeout=3),
            await adapter.request("memory", {"op": "status"}, timeout=3),
        ]
        assert agent.running and agent.processed == 6
        return answers

    answers = asyncio.run(with_agent(go))
    assert all("error" in a for a in answers[:5])
    assert "forget" not in answers[0]["error"] and "op" in answers[0]["error"]
    assert answers[5]["backend"] is True


def test_secrets_in_a_stored_record_are_scrubbed(memory_dir):
    ask({"op": "store", "task": "t", "record": {"result": "token: sk-abcdefghijklmnopqrstuvwxyz0123"}})
    reply = ask({"op": "recall", "task": "t"})
    assert "sk-abcdefghijklmnopqrstuvwxyz0123" not in reply["runs"][0]["result"]
    assert "[REDACTED]" in reply["runs"][0]["result"]


# --- shared with ORAM --------------------------------------------------------------------------------

def test_a_run_stored_by_oram_is_recalled_on_the_bus_and_back(memory_dir):
    asyncio.run(real_memory_system().execute_oram_loop("summarise the README"))
    reply = ask({"op": "recall", "task": "summarise the README"})
    assert reply["count"] == 1 and "quality 1.00" in reply["lines"][0]

    ask({"op": "store", "task": "summarise the README", "record": {"iterations": 1, "summary": "from a workflow"}})
    second = asyncio.run(real_memory_system().execute_oram_loop("summarise the README"))
    prior = second[0].reasoning["prior_runs"]
    assert len(prior) == 2 and "from a workflow" in prior[0]


def test_a_shared_memory_object_can_be_passed_in(memory_dir):
    memory = MemoryAgent()
    ask({"op": "store", "task": "t", "record": {"iterations": 1}}, memory=memory)
    assert len(memory.recall_runs("t")) == 1


# --- wiring ------------------------------------------------------------------------------------------

def test_start_default_agents_includes_memory(memory_dir):
    async def go():
        agents = await start_default_agents()
        try:
            assert [a.agent_id for a in agents] == ["provider", "memory"]
            assert isinstance(agents[1], MemoryBusAgent)
            reply = await MessageBusAdapter("wf").request("memory", {"op": "status"}, timeout=3)
            assert reply["backend"] is True
        finally:
            await stop_agents(agents)
        assert "memory" not in messagebus_adapter.get_default_bus().queues

    asyncio.run(go())


def test_runner_runs_a_store_and_recall_workflow_offline(memory_dir, tmp_path, capsys):
    from src.workflow import run as workflow_run

    wf = tmp_path / "mem.yaml"
    wf.write_text(
        "name: mem\ninput: {task: summarise the README}\nnodes:\n"
        "  - id: keep\n    type: bus\n"
        "    config: {operation: request, to: memory, content: {op: store, task: '{{task}}', record: {iterations: 1, summary: kept}}}\n"
        "  - id: remember\n    type: bus\n"
        "    config: {operation: request, to: memory, content: {op: recall, task: '{{task}}'}}\n"
        "edges:\n  - [keep, remember]\n",
        encoding="utf-8",
    )
    code = workflow_run.main([str(wf)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Bus agents started: provider, memory" in out and '"summary": "kept"' in out and '"count": 1' in out
    assert len(list(memory_dir.glob("*.jsonl"))) == 1


def test_the_bundled_example_loads():
    from src.workflow import load_workflow

    workflow, _ = load_workflow("examples/workflows/memory-recall.yaml")
    assert set(workflow.engine.nodes) == {"remember", "ask", "keep"}
