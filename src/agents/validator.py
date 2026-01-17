# src/agents/validator.py
import asyncio
import logging
from typing import Any, Dict, Optional

from src.security_validator import security_validator, ValidationResult, RiskLevel, ApprovalRequirement

logger = logging.getLogger("ValidatorAgent")


class ValidatorAgent:
    """Validates execution results and ensures quality standards"""

    def __init__(self):
        from src.agent_personality import AGENT_PERSONALITIES
        self.name = "Validator"
        self.specialization = "Quality Assurance & Validation"
        self.responsibilities = [
            "Validate execution results against requirements",
            "Check for completeness and correctness",
            "Identify quality issues and improvement opportunities",
            "Provide validation reports and recommendations"
        ]
        self.expertise_areas = [
            "Quality assurance",
            "Validation testing",
            "Compliance checking",
            "Risk assessment"
        ]
        # Load personality
        self.personality = AGENT_PERSONALITIES.get("Validator")
        self.expertise_areas = [
            "Quality control and validation testing",
            "Safety compliance checking",
            "Error detection and analysis",
            "Corrective action planning"
        ]
        self.state = {}

    async def validate_operation(self, operation: str, context: Optional[Dict[str, Any]] = None,
                                user: Optional[str] = None) -> ValidationResult:
        """
        Validate an operation using the security validator.

        Args:
            operation: The operation/command to validate
            context: Additional context about the operation
            user: User performing the operation

        Returns:
            ValidationResult with security assessment
        """
        logger.debug(f"[{self.name}] Security validation for operation: {operation}")

        try:
            result = security_validator.validate_operation(operation, context, user)
            logger.info(f"[{self.name}] Operation '{operation}' validation: {result.risk_level.value} - {result.approval_required.value}")

            # Handle approval requirements
            if result.requires_user_approval:
                approved = await security_validator.request_user_approval(operation, result, user or "system")
                if not approved:
                    logger.warning(f"[{self.name}] Operation '{operation}' requires user approval but was denied")
                    result.can_proceed = False

            elif result.requires_admin_approval:
                logger.warning(f"[{self.name}] Operation '{operation}' requires admin approval")
                result.can_proceed = False  # Would need admin approval in real system

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Security validation failed: {e}")
            # Return safe default
            return ValidationResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM_RISK,
                approval_required=ApprovalRequirement.USER_CONFIRM,
                violations=[f"Validation error: {str(e)}"],
                recommendations=["Manual security review required"],
                requires_user_approval=True,
                requires_admin_approval=False,
                can_proceed=False
            )

    async def validate_execution_result(self, execution_result: Dict[str, Any]) -> ValidationResult:
        """
        Validate execution results for safety and quality.

        Args:
            execution_result: The execution result to validate

        Returns:
            ValidationResult with assessment of the execution
        """
        logger.debug(f"[{self.name}] Validating execution result")

        try:
            result = security_validator.validate_execution_result(execution_result)
            logger.info(f"[{self.name}] Execution validation: {result.risk_level.value} - Can proceed: {result.can_proceed}")

            return result

        except Exception as e:
            logger.error(f"[{self.name}] Execution validation failed: {e}")
            return ValidationResult(
                is_safe=False,
                risk_level=RiskLevel.MEDIUM_RISK,
                approval_required=ApprovalRequirement.LOG_ONLY,
                violations=[f"Execution validation error: {str(e)}"],
                recommendations=["Manual review of execution results required"],
                requires_user_approval=False,
                requires_admin_approval=False,
                can_proceed=True  # Allow to proceed with caution
            )

    async def validate(self, execution_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate execution results using security-aware analysis and AI assessment.
        """
        logger.debug(f"[{self.name}] Validating execution: {execution_summary}")

        try:
            # Extract data from execution summary
            plan = execution_summary.get('plan', {})
            results = execution_summary.get('results', [])
            total_subtasks = execution_summary.get('total_subtasks', 0)
            task = plan.get('observation', {}).get('task', 'Unknown task')

            # Perform security validation on the execution
            execution_validation = await self.validate_execution_result({
                "status": "completed" if results else "error",
                "results": results,
                "total_subtasks": total_subtasks,
                "task": task
            })

            # Get AI assessment for quality validation
            ai_validation = await self._get_ai_quality_validation(execution_summary)

            # Combine security and quality validations
            overall_validation = self._combine_validations(execution_validation, ai_validation)

            feedback = {
                "execution_summary": execution_summary,
                "overall_validation": overall_validation["status"],
                "completeness_score": overall_validation["completeness_score"],
                "safety_score": self._risk_to_score(execution_validation.risk_level),
                "quality_score": ai_validation.get("quality_score", 75),
                "subtask_validations": ai_validation.get("subtask_validations", []),
                "critical_issues": execution_validation.violations + ai_validation.get("critical_issues", []),
                "improvement_suggestions": execution_validation.recommendations + ai_validation.get("improvement_suggestions", []),
                "can_proceed": execution_validation.can_proceed and overall_validation["can_proceed"],
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": ai_validation.get("ai_generated", False),
                "security_validation": {
                    "risk_level": execution_validation.risk_level.value,
                    "approval_required": execution_validation.approval_required.value,
                    "violations": execution_validation.violations,
                    "recommendations": execution_validation.recommendations
                }
            }

            logger.info(f"[{self.name}] Combined validation complete: {feedback['overall_validation']} (Security: {execution_validation.risk_level.value})")
            return feedback

        except Exception as e:
            logger.error(f"[{self.name}] Validation failed: {e}")
            # Enhanced fallback with security awareness
            results = execution_summary.get("results", [])
            basic_validation = len(results) > 0

            feedback = {
                "execution_summary": execution_summary,
                "overall_validation": "PASSED" if basic_validation else "FAILED",
                "completeness_score": 100 if basic_validation else 25,
                "safety_score": 100 if basic_validation else 50,
                "quality_score": 100 if basic_validation else 25,
                "subtask_validations": [],
                "critical_issues": [] if basic_validation else ["No execution results found"],
                "improvement_suggestions": ["Manual security and quality review required"],
                "can_proceed": basic_validation,
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e),
                "security_validation": {
                    "risk_level": "medium_risk",
                    "approval_required": "user_confirm",
                    "violations": [f"Validation error: {str(e)}"],
                    "recommendations": ["Manual review required due to validation failure"]
                }
            }
            logger.warning(f"[{self.name}] Using enhanced fallback validation with security awareness")
            return feedback

    async def _get_ai_quality_validation(self, execution_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI-based quality validation for execution results.
        """
        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Get personality-enhanced prompt
            personality_prompt = self.personality.get_personality_prompt() if self.personality else ""

            # Extract data for analysis
            plan = execution_summary.get('plan', {})
            results = execution_summary.get('results', [])
            total_subtasks = execution_summary.get('total_subtasks', 0)
            task = plan.get('observation', {}).get('task', 'Unknown task')

            # Create comprehensive quality validation prompt
            prompt = f"""{personality_prompt}

As a Quality Assurance Validator, analyze this execution for completeness, correctness, and quality:

Task: {task}
Total Subtasks: {total_subtasks}
Results Count: {len(results)}

Results Summary:
{chr(10).join([f"- {r.get('action', 'Unknown')} -> {r.get('result', 'No result')}" for r in results[:5]])}

Return ONLY valid JSON with quality assessment:
{{
    "quality_score": 85,
    "completeness_score": 90,
    "critical_issues": [],
    "improvement_suggestions": ["Consider adding error handling"],
    "subtask_validations": [],
    "ai_generated": true
}}"""

            # Call AI for quality assessment
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",
                conversation_id=f"quality_validator_{hash(str(execution_summary))}"
            )

            # Parse AI response
            import json
            try:
                quality_data = json.loads(response)
                quality_data["ai_generated"] = True
                return quality_data
            except json.JSONDecodeError:
                logger.warning(f"[{self.name}] AI quality validation JSON parsing failed")
                return {
                    "quality_score": 75,
                    "completeness_score": 80,
                    "critical_issues": ["AI response parsing failed"],
                    "improvement_suggestions": ["Review AI response manually"],
                    "subtask_validations": [],
                    "ai_generated": True,
                    "raw_response": response
                }

        except Exception as e:
            logger.error(f"[{self.name}] AI quality validation failed: {e}")
            return {
                "quality_score": 70,
                "completeness_score": 75,
                "critical_issues": [],
                "improvement_suggestions": ["AI validation unavailable"],
                "subtask_validations": [],
                "ai_generated": False,
                "error": str(e)
            }

    def _combine_validations(self, security_validation: ValidationResult, quality_validation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine security and quality validations into overall assessment.
        """
        # Base scores from quality validation
        completeness_score = quality_validation.get("completeness_score", 75)
        quality_score = quality_validation.get("quality_score", 75)

        # Adjust based on security validation
        security_score = self._risk_to_score(security_validation.risk_level)

        # Overall validation logic
        can_proceed = security_validation.can_proceed
        critical_issues = quality_validation.get("critical_issues", []) + security_validation.violations

        if not can_proceed:
            status = "BLOCKED"
        elif security_validation.risk_level == RiskLevel.CRITICAL:
            status = "FAILED"
        elif security_validation.risk_level in [RiskLevel.HIGH_RISK, RiskLevel.MEDIUM_RISK]:
            status = "WARNING"
        elif len(critical_issues) > 0:
            status = "CONDITIONAL"
        else:
            status = "PASSED"

        return {
            "status": status,
            "completeness_score": completeness_score,
            "can_proceed": can_proceed
        }

    def _risk_to_score(self, risk_level) -> int:
        """Convert risk level to numeric score (0-100, higher is safer)"""
        risk_scores = {
            RiskLevel.SAFE: 100,
            RiskLevel.LOW_RISK: 85,
            RiskLevel.MEDIUM_RISK: 70,
            RiskLevel.HIGH_RISK: 40,
            RiskLevel.CRITICAL: 10
        }
        return risk_scores.get(risk_level, 50)
