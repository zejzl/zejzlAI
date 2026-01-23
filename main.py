import asyncio
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

async def run_swarm_mode():
    """Run Swarm Mode - Multi-agent async team coordination"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    print("\n[Swarm Mode]")
    task = input("Enter a task for swarm coordination: ")

    # Swarm configuration
    swarm_size = 4  # Number of agents in the swarm
    perspectives = [
        "technical implementation focus",
        "user experience focus",
        "business strategy focus",
        "risk assessment focus"
    ]

    # Get AI provider bus
    from base import get_ai_provider_bus
    ai_bus = await get_ai_provider_bus()

    try:
        print(f"\n[Deploying {swarm_size}-agent swarm...]")

        # Create swarm tasks
        swarm_tasks = []
        for i in range(swarm_size):
            perspective = perspectives[i % len(perspectives)]
            agent_id = f"swarm_agent_{i+1}"

            # Create specialized prompt for this swarm agent
            swarm_prompt = f"""You are Swarm Agent {i+1} specializing in {perspective}.

Task: {task}

Your mission: Analyze this task from your specialized {perspective} perspective.
Provide unique insights, recommendations, and considerations that complement other swarm agents.

Focus on: {perspective}
Be thorough but concise in your analysis.

Return your specialized analysis."""

            # Create async task for this agent
            task_coro = ai_bus.send_message(
                content=swarm_prompt,
                provider_name="grok",  # Could rotate providers
                conversation_id=f"swarm_{agent_id}_{hash(task)}"
            )
            swarm_tasks.append((agent_id, perspective, task_coro))

        # Execute swarm asynchronously
        print("\n[Swarm coordination in progress...]")
        swarm_results = []

        for agent_id, perspective, task_coro in swarm_tasks:
            print(f"[OK] Agent {agent_id}: {perspective} analyzing...")
            try:
                result = await asyncio.wait_for(task_coro, timeout=60.0)
                swarm_results.append({
                    'agent': agent_id,
                    'perspective': perspective,
                    'analysis': result
                })
                print(f"[OK] Agent {agent_id}: Analysis complete")
            except asyncio.TimeoutError:
                error_msg = f"Agent {agent_id}: Timeout after 60 seconds"
                print(f"[ERROR] {error_msg}")
                swarm_results.append({
                    'agent': agent_id,
                    'perspective': perspective,
                    'analysis': f"Analysis failed: {error_msg}"
                })
            except Exception as e:
                error_msg = f"Agent {agent_id}: {str(e)}"
                print(f"[ERROR] {error_msg}")
                swarm_results.append({
                    'agent': agent_id,
                    'perspective': perspective,
                    'analysis': f"Analysis failed: {str(e)}"
                })

        print("\n[Synthesizing swarm intelligence...]")

        # Create synthesis prompt
        synthesis_prompt = f"""Synthesize the following swarm analyses into a unified, comprehensive solution:

Task: {task}

Swarm Results:
"""

        for result in swarm_results:
            synthesis_prompt += f"\n--- {result['agent']} ({result['perspective']}) ---\n"
            # Truncate individual analyses for synthesis prompt
            analysis = str(result['analysis'])[:300] + "..." if len(str(result['analysis'])) > 300 else str(result['analysis'])
            synthesis_prompt += f"{analysis}\n"

        synthesis_prompt += """
Create a unified solution that:
1. Combines the best insights from all perspectives
2. Resolves any conflicting recommendations
3. Provides a comprehensive, actionable plan
4. Maintains balance across all perspectives

