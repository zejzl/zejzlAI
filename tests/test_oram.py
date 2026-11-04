"""ORAM mode (src/oram.py) with stub agents: no network, no providers.

Three behaviours here were bugs found while writing these tests, and are fixed in the same PR:
- max_iterations=N ran N+1 iterations,
- a user-chosen max_iterations was overwritten by the iteration type's default,
- an agent reporting a top-level "error" still scored as a clean iteration.
"""

import asyncio

import pytest

from src.oram import FALLBACK_PROVENANCE, action_quality, phase_provenance, quality_factors, reasoning_quality, ORAMConfig, ORAMIterationType, ORAMSystem, execute_oram


class StubObserver:
    def __init__(self, **extra):
        self.extra = extra

    async def observe(self, task):
        return {"task": task, **self.extra}


class StubReasoner:
    def __init__(self, analysis=None, **fields):
        self.analysis = analysis
        self.fields = fields

    async def reason(self, observation):
        plan = dict(self.fields)
        if self.analysis:
            plan["analysis"] = self.analysis
        return plan


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


GOOD_PLAN = {"subtasks": [{"description": "read the file"}, {"description": "write the summary"}]}
GOOD_RESULTS = [{"expected_outcome": "a three-bullet summary of the file, each bullet one concrete fact",
                 "execution_plan": ["read the file", "write the summary"]}]


def good_system(**kw):
    """Every phase succeeds with substance: quality 1.0, which clears every convergence threshold."""
    return make_system(reasoner=StubReasoner("a" * 300, **GOOD_PLAN), actor=StubActor(GOOD_RESULTS), **kw)


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
    assert iterations[0].quality_score == pytest.approx(1.0)
    assert iterations[0].quality_factors == {"provenance": 1.0, "reasoning": 1.0, "action": 1.0, "total": 1.0}
    assert system.get_status()["iterations_executed"] == 1


@pytest.mark.parametrize("limit", [1, 2, 3, 6])
def test_loop_runs_exactly_max_iterations_when_it_never_converges(limit):
    config = ORAMConfig()
    config.max_iterations = limit
    system = make_system(config=config)                                 # empty reasoning/action: quality 0.133 < 0.85
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
    assert clean.quality_score == pytest.approx(1.0)
    assert failed.quality_score < clean.quality_score
    assert failed.quality_factors["provenance"] == pytest.approx(2 / 3, abs=1e-4)   # observer 0.0, the other two 1.0
    assert failed.quality_score == pytest.approx(0.4 * 2 / 3 + 0.3 + 0.3, abs=1e-3)


def test_an_error_nested_under_data_also_counts():
    failed, _ = run(good_system(observer=StubObserver(data={"error": "x"})).execute_oram_iteration("task"))
    assert failed.quality_score < 1.0


def test_a_crashing_agent_is_recorded_as_a_fallback_not_a_crash():
    class Boom:
        async def observe(self, task):
            raise RuntimeError("boom")

    iteration, _ = run(good_system(observer=Boom()).execute_oram_iteration("task"))
    assert iteration.observation["fallback"] is True and "boom" in iteration.observation["error"]
    assert iteration.quality_score < 1.0


# --- memory and insights -------------------------------------------------------------------------

def test_every_iteration_is_stored_in_memory_and_summarised():
    system = good_system()
    config_limit = 2
    system.config.max_iterations = config_limit
    system.config.convergence_threshold = 1.01  # unreachable, so the cap decides
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


def test_action_insight_surfaces_the_expected_outcome_not_just_a_count():
    """A later run reads these back (format_prior_runs); a bare item count
    tells it nothing about what was decided. The real Actor shape is a list
    of dicts with expected_outcome/execution_plan, not bare strings."""
    actor = StubActor([{
        "expected_outcome": "A working login form that redirects to /dashboard on success.",
        "execution_plan": ["Read the existing form component", "Add the redirect"],
    }])
    system = make_system(reasoner=StubReasoner("a" * 80), actor=actor)
    iteration, _ = run(system.execute_oram_iteration("task"))
    action_insights = [x for x in iteration.insights if x.startswith("Action:")]
    assert action_insights
    assert "working login form" in action_insights[0]
    assert "1 item(s)" in action_insights[0]


