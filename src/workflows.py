"""
Advanced Workflow Patterns for ZEJZL.NET Pantheon System

Implements parallel execution, conditional branching, and loops for complex
multi-agent workflows.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger("WorkflowSystem")


class WorkflowStepType(Enum):
    AGENT_EXECUTION = "agent_execution"
    CONDITIONAL_BRANCH = "conditional_branch"
    LOOP_CONTROL = "loop_control"
    PARALLEL_GROUP = "parallel_group"


@dataclass
class WorkflowStep:
    step_type: WorkflowStepType
    id: str
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    timeout: Optional[float] = None

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Step execution not implemented")


@dataclass
class AgentExecutionStep(WorkflowStep):
    agent_name: str = ""
    method_name: str = ""
    method_args: List[Any] = field(default_factory=list)
    method_kwargs: Dict[str, Any] = field(default_factory=dict)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Dynamic import of agent
            module_name = f"src.agents.{self.agent_name.lower()}"
            agent_module = __import__(module_name, fromlist=[self.agent_name])
            agent_class = getattr(agent_module, f"{self.agent_name}Agent")
            agent_instance = agent_class()

            method = getattr(agent_instance, self.method_name)
            start_time = asyncio.get_event_loop().time()
            result = await method(*self.method_args, **self.method_kwargs)
            execution_time = asyncio.get_event_loop().time() - start_time

            return {
                "step_id": self.id,
                "result": result,
                "execution_time": execution_time,
                "success": True,
                "timestamp": datetime.now()
            }
        except Exception as e:
            return {
                "step_id": self.id,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now()
            }


@dataclass
class ParallelGroupStep(WorkflowStep):
    parallel_steps: List[WorkflowStep] = field(default_factory=list)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.parallel_steps:
            return {"step_id": self.id, "parallel_results": [], "success": True}

        tasks = [step.execute(context) for step in self.parallel_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        all_successful = True

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({"step_index": i, "error": str(result), "success": False})
                all_successful = False
            else:
                processed_results.append(result)
                if not result.get("success", False):
                    all_successful = False

        return {
            "step_id": self.id,
            "parallel_results": processed_results,
            "all_successful": all_successful,
            "success": True,
            "timestamp": datetime.now()
        }


@dataclass
class ConditionalBranchStep(WorkflowStep):
    branches: Dict[str, Callable[[Dict[str, Any]], bool]] = field(default_factory=dict)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for branch_name, condition_func in self.branches.items():
            try:
                if condition_func(context):
                    return {
                        "step_id": self.id,
                        "branch_taken": branch_name,
                        "success": True,
                        "timestamp": datetime.now()
                    }
            except Exception as e:
                logger.error(f"Condition evaluation failed: {e}")

        return {
            "step_id": self.id,
            "branch_taken": "default",
            "success": True,
            "timestamp": datetime.now()
        }


@dataclass
class LoopControlStep(WorkflowStep):
    loop_id: str = ""
    control_type: str = "start"
    max_iterations: int = 10

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        loop_context = context.get("loops", {}).get(self.loop_id, {})
        current_iteration = loop_context.get("iteration", 0)

        if self.control_type == "start":
            context.setdefault("loops", {})
            context["loops"][self.loop_id] = {"iteration": 0, "active": True}
            return {"step_id": self.id, "loop_action": "started", "success": True}

        elif self.control_type == "continue":
            if current_iteration >= self.max_iterations:
                context["loops"][self.loop_id]["active"] = False
                return {"step_id": self.id, "loop_action": "broken", "reason": "max_iterations", "success": True}
            else:
                context["loops"][self.loop_id]["iteration"] = current_iteration + 1
                return {"step_id": self.id, "loop_action": "continued", "success": True}

        return {"step_id": self.id, "loop_action": "unknown", "success": False}


@dataclass
class WorkflowDefinition:
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    initial_context: Dict[str, Any] = field(default_factory=dict)


class WorkflowExecutor:
    async def execute_workflow(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        context = workflow.initial_context.copy()
        context.update({"executed_steps": [], "step_results": {}, "start_time": datetime.now()})

        for step in workflow.steps:
            # Check dependencies
            if not self._check_dependencies(step, context):
                continue

            # Check conditions
            if step.condition and not step.condition(context):
                continue

            # Execute step
            result = await step.execute(context)
            context["executed_steps"].append(step.id)
            context["step_results"][step.id] = result

        context["end_time"] = datetime.now()
        context["duration"] = (context["end_time"] - context["start_time"]).total_seconds()

        return {
            "workflow_name": workflow.name,
            "status": "completed",
            "context": context,
            "executed_steps_count": len(context["executed_steps"]),
            "success": True
        }

    def _check_dependencies(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        for dep_id in step.dependencies:
            if dep_id not in context["step_results"]:
                return False
            dep_result = context["step_results"][dep_id]
            if not dep_result.get("success", False):
                return False
        return True


def create_parallel_workflow(task: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        name="parallel_workflow",
        description="Parallel agent execution",
        steps=[
            ParallelGroupStep(
                step_type=WorkflowStepType.PARALLEL_GROUP,
                id="parallel_obs",
                parallel_steps=[
                    AgentExecutionStep(
                        step_type=WorkflowStepType.AGENT_EXECUTION,
                        id="observer",
                        agent_name="Observer",
                        method_name="observe",
                        method_args=[task]
                    ),
                    AgentExecutionStep(
                        step_type=WorkflowStepType.AGENT_EXECUTION,
                        id="analyzer",
                        agent_name="Analyzer",
                        method_name="analyze",
                        method_args=[{"task": task}]
                    )
                ]
            ),
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="reasoner",
                agent_name="Reasoner",
                method_name="reason",
                dependencies=["parallel_obs"]
            )
        ]
    )


def create_conditional_workflow(task: str) -> WorkflowDefinition:
    def complex_condition(context: Dict[str, Any]) -> bool:
        return "complex" in task.lower()

    return WorkflowDefinition(
        name="conditional_workflow",
        description="Conditional branching workflow",
        steps=[
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="observer",
                agent_name="Observer",
                method_name="observe",
                method_args=[task]
            ),
            ConditionalBranchStep(
                step_type=WorkflowStepType.CONDITIONAL_BRANCH,
                id="complexity_check",
                branches={
                    "complex": complex_condition,
                    "simple": lambda ctx: not complex_condition(ctx)
                },
                dependencies=["observer"]
            ),
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="complex_reasoner",
                agent_name="Reasoner",
                method_name="reason",
                condition=lambda ctx: ctx.get("step_results", {}).get("complexity_check", {}).get("branch_taken") == "complex",
                dependencies=["complexity_check"]
            ),
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="simple_actor",
                agent_name="Actor",
                method_name="act",
                condition=lambda ctx: ctx.get("step_results", {}).get("complexity_check", {}).get("branch_taken") == "simple",
                dependencies=["complexity_check"]
            )
        ]
    )


def create_loop_workflow(task: str) -> WorkflowDefinition:
    return WorkflowDefinition(
        name="loop_workflow",
        description="Iterative loop workflow",
        steps=[
            LoopControlStep(
                step_type=WorkflowStepType.LOOP_CONTROL,
                id="loop_start",
                loop_id="main_loop",
                control_type="start",
                max_iterations=3
            ),
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="validator",
                agent_name="Validator",
                method_name="validate",
                dependencies=["loop_start"]
            ),
            LoopControlStep(
                step_type=WorkflowStepType.LOOP_CONTROL,
                id="loop_continue",
                loop_id="main_loop",
                control_type="continue",
                dependencies=["validator"]
            ),
            AgentExecutionStep(
                step_type=WorkflowStepType.AGENT_EXECUTION,
                id="improver",
                agent_name="Improver",
                method_name="improve",
                dependencies=["loop_continue"]
            )
        ]
    )


async def execute_advanced_workflow(workflow_name: str, task: str) -> Dict[str, Any]:
    executor = WorkflowExecutor()

    if workflow_name == "parallel":
        workflow = create_parallel_workflow(task)
    elif workflow_name == "conditional":
        workflow = create_conditional_workflow(task)
    elif workflow_name == "loop":
        workflow = create_loop_workflow(task)
    else:
        raise ValueError(f"Unknown workflow: {workflow_name}")

    return await executor.execute_workflow(workflow)