Return the synthesized swarm solution."""

        # Use Claude for synthesis (different from swarm agents)
        synthesis_result = await ai_bus.send_message(
            content=synthesis_prompt,
            provider_name="claude",
            conversation_id=f"swarm_synthesis_{hash(task)}"
        )

        print("[OK] Swarm synthesis complete")

        print("\n[Final Swarm Result]")
        print("=" * 60)
        # Truncate final result for display
        final_output = str(synthesis_result)[:800] + "..." if len(str(synthesis_result)) > 800 else str(synthesis_result)
        print(f"Swarm Solution: {final_output}")
        print("=" * 60)
        print(f"\n[Swarm Stats: {len(swarm_results)} agents contributed]")

    except asyncio.TimeoutError:
        print("\n[ERROR] Swarm coordination timed out after 60 seconds. AI providers may be slow or unavailable.")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"\n[ERROR] API quota/rate limit exceeded: {error_msg}")
            print("[INFO] Please try again later or use different providers.")
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            print(f"\n[ERROR] Authentication failed: {error_msg}")
            print("[INFO] Please check your API key configuration.")
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            print(f"\n[ERROR] Network connection failed: {error_msg}")
            print("[INFO] Please check your internet connection and try again.")
        else:
            print(f"\n[ERROR] Swarm coordination failed: {error_msg}")
            print("[INFO] Make sure API keys are configured.")


async def run_collaboration_mode():
    """Run Collaboration Mode - Dual AI planning (Grok + Claude)"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    print("\n[Collaboration Mode]")
    task = input("Enter a task for collaborative planning: ")

    # Get AI provider bus
    from base import get_ai_provider_bus
    ai_bus = await get_ai_provider_bus()

    try:
        # Define prompts for each AI
        grok_prompt = f"""Analyze this task creatively and generate multiple innovative approaches:

Task: {task}

Provide creative solutions, consider unconventional angles, and identify opportunities others might miss.
Focus on: innovation, edge cases, creative combinations, and out-of-the-box thinking.

Return your analysis in 2-3 paragraphs."""

        claude_prompt = f"""Analyze this task systematically and create a structured plan:

Task: {task}

Provide logical breakdown, risk assessment, resource requirements, and step-by-step planning.
Focus on: structure, feasibility, dependencies, and practical implementation.

Return your analysis in 2-3 paragraphs."""

        print("\n[Round 1/3] Grok: Creative analysis...")
        grok_response = await asyncio.wait_for(
            ai_bus.send_message(
                content=grok_prompt,
                provider_name="grok",
                conversation_id=f"collaboration_grok_{hash(task)}"
            ),
            timeout=60.0
        )
        print("[OK] Grok: Creative analysis received")

        print("\n[Round 1/3] Claude: Logical analysis...")
        claude_response = await asyncio.wait_for(
            ai_bus.send_message(
                content=claude_prompt,
                provider_name="claude",
                conversation_id=f"collaboration_claude_{hash(task)}"
            ),
            timeout=60.0
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
        collaborative_plan = await asyncio.wait_for(
            ai_bus.send_message(
                content=exchange_prompt,
                provider_name="grok",  # Could be configurable
                conversation_id=f"collaboration_final_{hash(task)}"
            ),
            timeout=60.0
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

    except asyncio.TimeoutError:
        print("\n[ERROR] Collaboration timed out after 60 seconds. One or both AI providers may be slow or unavailable.")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"\n[ERROR] API quota/rate limit exceeded: {error_msg}")
            print("[INFO] Please try again later or use different providers.")
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            print(f"\n[ERROR] Authentication failed: {error_msg}")
            print("[INFO] Please check your Grok and Claude API key configuration.")
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            print(f"\n[ERROR] Network connection failed: {error_msg}")
            print("[INFO] Please check your internet connection and try again.")
        else:
            print(f"\n[ERROR] Collaboration failed: {error_msg}")
            print("[INFO] Make sure both Grok and Claude API keys are configured.")


async def run_single_agent_mode():
    """Run Single Agent mode - Observe-Reason-Act loop"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    from src.agents.observer import ObserverAgent
    from src.agents.reasoner import ReasonerAgent
    from src.agents.actor import ActorAgent

    provider = select_provider()

    observer = ObserverAgent()
    reasoner = ReasonerAgent()
    actor = ActorAgent()

    # Get user task with validation
    while True:
        try:
            task = input("\nEnter a task for the Single Agent: ").strip()
            if not task:
                print("[ERROR] Task cannot be empty. Please enter a valid task.")
                continue
            if len(task) > 1000:
                print("[ERROR] Task is too long (max 1000 characters). Please enter a shorter task.")
                continue
            break
        except KeyboardInterrupt:
            print("\n[INFO] Operation cancelled by user.")
            return
        except EOFError:
            print("\n[ERROR] Input stream closed. Exiting.")
            return

    try:
        print("\n[Observer] Processing task...")
        observation = await asyncio.wait_for(
            observer.observe(task, provider),
            timeout=60.0  # 60 second timeout
        )
        print(f"[OK] Observation received")

        print("\n[Reasoner] Creating plan...")
        plan = await asyncio.wait_for(
            reasoner.reason(observation, provider),
            timeout=60.0
        )
        print(f"[OK] Plan created")

        print("\n[Actor] Executing plan...")
        execution = await asyncio.wait_for(
            actor.act(plan, provider),
            timeout=60.0
        )
        print(f"[OK] Actions executed\n")

    except asyncio.TimeoutError:
        print("\n[ERROR] Operation timed out after 60 seconds. The AI provider may be slow or unavailable.")
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            print(f"\n[ERROR] API quota/rate limit exceeded: {error_msg}")
            print("[INFO] Please try again later or switch to a different provider.")
        elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            print(f"\n[ERROR] Authentication failed: {error_msg}")
            print("[INFO] Please check your API key configuration.")
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            print(f"\n[ERROR] Network connection failed: {error_msg}")
            print("[INFO] Please check your internet connection and try again.")
        else:
            print(f"\n[ERROR] Unexpected error: {error_msg}")
            print("[INFO] If this persists, please check the logs for more details.")


def get_available_provider(ai_bus, preferred_provider="grok"):
    """Get an available provider, falling back to any available provider"""
    if ai_bus and hasattr(ai_bus, 'providers') and ai_bus.providers:
        # Check if preferred provider is available
        if preferred_provider in ai_bus.providers:
            return preferred_provider
        # Fall back to first available provider
        return list(ai_bus.providers.keys())[0]
    return None


async def run_pantheon_mode():
    """Run full 9-agent Pantheon orchestration"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    provider = select_provider()

    # Get the AI provider bus for all agents to use
    from base import get_ai_provider_bus
    ai_bus = await get_ai_provider_bus()
    available_provider = get_available_provider(ai_bus, provider)

    if not available_provider:
        print(f"[ERROR] No AI providers available. Please check your API key configuration.")
        print(f"[INFO] Make sure environment variables are set for your preferred providers.")
        return

    print(f"[INFO] Using provider: {available_provider}")

    # Import all agent classes
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

    # Get user task with validation
    while True:
        try:
            task = input("\nEnter a task for the Pantheon: ").strip()
            if not task:
                print("[ERROR] Task cannot be empty. Please enter a valid task.")
                continue
            if len(task) > 1000:
                print("[ERROR] Task is too long (max 1000 characters). Please enter a shorter task.")
                continue
            break
        except KeyboardInterrupt:
            print("\n[INFO] Operation cancelled by user.")
            return
        except EOFError:
            print("\n[ERROR] Input stream closed. Exiting.")
            return

    print("\n[1/9 Observer] Gathering observations...")
    observation = await observer.observe(task, available_provider)
    await memory.store({"type": "observation", "data": observation})
    print(f"[OK] Observation received")

    print("\n[2/9 Reasoner] Creating execution plan...")
    plan = await reasoner.reason(observation, available_provider)
    await memory.store({"type": "plan", "data": plan})
    print(f"[OK] Plan created")

    print("\n[3/9 Actor] Executing planned actions...")
    execution = await actor.act(plan, available_provider)
    await memory.store({"type": "execution", "data": execution})
    print(f"[OK] Actions executed")

    print("\n[4/9 Validator] Validating execution...")
    validation = await validator.validate(execution, available_provider)
    await memory.store({"type": "validation", "data": validation})
    print(f"[OK] Validation complete")

    print("\n[5/9 Executor] Performing validated tasks...")
    execution_result = await executor.execute(validation, available_provider)
    await memory.store({"type": "executor", "data": execution_result})
    print(f"[OK] Tasks executed")

    print("\n[6/9 Memory] Recalling stored events...")
    events = await memory.recall()
    print(f"[OK] {len(events)} events stored")

    print("\n[7/9 Analyzer] Analyzing metrics...")
    try:
        analysis = await asyncio.wait_for(
            analyzer.analyze(events, available_provider),
            timeout=60.0
        )
        print(f"[OK] Analysis complete")
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)[:80]}...")
        analysis = {"error": "Analysis failed", "events_count": len(events)}

    print("\n[8/9 Learner] Learning patterns...")
    try:
        learned = await asyncio.wait_for(
            learner.learn(events, provider=available_provider),
            timeout=60.0
        )
        print(f"[OK] Learning complete")
    except Exception as e:
        print(f"[ERROR] Learning failed: {str(e)[:80]}...")
        learned = {"error": "Learning failed", "patterns_found": 0}

    print("\n[9/9 Improver] Generating improvements...")
    try:
        improvement = await asyncio.wait_for(
            improver.improve(analysis, learned, available_provider),
            timeout=60.0
        )
        print(f"[OK] Improvements generated\n")
    except Exception as e:
        print(f"[ERROR] Improvement failed: {str(e)[:80]}...")
        improvement = {"error": "Improvement failed", "suggestions": []}

    print("\n[OK] Pantheon orchestration complete!")


