"""Ranked cross-task recall for the ORAM file memory (ORAM_MEMORY_RANKED=1).

Off: the Reason step sees only earlier runs of the exact same task key (tests/test_oram_memory.py). On: it sees the
best-matching earlier runs of any task in ORAM_MEMORY_DIR, ranked by word overlap with the current task, then recency.
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

import base  # noqa: F401  (conftest wiring, as in the other ORAM tests)
from src.agents.memory import MemoryAgent, format_prior_runs, ranked_enabled, score_run, tokens
from tests.test_oram_memory import real_memory_system


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def memory_dir(tmp_path, monkeypatch):
    path = tmp_path / "oram-memory"
    monkeypatch.setenv("ORAM_MEMORY_DIR", str(path))
    monkeypatch.delenv("ORAM_MEMORY_RANKED", raising=False)
    return path


@pytest.fixture
def ranked(monkeypatch):
    monkeypatch.setenv("ORAM_MEMORY_RANKED", "1")


def stored(memory, task, days_ago=0.0, **fields):
    """A run written `days_ago` days back (the ts is rewritten after the append)."""
    record = {"iterations": 1, "summary": f"summary of {task}", **fields}
    path = memory.store_run(task, record)
    if days_ago:
        lines = path.read_text().splitlines()
        last = json.loads(lines[-1])
        last["ts"] = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")
        lines[-1] = json.dumps(last)
        path.write_text("\n".join(lines) + "\n")
    return path


# --- scoring ------------------------------------------------------------------------------------

def test_tokens_drop_stopwords_and_keep_file_names():
    assert tokens("Summarise the README of src/agents/memory.py") == {"summarise", "readme", "src", "agents", "memory.py"}
    assert tokens("the a of in") == frozenset()
    assert tokens(None) == frozenset() and tokens(42) == {"42"}


def test_score_is_zero_without_a_shared_word_and_one_ish_for_the_same_task():
    run_ = {"task": "summarise the trading-lab README", "ts": datetime.now(timezone.utc).isoformat()}
    assert score_run(run_, tokens("fix the login bug")) == 0.0
    assert score_run(run_, frozenset()) == 0.0
    same = score_run(run_, tokens("summarise the trading-lab README"))
    assert 0.75 < same <= 1.0  # 0.8 * 0.7 (task overlap) + 0.2 * recency, content empty here


def test_content_words_count_less_than_task_words():
    now = datetime.now(timezone.utc)
    by_task = {"task": "write a readme summary", "ts": now.isoformat()}
    by_content = {"task": "unrelated chore", "summary": "readme summary written", "ts": now.isoformat()}
    query = tokens("readme summary")
    assert score_run(by_task, query, now) > score_run(by_content, query, now) > 0.0


def test_recency_is_only_a_tie_breaker():
    now = datetime.now(timezone.utc)
    query = tokens("summarise the readme")
    old_exact = {"task": "summarise the readme", "ts": (now - timedelta(days=60)).isoformat()}
    new_partial = {"task": "summarise the board", "ts": now.isoformat()}
    bad_ts = {"task": "summarise the readme", "ts": "yesterday"}
    assert score_run(old_exact, query, now) > score_run(new_partial, query, now)
    assert score_run(bad_ts, query, now) < score_run(old_exact, query, now)  # unparsable ts = no recency credit


@pytest.mark.parametrize("value,expected", [("1", True), ("true", True), ("YES", True), ("on", True),
                                            ("0", False), ("", False), ("no", False)])
def test_ranked_enabled_reads_the_env_var(monkeypatch, value, expected):
    monkeypatch.setenv("ORAM_MEMORY_RANKED", value)
    assert ranked_enabled() is expected


# --- recall over the directory --------------------------------------------------------------------

def test_a_paraphrased_task_is_found_by_ranked_recall_but_not_by_exact_recall(memory_dir):
    memory = MemoryAgent()
    stored(memory, "summarise the trading-lab README")
    assert memory.recall_runs("write a README summary for trading-lab") == []
    found = memory.recall_ranked("write a README summary for trading-lab")
    assert [r["task"] for r in found] == ["summarise the trading-lab README"]


def test_an_unrelated_history_yields_nothing(memory_dir):
    memory = MemoryAgent()
    stored(memory, "summarise the trading-lab README")
    assert memory.recall_ranked("fix the login bug") == []
    assert memory.recall_ranked("the a of") == []
    assert memory.recall_ranked("summarise", limit=0) == []


def test_the_same_task_ranks_first_then_closer_matches_then_newer(memory_dir):
    memory = MemoryAgent()
    stored(memory, "summarise the README", days_ago=30)
    stored(memory, "summarise the README in 3 bullets", days_ago=10)
    stored(memory, "summarise the README in 3 bullets", days_ago=1)
    stored(memory, "summarise the board")
    ranked_tasks = [(r["task"], r["ts"][:10]) for r in memory.recall_ranked("summarise the README in 3 bullets")]
    assert [t for t, _ in ranked_tasks] == ["summarise the README in 3 bullets", "summarise the README in 3 bullets",
                                            "summarise the README", "summarise the board"]
    assert ranked_tasks[0][1] > ranked_tasks[1][1]  # of the two exact matches, the newer first


def test_limit_and_corrupt_lines(memory_dir):
    memory = MemoryAgent()
    for n in range(4):
        stored(memory, f"summarise file {n}")
    path = next(memory_dir.glob("*.jsonl"))
    with path.open("a") as handle:
        handle.write("{not json\n[1]\n")
    assert len(memory.recall_ranked("summarise file", limit=2)) == 2
    assert len(memory.recall_ranked("summarise file", limit=10)) == 4


def test_the_cache_sees_new_runs_and_deleted_files(memory_dir):
    memory = MemoryAgent()
    stored(memory, "summarise the README")
    assert len(memory.recall_ranked("summarise the README")) == 1
    stored(memory, "summarise the README")
    stored(memory, "summarise the changelog")
    assert len(memory.recall_ranked("summarise the README")) == 3
    for path in memory_dir.glob("*changelog*.jsonl"):
        path.unlink()
    assert len(memory.recall_ranked("summarise the README")) == 2
    assert all(path.is_file() for path in memory._runs_cache)


def test_without_a_directory_ranked_recall_is_empty(monkeypatch):
    monkeypatch.delenv("ORAM_MEMORY_DIR", raising=False)
    assert MemoryAgent().recall_ranked("anything") == []


def test_recall_prior_follows_the_flag(memory_dir, monkeypatch):
    memory = MemoryAgent()
    stored(memory, "summarise the trading-lab README")
    assert memory.recall_prior("write a README summary for trading-lab") == []
    monkeypatch.setenv("ORAM_MEMORY_RANKED", "1")
    assert len(memory.recall_prior("write a README summary for trading-lab")) == 1
    assert len(memory.recall_prior("summarise the trading-lab README")) == 1


# --- the Reason step ------------------------------------------------------------------------------

def test_format_marks_runs_of_other_tasks_only_when_the_current_task_is_given():
    runs = [{"ts": "2026-11-04T13:00:00+00:00", "task": "summarise   the README", "iterations": 1, "summary": "s"},
            {"ts": "2026-11-04T12:00:00+00:00", "task": "list token savings", "iterations": 2, "summary": "t"}]
    plain = format_prior_runs(runs)
    marked = format_prior_runs(runs, task="Summarise the README")
    assert not any(line.startswith("[task:") for line in plain)
    assert not marked[0].startswith("[task:")
    assert marked[1] == "[task: list token savings] t (2026-11-04 12:00, quality ?, 2 iterations)"


def test_flag_off_a_similar_task_gets_no_prior_runs(memory_dir):
    run(real_memory_system().execute_oram_loop("summarise the README"))
    second = run(real_memory_system().execute_oram_loop("summarise the README again"))
    assert "prior_runs" not in second[0].reasoning


def test_flag_on_a_similar_task_gets_the_other_run_marked(memory_dir, ranked):
    run(real_memory_system().execute_oram_loop("summarise the README"))
    second = run(real_memory_system().execute_oram_loop("summarise the README again"))
    prior = second[0].reasoning["prior_runs"]
    assert len(prior) == 1 and prior[0].startswith("[task: summarise the README] ") and "quality 1.00" in prior[0]
    assert second[0].observation["prior_runs"] == prior


def test_flag_on_the_same_task_is_not_marked(memory_dir, ranked):
    run(real_memory_system().execute_oram_loop("summarise the README"))
    second = run(real_memory_system().execute_oram_loop("summarise the README"))
    assert not second[0].reasoning["prior_runs"][0].startswith("[task:")


def test_flag_on_a_memory_without_recall_prior_still_works(memory_dir, ranked):
    class OldMemory(MemoryAgent):
        recall_prior = None  # a memory implementation that predates ranked recall

    system = real_memory_system()
    system.memory = OldMemory()
    run(system.execute_oram_loop("summarise the README"))
    second = real_memory_system()
    second.memory = OldMemory()
    out = run(second.execute_oram_loop("summarise the README"))
    assert len(out[0].reasoning["prior_runs"]) == 1
