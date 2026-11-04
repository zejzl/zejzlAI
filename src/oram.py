# src/oram.py
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ORAM")

CALLS_PER_ITERATION = 3          # Observer, Reasoner and Actor each make one provider call per iteration
PRIOR_RUNS_LIMIT = 5             # earlier runs of the same task shown to the Reasoner (file backend only)

# Quality scoring (see ORAMSystem._evaluate_iteration). Three factors, each 0..1, weighted:
#   provenance  did each phase come from the model (1.0), from the rule-based fallback (0.4), or fail (0.0)?
#               A model answer whose JSON could not be parsed (the agents keep it under "raw_response") counts 0.4.
#   reasoning   how much the Reasoner actually said: analysis length (full credit at 300 characters) and subtasks
#   action      what the Actor produced: per result, a real expected outcome (full credit at 60 characters) and plan steps
# Placeholder strings the agents emit when they have nothing score 0. The old scorer gave every clean run 0.95
# whatever the content, which made the score useless for convergence and for recall.
QUALITY_WEIGHTS = {"provenance": 0.4, "reasoning": 0.3, "action": 0.3}
FALLBACK_PROVENANCE = 0.4
ANALYSIS_FULL_CHARS = 300
OUTCOME_FULL_CHARS = 60
STEPS_FULL_COUNT = 2
QUALITY_PLACEHOLDERS = (
    "ai response parsing failed", "analysis not provided", "outcome not specified", "approach not specified",
    "no mitigation specified", "insight extraction encountered an error",
)


def _is_placeholder(text: str) -> bool:
    lowered = text.strip().lower()
    return not lowered or any(p in lowered for p in QUALITY_PLACEHOLDERS)


def text_quality(text: Any, full_at: int) -> float:
    """0 for missing or placeholder text, rising with length to 1.0 at `full_at` characters."""
    if not isinstance(text, str) or _is_placeholder(text):
        return 0.0
    return min(len(text.strip()) / full_at, 1.0)


def steps_quality(steps: Any, full_at: int = STEPS_FULL_COUNT) -> float:
    """Share of `full_at` real steps present. A step is a non-placeholder string or a dict with a description/text."""
    if not isinstance(steps, list):
        return 0.0
    real = 0
    for step in steps:
        if isinstance(step, dict):
            step = step.get("description") or step.get("text") or step.get("step") or ""
        if isinstance(step, str) and not _is_placeholder(step):
            real += 1
    return min(real / full_at, 1.0)


def phase_failed(phase: Any) -> bool:
    """Agents report a failure as a top-level "error" key (or one inside "data")."""
    if not isinstance(phase, dict):
        return False
    data = phase.get("data")
    return "error" in phase or (isinstance(data, dict) and "error" in data)


def phase_provenance(phase: Any) -> float:
    """1.0 model answer, 0.4 rule-based fallback or unparsed model answer, 0.0 failed or missing."""
    if not isinstance(phase, dict) or not phase or phase_failed(phase):
        return 0.0
    if phase.get("ai_generated") is False or phase.get("fallback") or "raw_response" in phase:
        return FALLBACK_PROVENANCE
    return 1.0


def reasoning_quality(reasoning: Any) -> float:
    if not isinstance(reasoning, dict):
        return 0.0
    return 0.7 * text_quality(reasoning.get("analysis"), ANALYSIS_FULL_CHARS) + 0.3 * steps_quality(reasoning.get("subtasks"))


def action_quality(action: Any) -> float:
    """Average over the Actor's results: half for a real expected outcome, half for plan steps."""
    results = action.get("results") if isinstance(action, dict) else None
    if not isinstance(results, list) or not results:
        return 0.0
    scores = []
    for result in results:
        if isinstance(result, dict):
            if "raw_response" in result:
                scores.append(0.0)
                continue
            outcome = text_quality(result.get("expected_outcome"), OUTCOME_FULL_CHARS)
            scores.append(0.5 * outcome + 0.5 * steps_quality(result.get("execution_plan")))
        else:
            scores.append(0.5 * text_quality(result, OUTCOME_FULL_CHARS))  # a bare step, no stated outcome
    return sum(scores) / len(scores)


