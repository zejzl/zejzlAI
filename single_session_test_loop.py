import asyncio
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent
from src.agents.validator import ValidatorAgent
from src.agents.memory import MemoryAgent

async def run_single_agent_with_validation():
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    memory = MemoryAgent()

    task = input("Enter a task for the Single Agent loop: ")

    # Observer
    observation = await observer.observe(task)
    await memory.store({"type": "observation", "data": observation})

    # Reasoner
    plan = await reasoner.reason(observation)
    await memory.store({"type": "plan", "data": plan})

    # Actor
    execution = await actor.act(plan)
    await memory.store({"type": "execution", "data": execution})

    # Validator
    validation = await validator.validate(execution)
    await memory.store({"type": "validation", "data": validation})

    # Print final validation result
    print(f"\n[Validation Output]: {validation}\n")
