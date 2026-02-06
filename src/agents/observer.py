# src/agents/observer.py
import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("ObserverAgent")


class ObserverAgent:
    """Analyzes and decomposes tasks into manageable components"""

    def __init__(self):
        from src.agent_personality import AGENT_PERSONALITIES
        self.name = "Observer"
        self.specialization = "Task Analysis & Decomposition"
        self.responsibilities = [
            "Analyze incoming tasks for complexity and requirements",
            "Break down complex tasks into manageable subtasks",
            "Identify dependencies and constraints",
            "Provide comprehensive task understanding"
        ]
        self.expertise_areas = [
            "Task decomposition",
            "Requirement analysis",
            "Complexity assessment",
            "Dependency mapping"
        ]
        # Load personality
        self.personality = AGENT_PERSONALITIES.get("Observer")
        self.expertise_areas = [
            "API integration and data scraping",
            "Real-time monitoring and alerting",
            "Data preprocessing and filtering",
            "Environmental sensing and telemetry"
        ]
        self.state = {}

    async def observe(self, task: str, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Use AI to analyze and break down the task into observable components.
        """
        logger.debug(f"[{self.name}] Observing task: {task}")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Create observation prompt
            # Get personality-enhanced prompt
            personality_prompt = self.personality.get_personality_prompt() if self.personality else ""

            # Use TOON format for token efficiency if available
            from ai_framework import TOON_AVAILABLE
            if TOON_AVAILABLE:
                format_instruction = """Return ONLY valid TOON format:
objective: "task goal"
requirements: ["req1", "req2"]
complexity_level: "Low"
estimated_effort: "Medium" """
            else:
                format_instruction = """Return ONLY valid JSON:
{
    "objective": "task goal",
    "requirements": ["req1", "req2"],
    "complexity_level": "Low",
    "estimated_effort": "Medium"
}"""

            prompt = f"""Analyze this task: {task}

{format_instruction}"""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name=provider or "grok",  # Use specified provider or default to Grok
                conversation_id=f"observer_{hash(task)}"
            )

            logger.debug(f"[{self.name}] AI response received: {response[:500]}...")

            # Parse response with TOON support for token efficiency
            from ai_framework import decode_from_llm

            observation_data = decode_from_llm(response, use_toon=TOON_AVAILABLE)

            # If TOON/JSON parsing failed, try fallback extraction
            if not isinstance(observation_data, dict):
                def extract_json_from_text(text):
                    """Extract JSON from text that might contain extra content"""
                    # Look for JSON-like content
                    json_match = re.search(r'\{.*\}', text, re.DOTALL)
                    if json_match:
                        try:
                            return json.loads(json_match.group())
                        except json.JSONDecodeError:
                            pass

                    # Try to find JSON between triple backticks
                    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
                    if code_block_match:
                        try:
                            return json.loads(code_block_match.group(1))
                        except json.JSONDecodeError:
                            pass

                    return None

                observation_data = extract_json_from_text(response)

                # Final fallback
                if not observation_data:
                    observation_data = {
                        "objective": task[:100],
                        "requirements": ["Analysis failed - using fallback"],
                        "complexity_level": "Unknown",
                        "estimated_effort": "Unknown"
                    }
                if not observation_data:
                    raise json.JSONDecodeError("Could not parse JSON from AI response", response, 0)

            # Parse fields that might be stringified JSON arrays
            requirements = observation_data.get("requirements", [task])
            if isinstance(requirements, str) and requirements.strip().startswith('['):
                try:
                    requirements = json.loads(requirements)
                except json.JSONDecodeError:
                    requirements = [task]
            
            constraints = observation_data.get("constraints", [])
            if isinstance(constraints, str) and constraints.strip().startswith('['):
                try:
                    constraints = json.loads(constraints)
                except json.JSONDecodeError:
                    constraints = []
            
            resources_needed = observation_data.get("resources_needed", ["AI assistance"])
            if isinstance(resources_needed, str) and resources_needed.strip().startswith('['):
                try:
                    resources_needed = json.loads(resources_needed)
                except json.JSONDecodeError:
                    resources_needed = ["AI assistance"]
            
            success_criteria = observation_data.get("success_criteria", ["Task completion"])
            if isinstance(success_criteria, str) and success_criteria.strip().startswith('['):
                try:
                    success_criteria = json.loads(success_criteria)
                except json.JSONDecodeError:
                    success_criteria = ["Task completion"]
            
            potential_challenges = observation_data.get("potential_challenges", [])
            if isinstance(potential_challenges, str) and potential_challenges.strip().startswith('['):
                try:
                    potential_challenges = json.loads(potential_challenges)
                except json.JSONDecodeError:
                    potential_challenges = []
            
            observation = {
                "task": task,
                "objective": observation_data.get("objective", f"Complete: {task}"),
                "requirements": requirements,
                "constraints": constraints,
                "resources_needed": resources_needed,
                "success_criteria": success_criteria,
                "potential_challenges": potential_challenges,
                "context": observation_data.get("context", "AI-generated analysis"),
                "complexity_level": observation_data.get("complexity_level", "Medium"),
                "estimated_effort": observation_data.get("estimated_effort", "Medium"),
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": True
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
