# src/agents/actor.py
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("ActorAgent")


class ActorAgent:
    """
    Actor Agent for Pantheon 9-Agent System.
    Responsible for executing subtasks provided by Reasoner.

    Specialization: Action Execution & Tool Integration
    Responsibilities:
    - Execute planned subtasks in sequence
    - Integrate with external tools and services
    - Handle execution errors and retries
    - Provide detailed execution feedback

    Expertise Areas:
    - Tool integration and API calling
    - Sequential task execution
    - Error handling and recovery
    - Execution monitoring and logging
    """

    def __init__(self):
        self.name = "Actor"
        self.specialization = "Action Execution & Tool Integration"
        self.responsibilities = [
            "Execute planned subtasks in sequence",
            "Integrate with external tools and services",
            "Handle execution errors and retries",
            "Provide detailed execution feedback"
        ]
        self.expertise_areas = [
            "Tool integration and API calling",
            "Sequential task execution",
            "Error handling and recovery",
            "Execution monitoring and logging"
        ]
        self.state = {}

    async def act(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to determine how to execute subtasks and provide execution guidance.
        """
        logger.debug(f"[{self.name}] Acting on plan: {plan}")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            subtasks = plan.get("subtasks", [])
            results = []

            for i, subtask in enumerate(subtasks):
                # Create prompt for action execution
                subtask_desc = subtask if isinstance(subtask, str) else subtask.get("description", str(subtask))

                prompt = f"""You are the Actor agent in a 9-agent AI pantheon system. Your role is action execution and tool integration.

Subtask to execute: {subtask_desc}

Based on the Reasoner's plan, provide specific, actionable steps for executing this subtask. Consider:
1. What concrete actions need to be taken
2. What tools or methods should be used
3. How to verify successful completion
4. Any potential issues and how to handle them

Provide your response as a JSON object with this structure:
{{
    "execution_steps": [
        "Step 1: Specific action to take",
        "Step 2: Next action...",
        "Step 3: Verification step"
    ],
    "tools_needed": ["tool1", "tool2"],
    "expected_outcome": "What success looks like",
    "risk_mitigation": "How to handle potential issues",
    "estimated_duration": "Time estimate"
}}

Be practical and specific. Focus on executable actions rather than abstract planning."""

                # Call AI
                response = await ai_bus.send_message(
                    content=prompt,
                    provider_name="grok",  # Use Grok for action planning
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
