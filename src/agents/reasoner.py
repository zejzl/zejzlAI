# src/agents/reasoner.py
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ReasonerAgent")


class ReasonerAgent:
    """
    Reasoner Agent for Pantheon 9-Agent System.
    Responsible for creating comprehensive execution plans from observations.

    SPECIALIZATION: Strategic Planning & Logic

    PLANNING CAPABILITIES:
    - AI-powered reasoning for complex task analysis
    - Intelligent fallback planning for reliability
    - Task type classification and appropriate strategy selection
    - Risk assessment and dependency identification
    - Success criteria definition and milestone planning

    INTELLIGENT FALLBACK SYSTEM:
    - Rule-based planning when AI is unavailable
    - Task-type-specific subtask generation
    - Requirement-driven plan enhancement
    - Complexity-aware step breakdown

    SUPPORTED TASK TYPES:
    - Research & Analysis: Multi-step investigation plans
    - Creation & Development: Phased implementation strategies
    - Writing & Documentation: Structured content creation
    - Planning & Organization: Comprehensive project plans
    - Problem Solving: Systematic troubleshooting approaches

    RESPONSIBILITIES:
    - Analyze observations and create detailed execution plans
    - Break down complex tasks into logical, manageable subtasks
    - Identify dependencies, risks, and success criteria
    - Provide clear reasoning for planning decisions
    - Ensure plan reliability with intelligent fallbacks

    EXPERTISE AREAS:
    - Task decomposition and strategic planning
    - Logic-based reasoning and requirement analysis
    - Risk assessment and mitigation strategies
    - Adaptive planning with AI and rule-based approaches
    - Plan validation and optimization
    """

    def __init__(self):
        self.name = "Reasoner"
        self.personality = None

    async def reason(self, observation: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
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
                provider_name=provider or "grok",  # Use specified provider or default to Grok
                conversation_id=f"reasoner_{hash(str(observation))}"
            )

            # Parse JSON response
            try:
                plan_data = json.loads(response)
                
                # Parse fields that might be stringified JSON arrays
                subtasks = plan_data.get("subtasks", [])
                if isinstance(subtasks, str) and subtasks.strip().startswith('['):
                    try:
                        subtasks = json.loads(subtasks)
                    except json.JSONDecodeError:
                        subtasks = []
                
                risks = plan_data.get("risks", [])
                if isinstance(risks, str) and risks.strip().startswith('['):
                    try:
                        risks = json.loads(risks)
                    except json.JSONDecodeError:
                        risks = []
                
                plan = {
                    "observation": observation,
                    "analysis": plan_data.get("analysis", "Analysis not provided"),
                    "subtasks": subtasks,
                    "risks": risks,
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
            # Enhanced fallback: Generate intelligent plan based on observation analysis
            plan = self._generate_fallback_plan(observation, str(e))
            logger.warning(f"[{self.name}] Using intelligent fallback plan")
            return plan

    def _generate_fallback_plan(self, observation: Dict[str, Any], error_reason: str) -> Dict[str, Any]:
        """
        Generate an intelligent fallback plan based on observation analysis.
        Even without AI, we can create reasonable plans for common task types.
        """
        task = observation.get('task', '').lower()
        requirements = observation.get('requirements', [])
        complexity = observation.get('complexity_level', 'Medium')

        subtasks = []

        # Analyze task type and generate appropriate subtasks
        if any(keyword in task for keyword in ['research', 'investigate', 'analyze', 'study']):
            # Research/analysis tasks
            subtasks = [
                "Gather information and data sources",
                "Analyze collected information for key insights",
                "Synthesize findings into actionable recommendations",
                "Validate results and identify limitations"
            ]
        elif any(keyword in task for keyword in ['create', 'build', 'develop', 'implement']):
            # Creation/development tasks
            subtasks = [
                "Define requirements and specifications",
                "Design solution architecture and approach",
                "Implement core functionality",
                "Test and validate implementation",
                "Document and prepare for deployment"
            ]
        elif any(keyword in task for keyword in ['write', 'document', 'report']):
            # Writing/documentation tasks
            subtasks = [
                "Research and gather relevant information",
                "Outline document structure and key points",
                "Write initial draft with comprehensive content",
                "Review and edit for clarity and accuracy",
                "Format and finalize document"
            ]
        elif any(keyword in task for keyword in ['plan', 'organize', 'schedule']):
            # Planning/organizational tasks
            subtasks = [
                "Identify objectives and success criteria",
                "Break down task into manageable components",
                "Assess resources and timeline requirements",
                "Create detailed execution plan with milestones",
                "Identify risks and contingency plans"
            ]
        else:
            # Generic fallback for unknown task types
            if complexity == 'Low':
                subtasks = [
                    "Analyze task requirements and constraints",
                    "Execute primary task activities",
                    "Verify completion and quality"
                ]
            elif complexity == 'High':
                subtasks = [
                    "Conduct thorough task analysis and planning",
                    "Break down complex task into phases",
                    "Execute first phase with detailed monitoring",
                    "Evaluate progress and adjust approach",
                    "Complete remaining phases iteratively",
                    "Conduct final validation and documentation"
                ]
            else:  # Medium complexity
                subtasks = [
                    "Analyze task requirements and approach",
                    "Execute main task activities",
                    "Monitor progress and quality",
                    "Complete remaining work and verification"
                ]

        # Enhance subtasks based on requirements
        if requirements:
            if any('research' in req.lower() or 'data' in req.lower() for req in requirements):
                if "Research and gather information" not in subtasks:
                    subtasks.insert(0, "Research and gather required information")

            if any('test' in req.lower() or 'validate' in req.lower() for req in requirements):
                if not any('test' in subtask.lower() or 'validate' in subtask.lower() for subtask in subtasks):
                    subtasks.append("Test and validate results")

            if any('document' in req.lower() or 'report' in req.lower() for req in requirements):
                if not any('document' in subtask.lower() for subtask in subtasks):
                    subtasks.append("Document results and create report")

        # Create structured plan
        plan = {
            "observation": observation,
            "analysis": {
                "task_type": self._classify_task_type(task),
                "complexity_level": complexity,
                "key_requirements": requirements[:3],  # Top 3 requirements
                "estimated_steps": len(subtasks),
                "reasoning_approach": "rule-based_fallback"
            },
            "subtasks": subtasks,
            "approach": f"Structured {len(subtasks)}-step approach based on task analysis",
            "risks": [
                "May not capture all nuances without AI reasoning",
                "Could miss creative or unconventional approaches"
            ],
            "success_criteria": [
                "Complete all planned subtasks",
                "Meet identified requirements",
                "Deliver quality results within reasonable time"
            ],
            "timestamp": asyncio.get_event_loop().time(),
            "ai_generated": False,
            "fallback_reason": error_reason,
            "fallback_type": "intelligent_rule_based"
        }

        return plan

    def _classify_task_type(self, task_description: str) -> str:
        """Classify task type based on keywords and patterns."""
        task_lower = task_description.lower()

        if any(word in task_lower for word in ['research', 'investigate', 'analyze', 'study', 'examine']):
            return "research/analysis"
        elif any(word in task_lower for word in ['create', 'build', 'develop', 'implement', 'design']):
            return "creation/development"
        elif any(word in task_lower for word in ['write', 'document', 'report', 'describe']):
            return "writing/documentation"
        elif any(word in task_lower for word in ['plan', 'organize', 'schedule', 'coordinate']):
            return "planning/organization"
        elif any(word in task_lower for word in ['fix', 'repair', 'resolve', 'troubleshoot']):
            return "problem_solving/maintenance"
        elif any(word in task_lower for word in ['learn', 'train', 'teach', 'educate']):
            return "learning/education"
        elif any(word in task_lower for word in ['review', 'evaluate', 'assess', 'audit']):
            return "review/evaluation"
        else:
            return "general_task"
