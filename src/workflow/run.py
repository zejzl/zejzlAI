"""
Run a workflow file from the command line.

    python -m src.workflow.run examples/workflows/hello.yaml
    python -m src.workflow.run examples/workflows/hello.yaml --input '{"user": {"name": "Zej"}}'

Exit codes: 0 success, 1 a node failed, 2 the file or the input is invalid.
The menu in main.py calls run() with the same arguments.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import List, Optional

from .engine import WorkflowEngine
from .loader import WorkflowDefinitionError, load_workflow
from .messagebus_adapter import MessageBusNode, start_default_agents, stop_agents


async def run(path: str, input_text: Optional[str] = None) -> int:
    """Load a workflow file, run it and print a summary. Returns a process exit code."""
    try:
        workflow, options = load_workflow(path)
        initial = dict(options.get("input", {}))
        if input_text:
            extra = json.loads(input_text)
            if not isinstance(extra, dict):
                raise ValueError("--input must be a JSON object")
            initial.update(extra)
    except (WorkflowDefinitionError, ValueError) as e:
        print(f"[WORKFLOW] Invalid workflow: {e}")
        return 2

    print(f"[WORKFLOW] Running '{workflow.name}' ({len(workflow.engine.nodes)} nodes)")
    engine = WorkflowEngine(workflow.name, timeout=options.get("timeout"))
    agents = []
    if any(isinstance(node, MessageBusNode) for node in workflow.engine.nodes.values()):
        agents = await start_default_agents()
        print(f"[WORKFLOW] Bus agents started: {', '.join(a.agent_id for a in agents)}")
    try:
        result = await engine.execute(workflow, initial)
    except Exception as e:
        print(f"[WORKFLOW] Failed: {type(e).__name__}: {e}")
        for node_id, status in workflow.get_status()["nodes"].items():
            print(f"[WORKFLOW]   {node_id}: {status}")
        return 1
    finally:
        await stop_agents(agents)

    skipped = [node_id for node_id, status in workflow.get_status()["nodes"].items() if status == "skipped"]
    summary = f"[WORKFLOW] {result['status']}: {result['nodes_executed']} nodes"
    if skipped:
        summary += f", {len(skipped)} skipped ({', '.join(skipped)})"
    print(f"{summary} in {result['duration']:.2f}s")
    print(json.dumps(result["data"], indent=2, default=str))
    return 0


async def run_and_cleanup(path: str, input_text: Optional[str] = None) -> int:
    """run(), then stop the shared provider bus if an agent node started it (its tasks keep the loop alive)."""
    try:
        return await run(path, input_text)
    finally:
        try:
            from base import cleanup_ai_provider_bus

            await cleanup_ai_provider_bus()
        except Exception as e:  # cleanup must never hide the workflow's own result
            print(f"[WARNING] provider bus cleanup failed: {e}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.workflow.run", description="Run a workflow from a YAML or JSON file.")
    parser.add_argument("path", help="workflow file (YAML or JSON)")
    parser.add_argument("--input", dest="input_text", help="initial data as a JSON object, merged over the file's `input`")
    args = parser.parse_args(argv)
    return asyncio.run(run_and_cleanup(args.path, args.input_text))


if __name__ == "__main__":
    sys.exit(main())
