# src/agents/analyzer.py
import asyncio
import logging
from typing import Any, Dict, List

logger = logging.getLogger("AnalyzerAgent")


class AnalyzerAgent:
    """
    Analyzer Agent for Pantheon 9-Agent System.
    Responsible for gathering metrics and performance analytics.

    Specialization: Metrics Collection & Performance Analysis
    Responsibilities:
    - Collect system and agent performance metrics
    - Analyze trends and identify patterns
    - Generate performance reports and insights
    - Monitor system health and efficiency

    Expertise Areas:
    - Performance metrics collection
    - Data analysis and trend identification
    - Report generation and visualization
    - System health monitoring
    """

    def __init__(self):
        self.name = "Analyzer"
        self.specialization = "Metrics Collection & Performance Analysis"
        self.responsibilities = [
            "Collect system and agent performance metrics",
            "Analyze trends and identify patterns",
            "Generate performance reports and insights",
            "Monitor system health and efficiency"
        ]
        self.expertise_areas = [
            "Performance metrics collection",
            "Data analysis and trend identification",
            "Report generation and visualization",
            "System health monitoring"
        ]

    async def analyze(self, memory_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Use AI to analyze system performance and generate insights from memory events.
        """
        logger.debug(f"[{self.name}] Analyzing {len(memory_events)} events")

        try:
            # Get AI provider bus
            from base import get_ai_provider_bus
            ai_bus = await get_ai_provider_bus()

            # Basic metrics calculation
            metrics = {}
            event_types = []
            timestamps = []

            for event in memory_events:
                typ = event.get("type", "unknown")
                metrics[typ] = metrics.get(typ, 0) + 1
                event_types.append(typ)
                if "timestamp" in event:
                    timestamps.append(event["timestamp"])

            # Create analysis prompt
            prompt = f"""You are the Analyzer agent in a 9-agent AI pantheon system. Your role is performance analysis and metrics generation.

Analyzing {len(memory_events)} system events with the following breakdown:
{metrics}

Event types observed: {list(set(event_types))}

Please analyze this data and provide insights about system performance, patterns, and optimization opportunities.

Consider:
1. Event distribution and frequency patterns
2. System throughput and efficiency metrics
3. Potential bottlenecks or areas for improvement
4. Success rates and failure patterns
5. Temporal patterns (if timestamps available)

Provide your response as a JSON object with this structure:
{{
    "performance_metrics": {{
        "total_events": 0,
        "events_per_type": {{"type": count}},
        "average_events_per_minute": 0.0,
        "peak_activity_periods": ["period1", "period2"]
    }},
    "efficiency_analysis": {{
        "throughput_score": 0-100,
        "bottleneck_indicators": ["indicator1"],
        "optimization_opportunities": ["opp1", "opp2"]
    }},
    "pattern_insights": {{
        "success_patterns": ["pattern1"],
        "failure_patterns": ["pattern1"],
        "trend_analysis": "Analysis of trends"
    }},
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "health_score": 0-100,
    "alerts": ["Any critical issues"]
}}

Be analytical and provide actionable insights based on the event data."""

            # Call AI
            response = await ai_bus.send_message(
                content=prompt,
                provider_name="grok",  # Use Grok for analysis
                conversation_id=f"analyzer_{hash(str(memory_events))}"
            )

            # Parse JSON response
            import json
            try:
                analysis_data = json.loads(response)
                result = {
                    "basic_metrics": metrics,
                    "performance_metrics": analysis_data.get("performance_metrics", {}),
                    "efficiency_analysis": analysis_data.get("efficiency_analysis", {}),
                    "pattern_insights": analysis_data.get("pattern_insights", {}),
                    "recommendations": analysis_data.get("recommendations", []),
                    "health_score": analysis_data.get("health_score", 50),
                    "alerts": analysis_data.get("alerts", []),
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                result = {
                    "basic_metrics": metrics,
                    "performance_metrics": {"total_events": len(memory_events)},
                    "efficiency_analysis": {"throughput_score": 50},
                    "pattern_insights": {"trend_analysis": "AI parsing failed"},
                    "recommendations": ["Review raw AI response"],
                    "health_score": 50,
                    "alerts": ["JSON parsing failed"],
                    "timestamp": asyncio.get_event_loop().time(),
                    "ai_generated": True,
                    "raw_response": response
                }

            logger.info(f"[{self.name}] AI analysis complete: health score {result.get('health_score', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] AI analysis failed: {e}")
            # Fallback to basic metrics
            metrics = {}
            for event in memory_events:
                typ = event.get("type", "unknown")
                metrics[typ] = metrics.get(typ, 0) + 1

            result = {
                "basic_metrics": metrics,
                "timestamp": asyncio.get_event_loop().time(),
                "ai_generated": False,
                "error": str(e)
            }
            logger.warning(f"[{self.name}] Using fallback basic analysis")
            return result
