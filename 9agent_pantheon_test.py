import asyncio
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent
from src.agents.validator import ValidatorAgent
from src.agents.memory import MemoryAgent
from src.agents.executor import ExecutorAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.learner import LearnerAgent
from src.agents.improver import ImproverAgent

async def run_pantheon_demo(task: str):
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    memory = MemoryAgent()
    executor = ExecutorAgent()
    analyzer = AnalyzerAgent()
    learner = LearnerAgent()
    improver = ImproverAgent()

    # Step 1: Observe
    observation = await observer.observe(task)
    await memory.store({"type": "observation", "data": observation})

    # Step 2: Reason
    plan = await reasoner.reason(observation)
    await memory.store({"type": "plan", "data": plan})

    # Step 3: Act
    execution = await actor.act(plan)
    await memory.store({"type": "execution", "data": execution})

    # Step 4: Validate
    validation = await validator.validate(execution)
    await memory.store({"type": "validation", "data": validation})

    # Step 5: Execute
    execution_result = await executor.execute(validation)
    await memory.store({"type": "executor", "data": execution_result})

    # Step 6: Analyze
    events = await memory.recall()
    analysis = await analyzer.analyze(events)

    # Step 7: Learn
    learned = await learner.learn(events)

    # Step 8: Improve
    improvement = await improver.improve(analysis, learned)

    print("\n[Pantheon Demo Complete]")
    print("Observation:", observation)
    print("Plan:", plan)
    print("Execution:", execution)
    print("Validation:", validation)
    print("Executor Result:", execution_result)
    print("Analysis:", analysis)
    print("Learned Patterns:", learned)
    print("Improvement Suggestions:", improvement)
