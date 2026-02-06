"""
Pantheon RLM - Recursive Language Model wrapper for zejzl.net 9-Agent Pantheon

This implements the RLM paradigm for multi-agent coordination:
1. Root call sees only metadata (agent names, descriptions)
2. Writes Python code to coordinate agents
3. Recursively invokes agents via sub-calls
4. Returns final result

Usage:
    from tools.pantheon_rlm import PantheonRLM
    
    rlm = PantheonRLM("pantheon_config.json")
    result = rlm.process_task("Research Training-Free GRPO")
    print(result)
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PantheonRLM:
    """RLM wrapper for zejzl.net 9-Agent Pantheon coordination."""
    
    def __init__(
        self,
        pantheon_config_path: str,
        model: str = "claude-sonnet-4-5",
        api_key: Optional[str] = None,
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize Pantheon RLM.
        
        Args:
            pantheon_config_path: Path to Pantheon configuration JSON
            model: LLM model to use (claude-sonnet-4-5, gpt-4o, etc.)
            api_key: API key (if None, reads from environment)
            max_iterations: Maximum RLM iterations
            verbose: Print debug output
        """
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Detect provider from model name
        if "claude" in model or "sonnet" in model:
            self.provider = "anthropic"
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("pip install anthropic")
                
        elif "gpt" in model or "o1" in model:
            self.provider = "openai"
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set")
            
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("pip install openai")
                
        elif "gemini" in model:
            self.provider = "gemini"
            self.api_key = api_key or os.getenv("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not set")
            
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError("pip install google-genai")
                
        elif "grok" in model:
            self.provider = "xai"
            self.api_key = api_key or os.getenv("GROK_API_KEY")
            if not self.api_key:
                raise ValueError("GROK_API_KEY not set")
            
            try:
                import openai
                # xAI uses OpenAI-compatible API
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.x.ai/v1"
                )
            except ImportError:
                raise ImportError("pip install openai")
        else:
            raise ValueError(f"Unsupported model: {model}")
        
        # Load Pantheon config as external variable (not in context)
        config_path = Path(pantheon_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Pantheon config not found: {pantheon_config_path}")
        
        with open(config_path) as f:
            self.pantheon_config = json.load(f)
        
        if self.verbose:
            print(f"[OK] Initialized Pantheon RLM")
            print(f"   Provider: {self.provider}")
            print(f"   Model: {self.model}")
            print(f"   Agents: {len(self.pantheon_config.get('agents', []))}")
    
    def process_task(self, task: str) -> str:
        """
        Process task using RLM paradigm.
        
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
            "pantheon_config": self.pantheon_config,  # External variable
            "results": {},  # Store sub-call results
            "final_answer": None,
            "task": task
        }
        
        # Root prompt with metadata only
        root_prompt = self._build_root_prompt(task)
        
        # Message history (RLM iterations)
        history = [{"role": "user", "content": root_prompt}]
        
        # RLM loop
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n--- Iteration {iteration + 1}/{self.max_iterations} ---")
            
            # Root LLM call (sees only metadata + code history)
            response = self._llm_call(history)
            
            if self.verbose:
                print(f"LLM Response:\n{response[:500]}...")
            
            # Extract code blocks
            code_blocks = self._extract_code_blocks(response)
            
            if not code_blocks:
                # No code to execute, might be done or error
                if self.verbose:
                    print("[WARN]  No code blocks found")
                
                # Check if response contains final answer
                if "final_answer" in response.lower() or repl_state.get("final_answer"):
                    break
                
                # Otherwise, prompt for code
                history.append({"role": "assistant", "content": response})
                history.append({
                    "role": "user",
                    "content": "Please write Python code to solve the task. Use sub_agent() to invoke agents."
                })
                continue
            
            # Execute all code blocks
            all_stdout = []
            for code in code_blocks:
                stdout, repl_state = self._execute_repl(code, repl_state)
                all_stdout.append(stdout)
            
            combined_stdout = "\n".join(all_stdout)
            
            if self.verbose:
                print(f"\nExecution output:\n{combined_stdout[:300]}...")
            
            # Append to history (only metadata about output)
            history.append({"role": "assistant", "content": response})
            history.append({
                "role": "user",
                "content": self._format_execution_result(combined_stdout)
            })
            
            # Check if done
            if repl_state.get("final_answer"):
                if self.verbose:
                    print(f"\n[OK] Task complete after {iteration + 1} iterations")
                break
        
        final_answer = repl_state.get("final_answer", "ERROR: Max iterations reached without final answer")
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"FINAL ANSWER:")
            print(f"{'='*60}")
            print(final_answer)
            print(f"{'='*60}\n")
        
        return final_answer
    
    def _build_root_prompt(self, task: str) -> str:
        """Build root prompt with metadata only (not full config)."""
        agents = self.pantheon_config.get("agents", [])
        
        # Extract agent metadata (names + short descriptions)
        agent_metadata = {}
        for agent in agents:
            name = agent.get("name", "Unknown")
            desc = agent.get("description", "")[:100]  # First 100 chars only
            agent_metadata[name] = desc
        
        prompt = f"""You are a Recursive Language Model (RLM) coordinating a 9-agent Pantheon system.

TASK: {task}

AVAILABLE AGENTS (in variable `pantheon_config`):
{json.dumps(agent_metadata, indent=2)}

YOUR JOB:
1. Write Python code to identify relevant agents (usually 2-3 needed)
2. Use `sub_agent(agent_name, subtask)` to invoke agents recursively
3. Store results in `results` dict (don't print everything)
4. When done, set `final_answer` variable

REPL ENVIRONMENT:
- pantheon_config: Full Pantheon configuration (9 agents)
- results: Dict to store sub-agent outputs
- sub_agent(name, task): Invoke agent recursively
- final_answer: Set this to finish (will be returned to user)
- task: The original user task

EXAMPLE:
```python
# Identify relevant agents for research task
relevant_agents = ["Searcher", "Neuron", "Explainer"]

# Research phase
results["search"] = sub_agent("Searcher", "Find information about Training-Free GRPO")

# Analysis phase
results["analysis"] = sub_agent("Neuron", f"Analyze this research: {{results['search']}}")

# Synthesis phase
results["explanation"] = sub_agent("Explainer", f"Explain in simple terms: {{results['analysis']}}")

# Set final answer
final_answer = results["explanation"]
```

IMPORTANT:
- Only invoke 2-4 agents (not all 9)
- Keep sub-tasks focused and short
- Store intermediate results symbolically
- Don't print large outputs (use variables)

Write Python code to solve the task:
"""
        return prompt
    
    def _llm_call(self, messages: list) -> str:
        """Make LLM API call."""
        if self.provider == "anthropic":
            # Anthropic: Extract system message
            system = None
            user_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=user_messages,
                system=system if system else anthropic.NOT_GIVEN
            )
            return response.content[0].text
            
        elif self.provider == "openai" or self.provider == "xai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content
            
        elif self.provider == "gemini":
            # Convert messages to Gemini format
            contents = []
            for msg in messages:
                role = "user" if msg["role"] in ["user", "system"] else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            return response.text
        
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _extract_code_blocks(self, text: str) -> list:
        """Extract Python code blocks from markdown (robust parsing)."""
        code_blocks = []
        lines = text.split("\n")
        in_code_block = False
        current_block = []
        
        # Try standard markdown code blocks first
        for line in lines:
            if line.strip().startswith("```python") or line.strip().startswith("```py"):
                in_code_block = True
                current_block = []
            elif line.strip() == "```" and in_code_block:
                if current_block:
                    code_blocks.append("\n".join(current_block))
                in_code_block = False
                current_block = []
            elif in_code_block:
                current_block.append(line)
        
        # If no code blocks found, try to extract Python-like code
        if not code_blocks:
            # Look for Python syntax patterns
            potential_code = []
            for line in lines:
                stripped = line.strip()
                # Python code indicators
                if (stripped.startswith("#") or 
                    stripped.startswith("import ") or
                    stripped.startswith("from ") or
                    "=" in stripped and "sub_agent(" in stripped or
                    stripped.startswith("results[") or
                    stripped.startswith("final_answer") or
                    stripped.startswith("relevant_agents")):
                    potential_code.append(line)
                elif potential_code and stripped and not stripped.endswith(":"):
                    # Continue capturing indented code
                    if line.startswith(" ") or line.startswith("\t"):
                        potential_code.append(line)
            
            if potential_code:
                code_blocks.append("\n".join(potential_code))
        
        return code_blocks
    
    def _execute_repl(self, code: str, state: Dict[str, Any]) -> tuple:
        """Execute code in REPL environment with sub_agent capability."""
        
        # Provide sub_agent function in REPL
        def sub_agent(agent_name: str, subtask: str) -> str:
            """Invoke agent as sub-call."""
            agent_config = next(
                (a for a in state["pantheon_config"]["agents"] if a["name"] == agent_name),
                None
            )
            
            if not agent_config:
                return f"ERROR: Agent {agent_name} not found"
            
            if self.verbose:
                print(f"\n  -> Invoking {agent_name}: {subtask[:60]}...")
            
            # Sub-call with agent-specific context (only relevant config)
            sub_prompt = f"""Agent: {agent_config['name']}
Role: {agent_config.get('description', 'N/A')}
Subtask: {subtask}

Provide a focused response for this subtask (2-3 sentences)."""
            
            sub_messages = [{"role": "user", "content": sub_prompt}]
            sub_response = self._llm_call(sub_messages)
            
            if self.verbose:
                print(f"  <- {agent_name}: {sub_response[:100]}...")
            
            return sub_response
        
        # Execute code with REPL globals
        exec_globals = {
            "pantheon_config": state["pantheon_config"],
            "results": state["results"],
            "sub_agent": sub_agent,
            "final_answer": state.get("final_answer"),
            "task": state.get("task"),
            # Common imports
            "json": json,
            "datetime": datetime,
        }
        
        stdout_lines = []
        stderr_lines = []
        
        try:
            # Capture stdout
            from io import StringIO
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            # Execute code
            exec(code, exec_globals)
            
            # Capture output
            stdout_lines.append(sys.stdout.getvalue())
            stderr_lines.append(sys.stderr.getvalue())
            
            # Restore stdout
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            if not stderr_lines[0]:
                stdout_lines.append("[OK] Code executed successfully")
            
        except Exception as e:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            stdout_lines.append(f"[ERROR] ERROR: {e}")
        
        # Update state from execution
        state["results"] = exec_globals.get("results", state["results"])
        state["final_answer"] = exec_globals.get("final_answer")
        
        stdout = "\n".join(stdout_lines)
        stderr = "\n".join(stderr_lines)
        
        return stdout + stderr, state
    
    def _format_execution_result(self, stdout: str, max_chars: int = 300) -> str:
        """Format execution result with metadata only (not full output)."""
        if len(stdout) <= max_chars:
            return f"Execution result:\n{stdout}"
        else:
            return f"Execution result (truncated):\nLength: {len(stdout)} chars\nPreview: {stdout[:max_chars]}..."


def test_pantheon_rlm():
    """Test Pantheon RLM with sample task."""
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    # Also try zejzl.net .env
    load_dotenv("C:/Users/Administrator/Desktop/ZejzlAI/zejzl_net/.env")
    
    parser = argparse.ArgumentParser(description="Test Pantheon RLM")
    parser.add_argument("--config", default="pantheon_config.json", help="Pantheon config path")
    parser.add_argument("--model", default="grok-3", help="Model to use")
    parser.add_argument("--task", default="Explain what Training-Free GRPO is and why it matters", help="Test task")
    args = parser.parse_args()
    
    print("="*60)
    print("PANTHEON RLM TEST")
    print("="*60)
    
    rlm = PantheonRLM(
        pantheon_config_path=args.config,
        model=args.model,
        verbose=True
    )
    
    result = rlm.process_task(args.task)
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_pantheon_rlm()