def test_action_insight_falls_back_to_the_first_step_without_an_outcome():
    actor = StubActor([{
        "expected_outcome": "Outcome not specified",
        "execution_plan": ["Inspect the failing test first"],
    }])
    system = make_system(reasoner=StubReasoner("a" * 80), actor=actor)
    iteration, _ = run(system.execute_oram_iteration("task"))
    action_insights = [x for x in iteration.insights if x.startswith("Action:")]
    assert action_insights
    assert "Inspect the failing test first" in action_insights[0]


def test_action_insight_falls_back_to_a_count_with_nothing_substantive():
    actor = StubActor([{"expected_outcome": "", "execution_plan": []}])
    system = make_system(reasoner=StubReasoner("a" * 80), actor=actor)
    iteration, _ = run(system.execute_oram_iteration("task"))
    assert "Action: Generated 1 execution items" in iteration.insights


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


# --- scoring: the factors ------------------------------------------------------------------------

def test_a_rule_based_fallback_scores_below_a_model_answer_and_above_a_failure():
    model = {"analysis": "x" * 300, "subtasks": [{"description": "a"}, {"description": "b"}], "ai_generated": True}
    fallback = {**model, "ai_generated": False, "fallback_reason": "no key"}
    unparsed = {**model, "raw_response": "```json ..."}
    failed = {**model, "error": "provider down"}
    assert phase_provenance(model) == 1.0
    assert phase_provenance(fallback) == phase_provenance(unparsed) == FALLBACK_PROVENANCE
    assert phase_provenance(failed) == 0.0 and phase_provenance({}) == 0.0 and phase_provenance("text") == 0.0


def test_placeholders_and_thin_content_score_low():
    assert reasoning_quality({"analysis": "AI response parsing failed", "subtasks": []}) == 0.0
    assert reasoning_quality({"analysis": "Analysis not provided"}) == 0.0
    assert reasoning_quality({"analysis": "a" * 150}) == pytest.approx(0.35)              # half length, no subtasks
    assert reasoning_quality({"analysis": "a" * 300, "subtasks": [{"description": "one"}]}) == pytest.approx(0.85)
    assert reasoning_quality({"analysis": {"task_type": "x"}}) == 0.0                     # the fallback's dict analysis
    assert action_quality({"results": []}) == 0.0 and action_quality({}) == 0.0
    assert action_quality({"results": [{"expected_outcome": "Outcome not specified", "execution_plan": []}]}) == 0.0
    assert action_quality({"results": [{"expected_outcome": "AI response parsing failed", "execution_plan": ["x"],
                                        "raw_response": "..."}]}) == 0.0
    assert action_quality({"results": [{"expected_outcome": "o" * 60, "execution_plan": ["read", "write"]}]}) == 1.0
    assert action_quality({"results": [{"expected_outcome": "o" * 30, "execution_plan": ["read"]}]}) == pytest.approx(0.5)
    assert action_quality({"results": ["step"]}) == pytest.approx(0.5 * 4 / 60)            # a bare step string


def test_the_total_is_the_weighted_sum_and_lands_on_the_iteration_and_in_the_stored_run(tmp_path, monkeypatch):
    factors = quality_factors({"task": "t"}, {"analysis": "a" * 150}, {"results": [{"expected_outcome": "o" * 60,
                                                                                    "execution_plan": ["read", "write"]}]})
    assert factors == {"provenance": 1.0, "reasoning": 0.35, "action": 1.0, "total": pytest.approx(0.4 + 0.105 + 0.3)}
    iteration, _ = run(good_system().execute_oram_iteration("task"))
    assert iteration.quality_factors["total"] == iteration.quality_score == 1.0


def test_a_mediocre_run_keeps_iterating_up_to_the_cap():
    thin = make_system(reasoner=StubReasoner("a" * 100, subtasks=[{"description": "one"}]),
                       actor=StubActor([{"expected_outcome": "done", "execution_plan": ["x"]}]))
    thin.config.max_iterations = 3
    iterations = run(thin.execute_oram_loop("task", ORAMIterationType.BASIC))
    assert len(iterations) == 3 and all(0.4 < i.quality_score < 0.85 for i in iterations)