def quality_factors(observation: Any, reasoning: Any, action: Any) -> Dict[str, float]:
    """The three factors and their weighted total, each rounded to 4 places."""
    provenance = (phase_provenance(observation) + phase_provenance(reasoning) + phase_provenance(action)) / 3
    factors = {"provenance": provenance, "reasoning": reasoning_quality(reasoning), "action": action_quality(action)}
    total = sum(QUALITY_WEIGHTS[name] * value for name, value in factors.items())
    factors = {name: round(value, 4) for name, value in factors.items()}
    factors["total"] = round(total, 4)
    return factors


FILE_MEMORY_MAX_ITERATIONS = 3   # execute_oram's default when ORAM_MEMORY_DIR is set and no limit is given


class ORAMIterationType(Enum):
    """Types of ORAM iterations for different use cases."""
    BASIC = "basic"
    DEEP_ANALYSIS = "deep_analysis"
    CREATIVE = "creative"
    PROBLEM_SOLVING = "problem_solving"
    OPTIMIZATION = "optimization"


@dataclass
class ORAMIteration:
    """Single ORAM iteration result."""
    iteration_id: int
    observation: Dict[str, Any]
    reasoning: Dict[str, Any]
    action: Dict[str, Any]
    memory_update: Dict[str, Any]
    iteration_type: ORAMIterationType
    timestamp: float
    quality_score: float = 0.0
    insights: Optional[List[str]] = None
    quality_factors: Optional[Dict[str, float]] = None  # provenance, reasoning, action, total (see quality_factors())
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []
        if self.quality_factors is None:
            self.quality_factors = {}


class ORAMConfig:
    """Configuration for ORAM iterations."""

    def __init__(self):
        self._max_iterations: int = 5
        self._max_iterations_explicit = False
        self.convergence_threshold: float = 0.85
        self.insight_threshold: float = 0.7
        self.memory_retention_limit: int = 100
        self.adaptive_iterations: bool = True
        self.learning_enabled: bool = True

    @property
    def max_iterations(self) -> int:
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int) -> None:
        # A value set by the caller (menu prompt, execute_oram) wins over the iteration type's default.
        self._max_iterations = value
        self._max_iterations_explicit = True

    def set_iteration_type(self, iteration_type: ORAMIterationType):
        """Configure settings for specific iteration type."""
        if iteration_type == ORAMIterationType.DEEP_ANALYSIS:
            self._apply_default_max(7)
            self.convergence_threshold = 0.9
        elif iteration_type == ORAMIterationType.CREATIVE:
            self._apply_default_max(6)
            self.convergence_threshold = 0.8
        elif iteration_type == ORAMIterationType.PROBLEM_SOLVING:
            self._apply_default_max(8)
            self.convergence_threshold = 0.85
        elif iteration_type == ORAMIterationType.OPTIMIZATION:
            self._apply_default_max(5)
            self.convergence_threshold = 0.9

    def _apply_default_max(self, value: int) -> None:
        """Set the iteration type's default count, unless the caller already chose one."""
        if not self._max_iterations_explicit:
            self._max_iterations = value


