# src/agents/reasoner.py
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("ReasonerAgent")


class ReasonerAgent:
    """
    Reasoner Agent for Pantheon 9-Agent System.
    Responsible for generating plans and breaking tasks into subtasks.

    Specialization: Strategic Planning & Task Decomposition
    Responsibilities:
    - Analyze observations to understand task requirements
    - Generate comprehensive execution plans
    - Break complex tasks into manageable subtasks
    - Optimize task sequences for efficiency

    Expertise Areas:
    - Strategic planning and roadmap development
    - Task decomposition and workflow design
    - Resource allocation and scheduling
    - Risk assessment and contingency planning
    """

    def __init__(self):
        self.name = "Reasoner"
        self.specialization = "Strategic Planning & Task Decomposition"
        self.responsibilities = [
            "Analyze observations to understand task requirements",
            "Generate comprehensive execution plans",
            "Break complex tasks into manageable subtasks",
            "Optimize task sequences for efficiency"
        ]
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

            # Create prompt for reasoning
            task = observation.get('task', 'Unknown task')
            context = observation.get('context', '')

            prompt = f"""You are the Reasoner agent in a 9-agent AI pantheon system. Your role is strategic planning and task decomposition.

Observation: {task}
Context: {context}

As the Reasoner, analyze this observation and create a comprehensive execution plan. Break the task into logical, manageable subtasks with clear dependencies and success criteria.

Provide your response as a JSON object with this structure:
{{
    "analysis": "Brief analysis of the task requirements",
    "subtasks": [
        {{
            "id": "subtask_1",
            "description": "Clear description of what to do",
            "dependencies": ["subtask_id if any"],
            "success_criteria": "How to know this subtask is complete",
            "estimated_effort": "Low/Medium/High"
        }}
    ],
    "risks": ["Potential issues or challenges"],
    "approach": "Overall strategy for execution"
}}

Be thorough but practical. Focus on actionable steps."""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",  # Use Grok for reasoning
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
