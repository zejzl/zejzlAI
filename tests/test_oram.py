"""ORAM mode (src/oram.py) with stub agents: no network, no providers.

Three behaviours here were bugs found while writing these tests, and are fixed in the same PR:
- max_iterations=N ran N+1 iterations,
- a user-chosen max_iterations was overwritten by the iteration type's default,
- an agent reporting a top-level "error" still scored as a clean iteration.
"""

import asyncio

import pytest

from src.oram import ORAMConfig, ORAMIterationType, ORAMSystem, execute_oram


class StubObserver:
    def __init__(self, **extra):
        self.extra = extra

    async def observe(self, task):
        return {"task": task, **self.extra}


class StubReasoner:
    def __init__(self, analysis=None):
        self.analysis = analysis

    async def reason(self, observation):
        return {"analysis": self.analysis} if self.analysis else {}


class StubActor:
    def __init__(self, results=None):
        self.results = results

    async def act(self, plan):
        return {"results": self.results} if self.results else {}


class StubMemory:
    def __init__(self):
        self.events = []

    async def store(self, event):
        self.events.append(event)


def make_system(config=None, observer=None, reasoner=None, actor=None):
    """An ORAMSystem wired to stubs, skipping the real agents (which would call providers)."""
    system = ORAMSystem.__new__(ORAMSystem)
    system.config = config or ORAMConfig()
    system.memory_buffer, system.iteration_history = [], []
    system.convergence_metrics, system.insight_repository = [], []
    system.observer = observer or StubObserver()
    system.reasoner = reasoner or StubReasoner()
    system.actor = actor or StubActor()
    system.memory = StubMemory()
    return system


def run(coro):
    return asyncio.run(coro)


def good_system(**kw):
    """Every phase succeeds with substance: quality 0.95, which clears every convergence threshold."""
    return make_system(reasoner=StubReasoner("a" * 80), actor=StubActor(["step"]), **kw)


# --- configuration -------------------------------------------------------------------------------

@pytest.mark.parametrize("kind, iterations, threshold", [
    (ORAMIterationType.BASIC, 5, 0.85),
    (ORAMIterationType.DEEP_ANALYSIS, 7, 0.9),
    (ORAMIterationType.CREATIVE, 6, 0.8),
    (ORAMIterationType.PROBLEM_SOLVING, 8, 0.85),
    (ORAMIterationType.OPTIMIZATION, 5, 0.9),
])
def test_iteration_type_sets_its_defaults(kind, iterations, threshold):
    config = ORAMConfig()
    config.set_iteration_type(kind)
    assert (config.max_iterations, config.convergence_threshold) == (iterations, threshold)


def test_a_user_chosen_max_iterations_beats_the_type_default():
    config = ORAMConfig()
    config.max_iterations = 3
    config.set_iteration_type(ORAMIterationType.PROBLEM_SOLVING)      # default would be 8
    assert config.max_iterations == 3
    assert config.convergence_threshold == 0.85                         # other settings still follow the type


# --- the loop ------------------------------------------------------------------------------------

def test_loop_stops_as_soon_as_quality_converges():
    system = good_system()
    iterations = run(system.execute_oram_loop("task", ORAMIterationType.BASIC))
    assert len(iterations) == 1
    assert iterations[0].quality_score == pytest.approx(0.95)
    assert system.get_status()["iterations_executed"] == 1


@pytest.mark.parametrize("limit", [1, 2, 3, 6])
def test_loop_runs_exactly_max_iterations_when_it_never_converges(limit):
    config = ORAMConfig()
    config.max_iterations = limit
    system = make_system(config=config)                                 # empty reasoning/action: quality 0.775 < 0.85
    iterations = run(system.execute_oram_loop("task", ORAMIterationType.BASIC))
    assert len(iterations) == limit
    assert [i.iteration_id for i in iterations] == list(range(1, limit + 1))


def test_loop_honours_a_user_limit_for_every_iteration_type():
    for kind in ORAMIterationType:
        config = ORAMConfig()
        config.max_iterations = 2
        system = make_system(config=config)
        assert len(run(system.execute_oram_loop("task", kind))) == 2, kind


