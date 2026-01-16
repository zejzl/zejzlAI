import asyncio
from src.agents.observer import ObserverAgent
from src.agents.reasoner import ReasonerAgent
from src.agents.actor import ActorAgent

async def run_single_agent_demo():
    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    task = input("Enter a task for the Single Agent loop: ")

    # Observer
    observation = await observer.observe(task)

    # Reasoner
    plan = await reasoner.reason(observation)

    # Actor
    execution = await actor.act(plan)

    print(f"\n[Execution Output]: {execution}\n")
