import asyncio
import sys


async def run_single_agent_mode():
    """Run Single Agent mode - Observe-Reason-Act loop"""
    from src.agents.observer import ObserverAgent
    from src.agents.reasoner import ReasonerAgent
    from src.agents.actor import ActorAgent

    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    task = input("\nEnter a task for the Single Agent: ")

    print("\n[Observer] Processing task...")
    observation = await observer.observe(task)
    print(f"Observation: {observation}")

    print("\n[Reasoner] Creating plan...")
    plan = await reasoner.reason(observation)
    print(f"Plan: {plan}")

    print("\n[Actor] Executing plan...")
    execution = await actor.act(plan)
    print(f"Execution: {execution}\n")


async def run_pantheon_mode():
    """Run full 9-agent Pantheon orchestration"""
    from src.agents.observer import ObserverAgent
    from src.agents.reasoner import ReasonerAgent
    from src.agents.actor import ActorAgent
    from src.agents.validator import ValidatorAgent
    from src.agents.memory import MemoryAgent
    from src.agents.executor import ExecutorAgent
    from src.agents.analyzer import AnalyzerAgent
    from src.agents.learner import LearnerAgent
    from src.agents.improver import ImproverAgent

    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()
    validator = ValidatorAgent()
    memory = MemoryAgent()
    executor = ExecutorAgent()
    analyzer = AnalyzerAgent()
    learner = LearnerAgent()
    improver = ImproverAgent()

    task = input("\nEnter a task for the Pantheon: ")

    print("\n[1/9 Observer] Gathering observations...")
    observation = await observer.observe(task)
    await memory.store({"type": "observation", "data": observation})
    print(f"Observation: {observation}")

    print("\n[2/9 Reasoner] Creating execution plan...")
    plan = await reasoner.reason(observation)
    await memory.store({"type": "plan", "data": plan})
    print(f"Plan: {plan}")

    print("\n[3/9 Actor] Executing planned actions...")
    execution = await actor.act(plan)
    await memory.store({"type": "execution", "data": execution})
    print(f"Execution: {execution}")

    print("\n[4/9 Validator] Validating execution...")
    validation = await validator.validate(execution)
    await memory.store({"type": "validation", "data": validation})
    print(f"Validation: {validation}")

    print("\n[5/9 Executor] Performing validated tasks...")
    execution_result = await executor.execute(validation)
    await memory.store({"type": "executor", "data": execution_result})
    print(f"Executor Result: {execution_result}")

    print("\n[6/9 Memory] Recalling stored events...")
    events = await memory.recall()
    print(f"Memory Events: {len(events)} events stored")

    print("\n[7/9 Analyzer] Analyzing metrics...")
    analysis = await analyzer.analyze(events)
    print(f"Analysis: {analysis}")

    print("\n[8/9 Learner] Learning patterns...")
    learned = await learner.learn(events)
    print(f"Learned: {learned}")

    print("\n[9/9 Improver] Generating improvements...")
    improvement = await improver.improve(analysis, learned)
    print(f"Improvement: {improvement}\n")

    print("\n✓ Pantheon orchestration complete!")


def run_interactive_menu(debug: bool = True, max_iterations: int = 10, max_rounds: int = 5, skip_boot: bool = False):
    """
    Run interactive menu mode - user selects agent mode.
    """
    print("""
===================================================================

     ZEJZL.NET - AI FRAMEWORK CLI
     PANTHEON 9-AGENT SYSTEM

===================================================================

        [INTERACTIVE MODE] Welcome to zejzl.net - Choose your agent mode!

        1. Single Agent - Observe-Reason-Act loop
        4. Pantheon Mode - Full 9-agent orchestration with validation & learning
        9. Quit

        (Note: Modes 2,3,5,6,7,8 are not yet implemented)
""")

    choice = input("        Choose mode (1, 4, or 9): ").strip()

    if choice == "1":
        print("\n[Starting Single Agent Mode...]")
        asyncio.run(run_single_agent_mode())
    elif choice == "4":
        print("\n[Starting Pantheon Mode...]")
        asyncio.run(run_pantheon_mode())
    elif choice == "9":
        print("\n        Goodbye! :)\n")
        sys.exit(0)
    else:
        print(f"\n        Mode {choice} is not yet implemented. Please choose 1, 4, or 9.\n")

    return choice


if __name__ == "__main__":
    try:
        while True:
            choice = run_interactive_menu()
            if choice == "9":
                break

            # Ask if user wants to continue
            again = input("\n        Run another task? (y/n): ").strip().lower()
            if again != 'y':
                print("\n        Goodbye! :)\n")
                break
    except KeyboardInterrupt:
        print("\n\n        Interrupted. Goodbye! :)\n")
        sys.exit(0)
