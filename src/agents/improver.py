# src/agents/improver.py
import asyncio
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("ImproverAgent")


class ImproverAgent:
    """Identifies optimization opportunities and drives system improvements"""

    def __init__(self):
        from src.agent_personality import AGENT_PERSONALITIES
        self.name = "Improver"
        self.specialization = "System Optimization & Continuous Improvement"
        self.responsibilities = [
            "Identify optimization opportunities",
            "Develop improvement strategies",
            "Implement system enhancements",
            "Monitor improvement effectiveness"
        ]
        self.expertise_areas = [
            "System optimization",
            "Process improvement",
            "Performance enhancement",
            "Innovation implementation"
        ]
        # Load personality
        self.personality = AGENT_PERSONALITIES.get("Improver")
        self.expertise_areas = [
            "Self-healing system design",
            "Magic system integration and rituals",
            "System resilience and fault tolerance",
            "Continuous improvement strategies"
        ]

    async def improve(self, analysis: Dict[str, Any], learned_patterns: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Use AI to generate sophisticated improvement suggestions based on analysis and learned patterns.
        Includes magic-based self-healing recommendations.
        """
        logger.debug("[%s] Improving system based on analysis and learned patterns", self.name)

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Prepare analysis data for AI
            health_score = analysis.get("health_score", 50)
            bottlenecks = learned_patterns.get("bottlenecks", [])
            recommendations = analysis.get("recommendations", [])
            alerts = analysis.get("alerts", [])

            # Get personality-enhanced prompt
            personality_prompt = self.personality.get_personality_prompt() if self.personality else ""

            prompt = f"""{personality_prompt}

System Analysis:
- Health Score: {health_score}/100
- Bottlenecks: {len(bottlenecks)}
- Existing Recommendations: {len(recommendations)}
- Active Alerts: {len(alerts)}

Bottlenecks: {bottlenecks[:5]}  # Show first 5
Current Recommendations: {recommendations[:5]}  # Show first 5
Alerts: {alerts[:3]}  # Show first 3

The system has a magic self-healing system with:
- Blue Spark Healing: Energy-based healing for failures
- Acorn Vitality Boost: Performance enhancement (10-50% improvement)
- Fairy Shield: Protection during critical operations
- Circuit Breakers: Automatic failure recovery
- Learning Preferences: DPO-style pattern learning

Based on this analysis, generate specific, actionable improvement suggestions. Consider:

1. Magic system integration opportunities
2. Circuit breaker implementations
3. Performance optimization strategies
4. Self-healing enhancements
5. Pattern-based improvements
6. Architectural recommendations

Provide your response as a JSON object with this structure:
{{
    "magic_improvements": [
        {{
            "type": "healing|boost|shield|circuit_breaker",
            "target": "component_name",
            "description": "What to improve",
            "expected_impact": "Expected benefit",
            "implementation_effort": "Low/Medium/High"
        }}
    ],
    "system_optimizations": [
        "Specific optimization suggestion 1",
        "Specific optimization suggestion 2"
    ],
    "architectural_changes": [
        "Suggested architectural improvement"
    ],
    "monitoring_enhancements": [
        "Additional monitoring to implement"
    ],
    "priority_actions": [
        "High-priority action item 1",
        "High-priority action item 2"
    ],
    "long_term_vision": "Strategic improvement direction"
}}

{self.personality.get_communication_prompt() if self.personality else 'Focus on practical, implementable suggestions'} that leverage the magic system capabilities."""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name=provider or "grok",  # Use specified provider or default to Grok
                conversation_id=f"improver_{hash(str(analysis) + str(learned_patterns))}"
            )

            # Parse JSON response
            try:
                improvement_data = json.loads(response)
                
                # Parse fields that might be stringified JSON arrays
                magic_improvements = improvement_data.get("magic_improvements", [])
                if isinstance(magic_improvements, str) and magic_improvements.strip().startswith('['):
                    try:
                        magic_improvements = json.loads(magic_improvements)
                    except json.JSONDecodeError:
                        magic_improvements = []
                
                system_optimizations = improvement_data.get("system_optimizations", [])
                if isinstance(system_optimizations, str) and system_optimizations.strip().startswith('['):
                    try:
                        system_optimizations = json.loads(system_optimizations)
                    except json.JSONDecodeError:
                        system_optimizations = []
                
                architectural_changes = improvement_data.get("architectural_changes", [])
                if isinstance(architectural_changes, str) and architectural_changes.strip().startswith('['):
                    try:
                        architectural_changes = json.loads(architectural_changes)
                    except json.JSONDecodeError:
                        architectural_changes = []
                
                monitoring_enhancements = improvement_data.get("monitoring_enhancements", [])
                if isinstance(monitoring_enhancements, str) and monitoring_enhancements.strip().startswith('['):
                    try:
                        monitoring_enhancements = json.loads(monitoring_enhancements)
                    except json.JSONDecodeError:
                        monitoring_enhancements = []
                
                priority_actions = improvement_data.get("priority_actions", [])
                if isinstance(priority_actions, str) and priority_actions.strip().startswith('['):
                    try:
                        priority_actions = json.loads(priority_actions)
                    except json.JSONDecodeError:
                        priority_actions = []
                
                result = {
                    "magic_improvements": magic_improvements,
                    "system_optimizations": system_optimizations,
                    "architectural_changes": architectural_changes,
                    "monitoring_enhancements": monitoring_enhancements,
                    "priority_actions": priority_actions,
                    "long_term_vision": improvement_data.get("long_term_vision", "Continuous improvement through magic integration"),
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                result = {
                    "magic_improvements": [
                        {"type": "healing", "description": "Enable blue spark healing", "target": "validation_failures"}
                    ],
                    "system_optimizations": ["Implement circuit breakers", "Add performance monitoring"],
                    "architectural_changes": ["Integrate magic system deeper"],
                    "monitoring_enhancements": ["Track healing success rates"],
                    "priority_actions": ["Review AI response manually"],
                    "long_term_vision": "Full magic system integration",
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True,
                    "raw_response": response
                }

            logger.info(f"[{self.name}] AI-generated improvements: {len(result['magic_improvements'])} magic suggestions")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] AI improvement generation failed: {e}")
            # Fallback to basic suggestions
            suggestions = {}

            # Analyze bottlenecks from learned patterns
            if "bottlenecks" in learned_patterns:
                for bottleneck in learned_patterns["bottlenecks"]:
                    if bottleneck["type"] == "validation_failure":
                        suggestions["magic_healing"] = "Enable blue spark healing for validation failures"
                    elif bottleneck["type"] == "execution_error":
                        suggestions["circuit_breaker"] = "Implement circuit breaker for execution errors"
                    elif bottleneck["type"] == "performance_bottleneck":
                        suggestions["acorn_boost"] = "Apply acorn vitality boost for performance"

            # Add success pattern reinforcement
            if learned_patterns.get("success_paths"):
                suggestions["pattern_reinforcement"] = f"Reinforce {len(learned_patterns['success_paths'])} successful patterns"

            # Include magic system recommendations
            suggestions.update({
                "fairy_shield": "Activate fairy shield for protection during high-risk operations",
                "magic_recharge": "Monitor energy levels and implement automatic recharging",
                "ritual_blessings": "Use holly blessing rituals for critical task success"
            })

            result = {
                "suggestions": suggestions,
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }
            logger.warning(f"[{self.name}] Using fallback basic improvement suggestions")
            return result