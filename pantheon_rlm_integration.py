"""
Pantheon RLM Integration for ZEJZL.NET

Bridges the RLM framework with real zejzl.net agent implementations.
Instead of generic sub-calls, this uses actual PantheonAgent classes.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ZejzlPantheonRLM:
    """
    RLM wrapper that uses real zejzl.net agents instead of generic sub-calls.
    """
    
    def __init__(
        self,
        pantheon_config_path: str = "pantheon_config.json",
        model: str = "grok-3",
        api_key: Optional[str] = None,
        max_iterations: int = 10,
        verbose: bool = True,
        use_real_agents: bool = True
    ):
        """
        Initialize Zejzl Pantheon RLM.
        
        Args:
            pantheon_config_path: Path to Pantheon config
            model: LLM model for root coordination
            api_key: API key (if None, reads from env)
            max_iterations: Max RLM iterations
            verbose: Print debug output
            use_real_agents: Use real agent classes vs generic sub-calls
        """
        # Import pantheon_rlm for base functionality
        from pantheon_rlm import PantheonRLM
        
        # Initialize base RLM
        self.base_rlm = PantheonRLM(
            pantheon_config_path=pantheon_config_path,
            model=model,
            api_key=api_key,
            max_iterations=max_iterations,
            verbose=verbose
        )
        
        self.use_real_agents = use_real_agents
        self.verbose = verbose
        
        # Load agent classes if using real agents
        self.agent_instances = {}
        if use_real_agents:
            self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize real zejzl.net agent instances from config."""
        # Build agent map from pantheon config
        agent_map = {}
        for agent_config in self.base_rlm.pantheon_config.get("agents", []):
            agent_name = agent_config.get("name")
            module_name = agent_config.get("module")
            class_name = agent_config.get("class")
            if agent_name and module_name and class_name:
                agent_map[agent_name] = (module_name, class_name)
        
        for agent_name, (module_name, class_name) in agent_map.items():
            try:
                # Import module dynamically
                module = __import__(module_name, fromlist=[class_name])
                agent_class = getattr(module, class_name)
                
                # Instantiate agent
                self.agent_instances[agent_name] = agent_class()
                
                if self.verbose:
                    print(f"[OK] Loaded {agent_name} ({class_name})")
                    
            except Exception as e:
                if self.verbose:
                    print(f"[WARN] Could not load {agent_name}: {e}")
                # Agent will fall back to generic sub-call
    
    async def process_task_async(self, task: str) -> str:
        """
        Process task using RLM with real agents (async).
        
        Args:
            task: User task/question
            
        Returns:
            Final answer string
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"TASK: {task}")
            print(f"{'='*60}\n")
        
        # Initialize REPL state
        repl_state = {
            "pantheon_config": self.base_rlm.pantheon_config,
            "results": {},
            "final_answer": None,
            "task": task
        }
        
        # Root prompt
        root_prompt = self.base_rlm._build_root_prompt(task)
        history = [{"role": "user", "content": root_prompt}]
        
        # RLM loop
        for iteration in range(self.base_rlm.max_iterations):
            if self.verbose:
                print(f"\n--- Iteration {iteration + 1}/{self.base_rlm.max_iterations} ---")
            
            # Root LLM call
            response = self.base_rlm._llm_call(history)
            
            if self.verbose:
                print(f"LLM Response:\n{response[:500]}...")
            
            # Extract code blocks
            code_blocks = self.base_rlm._extract_code_blocks(response)
            
            if not code_blocks:
                if self.verbose:
                    print("[WARN] No code blocks found")
                
                if "final_answer" in response.lower() or repl_state.get("final_answer"):
                    break
                
                history.append({"role": "assistant", "content": response})
                history.append({
                    "role": "user",
                    "content": "Please write Python code to solve the task using sub_agent()."
                })
                continue
            
            # Execute code blocks with real agents
            all_stdout = []
            for code in code_blocks:
                stdout, repl_state = await self._execute_repl_async(code, repl_state)
                all_stdout.append(stdout)
            
            combined_stdout = "\n".join(all_stdout)
            
            if self.verbose:
                print(f"\nExecution output:\n{combined_stdout[:300]}...")
            
            # Update history
            history.append({"role": "assistant", "content": response})
            history.append({
                "role": "user",
                "content": self.base_rlm._format_execution_result(combined_stdout)
            })
            
            if repl_state.get("final_answer"):
                if self.verbose:
                    print(f"\n[OK] Task complete after {iteration + 1} iterations")
                break
        
        final_answer = repl_state.get("final_answer", "ERROR: Max iterations reached")
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"FINAL ANSWER:")
            print(f"{'='*60}")
            print(final_answer)
            print(f"{'='*60}\n")
        
        return final_answer
    
    async def _execute_repl_async(self, code: str, state: Dict[str, Any]) -> tuple:
        """Execute code with real agent calls (async)."""
        
        # Define async sub_agent function
        async def sub_agent(agent_name: str, subtask: str) -> str:
            """Invoke real agent or fallback to generic sub-call."""
            
            if self.verbose:
                print(f"\n  -> Invoking {agent_name}: {subtask[:60]}...")
            
            # Try using real agent first
            if self.use_real_agents and agent_name in self.agent_instances:
                try:
                    agent = self.agent_instances[agent_name]
                    
                    # Call agent's main method based on agent type
                    if hasattr(agent, 'observe'):
                        result = await agent.observe(subtask)
                    elif hasattr(agent, 'act'):
                        result = await agent.act(subtask)
                    elif hasattr(agent, 'reason'):
                        result = await agent.reason(subtask)
                    elif hasattr(agent, 'analyze'):
                        result = await agent.analyze(subtask)
                    elif hasattr(agent, 'validate'):
                        result = await agent.validate(subtask)
                    elif hasattr(agent, 'improve'):
                        result = await agent.improve(subtask)
                    elif hasattr(agent, 'learn'):
                        result = await agent.learn(subtask)
                    elif hasattr(agent, 'remember'):
                        result = await agent.remember(subtask)
                    elif hasattr(agent, 'reach_consensus'):
                        result = await agent.reach_consensus([subtask])
                    elif hasattr(agent, 'resolve_conflict'):
                        # ConsensusManager uses resolve_conflict
                        from src.agents.consensus import ConflictType, AgentOpinion
                        # Create a simple opinion for the task
                        opinion = AgentOpinion(
                            agent_name="system",
                            agent_role="coordinator",
                            opinion=subtask,
                            confidence=0.8,
                            reasoning="User task"
                        )
                        result = await agent.resolve_conflict(
                            ConflictType.PLANNING_DISPUTE,
                            [opinion]
                        )
                    else:
                        raise AttributeError(f"No main method found for {agent_name}")
                    
                    # Extract text from result (handle Dict or str)
                    if isinstance(result, dict):
                        response_text = result.get('analysis', result.get('plan', result.get('response', str(result))))
                    else:
                        response_text = str(result)
                    
                    if self.verbose:
                        print(f"  <- {agent_name} (REAL): {response_text[:100]}...")
                    
                    return response_text
                    
                except Exception as e:
                    if self.verbose:
                        print(f"  [WARN] Real agent {agent_name} failed: {e}")
                    # Fall through to generic sub-call
            
            # Fallback: Generic AI sub-call (like base pantheon_rlm)
            agent_config = next(
                (a for a in state["pantheon_config"]["agents"] if a["name"] == agent_name),
                None
            )
            
            if not agent_config:
                return f"ERROR: Agent {agent_name} not found"
            
            sub_prompt = f"""Agent: {agent_config['name']}
