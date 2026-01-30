"""
Test script to run the Pantheon mode programmatically
This simulates what would happen during a full 9-agent orchestration
"""
import asyncio
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Suppress all logging for clean output
logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[])
logging.getLogger().setLevel(logging.CRITICAL)

async def test_pantheon():
    """Test the Pantheon orchestration with a sample task"""
    
    print("\n" + "="*70)
    print("  ZEJZL.NET PANTHEON - 9-AGENT ORCHESTRATION TEST")
    print("="*70)
    
    # Import required modules
    try:
        from base import get_ai_provider_bus
        from src.agents.observer import ObserverAgent
        from src.agents.reasoner import ReasonerAgent
        from src.agents.actor import ActorAgent
        from src.agents.validator import ValidatorAgent
        from src.agents.memory import MemoryAgent
        from src.agents.executor import ExecutorAgent
        from src.agents.analyzer import AnalyzerAgent
        from src.agents.learner import LearnerAgent
        from src.agents.improver import ImproverAgent
        
        print("\n[OK] All agent modules imported successfully")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to import modules: {e}")
        return False
    
    # Initialize AI provider bus
    try:
        ai_bus = await get_ai_provider_bus()
        print(f"[OK] AI Provider Bus initialized")
        print(f"     Available providers: {list(ai_bus.providers.keys())}")
        
        # Check which providers are actually configured
        if not ai_bus.providers:
            print("\n[WARNING] No AI providers configured!")
            print("          Need API keys in .env file for at least one provider:")
            print("          - OPENAI_API_KEY")
            print("          - ANTHROPIC_API_KEY")
            print("          - GEMINI_API_KEY")
            print("          - GROK_API_KEY")
            return False
            
        provider = list(ai_bus.providers.keys())[0]
        print(f"     Using provider: {provider}")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize AI bus: {e}")
        return False
    
    # Initialize all 9 agents
    print("\n" + "="*70)
    print("  INITIALIZING 9-AGENT PANTHEON")
    print("="*70)
    
    try:
        agents = {
            "Observer": ObserverAgent(),
            "Reasoner": ReasonerAgent(),
            "Actor": ActorAgent(),
            "Validator": ValidatorAgent(),
            "Memory": MemoryAgent(),
            "Executor": ExecutorAgent(),
            "Analyzer": AnalyzerAgent(),
            "Learner": LearnerAgent(),
            "Improver": ImproverAgent()
        }
        
        for name, agent in agents.items():
            print(f"[OK] {name} Agent initialized")
            
    except Exception as e:
        print(f"\n[ERROR] Failed to initialize agents: {e}")
        return False
    
    # Test task
    task = "Analyze the benefits of implementing a caching layer for API responses"
    print(f"\n[TASK] {task}")
    
    # Run the full Pantheon orchestration
    print("\n" + "="*70)
    print("  PANTHEON ORCHESTRATION SEQUENCE")
    print("="*70)
    
    results = {}
    
    try:
        # 1. Observer
        print("\n[1/9] OBSERVER - Gathering observations...")
        observation = await agents["Observer"].observe(task, provider)
        await agents["Memory"].store({"type": "observation", "data": observation})
        results["observation"] = observation
        print(f"      [OK] Complexity: {observation.get('complexity_level', 'Unknown')}")
        print(f"      [OK] Requirements: {len(observation.get('requirements', []))} identified")
        
        # 2. Reasoner
        print("\n[2/9] REASONER - Creating execution plan...")
        plan = await agents["Reasoner"].reason(observation, provider)
        await agents["Memory"].store({"type": "plan", "data": plan})
        results["plan"] = plan
        print(f"      [OK] Plan created with {len(plan.get('steps', []))} steps")
        
        # 3. Actor
        print("\n[3/9] ACTOR - Executing planned actions...")
        execution = await agents["Actor"].act(plan, provider)
        await agents["Memory"].store({"type": "execution", "data": execution})
        results["execution"] = execution
        print(f"      [OK] Actions executed")
        
        # 4. Validator
        print("\n[4/9] VALIDATOR - Validating execution...")
        validation = await agents["Validator"].validate(execution, provider)
        await agents["Memory"].store({"type": "validation", "data": validation})
        results["validation"] = validation
        print(f"      [OK] Validation complete")
        
        # 5. Executor
        print("\n[5/9] EXECUTOR - Performing validated tasks...")
        execution_result = await agents["Executor"].execute(validation, provider)
        await agents["Memory"].store({"type": "executor", "data": execution_result})
        results["executor"] = execution_result
        print(f"      [OK] Tasks executed")
        
        # 6. Memory
        print("\n[6/9] MEMORY - Recalling stored events...")
        events = await agents["Memory"].recall()
        results["events"] = events
        print(f"      [OK] {len(events)} events retrieved")
        
        # 7. Analyzer
        print("\n[7/9] ANALYZER - Analyzing metrics...")
        analysis = await asyncio.wait_for(
            agents["Analyzer"].analyze(events, provider),
            timeout=60.0
        )
        results["analysis"] = analysis
        print(f"      [OK] Analysis complete")
        
        # 8. Learner
        print("\n[8/9] LEARNER - Learning patterns...")
        learned = await asyncio.wait_for(
            agents["Learner"].learn(events, provider=provider),
            timeout=60.0
        )
        results["learned"] = learned
        print(f"      [OK] Learning complete")
        
        # 9. Improver
        print("\n[9/9] IMPROVER - Generating improvements...")
        improvement = await asyncio.wait_for(
            agents["Improver"].improve(analysis, learned, provider),
            timeout=60.0
        )
        results["improvement"] = improvement
        print(f"      [OK] Improvements generated")
        
    except Exception as e:
        print(f"\n[ERROR] Orchestration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    print("\n" + "="*70)
    print("  PANTHEON ORCHESTRATION COMPLETE")
    print("="*70)
    print(f"\n[OK] All 9 agents executed successfully")
    print(f"[OK] {len(events)} events stored in memory")
    print(f"[OK] Orchestration complete!")
    
    print("\n" + "="*70)
    print("  RESULTS SUMMARY")
    print("="*70)
    print(f"\nObservation: {results['observation'].get('objective', 'N/A')}")
    print(f"Plan Steps: {len(results['plan'].get('steps', []))}")
    print(f"Memory Events: {len(results['events'])}")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_pantheon())
    sys.exit(0 if success else 1)
