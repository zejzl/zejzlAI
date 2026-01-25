# src/oram.py
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("ORAM")


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
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []


class ORAMConfig:
    """Configuration for ORAM iterations."""
    
    def __init__(self):
        self.max_iterations: int = 5
        self.convergence_threshold: float = 0.85
        self.insight_threshold: float = 0.7
        self.memory_retention_limit: int = 100
        self.adaptive_iterations: bool = True
        self.learning_enabled: bool = True
        
    def set_iteration_type(self, iteration_type: ORAMIterationType):
        """Configure settings for specific iteration type."""
        if iteration_type == ORAMIterationType.DEEP_ANALYSIS:
            self.max_iterations = 7
            self.convergence_threshold = 0.9
        elif iteration_type == ORAMIterationType.CREATIVE:
            self.max_iterations = 6
            self.convergence_threshold = 0.8
        elif iteration_type == ORAMIterationType.PROBLEM_SOLVING:
            self.max_iterations = 8
            self.convergence_threshold = 0.85
        elif iteration_type == ORAMIterationType.OPTIMIZATION:
            self.max_iterations = 5
            self.convergence_threshold = 0.9


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
        reasoning = await self._reason_about_observation(observation, iteration_id)
        
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
    
    async def _reason_about_observation(self, observation: Dict[str, Any], iteration_id: int) -> Dict[str, Any]:
        """Execute reasoning phase."""
        try:
            reasoning = await self.reasoner.reason(observation)
            
            # Add iteration context
            reasoning["iteration_id"] = iteration_id
            reasoning["oram_iteration"] = True
            
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
        """Evaluate iteration quality and extract insights."""
        try:
            quality_factors = []
            
            # Check for errors in any phase
            has_errors = any(
                "error" in phase.get("data", {}) 
                for phase in [
                    iteration.observation, 
                    iteration.reasoning, 
                    iteration.action
                ]
            )
            
            if has_errors:
                quality_factors.append(0.3)  # Penalty for errors
            else:
                quality_factors.append(1.0)  # Full credit for no errors
            
            # Evaluate reasoning depth
            if isinstance(iteration.reasoning, dict) and iteration.reasoning.get("analysis"):
                quality_factors.append(0.9)
            else:
                quality_factors.append(0.5)
            
            # Evaluate action completeness
            if isinstance(iteration.action, dict) and iteration.action.get("results"):
                quality_factors.append(0.9)
            else:
                quality_factors.append(0.6)
            
            # Evaluate memory integration
            if isinstance(iteration.memory_update, dict) and iteration.memory_update.get("stored"):
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.7)
            
            # Calculate overall quality score
            iteration.quality_score = sum(quality_factors) / len(quality_factors)
            
            # Extract insights
            iteration.insights = await self._extract_insights(iteration)
            
            # Update insight repository
            self.insight_repository.extend(iteration.insights)
            
        except Exception as e:
            logger.warning(f"[ORAM] Iteration evaluation failed: {e}")
            iteration.quality_score = 0.5
            iteration.insights = ["Evaluation error occurred"]
    
    async def _extract_insights(self, iteration: ORAMIteration) -> List[str]:
        """Extract insights from iteration results."""
        insights = []
        
        try:
            # Extract reasoning insights
            if isinstance(iteration.reasoning, dict):
                analysis = iteration.reasoning.get("analysis", "")
                if analysis and len(analysis) > 50:
                    insights.append(f"Reasoning: Key finding - {analysis[:100]}...")
            
            # Extract action insights
            if isinstance(iteration.action, dict):
                results = iteration.action.get("results", [])
                if results:
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
        # Stop if max iterations reached
        if len(self.iteration_history) >= self.config.max_iterations:
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
        await self._generate_loop_summary(iterations)
        
        return iterations
    
    async def _generate_loop_summary(self, iterations: List[ORAMIteration]):
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
                "iteration_type": iterations[0].iteration_type.value if iterations else "none"
            }
            
            logger.info(f"[ORAM] Summary: {summary}")
            
            # Store summary in memory
            if hasattr(self, 'memory'):
                await self.memory.store({
                    "type": "oram_summary",
                    "summary": summary,
                    "timestamp": asyncio.get_event_loop().time()
                })
            
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
    max_iterations: int = 5,
    context: Optional[Dict[str, Any]] = None
) -> List[ORAMIteration]:
    """
    Convenience function to execute ORAM iterations with custom settings.
    
    Args:
        task: The task to process
        iteration_type: Type of iteration strategy
        max_iterations: Maximum iterations to execute
        context: Additional context for processing
        
    Returns:
        List of executed iterations
    """
    config = ORAMConfig()
    config.max_iterations = max_iterations
    
    oram = ORAMSystem(config)
    return await oram.execute_oram_loop(task, iteration_type, context)