class ORAMSystem:
    """
    Observer-Reasoner-Actor + Memory (ORAM) iterative processing system.
    
    Implements clean, non-intrusive iteration loops that work alongside
    the existing Pantheon system without interference.
    
    Features:
    - Adaptive iteration control based on convergence
    - Memory consolidation and learning
    - Quality scoring and insight extraction
    - Multiple iteration strategies
    - Clean separation from Pantheon agents
    """
    
    def __init__(self, config: Optional[ORAMConfig] = None):
        self.config = config or ORAMConfig()
        self.memory_buffer: List[Dict[str, Any]] = []
        self.iteration_history: List[ORAMIteration] = []
        self.convergence_metrics: List[float] = []
        self.insight_repository: List[str] = []
        
        # Import agent instances (non-intrusive)
        self._init_agents()
        
    def _init_agents(self):
        """Initialize agent instances for ORAM processing."""
        try:
            from src.agents.observer import ObserverAgent
            from src.agents.reasoner import ReasonerAgent  
            from src.agents.actor import ActorAgent
            from src.agents.memory import MemoryAgent
            
            self.observer = ObserverAgent()
            self.reasoner = ReasonerAgent()
            self.actor = ActorAgent()
            self.memory = MemoryAgent()
            
            logger.info("[ORAM] Agent instances initialized for iterative processing")
            
        except ImportError as e:
            logger.error(f"[ORAM] Failed to import agents: {e}")
            raise
    
    async def execute_oram_iteration(
        self, 
        task: str, 
        iteration_type: ORAMIterationType = ORAMIterationType.BASIC,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ORAMIteration, bool]:
        """
        Execute a single ORAM iteration.
        
        Args:
            task: The task to process
            iteration_type: Type of iteration strategy
            context: Additional context for processing
            
        Returns:
            Tuple of (iteration_result, should_continue)
        """
        context = context or {}
        iteration_id = len(self.iteration_history) + 1
        timestamp = asyncio.get_event_loop().time()
        
        logger.debug(f"[ORAM] Starting iteration {iteration_id}: {task}")
        
        # 1. OBSERVE: Gather observations about the task
        observation = await self._observe_task(task, context, iteration_id)
        
        # 2. REASON: Analyze and reason about observations
        reasoning = await self._reason_about_observation(observation, iteration_id, task=task)
        
        # 3. ACT: Determine actions based on reasoning
        action = await self._determine_action(reasoning, iteration_id)
        
        # 4. MEMORY: Update memory with iteration results
        memory_update = await self._update_memory(observation, reasoning, action, iteration_id)
        
        # Create iteration object
        iteration = ORAMIteration(
            iteration_id=iteration_id,
            observation=observation,
            reasoning=reasoning,
            action=action,
            memory_update=memory_update,
            iteration_type=iteration_type,
            timestamp=timestamp
        )
        
        # 5. EVALUATE: Score iteration quality and extract insights
        await self._evaluate_iteration(iteration)
        
        # 6. CHECK CONVERGENCE: Determine if more iterations needed
        should_continue = await self._check_convergence(iteration)
        
        # Store iteration
        self.iteration_history.append(iteration)
        self.convergence_metrics.append(iteration.quality_score)
        
        logger.info(f"[ORAM] Iteration {iteration_id} complete, quality: {iteration.quality_score:.3f}, continue: {should_continue}")
        
        return iteration, should_continue
    
    async def _observe_task(self, task: str, context: Dict[str, Any], iteration_id: int) -> Dict[str, Any]:
        """Execute observation phase."""
        try:
            # Enhanced observation with iteration context
            enhanced_task = f"Iteration {iteration_id}: {task}"
            if context:
                enhanced_task += f" (Context: {context})"
            
            observation = await self.observer.observe(enhanced_task)
            
            # Add iteration-specific metadata
            observation["iteration_id"] = iteration_id
            observation["oram_context"] = context
            observation["previous_iterations"] = len(self.iteration_history)
            
            return observation
            
        except Exception as e:
            logger.warning(f"[ORAM] Observation failed for iteration {iteration_id}: {e}")
            return {"error": str(e), "iteration_id": iteration_id, "fallback": True}
    
    async def _reason_about_observation(
        self, observation: Dict[str, Any], iteration_id: int, task: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute reasoning phase."""
        try:
            # Earlier runs of the same task from the file memory backend (ORAM_MEMORY_DIR); empty when it is off.
            prior_runs = self._recall_prior_runs(task) if task else []
            if prior_runs:
                observation["prior_runs"] = prior_runs

            reasoning = await self.reasoner.reason(observation)
            
            # Add iteration context
            reasoning["iteration_id"] = iteration_id
            reasoning["oram_iteration"] = True
            if prior_runs:
                reasoning["prior_runs"] = prior_runs
            
            # Include learning from previous iterations if available
            if self.iteration_history:
                reasoning["previous_insights"] = [insight for iteration in self.iteration_history[-3:] for insight in iteration.insights]
            
            return reasoning
            
        except Exception as e:
            logger.warning(f"[ORAM] Reasoning failed for iteration {iteration_id}: {e}")
            return {"error": str(e), "iteration_id": iteration_id, "fallback": True}
    
    async def _determine_action(self, reasoning: Dict[str, Any], iteration_id: int) -> Dict[str, Any]:
        """Execute action phase."""
        try:
            action = await self.actor.act(reasoning)
            
            # Add iteration context
            action["iteration_id"] = iteration_id
            action["oram_iteration"] = True
            
            # Enhance with iteration-specific considerations
            if iteration_id > 1:
                action["refinement_based_on"] = f"iteration_{iteration_id-1}"
            
            return action
            
        except Exception as e:
            logger.warning(f"[ORAM] Action planning failed for iteration {iteration_id}: {e}")
            return {"error": str(e), "iteration_id": iteration_id, "fallback": True}
    
    async def _update_memory(
        self, 
        observation: Dict[str, Any], 
        reasoning: Dict[str, Any], 
        action: Dict[str, Any], 
        iteration_id: int
    ) -> Dict[str, Any]:
        """Update memory with iteration results."""
        try:
            # Create memory event for this iteration
            memory_event = {
                "type": "oram_iteration",
                "iteration_id": iteration_id,
                "observation": observation,
                "reasoning": reasoning,
                "action": action,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Store in agent memory
            await self.memory.store(memory_event)
            
            # Update local memory buffer
            self.memory_buffer.append(memory_event)
            
            # Maintain memory buffer size
            if len(self.memory_buffer) > self.config.memory_retention_limit:
                self.memory_buffer = self.memory_buffer[-self.config.memory_retention_limit:]
            
            return {
                "stored": True,
                "iteration_id": iteration_id,
                "memory_buffer_size": len(self.memory_buffer)
            }
            
        except Exception as e:
            logger.warning(f"[ORAM] Memory update failed for iteration {iteration_id}: {e}")
            return {"error": str(e), "iteration_id": iteration_id, "fallback": True}
    
    async def _evaluate_iteration(self, iteration: ORAMIteration):
        """Score the iteration (quality_factors() above, kept on the iteration) and extract insights."""
        try:
            iteration.quality_factors = quality_factors(iteration.observation, iteration.reasoning, iteration.action)
            iteration.quality_score = iteration.quality_factors["total"]

            # Extract insights
            iteration.insights = await self._extract_insights(iteration)

            # Update insight repository
            self.insight_repository.extend(iteration.insights)

        except Exception as e:
            logger.warning(f"[ORAM] Iteration evaluation failed: {e}")
            iteration.quality_score = 0.5
            iteration.quality_factors = {}
            iteration.insights = ["Evaluation error occurred"]

    async def _extract_insights(self, iteration: ORAMIteration) -> List[str]:
        """Extract insights from iteration results.

        What ends up here is what a later run of the same task gets to see
        (src/agents/memory.py format_prior_runs, when ORAM_MEMORY_DIR is
        set), so this prefers the Reasoner's actual analysis and the
        Actor's actual expected outcome over a bare item count -- a count
        tells a future run nothing about what was decided or produced.
        """
        insights = []

        try:
            # Extract reasoning insights: the Reasoner's own analysis text.
            if isinstance(iteration.reasoning, dict):
                analysis = iteration.reasoning.get("analysis", "")
                if isinstance(analysis, str) and len(analysis) > 50:
                    insights.append(f"Reasoning: {analysis[:180]}")

            # Extract action insights: what the Actor actually decided to do
            # and expects to happen, not just how many items it produced.
            if isinstance(iteration.action, dict):
                results = iteration.action.get("results", [])
                if results:
                    first = results[0] if isinstance(results[0], dict) else {}
                    outcome = first.get("expected_outcome", "")
                    plan = first.get("execution_plan", [])
                    first_step = plan[0] if isinstance(plan, list) and plan else ""
                    if isinstance(outcome, str) and outcome and outcome != "Outcome not specified":
                        insights.append(f"Action: {len(results)} item(s); expects {outcome[:150]}")
                    elif isinstance(first_step, str) and first_step:
                        insights.append(f"Action: {len(results)} item(s); first step: {first_step[:150]}")
                    else:
                        insights.append(f"Action: Generated {len(results)} execution items")
            
            # Extract iterative improvement insights
            if iteration.iteration_id > 1:
                prev_iteration = self.iteration_history[-2] if len(self.iteration_history) > 1 else None
                if prev_iteration:
                    quality_change = iteration.quality_score - prev_iteration.quality_score
                    if quality_change > 0.1:
                        insights.append(f"Improvement: {quality_change:+.2f} quality increase from previous iteration")
            
            # Extract convergence insights
            if len(self.convergence_metrics) >= 3:
                recent_trend = self.convergence_metrics[-3:]
                if all(score > 0.8 for score in recent_trend):
                    insights.append("Convergence: High-quality pattern detected")
            
        except Exception as e:
            logger.warning(f"[ORAM] Insight extraction failed: {e}")
            insights.append("Insight extraction encountered an error")
        
        return insights[:3]  # Limit to top 3 insights
    
    async def _check_convergence(self, iteration: ORAMIteration) -> bool:
        """Determine if more iterations are needed."""
        # Stop if max iterations reached. The current iteration is not in the history yet, so count it.
        if len(self.iteration_history) + 1 >= self.config.max_iterations:
            return False
        
        # Stop if convergence threshold reached
        if iteration.quality_score >= self.config.convergence_threshold:
            return False
        
        # Stop if quality is degrading
        if len(self.convergence_metrics) >= 3:
            recent_scores = self.convergence_metrics[-3:]
            if recent_scores[0] > recent_scores[1] > recent_scores[2]:  # Declining trend
                return False
        
        # Continue for adaptive iterations
        if self.config.adaptive_iterations:
            return True
        
        return False
    
    async def execute_oram_loop(
        self, 
        task: str, 
        iteration_type: ORAMIterationType = ORAMIterationType.BASIC,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ORAMIteration]:
        """
        Execute complete ORAM iteration loop.
        
        Args:
            task: The task to process
            iteration_type: Type of iteration strategy  
            context: Additional context for processing
            
        Returns:
            List of all iterations executed
        """
        logger.info(f"[ORAM] Starting ORAM loop: {task} (Type: {iteration_type.value})")
        
        # Configure for specific iteration type
        self.config.set_iteration_type(iteration_type)
        
        iterations = []
        should_continue = True
        
        while should_continue:
            iteration, should_continue = await self.execute_oram_iteration(
                task, iteration_type, context
            )
            iterations.append(iteration)
            
            # Add delay between iterations for processing
            await asyncio.sleep(0.1)
        
        logger.info(f"[ORAM] Loop complete: {len(iterations)} iterations executed")
        
        # Generate summary
        await self._generate_loop_summary(iterations, task=task)
        
        return iterations
    
    def _recall_prior_runs(self, task: str) -> List[str]:
        """Earlier runs as short lines for the reasoning prompt. Empty unless the file backend is on.

        Same task only, or (ORAM_MEMORY_RANKED=1) the best-matching runs of any task, see MemoryAgent.recall_prior.
        """
        recall = getattr(self.memory, "recall_prior", None) or getattr(self.memory, "recall_runs", None)
        if recall is None or not getattr(self.memory, "file_backend_enabled", False):
            return []
        try:
            from src.agents.memory import format_prior_runs
            return format_prior_runs(recall(task, limit=PRIOR_RUNS_LIMIT), task=task)
        except Exception as e:
            logger.warning(f"[ORAM] Recall of prior runs failed: {e}")
            return []

    def _store_run(self, task: Optional[str], iterations: List[ORAMIteration], summary: Dict[str, Any]) -> None:
        """Write one result line for this run to the file backend. No-op when it is off or the task is unknown."""
        store_run = getattr(self.memory, "store_run", None)
        if store_run is None or not getattr(self.memory, "file_backend_enabled", False) or not task:
            return
        try:
            last = iterations[-1]
            insights = [insight for iteration in iterations for insight in (iteration.insights or [])]
            final_action = last.action.get("results", last.action) if isinstance(last.action, dict) else last.action
            summary_text = (
                f"{summary['total_iterations']} iterations, average quality {summary['average_quality']:.2f}, "
                f"best {summary['best_quality']:.2f}, converged={summary['convergence_achieved']}, "
                f"{summary['total_insights']} insights"
            )
            if insights:
                summary_text += f"; {insights[0]}"
            store_run(task, {
                "iteration_type": summary["iteration_type"],
                "iterations": summary["total_iterations"],
                "calls": CALLS_PER_ITERATION * summary["total_iterations"],
                "average_quality": round(summary["average_quality"], 4),
                "best_quality": round(summary["best_quality"], 4),
                "quality_factors": summary.get("quality_factors", {}),
                "convergence_achieved": summary["convergence_achieved"],
                "total_insights": summary["total_insights"],
                "insights": insights[:6],
                "summary": summary_text,
                "result": json.dumps(final_action, ensure_ascii=False, default=str),
            })
        except Exception as e:
            logger.warning(f"[ORAM] Storing the run failed: {e}")

    async def _generate_loop_summary(self, iterations: List[ORAMIteration], task: Optional[str] = None):
        """Generate summary of the ORAM loop."""
        try:
            if not iterations:
                logger.info("[ORAM] No iterations executed")
                return
            
            # Calculate metrics
            total_iterations = len(iterations)
            avg_quality = sum(iter.quality_score for iter in iterations) / total_iterations
            best_iteration = max(iterations, key=lambda x: x.quality_score)
            total_insights = sum(len(iter.insights) for iter in iterations)
            
            # Generate summary
            summary = {
                "total_iterations": total_iterations,
                "average_quality": avg_quality,
                "best_quality": best_iteration.quality_score,
                "total_insights": total_insights,
                "convergence_achieved": best_iteration.quality_score >= self.config.convergence_threshold,
                "iteration_type": iterations[0].iteration_type.value if iterations else "none",
                "quality_factors": dict(best_iteration.quality_factors or {})
            }
            
            logger.info(f"[ORAM] Summary: {summary}")
            
            # Store summary in memory
            if hasattr(self, 'memory'):
                await self.memory.store({
                    "type": "oram_summary",
                    "summary": summary,
                    "timestamp": asyncio.get_event_loop().time()
                })
                self._store_run(task, iterations, summary)
            
        except Exception as e:
            logger.warning(f"[ORAM] Summary generation failed: {e}")
    
    def get_iteration_history(self) -> List[ORAMIteration]:
        """Get complete iteration history."""
        return self.iteration_history.copy()
    
    def get_insights(self) -> List[str]:
        """Get all insights extracted."""
        return self.insight_repository.copy()
    
    def get_convergence_metrics(self) -> List[float]:
        """Get convergence quality metrics."""
        return self.convergence_metrics.copy()
    
    def clear_history(self):
        """Clear iteration history and reset state."""
        self.iteration_history.clear()
        self.convergence_metrics.clear()
        self.insight_repository.clear()
        logger.info("[ORAM] History cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current ORAM system status."""
        return {
            "iterations_executed": len(self.iteration_history),
            "insights_generated": len(self.insight_repository),
            "current_config": {
                "max_iterations": self.config.max_iterations,
                "convergence_threshold": self.config.convergence_threshold,
                "adaptive_iterations": self.config.adaptive_iterations
            },
            "memory_buffer_size": len(self.memory_buffer),
            "last_iteration_quality": self.convergence_metrics[-1] if self.convergence_metrics else 0.0
        }


# Convenience function for quick ORAM execution
async def execute_oram(
    task: str, 
    iteration_type: ORAMIterationType = ORAMIterationType.BASIC,
    max_iterations: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None
) -> List[ORAMIteration]:
    """
    Convenience function to execute ORAM iterations with custom settings.
    
    Args:
        task: The task to process
        iteration_type: Type of iteration strategy
        max_iterations: Maximum iterations to execute. None (the default) uses the iteration type's own count
            (basic 5, deep analysis 7, creative 6, problem solving 8, optimization 5); a number overrides it.
            With the file memory backend on (ORAM_MEMORY_DIR set) None means 3, the agreed cap per run.
        context: Additional context for processing
        
    Returns:
        List of executed iterations
    """
    config = ORAMConfig()
    if max_iterations is not None:
        config.max_iterations = max_iterations
    else:
        from src.agents.memory import memory_dir
        if memory_dir() is not None:
            config.max_iterations = FILE_MEMORY_MAX_ITERATIONS
    
    oram = ORAMSystem(config)
    return await oram.execute_oram_loop(task, iteration_type, context)