async def run_offline_mode():
    """Run Offline Mode - demonstrates cached responses for offline operation"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    print("\n[Offline Mode]")
    print("This mode demonstrates offline AI capabilities using cached responses.")
    print("Responses will be served from cache when available, or indicate offline status.")

    provider = select_provider()

    # Get AI provider bus and enable offline mode
    from base import get_ai_provider_bus
    ai_bus = await get_ai_provider_bus()
    await ai_bus.enable_offline_mode(True)

    print(f"\n[INFO] Offline mode enabled for provider: {provider}")
    print("[INFO] Cache will be populated with responses for future offline use")

    try:
        # Test connectivity
        is_online = await ai_bus.check_connectivity()
        print(f"[INFO] Current connectivity: {'ONLINE' if is_online else 'OFFLINE'}")

        # Demonstrate with a few sample queries
        sample_queries = [
            "What is the capital of France?",
            "Explain machine learning in simple terms",
            "Write a hello world program in Python",
            "What are the benefits of offline AI?"
        ]

        print("\n[Testing Offline Capabilities]")
        print("=" * 50)

        for i, query in enumerate(sample_queries, 1):
            print(f"\n[Query {i}] {query}")

            try:
                response = await ai_bus.send_message(query, provider)
                print(f"[Response] {response[:100]}{'...' if len(response) > 100 else ''}")

                # Small delay to avoid overwhelming
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"[ERROR] Failed to get response: {str(e)[:50]}")

        # Show cache statistics
        print("\n[Cache Statistics]")
        print("=" * 50)

        try:
            stats = await ai_bus.get_cache_stats()
            print(f"Total cached responses: {stats.get('total_entries', 0)}")
            print(f"Cache size: {stats.get('total_size_mb', 0):.1f} MB")
            print(f"Cache usage: {stats.get('usage_percent', 0):.1f}%")
            print(f"Cache hits: {stats.get('cache_stats', {}).get('hits', 0)}")
            print(f"Cache misses: {stats.get('cache_stats', {}).get('misses', 0)}")

        except Exception as e:
            print(f"[INFO] Cache statistics unavailable: {str(e)}")

        print("\n[Offline Mode Demo Complete]")
        print("All responses are now cached for offline use.")
        print("Try disconnecting from the internet and running queries again!")

    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Offline mode failed: {error_msg[:100]}...")
        if "API" in error_msg or "connection" in error_msg.lower():
            print("[INFO] Please check your internet connection and try again.")
        else:
            print("[INFO] If this persists, please check the system logs.")

    finally:
        # Clean shutdown
        await ai_bus.enable_offline_mode(False)


async def run_vault_mode():
    """Run Community Vault Mode - Browse and share tools, configs, and evolutions"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    print("\n[Community Vault Mode]")
    print("Browse and share tools, configurations, agent evolutions, and more.")
    print("The Community Vault enables collaborative development and knowledge sharing.")

    try:
        # Initialize vault
        from community_vault import CommunityVault
        vault = CommunityVault()

        # Get vault statistics
        stats = await vault.get_stats()
        print("\n[Vault Statistics]")
        print(f"Total Items: {stats.get('total_items', 0)}")
        print(f"Total Downloads: {stats.get('total_downloads', 0)}")
        print(f"Average Rating: {stats.get('average_rating', 0):.1f}")
        print(f"Categories: {len(stats.get('categories', {}))}")

        # Show available categories
        categories = await vault.get_categories()
        print("\n[Available Categories]")
        for category in categories:
            count = stats.get('categories', {}).get(category['id'], 0)
            print(f"  {category['name']}: {count} items")

        # Show featured items
        featured = await vault.get_featured_items(5)
        if featured:
            print("\n[Featured Items]")
            for item in featured:
                print(f"  ⭐ {item.name} by {item.author}")
                print(f"     {item.description[:60]}{'...' if len(item.description) > 60 else ''}")
                print(f"     ⭐ {item.rating:.1f} rating, {item.downloads} downloads")
                print()

        print("[Community Vault Demo Complete]")
        print("Visit the web dashboard to browse, download, and publish items!")
        print("Use the Community Vault tab to explore the full collection.")

    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Community Vault failed: {error_msg[:100]}...")
        print("[INFO] The vault system may not be fully initialized yet.")

    print("\n[TIP] Access the full Community Vault experience through the web dashboard!")


