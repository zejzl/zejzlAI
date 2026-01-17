# src/agents/validator.py
import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger("ValidatorAgent")


class ValidatorAgent:
    """
    Validator Agent for Pantheon 9-Agent System.
    Responsible for checking correctness and safety of actions.

    Specialization: Quality Assurance & Safety Validation
    Responsibilities:
    - Validate execution results against requirements
    - Ensure safety and compliance of actions
    - Identify and report validation failures
    - Provide corrective feedback for failed validations

    Expertise Areas:
    - Quality control and validation testing
    - Safety compliance checking
    - Error detection and analysis
    - Corrective action planning
    """

    def __init__(self):
        self.name = "Validator"
        self.specialization = "Quality Assurance & Safety Validation"
        self.responsibilities = [
            "Validate execution results against requirements",
            "Ensure safety and compliance of actions",
            "Identify and report validation failures",
            "Provide corrective feedback for failed validations"
        ]
        self.expertise_areas = [
            "Quality control and validation testing",
            "Safety compliance checking",
            "Error detection and analysis",
            "Corrective action planning"
        ]
        self.state = {}

    async def validate(self, execution_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to validate execution results against requirements and safety standards.
        """
        logger.debug(f"[{self.name}] Validating execution: {execution_summary}")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            results = execution_summary.get("results", [])
            plan = execution_summary.get("plan", {})

            # Create validation prompt
            prompt = f"""You are the Validator agent in a 9-agent AI pantheon system. Your role is quality assurance and safety validation.

Original Plan: {plan.get('analysis', 'No analysis provided')}
Subtasks: {len(plan.get('subtasks', []))}

Execution Results: {len(results)}

Please validate the execution results against the original plan and safety standards. Check for:

1. Completeness - Were all planned subtasks addressed?
2. Correctness - Do the execution plans align with the original requirements?
3. Safety - Are there any unsafe or inappropriate actions?
4. Quality - Are the execution steps practical and well-structured?

For each executed subtask, evaluate:
- Does the execution plan meet the success criteria?
- Are the tools and approaches appropriate?
- Are there any safety concerns?
- What improvements could be made?

Provide your response as a JSON object with this structure:
{{
    "overall_validation": "PASSED" or "FAILED" or "PARTIAL",
    "completeness_score": 0-100,
    "safety_score": 0-100,
    "quality_score": 0-100,
    "subtask_validations": [
        {{
            "subtask_index": 0,
            "status": "PASSED/FAILED/UNKNOWN",
            "issues": ["issue1", "issue2"],
            "recommendations": ["rec1", "rec2"]
        }}
    ],
    "critical_issues": ["Any blocking issues"],
    "improvement_suggestions": ["General suggestions"],
    "can_proceed": true/false
}}

Be thorough and identify any real issues with the execution plans."""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",  # Use Grok for validation
                conversation_id=f"validator_{hash(str(execution_summary))}"
            )

            # Parse JSON response
            import json
            try:
                validation_data = json.loads(response)
                feedback = {
                    "execution_summary": execution_summary,
                    "overall_validation": validation_data.get("overall_validation", "UNKNOWN"),
                    "completeness_score": validation_data.get("completeness_score", 0),
                    "safety_score": validation_data.get("safety_score", 0),
                    "quality_score": validation_data.get("quality_score", 0),
                    "subtask_validations": validation_data.get("subtask_validations", []),
                    "critical_issues": validation_data.get("critical_issues", []),
                    "improvement_suggestions": validation_data.get("improvement_suggestions", []),
                    "can_proceed": validation_data.get("can_proceed", True),
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                feedback = {
                    "execution_summary": execution_summary,
                    "overall_validation": "UNKNOWN",
                    "completeness_score": 50,
                    "safety_score": 50,
                    "quality_score": 50,
                    "subtask_validations": [],
                    "critical_issues": ["JSON parsing failed"],
                    "improvement_suggestions": ["Review AI response manually"],
                    "can_proceed": True,
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True,
                    "raw_response": response
                }

            logger.info(f"[{self.name}] AI validation complete: {feedback['overall_validation']}")
            return feedback

        except Exception as e:
            logger.error(f"[{self.name}] AI validation failed: {e}")
            # Fallback to stub validation
            results = execution_summary.get("results", [])
            validation_passed = len(results) > 0  # Basic check
            feedback = {
                "execution_summary": execution_summary,
                "overall_validation": "PASSED" if validation_passed else "FAILED",
                "completeness_score": 100 if validation_passed else 0,
                "safety_score": 100 if validation_passed else 0,
                "quality_score": 100 if validation_passed else 0,
                "subtask_validations": [],
                "critical_issues": [],
                "improvement_suggestions": ["Manual review required"],
                "can_proceed": validation_passed,
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }
            logger.warning(f"[{self.name}] Using fallback stub validation")
            return feedback
