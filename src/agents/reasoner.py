# src/agents/reasoner.py
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("ReasonerAgent")


class ReasonerAgent:
    """Develops strategic plans and logical reasoning for task execution"""

    def __init__(self):
        from src.agent_personality import AGENT_PERSONALITIES
        self.name = "Reasoner"
        self.specialization = "Strategic Planning & Logical Reasoning"
        self.responsibilities = [
            "Analyze task observations to develop comprehensive plans",
            "Identify logical dependencies and execution sequences",
            "Assess risks and develop mitigation strategies",
            "Create structured, actionable execution plans"
        ]
        self.expertise_areas = [
            "Strategic planning",
            "Risk assessment",
            "Logical reasoning",
            "Dependency analysis"
        ]
        # Load personality
        self.personality = AGENT_PERSONALITIES.get("Reasoner")
        self.expertise_areas = [
            "Strategic planning and roadmap development",
            "Task decomposition and workflow design",
            "Resource allocation and scheduling",
            "Risk assessment and contingency planning"
        ]
        self.state = {}

    async def reason(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to reason on an observation and produce a comprehensive plan.
        """
        logger.debug(f"[{self.name}] Reasoning on observation: {observation}")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Get personality-enhanced prompt
            personality_prompt = self.personality.get_personality_prompt() if self.personality else ""

            # Create prompt for reasoning
            task = observation.get('task', 'Unknown task')
            context = observation.get('context', '')

            prompt = f"""Analyze this task and create a JSON plan: {task}

Return ONLY valid JSON:
{{
    "analysis": "task analysis",
    "subtasks": [{{"id": "1", "description": "step description", "success_criteria": "completion check", "estimated_effort": "Low"}}],
    "risks": ["risk1"],
    "approach": "strategy"
}}"""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="claude",  # Try Claude 3.5 Sonnet
                conversation_id=f"reasoner_{hash(str(observation))}"
            )

            # Parse JSON response
            import json
            try:
                plan_data = json.loads(response)
                plan = {
                    "observation": observation,
                    "analysis": plan_data.get("analysis", "Analysis not provided"),
                    "subtasks": plan_data.get("subtasks", []),
                    "risks": plan_data.get("risks", []),
                    "approach": plan_data.get("approach", "Approach not specified"),
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                plan = {
                    "observation": observation,
                    "analysis": "AI response parsing failed",
                    "subtasks": [{"description": response[:200], "id": "fallback"}],
                    "risks": ["JSON parsing failed"],
                    "approach": "Direct AI response",
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True,
                    "raw_response": response
                }

            logger.info(f"[{self.name}] AI-generated plan with {len(plan.get('subtasks', []))} subtasks")
            return plan

        except Exception as e:
            logger.error(f"[{self.name}] AI reasoning failed: {e}")
            # Fallback to stub
            plan = {
                "observation": observation,
                "subtasks": [
                    f"Step 1 for '{observation.get('task', 'task')}'",
                    f"Step 2 for '{observation.get('task', 'task')}'",
                ],
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }
            logger.warning(f"[{self.name}] Using fallback stub plan")
            return plan
