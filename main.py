import asyncio
import sys
import logging

def select_provider():
    """Allow user to select an AI provider"""
    print("\nAvailable AI Providers:")
    print("1. grok (default)")
    print("2. chatgpt")
    print("3. claude")
    print("4. gemini")
    print("5. deepseek")
    print("6. qwen")
    print("7. zai")

    choice = input("\nSelect provider (1-7, or press Enter for grok): ").strip()

    provider_map = {
        "1": "grok",
        "2": "chatgpt",
        "3": "claude",
        "4": "gemini",
        "5": "deepseek",
        "6": "qwen",
        "7": "zai"
    }

    return provider_map.get(choice, "grok")

async def run_single_agent_mode():
    """Run Single Agent mode - Observe-Reason-Act loop"""
    # Suppress all logging for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True)
    logging.getLogger().setLevel(logging.CRITICAL)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.CRITICAL)

    from src.agents.observer import ObserverAgent
    from src.agents.reasoner import ReasonerAgent
    from src.agents.actor import ActorAgent

    provider = select_provider()

    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    task = input("\nEnter a task for the Single Agent: ")

    print("\n[Observer] Processing task...")
    observation = await observer.observe(task, provider)
    print(f"[OK] Observation received")

    print("\n[Reasoner] Creating plan...")
    plan = await reasoner.reason(observation, provider)
    print(f"[OK] Plan created")

    print("\n[Actor] Executing plan...")
    execution = await actor.act(plan, provider)
    print(f"[OK] Actions executed\n")


async def run_pantheon_mode():
    """Run full 9-agent Pantheon orchestration"""
    # Suppress all logging for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True)
    logging.getLogger().setLevel(logging.CRITICAL)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.CRITICAL)

    from src.agents.observer import ObserverAgent
    from src.agents.reasoner import ReasonerAgent
    from src.agents.actor import ActorAgent
    from src.agents.validator import ValidatorAgent
    from src.agents.memory import MemoryAgent
    from src.agents.executor import ExecutorAgent
    from src.agents.analyzer import AnalyzerAgent
    from src.agents.learner import LearnerAgent
    from src.agents.improver import ImproverAgent

    provider = select_provider()

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
    observation = await observer.observe(task, provider)
    await memory.store({"type": "observation", "data": observation})
    print(f"[OK] Observation received")

    print("\n[2/9 Reasoner] Creating execution plan...")
    plan = await reasoner.reason(observation, provider)
    await memory.store({"type": "plan", "data": plan})
    print(f"[OK] Plan created")

    print("\n[3/9 Actor] Executing planned actions...")
    execution = await actor.act(plan, provider)
    await memory.store({"type": "execution", "data": execution})
    print(f"[OK] Actions executed")

    print("\n[4/9 Validator] Validating execution...")
    validation = await validator.validate(execution, provider)
    await memory.store({"type": "validation", "data": validation})
    print(f"[OK] Validation complete")

    print("\n[5/9 Executor] Performing validated tasks...")
    execution_result = await executor.execute(validation, provider)
    await memory.store({"type": "executor", "data": execution_result})
    print(f"[OK] Tasks executed")

    print("\n[6/9 Memory] Recalling stored events...")
    events = await memory.recall()
    print(f"[OK] {len(events)} events stored")

    print("\n[7/9 Analyzer] Analyzing metrics...")
    analysis = await analyzer.analyze(events, provider)
    print(f"[OK] Analysis complete")

    print("\n[8/9 Learner] Learning patterns...")
    learned = await learner.learn(events, provider=provider)
    print(f"[OK] Learning complete")

    print("\n[9/9 Improver] Generating improvements...")
    improvement = await improver.improve(analysis, learned, provider)
    print(f"[OK] Improvements generated\n")

    print("\n[OK] Pantheon orchestration complete!")


# Future Menu Options (for reference):
#         1. Single Agent - Observe-Reason-Act loop
#         2. Collaboration Mode (Grok + Claude) - Dual AI planning
#         3. Swarm Mode (Multi-agent) - Async team coordination
#         4. Pantheon Mode (9-agent) - Full AI orchestration with validation & learning
#         5. Learning Loop - Continuous optimization cycle
#         6. Offline Mode - Cached/local fallback (no API, uses vault/KB)
#         7. Community Vault Sync - Pull/push evolutions and tools
#         8. Save Game - Invoke progress save script
#         9. Quit

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
        input("        Press Enter to exit...")
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
                input("        Press Enter to exit...")
                break
    except KeyboardInterrupt:
        print("\n\n        Interrupted. Goodbye! :)\n")
        input("        Press Enter to exit...")
        sys.exit(0)