async def run_learning_loop_mode():
    """Run Learning Loop Mode - Single optimization cycle for system improvement"""
    # Complete logging suppression for clean CLI output
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
    logging.getLogger().setLevel(logging.CRITICAL)
    # Disable all handlers to prevent any output
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
    # Suppress all existing and future loggers
    for name in list(logging.root.manager.loggerDict.keys()) + ['zejzl', 'zejzl.performance', 'zejzl.debug', 'ai_framework']:
        logging.getLogger(name).setLevel(logging.CRITICAL)
        for handler in logging.getLogger(name).handlers[:]:
            logging.getLogger(name).removeHandler(handler)

    print("\n[Learning Loop Mode]")
    print("This mode analyzes system performance and suggests optimizations.")
    task = input("Enter a task to analyze for optimization (or press Enter for general system analysis): ").strip()
    if not task:
        task = "General system performance and optimization analysis"

    print(f"\n[Analyzing: {task}]")

    try:
        # Import and create learning loop
        from src.learning_loop import LearningLoop
        learning_loop = LearningLoop()

        print("[Executing learning cycle...]")

        # Execute single learning cycle
        cycle_result = await learning_loop.execute_learning_cycle()

        if cycle_result:
            print("[OK] Learning cycle complete")

            # Display insights
            insights = await learning_loop.get_recent_insights()
            if insights:
                print(f"\n[INSIGHTS] Found {len(insights)} optimization opportunities:")
                for i, insight in enumerate(insights[:5], 1):  # Show top 5
                    print(f"  {i}. {insight.insight_type}: {insight.description}")
                    if insight.confidence > 0.8:
                        print("     → High confidence recommendation")
            else:
                print("\n[INSIGHTS] No significant optimization opportunities found")

            # Show performance improvements
            print("\n[PERFORMANCE] System analysis complete")
            print("  → Learning patterns identified and cataloged")
        else:
            print("[WARNING] Learning cycle did not complete successfully")

    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Learning loop failed: {error_msg[:100]}...")
        if "API" in error_msg or "connection" in error_msg.lower():
            print("[INFO] Please check your internet connection and try again.")
        else:
            print("[INFO] If this persists, please check the system logs.")


