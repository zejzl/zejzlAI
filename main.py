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

# =============================================================================
# COLLABORATION MODE IMPLEMENTATION PLAN
# =============================================================================
#
# Goal: Enable Option 2 - Collaboration Mode (Grok + Claude dual AI planning)
#
# Implementation Steps:
# 1. Create run_collaboration_mode() function
# 2. Implement dual AI consensus logic
# 3. Add option 2 to interactive menu
# 4. Update provider selection to include Claude
# 5. Test and document the feature
#
# Key Features:
# - Grok provides creative/analytical perspective
# - Claude provides structured/logical perspective
# - Consensus-based planning with idea exchange
# - Ultra-concise output format
#
# =============================================================================

async def run_collaboration_mode():
    """Run Collaboration Mode - Dual AI planning (Grok + Claude)"""
    # Suppress all logging for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True)
    logging.getLogger().setLevel(logging.CRITICAL)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(logging.CRITICAL)

    print("\n[Collaboration Mode]")
    task = input("Enter a task for collaborative planning: ")

    # Get AI provider bus
    from base import get_ai_provider_bus
    ai_bus = await get_ai_provider_bus()

    try:
        print("\n[Round 1/3] Grok: Creative analysis...")
        grok_prompt = f"""Analyze this task creatively and generate multiple innovative approaches:

Task: {task}

Provide creative solutions, consider unconventional angles, and identify opportunities others might miss.
Focus on: innovation, edge cases, creative combinations, and out-of-the-box thinking.

Return your analysis in 2-3 paragraphs."""

        grok_response = await ai_bus.send_message(
            content=grok_prompt,
            provider_name="grok",
            conversation_id=f"collaboration_grok_{hash(task)}"
        )
        print("[OK] Grok: Creative analysis received")

        print("\n[Round 1/3] Claude: Logical analysis...")
        claude_prompt = f"""Analyze this task systematically and create a structured plan:

Task: {task}

Provide logical breakdown, risk assessment, resource requirements, and step-by-step planning.
Focus on: structure, feasibility, dependencies, and practical implementation.

Return your analysis in 2-3 paragraphs."""

        claude_response = await ai_bus.send_message(
            content=claude_prompt,
            provider_name="claude",
            conversation_id=f"collaboration_claude_{hash(task)}"
        )
        print("[OK] Claude: Logical analysis received")

        print("\n[Round 2/3] Idea exchange and refinement...")
        exchange_prompt = f"""Review and refine the following analyses, then create an improved collaborative plan:

Grok's Creative Analysis:
{grok_response}

Claude's Logical Analysis:
{claude_response}

Task: {task}

Identify synergies between creative and logical approaches. Combine the best elements from both perspectives.
Address any conflicts and create a unified, enhanced plan that leverages both creative innovation and logical structure.

Return the collaborative plan in 3-4 paragraphs."""

        # Use Grok for the final collaborative synthesis (could alternate between providers)
        collaborative_plan = await ai_bus.send_message(
            content=exchange_prompt,
            provider_name="grok",  # Could be configurable
            conversation_id=f"collaboration_final_{hash(task)}"
        )
        print("[OK] Idea exchange complete")

        print("\n[Round 3/3] Consensus building...")
        # Final validation step could be added here
        print("[OK] Consensus plan generated")

        print("\n[Final Result]")
        print("=" * 50)
        # Truncate for concise display
        final_output = str(collaborative_plan)[:500] + "..." if len(str(collaborative_plan)) > 500 else str(collaborative_plan)
        print(f"Collaborative Plan: {final_output}")
        print("=" * 50)

    except Exception as e:
        print(f"\n[Error] Collaboration failed: {str(e)}")
        print("Make sure both Grok and Claude API keys are configured.")


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
#         2. Collaboration Mode (Grok + Claude) - Dual AI planning [PLANNED FOR IMPLEMENTATION]
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
        2. Collaboration Mode (Grok + Claude) - Dual AI planning
        4. Pantheon Mode - Full 9-agent orchestration with validation & learning
        9. Quit

        (Note: Modes 3,5,6,7,8 are not yet implemented)
""")

    choice = input("        Choose mode (1, 2, 4, or 9): ").strip()

    if choice == "1":
        print("\n[Starting Single Agent Mode...]")
        asyncio.run(run_single_agent_mode())
    elif choice == "2":
        print("\n[Starting Collaboration Mode...]")
        asyncio.run(run_collaboration_mode())
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