def test_loop_without_adaptive_iterations_stops_after_one():
    config = ORAMConfig()
    config.adaptive_iterations = False
    iterations = run(make_system(config=config).execute_oram_loop("task"))
    assert len(iterations) == 1


def test_a_declining_quality_trend_stops_the_loop():
    # The trend check reads the three scores recorded before the current one, so it fires on the fourth pass.
    scores = iter([0.8, 0.7, 0.6, 0.5, 0.4, 0.3])
    system = make_system()

    async def fake_evaluate(iteration):
        iteration.quality_score = next(scores)
        iteration.insights = []

    system._evaluate_iteration = fake_evaluate
    system.config.max_iterations = 10
    system.config.convergence_threshold = 0.99
    iterations = run(system.execute_oram_loop("task"))
    assert len(iterations) == 4 and system.convergence_metrics == [0.8, 0.7, 0.6, 0.5]


# --- scoring -------------------------------------------------------------------------------------

def test_an_agent_error_lowers_the_quality_score():
    clean, _ = run(good_system().execute_oram_iteration("task"))
    failed, _ = run(good_system(observer=StubObserver(error="provider down", fallback=True)).execute_oram_iteration("task"))
    assert clean.quality_score == pytest.approx(0.95)
    assert failed.quality_score < clean.quality_score
    assert failed.quality_score == pytest.approx((0.3 + 0.9 + 0.9 + 1.0) / 4)


def test_an_error_nested_under_data_also_counts():
    failed, _ = run(good_system(observer=StubObserver(data={"error": "x"})).execute_oram_iteration("task"))
    assert failed.quality_score < 0.95


def test_a_crashing_agent_is_recorded_as_a_fallback_not_a_crash():
    class Boom:
        async def observe(self, task):
            raise RuntimeError("boom")

    iteration, _ = run(good_system(observer=Boom()).execute_oram_iteration("task"))
    assert iteration.observation["fallback"] is True and "boom" in iteration.observation["error"]
    assert iteration.quality_score < 0.95


# --- memory and insights -------------------------------------------------------------------------

def test_every_iteration_is_stored_in_memory_and_summarised():
    system = good_system()
    config_limit = 2
    system.config.max_iterations = config_limit
    system.config.convergence_threshold = 0.99
    run(system.execute_oram_loop("task"))
    kinds = [e["type"] for e in system.memory.events]
    assert kinds.count("oram_iteration") == config_limit and kinds[-1] == "oram_summary"
    assert system.get_status()["memory_buffer_size"] == config_limit


def test_memory_buffer_is_capped():
    system = make_system()
    system.config.memory_retention_limit = 3
    system.config.max_iterations = 8
    run(system.execute_oram_loop("task"))
    assert len(system.memory_buffer) == 3
    assert [e["iteration_id"] for e in system.memory_buffer] == [6, 7, 8]


def test_insights_are_collected_and_limited_to_three_per_iteration():
    system = good_system()
    system.config.max_iterations = 4
    system.config.convergence_threshold = 0.99
    iterations = run(system.execute_oram_loop("task"))
    assert all(len(i.insights) <= 3 for i in iterations)
    assert system.get_insights() == [x for i in iterations for x in i.insights]
    assert any(x.startswith("Reasoning:") for x in system.get_insights())


def test_clear_history_resets_state():
    system = good_system()
    run(system.execute_oram_loop("task"))
    system.clear_history()
    assert system.get_status()["iterations_executed"] == 0 and system.get_insights() == []
    assert system.get_convergence_metrics() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,expected", [(ORAMIterationType.PROBLEM_SOLVING, 8), (ORAMIterationType.DEEP_ANALYSIS, 7),
                                           (ORAMIterationType.BASIC, 5)])
async def test_execute_oram_without_a_limit_uses_the_iteration_types_own_count(monkeypatch, kind, expected):
    seen = {}

    async def fake_loop(self, task, iteration_type, context=None):
        self.config.set_iteration_type(iteration_type)
        seen["limit"] = self.config.max_iterations
        return []

    monkeypatch.setattr(ORAMSystem, "execute_oram_loop", fake_loop)
    await execute_oram("task", kind)
    assert seen["limit"] == expected
    await execute_oram("task", kind, max_iterations=3)
    assert seen["limit"] == 3