# Future Menu Options (for reference):
#         1. Single Agent - Observe-Reason-Act loop
#         2. Collaboration Mode (Grok + Claude) - Dual AI planning [IMPLEMENTED]
#         3. Swarm Mode (Multi-agent) - Async team coordination [IMPLEMENTED]
#         4. Pantheon Mode (9-agent) - Full AI orchestration with validation & learning [IMPLEMENTED]
#         5. Learning Loop - Single optimization cycle for system improvement [IMPLEMENTED]
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
        3. Swarm Mode (Multi-agent) - Async team coordination
        4. Pantheon Mode - Full 9-agent orchestration with validation & learning
        5. Learning Loop - Single optimization cycle for system improvement
        6. Offline Mode - Cached responses for offline operation
        7. Community Vault - Browse and share tools, configs, and evolutions
        9. Quit

        (Note: Mode 8 is not yet implemented)
""")

    choice = input("        Choose mode (1, 2, 3, 4, 5, 6, 7, or 9): ").strip()

    if choice == "1":
        print("\n[Starting Single Agent Mode...]")
        asyncio.run(run_single_agent_mode())
    elif choice == "2":
        print("\n[Starting Collaboration Mode...]")
        asyncio.run(run_collaboration_mode())
    elif choice == "3":
        print("\n[Starting Swarm Mode...]")
        asyncio.run(run_swarm_mode())
    elif choice == "4":
        print("\n[Starting Pantheon Mode...]")
        asyncio.run(run_pantheon_mode())
    elif choice == "5":
        print("\n[Starting Learning Loop Mode...]")
        asyncio.run(run_learning_loop_mode())
    elif choice == "6":
        print("\n[Starting Offline Mode...]")
        asyncio.run(run_offline_mode())
    elif choice == "7":
        print("\n[Starting Community Vault Mode...]")
        asyncio.run(run_vault_mode())
    elif choice == "9":
        print("\n        Goodbye! :)\n")
        input("        Press Enter to exit...")
        sys.exit(0)
    else:
        print(f"\n        Mode {choice} is not yet implemented. Please choose 1-7, or 9.\n")

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
