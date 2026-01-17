# src/agents/observer.py
import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger("ObserverAgent")


class ObserverAgent:
    """
    Observer Agent for Pantheon 9-Agent System.
    Responsible for gathering observations from environment, APIs, or files.

    Specialization: Data Collection & Environmental Monitoring
    Responsibilities:
    - Gather real-time data from various sources
    - Monitor system environment and external APIs
    - Process and filter relevant information
    - Provide contextual data for decision making

    Expertise Areas:
    - API integration and data scraping
    - Real-time monitoring and alerting
    - Data preprocessing and filtering
    - Environmental sensing and telemetry
    """

    def __init__(self):
        self.name = "Observer"
        self.specialization = "Data Collection & Environmental Monitoring"
        self.responsibilities = [
            "Gather real-time data from various sources",
            "Monitor system environment and external APIs",
            "Process and filter relevant information",
            "Provide contextual data for decision making"
        ]
        self.expertise_areas = [
            "API integration and data scraping",
            "Real-time monitoring and alerting",
            "Data preprocessing and filtering",
            "Environmental sensing and telemetry"
        ]
        self.state = {}

    async def observe(self, task: str) -> Dict[str, Any]:
        """
        Use AI to analyze and break down the task into observable components.
        """
        logger.debug(f"[{self.name}] Observing task: {task}")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Create observation prompt
            prompt = f"""You are the Observer agent in a 9-agent AI pantheon system. Your role is initial task perception and analysis.

Task to observe: {task}

As the Observer, analyze this task and provide a comprehensive observation that will inform the rest of the pantheon. Consider:

1. What is the core objective of this task?
2. What are the key requirements and constraints?
3. What resources or information will be needed?
4. What are the success criteria?
5. What potential challenges or complexities exist?
6. What context or background information is relevant?

Provide your response as a JSON object with this structure:
{{
    "task": "The original task",
    "objective": "Clear statement of what needs to be accomplished",
    "requirements": [
        "Requirement 1",
        "Requirement 2"
    ],
    "constraints": [
        "Constraint 1",
        "Constraint 2"
    ],
    "resources_needed": [
        "Resource 1",
        "Resource 2"
    ],
    "success_criteria": [
        "Criterion 1",
        "Criterion 2"
    ],
    "potential_challenges": [
        "Challenge 1",
        "Challenge 2"
    ],
    "context": "Relevant background information",
    "complexity_level": "Low/Medium/High",
    "estimated_effort": "Rough effort estimate"
}}

Be thorough and analytical. Your observation will guide the entire pantheon's approach to this task."""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",  # Use Grok for observation
                conversation_id=f"observer_{hash(task)}"
            )

            # Parse JSON response
            import json
            try:
                observation_data = json.loads(response)
                observation = {
                    "task": task,
                    "objective": observation_data.get("objective", "Objective not specified"),
                    "requirements": observation_data.get("requirements", []),
                    "constraints": observation_data.get("constraints", []),
                    "resources_needed": observation_data.get("resources_needed", []),
                    "success_criteria": observation_data.get("success_criteria", []),
                    "potential_challenges": observation_data.get("potential_challenges", []),
                    "context": observation_data.get("context", "No additional context"),
                    "complexity_level": observation_data.get("complexity_level", "Medium"),
                    "estimated_effort": observation_data.get("estimated_effort", "Unknown"),
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                observation = {
                    "task": task,
                    "objective": f"Complete: {task}",
                    "requirements": [task],
                    "constraints": [],
                    "resources_needed": ["AI assistance"],
                    "success_criteria": ["Task completion"],
                    "potential_challenges": ["AI response parsing failed"],
                    "context": "Task analysis failed",
                    "complexity_level": "Medium",
                    "estimated_effort": "Unknown",
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True,
                    "raw_response": response
                }

            logger.info(f"[{self.name}] AI observation complete: {observation['complexity_level']} complexity")
            return observation

        except Exception as e:
            logger.error(f"[{self.name}] AI observation failed: {e}")
            # Fallback to basic observation
            observation = {
                "task": task,
                "objective": f"Complete: {task}",
                "requirements": [task],
                "constraints": [],
                "resources_needed": [],
                "success_criteria": [f"Successfully complete '{task}'"],
                "potential_challenges": [],
                "context": "Basic observation due to AI failure",
                "complexity_level": "Unknown",
                "estimated_effort": "Unknown",
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }
            logger.warning(f"[{self.name}] Using fallback basic observation")
            return observation
