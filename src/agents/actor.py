# src/agents/actor.py
import asyncio
import logging
from typing import Any, Dict, List, Optional

from base import PantheonAgent, AgentConfig
from messagebus import Message

logger = logging.getLogger("ActorAgent")


class ActorAgent(PantheonAgent):
    """Executes plans and coordinates task implementation"""

    def __init__(self, message_bus=None):
        from src.agent_personality import AGENT_PERSONALITIES
        config = AgentConfig(
            name="Actor",
            role="Plan Execution & Task Coordination",
            channels=["actor_channel"]
        )
        super().__init__(config, message_bus)

        self.specialization = "Plan Execution & Task Coordination"
        self.responsibilities = [
            "Execute planned subtasks in proper sequence",
            "Coordinate with other agents as needed",
            "Monitor execution progress and quality",
            "Adapt execution based on real-time feedback"
        ]
        self.expertise_areas = [
            "Task execution",
            "Process coordination",
            "Quality monitoring",
            "Adaptive execution"
        ]
        # Load personality
        self.personality = AGENT_PERSONALITIES.get("Actor")
        self.expertise_areas = [
            "Tool integration and API calling",
            "Sequential task execution",
            "Error handling and recovery",
            "Execution monitoring and logging"
        ]
        self.state = {}

    async def process(self, message: Message):
        """Process incoming message (not implemented)"""
        pass

    async def act(self, plan: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Use AI to determine how to execute subtasks and provide execution guidance.
        """
        logger.debug(f"[{self.name}] Acting on plan: {plan}")

        try:
            subtasks = plan.get("subtasks", [])
            results = []

            for i, subtask in enumerate(subtasks):
                # Get personality-enhanced prompt
                personality_prompt = self.personality.get_personality_prompt() if self.personality else ""

                # Create prompt for action execution
                subtask_desc = subtask if isinstance(subtask, str) else subtask.get("description", str(subtask))

                prompt = f"""Create execution steps for: {subtask_desc}

Return ONLY valid JSON:
{{
    "execution_steps": ["step 1", "step 2"],
    "tools_needed": ["tool1"],
    "expected_outcome": "success criteria",
    "risk_mitigation": "risk handling",
    "estimated_duration": "time estimate"
}}"""

                # Call AI via the integrated call_ai method
                response = await self.call_ai(
                    prompt=prompt,
                    provider=provider,
                    conversation_id=f"actor_{hash(str(plan))}_{i}"
                )

                # Parse JSON response
                import json
                try:
                    action_data = json.loads(response)
                    result = {
                        "subtask": subtask,
                        "execution_plan": action_data.get("execution_steps", []),
                        "tools_needed": action_data.get("tools_needed", []),
                        "expected_outcome": action_data.get("expected_outcome", "Outcome not specified"),
                        "risk_mitigation": action_data.get("risk_mitigation", "No mitigation specified"),
                        "estimated_duration": action_data.get("estimated_duration", "Unknown"),
                        "ai_generated": True
                    }
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    result = {
                        "subtask": subtask,
                        "execution_plan": [response[:200]],
                        "tools_needed": [],
                        "expected_outcome": "AI response parsing failed",
                        "risk_mitigation": "Manual review required",
                        "estimated_duration": "Unknown",
                        "ai_generated": True,
                        "raw_response": response
                    }

                logger.info(f"[{self.name}] Generated execution plan for subtask {i+1}")
                results.append(result)

            execution_summary = {
                "plan": plan,
                "results": results,
                "total_subtasks": len(subtasks),
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": True
            }

            logger.info(f"[{self.name}] Execution planning complete for {len(subtasks)} subtasks")
            return execution_summary

        except Exception as e:
            logger.error(f"[{self.name}] AI action planning failed: {e}")
            # Fallback to stub
            results = []
            for subtask in plan.get("subtasks", []):
                subtask_desc = subtask if isinstance(subtask, str) else subtask.get("description", str(subtask))
                result = {
                    "subtask": subtask,
                    "execution_plan": [f"Execute '{subtask_desc}' (stub)"],
                    "tools_needed": [],
                    "expected_outcome": "Stub execution",
                    "risk_mitigation": "None",
                    "estimated_duration": "Unknown",
                    "ai_generated": False,
                    "error": str(e)
                }
                results.append(result)

            execution_summary = {
                "plan": plan,
                "results": results,
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False
            }
            logger.warning(f"[{self.name}] Using fallback stub execution")
            return execution_summary
