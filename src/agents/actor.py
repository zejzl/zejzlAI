# src/agents/actor.py
import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ActorAgent")


class ActorAgent:
    """
    Actor Agent for Pantheon 9-Agent System.
    Responsible for determining how to execute subtasks and provide execution guidance.

    SPECIALIZATION: Action Planning & Execution Strategy

    EXECUTION PLANNING CAPABILITIES:
    - AI-powered execution strategy development
    - Intelligent fallback planning for reliability
    - Task-type-specific execution approaches
    - Comprehensive risk assessment and mitigation

    INTELLIGENT FALLBACK SYSTEM:
    - Rule-based execution planning when AI unavailable
    - Subtask analysis for appropriate tool selection
    - Duration estimation and resource planning
    - Risk identification and mitigation strategies

    SUPPORTED EXECUTION TYPES:
    - Research Tasks: Systematic information gathering and analysis
    - Development Tasks: Phased implementation with testing
    - Writing Tasks: Structured content creation workflow
    - Planning Tasks: Timeline creation and milestone setting
    - Testing Tasks: Comprehensive validation procedures

    EXECUTION FEATURES:
    - Tool and resource requirement identification
    - Time estimation based on task complexity
    - Risk assessment and mitigation planning
    - Step-by-step execution guidance
    - Quality assurance and validation criteria

    RESPONSIBILITIES:
    - Convert high-level plans into detailed execution steps
    - Identify required tools, resources, and skills
    - Assess execution risks and provide mitigation strategies
    - Create comprehensive execution guidance with timelines
    - Ensure execution feasibility and success probability

    EXPERTISE AREAS:
    - Execution planning and strategic sequencing
    - Resource assessment and requirement analysis
    - Risk analysis and contingency planning
    - Timeline estimation and milestone setting
    - Quality assurance and success criteria definition
    """

    def __init__(self):
        self.name = "Actor"

    async def act(self, plan: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
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

                # Call AI
                response = await ai_bus.send_message(
                    content=prompt,
                    provider_name=provider or "grok",  # Use specified provider or default to Grok
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
            # Enhanced fallback: Generate intelligent execution plans based on subtask analysis
            results = self._generate_fallback_execution_plans(plan.get("subtasks", []), str(e))
            execution_summary = {
                "plan": plan,
                "results": results,
                "total_subtasks": len(results),
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "fallback_reason": str(e),
                "fallback_type": "intelligent_rule_based"
            }
            logger.warning(f"[{self.name}] Using intelligent fallback execution planning")
            return execution_summary

    def _generate_fallback_execution_plans(self, subtasks: List[str], error_reason: str) -> List[Dict[str, Any]]:
        """
        Generate intelligent execution plans for subtasks based on their content analysis.
        Provides realistic execution steps, tools, and estimates without AI.
        """
        results = []

        for i, subtask in enumerate(subtasks):
            subtask_desc = subtask if isinstance(subtask, str) else subtask.get("description", str(subtask))
            subtask_lower = subtask_desc.lower()

            # Analyze subtask type and generate appropriate execution plan
            if any(keyword in subtask_lower for keyword in ['research', 'investigate', 'analyze', 'gather']):
                # Research/analysis subtasks
                execution_plan = [
                    f"Identify relevant sources and data for {subtask_desc}",
                    f"Collect and organize information related to {subtask_desc}",
                    f"Analyze findings and extract key insights",
                    f"Document results and prepare summary"
                ]
                tools_needed = ["search_engines", "note_taking", "data_analysis"]
                estimated_duration = "2-4 hours"
                risks = ["Information overload", "Source reliability issues"]

            elif any(keyword in subtask_lower for keyword in ['create', 'build', 'develop', 'implement']):
                # Creation/development subtasks
                execution_plan = [
                    f"Design approach and architecture for {subtask_desc}",
                    f"Implement core functionality for {subtask_desc}",
                    f"Test implementation and fix issues",
                    f"Refine and optimize the solution"
                ]
                tools_needed = ["development_tools", "testing_frameworks", "version_control"]
                estimated_duration = "4-8 hours"
                risks = ["Technical complexity", "Integration challenges"]

            elif any(keyword in subtask_lower for keyword in ['write', 'document', 'report']):
                # Writing/documentation subtasks
                execution_plan = [
                    f"Outline content structure for {subtask_desc}",
                    f"Write initial draft with key information",
                    f"Review and edit for clarity and accuracy",
                    f"Format and finalize the document"
                ]
                tools_needed = ["word_processing", "research_tools", "editing_tools"]
                estimated_duration = "2-6 hours"
                risks = ["Content organization", "Time estimation accuracy"]

            elif any(keyword in subtask_lower for keyword in ['plan', 'organize', 'schedule']):
                # Planning/organizational subtasks
                execution_plan = [
                    f"Define objectives and deliverables for {subtask_desc}",
                    f"Break down into specific actionable items",
                    f"Estimate time and resource requirements",
                    f"Create timeline and milestone schedule"
                ]
                tools_needed = ["project_management", "scheduling_tools", "resource_planning"]
                estimated_duration = "1-3 hours"
                risks = ["Scope creep", "Resource availability"]

            elif any(keyword in subtask_lower for keyword in ['test', 'validate', 'verify']):
                # Testing/validation subtasks
                execution_plan = [
                    f"Define test criteria and success metrics for {subtask_desc}",
                    f"Execute tests systematically",
                    f"Analyze results and identify issues",
                    f"Document findings and recommendations"
                ]
                tools_needed = ["testing_tools", "monitoring_tools", "reporting_tools"]
                estimated_duration = "1-4 hours"
                risks = ["Incomplete test coverage", "False results"]

            else:
                # Generic fallback for unknown subtask types
                execution_plan = [
                    f"Analyze requirements for {subtask_desc}",
                    f"Execute the main activities for {subtask_desc}",
                    f"Verify completion and quality of {subtask_desc}"
                ]
                tools_needed = ["basic_tools", "verification_methods"]
                estimated_duration = "1-2 hours"
                risks = ["Unclear requirements", "Quality assessment"]

            # Create result entry
            result = {
                "subtask": subtask,
                "execution_plan": execution_plan,
                "tools_needed": tools_needed,
                "expected_outcome": f"Successfully complete {subtask_desc} with quality results",
                "risk_mitigation": f"Address identified risks: {', '.join(risks[:2])}",
                "estimated_duration": estimated_duration,
                "ai_generated": False,
                "fallback_reason": error_reason,
                "planning_method": "rule_based_analysis"
            }
            results.append(result)

        return results