Role: {agent_config.get('description', 'N/A')}
Subtask: {subtask}

Provide a focused response (2-3 sentences)."""
            
            sub_messages = [{"role": "user", "content": sub_prompt}]
            sub_response = self.base_rlm._llm_call(sub_messages)
            
            if self.verbose:
                print(f"  <- {agent_name} (GENERIC): {sub_response[:100]}...")
            
            return sub_response
        
        # Create wrapper to collect async calls
        pending_awaitables = {}
        
        def sub_agent_sync(agent_name: str, subtask: str):
            """Synchronous wrapper that stores coroutine for later execution."""
            coro = sub_agent(agent_name, subtask)
            # Store coroutine with unique key
            key = f"__await_{len(pending_awaitables)}"
            pending_awaitables[key] = coro
            return key  # Return placeholder
        
        # Execute code with sync wrapper
        exec_globals = {
            "pantheon_config": state["pantheon_config"],
            "results": state["results"],
            "sub_agent": sub_agent_sync,  # Use sync wrapper
            "final_answer": state.get("final_answer"),
            "task": state.get("task"),
            "json": json,
            "datetime": datetime,
            "asyncio": asyncio,
        }
        
        stdout_lines = []
        
        try:
            # Execute code (collects coroutines)
            exec(code, exec_globals)
            
            # Now execute all pending async calls
            if pending_awaitables:
                results_dict = exec_globals.get("results", {})
                for result_key, coro in pending_awaitables.items():
                    # Execute coroutine
                    result = await coro
                    # Replace placeholder in results with actual result
                    for key, value in results_dict.items():
                        if value == result_key:
                            results_dict[key] = result
                exec_globals["results"] = results_dict
            
            stdout_lines.append("[OK] Code executed successfully")
            
        except Exception as e:
            stdout_lines.append(f"[ERROR] {e}")
        
        # Update state
        state["results"] = exec_globals.get("results", state["results"])
        state["final_answer"] = exec_globals.get("final_answer")
        
        return "\n".join(stdout_lines), state
    
    def process_task(self, task: str) -> str:
        """Synchronous wrapper for process_task_async."""
        return asyncio.run(self.process_task_async(task))


def test_zejzl_rlm():
    """Test Zejzl Pantheon RLM with real agents."""
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    load_dotenv("C:/Users/Administrator/Desktop/ZejzlAI/zejzl_net/.env")
    
    parser = argparse.ArgumentParser(description="Test Zejzl Pantheon RLM")
    parser.add_argument("--config", default="pantheon_config.json")
    parser.add_argument("--model", default="grok-3")
    parser.add_argument("--task", default="Analyze zejzl.net scaling strategy")
    parser.add_argument("--no-real-agents", action="store_true", help="Use generic sub-calls only")
    args = parser.parse_args()
    
    print("="*60)
    print("ZEJZL PANTHEON RLM TEST")
    print("="*60)
    
    rlm = ZejzlPantheonRLM(
        pantheon_config_path=args.config,
        model=args.model,
        use_real_agents=not args.no_real_agents,
        verbose=True
    )
    
    result = rlm.process_task(args.task)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_zejzl_rlm()
