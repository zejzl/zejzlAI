#!/usr/bin/env python3
"""
ZEJZL.NET Insight Extraction and Memory Consolidation System
Extracts insights from data, consolidates memories, and provides intelligent recommendations
"""

import asyncio
import logging
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
from pathlib import Path
import statistics
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    PERFORMANCE = "performance"
    USER_BEHAVIOR = "user_behavior"
    REVENUE = "revenue"
    TECHNICAL = "technical"
    BUSINESS = "business"
    SECURITY = "security"
    PREDICTIVE = "predictive"


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"  # < 7 days
    MEDIUM_TERM = "medium_term"  # 7-30 days
    LONG_TERM = "long_term"  # > 30 days
    PERMANENT = "permanent"  # Critical insights


class ConfidenceLevel(str, Enum):
    LOW = "low"  # < 50% confidence
    MEDIUM = "medium"  # 50-80% confidence
    HIGH = "high"  # > 80% confidence


@dataclass
class Insight:
    id: str
    type: InsightType
    title: str
    description: str
    data_source: str
    confidence: ConfidenceLevel
    impact_score: float  # 0-100
    urgency: float  # 0-100
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    related_insights: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    memory_type: MemoryType = MemoryType.MEDIUM_TERM


@dataclass
class Memory:
    id: str
    content: str
    type: MemoryType
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance_score: float = 0.0  # 0-100
    related_memories: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    id: str
    name: str
    description: str
    pattern_type: str  # "trend", "anomaly", "correlation", "seasonal"
    confidence: float  # 0-100
    frequency: float  # How often this pattern occurs
    impact: str  # "positive", "negative", "neutral"
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)


class InsightExtractionEngine:
    """Extracts insights from various data sources"""

    def __init__(self):
        self.insights: Dict[str, Insight] = {}
        self.patterns: Dict[str, Pattern] = {}
        self.initialize_database()

    def initialize_database(self):
        """Initialize insight database"""
        conn = sqlite3.connect("insights_memory.db")
        cursor = conn.cursor()

        # Insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                type TEXT,
                title TEXT,
                description TEXT,
                data_source TEXT,
                confidence TEXT,
                impact_score REAL,
                urgency REAL,
                created_at TEXT,
                expires_at TEXT,
                tags TEXT,
                related_insights TEXT,
                action_items TEXT,
                metrics TEXT,
                memory_type TEXT
            )
        """)

        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT,
                type TEXT,
                created_at TEXT,
                last_accessed TEXT,
                access_count INTEGER,
                importance_score REAL,
                related_memories TEXT,
                tags TEXT,
                metadata TEXT
            )
        """)

        # Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                pattern_type TEXT,
                confidence REAL,
                frequency REAL,
                impact TEXT,
                data_points TEXT,
                discovered_at TEXT,
                last_observed TEXT,
                recommendations TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Insight extraction database initialized")

    async def extract_insights_from_performance_data(
        self, performance_data: Dict[str, Any]
    ) -> List[Insight]:
        """Extract insights from performance monitoring data"""
        insights = []

        # CPU usage insights
        cpu_percent = performance_data.get("cpu", {}).get("percent", 0)
        if cpu_percent > 80:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.PERFORMANCE,
                    title="High CPU Usage Detected",
                    description=f"CPU usage is at {cpu_percent}%, which may indicate performance bottlenecks",
                    data_source="performance_monitor",
                    confidence=ConfidenceLevel.HIGH
                    if cpu_percent > 90
                    else ConfidenceLevel.MEDIUM,
                    impact_score=cpu_percent,
                    urgency=cpu_percent,
                    tags=["cpu", "performance", "bottleneck"],
                    action_items=[
                        "Investigate CPU-intensive processes",
                        "Consider scaling up resources",
                        "Optimize code for better CPU efficiency",
                    ],
                    metrics={"cpu_percent": cpu_percent, "threshold": 80},
                )
            )

        # Memory usage insights
        memory_percent = performance_data.get("memory", {}).get("percent", 0)
        if memory_percent > 85:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.PERFORMANCE,
                    title="High Memory Usage Alert",
                    description=f"Memory usage is at {memory_percent}%, potential memory leak or insufficient resources",
                    data_source="performance_monitor",
                    confidence=ConfidenceLevel.HIGH
                    if memory_percent > 95
                    else ConfidenceLevel.MEDIUM,
                    impact_score=memory_percent,
                    urgency=memory_percent,
                    tags=["memory", "performance", "resource"],
                    action_items=[
                        "Check for memory leaks",
                        "Monitor memory allocation patterns",
                        "Consider increasing memory resources",
                    ],
                    metrics={"memory_percent": memory_percent, "threshold": 85},
                )
            )

        # Response time insights
        response_time = performance_data.get("response_time", 0)
        if response_time > 1000:  # > 1 second
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.PERFORMANCE,
                    title="Slow Response Time Detected",
                    description=f"Response time is {response_time}ms, which may impact user experience",
                    data_source="performance_monitor",
                    confidence=ConfidenceLevel.MEDIUM,
                    impact_score=min(100, response_time / 10),
                    urgency=response_time / 10,
                    tags=["response_time", "performance", "user_experience"],
                    action_items=[
                        "Profile slow endpoints",
                        "Optimize database queries",
                        "Implement caching strategies",
                    ],
                    metrics={"response_time_ms": response_time, "threshold": 1000},
                )
            )

        return insights

    async def extract_insights_from_user_behavior(
        self, behavioral_data: Dict[str, Any]
    ) -> List[Insight]:
        """Extract insights from user behavior analytics"""
        insights = []

        # Engagement insights
        engagement_score = behavioral_data.get("engagement_score", 0)
        if engagement_score < 30:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.USER_BEHAVIOR,
                    title="Low User Engagement Detected",
                    description=f"User engagement score is {engagement_score}, indicating potential disinterest or usability issues",
                    data_source="behavioral_analytics",
                    confidence=ConfidenceLevel.MEDIUM,
                    impact_score=100 - engagement_score,
                    urgency=50,
                    tags=["engagement", "user_behavior", "retention"],
                    action_items=[
                        "Analyze user journey for friction points",
                        "Implement onboarding improvements",
                        "Add gamification or engagement features",
                    ],
                    metrics={"engagement_score": engagement_score, "threshold": 30},
                )
            )

        # Churn risk insights
        risk_score = behavioral_data.get("risk_score", 0)
        if risk_score > 70:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.USER_BEHAVIOR,
                    title="High Churn Risk Identified",
                    description=f"User has {risk_score}% churn risk, immediate intervention recommended",
                    data_source="behavioral_analytics",
                    confidence=ConfidenceLevel.HIGH
                    if risk_score > 85
                    else ConfidenceLevel.MEDIUM,
                    impact_score=risk_score,
                    urgency=risk_score,
                    tags=["churn", "retention", "risk"],
                    action_items=[
                        "Reach out to user with personalized support",
                        "Offer retention incentives",
                        "Identify and address pain points",
                    ],
                    metrics={"risk_score": risk_score, "threshold": 70},
                )
            )

        # Feature usage insights
        features_used = behavioral_data.get("features_used", [])
        if len(features_used) < 2:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.USER_BEHAVIOR,
                    title="Limited Feature Adoption",
                    description=f"User only uses {len(features_used)} features, may need feature discovery improvements",
                    data_source="behavioral_analytics",
                    confidence=ConfidenceLevel.LOW,
                    impact_score=50,
                    urgency=30,
                    tags=["features", "adoption", "discovery"],
                    action_items=[
                        "Implement feature tutorials",
                        "Add in-app feature recommendations",
                        "Improve UI/UX for feature visibility",
                    ],
                    metrics={"features_used": len(features_used), "threshold": 2},
                )
            )

        return insights

    async def extract_insights_from_revenue_data(
        self, revenue_data: Dict[str, Any]
    ) -> List[Insight]:
        """Extract insights from revenue analytics"""
        insights = []

        # Conversion rate insights
        conversion_rate = revenue_data.get("conversion_rate", 0)
        if conversion_rate < 5:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.REVENUE,
                    title="Low Conversion Rate Alert",
                    description=f"Conversion rate is {conversion_rate}%, below industry average of 5-10%",
                    data_source="revenue_analytics",
                    confidence=ConfidenceLevel.HIGH,
                    impact_score=100 - (conversion_rate * 10),
                    urgency=80,
                    tags=["conversion", "revenue", "optimization"],
                    action_items=[
                        "Optimize trial-to-paid conversion flow",
                        "A/B test pricing and messaging",
                        "Improve value proposition communication",
                    ],
                    metrics={"conversion_rate": conversion_rate, "industry_avg": 7.5},
                )
            )

        # Churn rate insights
        churn_rate = revenue_data.get("churn_rate", 0)
        if churn_rate > 10:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.REVENUE,
                    title="High Churn Rate Warning",
                    description=f"Churn rate is {churn_rate}%, indicating customer satisfaction issues",
                    data_source="revenue_analytics",
                    confidence=ConfidenceLevel.HIGH
                    if churn_rate > 15
                    else ConfidenceLevel.MEDIUM,
                    impact_score=churn_rate * 5,
                    urgency=churn_rate * 5,
                    tags=["churn", "retention", "revenue"],
                    action_items=[
                        "Implement customer success program",
                        "Conduct exit interviews",
                        "Improve product value and support",
                    ],
                    metrics={"churn_rate": churn_rate, "threshold": 10},
                )
            )

        # MRR insights
        mrr = revenue_data.get("mrr", 0)
        if mrr < 1000:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.REVENUE,
                    title="Low MRR Growth Opportunity",
                    description=f"MRR is ${mrr}, significant growth potential available",
                    data_source="revenue_analytics",
                    confidence=ConfidenceLevel.MEDIUM,
                    impact_score=100 - (mrr / 10),
                    urgency=60,
                    tags=["mrr", "growth", "revenue"],
                    action_items=[
                        "Scale customer acquisition",
                        "Implement upselling strategies",
                        "Expand to new markets",
                    ],
                    metrics={"mrr": mrr, "target": 5000},
                )
            )

        return insights

    async def extract_insights_from_technical_data(
        self, technical_data: Dict[str, Any]
    ) -> List[Insight]:
        """Extract insights from technical monitoring"""
        insights = []

        # Error rate insights
        error_rate = technical_data.get("error_rate", 0)
        if error_rate > 5:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.TECHNICAL,
                    title="High Error Rate Detected",
                    description=f"Error rate is {error_rate}%, indicating system instability",
                    data_source="technical_monitoring",
                    confidence=ConfidenceLevel.HIGH
                    if error_rate > 10
                    else ConfidenceLevel.MEDIUM,
                    impact_score=error_rate * 10,
                    urgency=error_rate * 10,
                    tags=["errors", "stability", "technical"],
                    action_items=[
                        "Investigate error logs for root causes",
                        "Implement better error handling",
                        "Add monitoring and alerting",
                    ],
                    metrics={"error_rate": error_rate, "threshold": 5},
                )
            )

        # Uptime insights
        uptime = technical_data.get("uptime", 100)
        if uptime < 99:
            insights.append(
                Insight(
                    id=str(uuid.uuid4()),
                    type=InsightType.TECHNICAL,
                    title="System Uptime Below Target",
                    description=f"Uptime is {uptime}%, below 99% target for production systems",
                    data_source="technical_monitoring",
                    confidence=ConfidenceLevel.MEDIUM,
                    impact_score=100 - uptime,
                    urgency=100 - uptime,
                    tags=["uptime", "reliability", "technical"],
                    action_items=[
                        "Improve system reliability",
                        "Implement redundancy and failover",
                        "Add health checks and auto-recovery",
                    ],
                    metrics={"uptime": uptime, "target": 99},
                )
            )

        return insights

    async def detect_patterns(self, data: List[Dict[str, Any]]) -> List[Pattern]:
        """Detect patterns in time-series or categorical data"""
        patterns = []

        if not data:
            return patterns

        # Trend detection
        trend_pattern = self.detect_trend_pattern(data)
        if trend_pattern:
            patterns.append(trend_pattern)

        # Anomaly detection
        anomaly_pattern = self.detect_anomaly_pattern(data)
        if anomaly_pattern:
            patterns.append(anomaly_pattern)

        # Correlation detection
        correlation_pattern = self.detect_correlation_pattern(data)
        if correlation_pattern:
            patterns.append(correlation_pattern)

        return patterns

    def detect_trend_pattern(self, data: List[Dict[str, Any]]) -> Optional[Pattern]:
        """Detect trend patterns in data"""
        if len(data) < 3:
            return None

        # Extract numeric values for trend analysis
        numeric_values = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_values.append(value)

        if len(numeric_values) < 3:
            return None

        # Calculate trend
        first_half = numeric_values[: len(numeric_values) // 2]
        second_half = numeric_values[len(numeric_values) // 2 :]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        trend_direction = "increasing" if second_avg > first_avg else "decreasing"
        trend_magnitude = (
            abs(second_avg - first_avg) / first_avg if first_avg != 0 else 0
        )

        if trend_magnitude > 0.1:  # 10% change threshold
            return Pattern(
                id=str(uuid.uuid4()),
                name=f"{trend_direction.title()} Trend",
                description=f"Data shows {trend_direction} trend with {trend_magnitude:.1%} change",
                pattern_type="trend",
                confidence=min(100, trend_magnitude * 100),
                frequency=1.0,  # Occurs in this dataset
                impact="positive" if trend_direction == "increasing" else "negative",
                data_points=data[:5],  # Sample data points
                recommendations=[
                    f"Monitor {trend_direction} trend",
                    "Investigate underlying causes",
                    "Plan for future implications",
                ],
            )

        return None

    def detect_anomaly_pattern(self, data: List[Dict[str, Any]]) -> Optional[Pattern]:
        """Detect anomaly patterns using statistical methods"""
        if len(data) < 5:
            return None

        # Extract numeric values
        numeric_values = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_values.append(value)

        if len(numeric_values) < 5:
            return None

        # Calculate statistics
        mean = statistics.mean(numeric_values)
        std_dev = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0

        # Find anomalies (values > 2 standard deviations from mean)
        anomalies = [v for v in numeric_values if abs(v - mean) > 2 * std_dev]

        if anomalies:
            return Pattern(
                id=str(uuid.uuid4()),
                name="Statistical Anomaly Detected",
                description=f"Found {len(anomalies)} anomalous values in dataset",
                pattern_type="anomaly",
                confidence=min(100, (len(anomalies) / len(numeric_values)) * 100),
                frequency=len(anomalies) / len(numeric_values),
                impact="negative",
                data_points=[
                    {"value": a, "z_score": (a - mean) / std_dev if std_dev != 0 else 0}
                    for a in anomalies[:5]
                ],
                recommendations=[
                    "Investigate anomalous data points",
                    "Check for data quality issues",
                    "Monitor for recurring anomalies",
                ],
            )

        return None

    def detect_correlation_pattern(
        self, data: List[Dict[str, Any]]
    ) -> Optional[Pattern]:
        """Detect correlation patterns between variables"""
        if len(data) < 10:
            return None

        # Extract pairs of numeric variables
        numeric_pairs = []
        for item in data:
            numeric_values = [
                (k, v) for k, v in item.items() if isinstance(v, (int, float))
            ]
            if len(numeric_values) >= 2:
                numeric_pairs.append(numeric_values)

        if len(numeric_pairs) < 5:
            return None

        # Calculate correlations (simplified)
        correlations = []
        for pair in numeric_pairs[:5]:  # Sample first 5 pairs
            if len(pair) >= 2:
                # In real implementation, you'd calculate actual correlation coefficient
                # For now, use mock correlation
                mock_correlation = 0.7  # Mock strong correlation
                correlations.append(
                    {
                        "variables": [pair[0][0], pair[1][0]],
                        "correlation": mock_correlation,
                    }
                )

        strong_correlations = [c for c in correlations if abs(c["correlation"]) > 0.7]

        if strong_correlations:
            return Pattern(
                id=str(uuid.uuid4()),
                name="Strong Correlation Pattern",
                description=f"Found {len(strong_correlations)} strong correlations between variables",
                pattern_type="correlation",
                confidence=80,
                frequency=len(strong_correlations) / len(correlations),
                impact="neutral",
                data_points=strong_correlations[:3],
                recommendations=[
                    "Investigate causal relationships",
                    "Leverage correlations for predictions",
                    "Monitor correlation stability",
                ],
            )

        return None


class MemoryConsolidationEngine:
    """Consolidates memories and manages long-term storage"""

    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.initialize_database()

    def initialize_database(self):
        """Initialize memory database"""
        conn = sqlite3.connect("insights_memory.db")
        cursor = conn.cursor()

        # Memories table already created in InsightExtractionEngine
        conn.close()
        logger.info("Memory consolidation database initialized")

    async def consolidate_insights(self, insights: List[Insight]) -> List[Memory]:
        """Consolidate insights into memories"""
        consolidated_memories = []

        # Group insights by type and similarity
        insight_groups = self.group_similar_insights(insights)

        for group in insight_groups:
            if len(group) > 1:
                # Create consolidated memory from multiple insights
                memory = await self.create_consolidated_memory(group)
                consolidated_memories.append(memory)
            else:
                # Create memory from single insight
                memory = await self.create_memory_from_insight(group[0])
                consolidated_memories.append(memory)

        return consolidated_memories

    def group_similar_insights(self, insights: List[Insight]) -> List[List[Insight]]:
        """Group insights by similarity"""
        groups = []
        processed = set()

        for insight in insights:
            if insight.id in processed:
                continue

            # Find similar insights
            similar_insights = [insight]
            processed.add(insight.id)

            for other_insight in insights:
                if other_insight.id in processed:
                    continue

                if self.are_insights_similar(insight, other_insight):
                    similar_insights.append(other_insight)
                    processed.add(other_insight.id)

            groups.append(similar_insights)

        return groups

    def are_insights_similar(self, insight1: Insight, insight2: Insight) -> bool:
        """Check if two insights are similar"""
        # Same type
        if insight1.type == insight2.type:
            return True

        # Same tags
        common_tags = set(insight1.tags) & set(insight2.tags)
        if len(common_tags) >= 2:
            return True

        # Similar titles (simplified)
        title1_words = set(insight1.title.lower().split())
        title2_words = set(insight2.title.lower().split())
        common_words = title1_words & title2_words
        if len(common_words) >= 3:
            return True

        return False

    async def create_consolidated_memory(self, insights: List[Insight]) -> Memory:
        """Create consolidated memory from multiple insights"""
        # Combine insights into memory
        combined_title = f"Consolidated: {insights[0].type.value.title()} Insights"
        combined_content = f"Consolidated from {len(insights)} insights:\n"

        for insight in insights:
            combined_content += f"- {insight.title}: {insight.description}\n"

        # Calculate combined importance
        combined_importance = statistics.mean(
            [insight.impact_score for insight in insights]
        )

        # Determine memory type based on importance
        if combined_importance > 80:
            memory_type = MemoryType.PERMANENT
        elif combined_importance > 50:
            memory_type = MemoryType.LONG_TERM
        else:
            memory_type = MemoryType.MEDIUM_TERM

        memory = Memory(
            id=str(uuid.uuid4()),
            content=combined_content,
            type=memory_type,
            importance_score=combined_importance,
            tags=list(set([tag for insight in insights for tag in insight.tags])),
            metadata={
                "source_insights": [insight.id for insight in insights],
                "consolidated_at": datetime.now().isoformat(),
                "insight_count": len(insights),
            },
        )

        self.memories[memory.id] = memory
        await self.save_memory(memory)

        return memory

    async def create_memory_from_insight(self, insight: Insight) -> Memory:
        """Create memory from single insight"""
        content = f"{insight.title}: {insight.description}\n"
        content += f"Data Source: {insight.data_source}\n"
        content += f"Confidence: {insight.confidence.value}\n"
        content += f"Impact Score: {insight.impact_score}\n"

        if insight.action_items:
            content += f"Action Items: {', '.join(insight.action_items)}\n"

        # Determine memory type based on insight importance
        if insight.impact_score > 80:
            memory_type = MemoryType.PERMANENT
        elif insight.impact_score > 50:
            memory_type = MemoryType.LONG_TERM
        else:
            memory_type = MemoryType.MEDIUM_TERM

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            type=memory_type,
            importance_score=insight.impact_score,
            tags=insight.tags,
            metadata={
                "source_insight": insight.id,
                "insight_type": insight.type.value,
                "created_from": "insight",
            },
        )

        self.memories[memory.id] = memory
        await self.save_memory(memory)

        return memory

    async def save_memory(self, memory: Memory):
        """Save memory to database"""
        conn = sqlite3.connect("insights_memory.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO memories 
            (id, content, type, created_at, last_accessed, access_count, 
             importance_score, related_memories, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                memory.id,
                memory.content,
                memory.type.value,
                memory.created_at.isoformat(),
                memory.last_accessed.isoformat(),
                memory.access_count,
                memory.importance_score,
                json.dumps(memory.related_memories),
                json.dumps(memory.tags),
                json.dumps(memory.metadata),
            ),
        )

        conn.commit()
        conn.close()

    async def cleanup_old_memories(self):
        """Clean up old or low-importance memories"""
        cutoff_date = datetime.now() - timedelta(days=90)

        for memory_id, memory in list(self.memories.items()):
            # Remove old short-term memories
            if memory.type == MemoryType.SHORT_TERM and memory.created_at < cutoff_date:
                del self.memories[memory_id]
                await self.delete_memory_from_db(memory_id)

            # Remove low-importance memories
            elif memory.importance_score < 20 and memory.type != MemoryType.PERMANENT:
                del self.memories[memory_id]
                await self.delete_memory_from_db(memory_id)

    async def delete_memory_from_db(self, memory_id: str):
        """Delete memory from database"""
        conn = sqlite3.connect("insights_memory.db")
        cursor = conn.cursor()

        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

        conn.commit()
        conn.close()

    async def search_memories(self, query: str, limit: int = 10) -> List[Memory]:
        """Search memories by content"""
        results = []
        query_lower = query.lower()

        for memory in self.memories.values():
            if (
                query_lower in memory.content.lower()
                or query_lower in " ".join(memory.tags).lower()
            ):
                results.append(memory)
                if len(results) >= limit:
                    break

        # Sort by importance score
        results.sort(key=lambda m: m.importance_score, reverse=True)

        return results


# Global engines
insight_engine = InsightExtractionEngine()
memory_engine = MemoryConsolidationEngine()


async def main():
    """Main insight extraction and memory consolidation function"""
    logger.info("🧠 Starting ZEJZL.NET Insight Extraction and Memory Consolidation")

    # Sample data for demonstration
    performance_data = {
        "cpu": {"percent": 85},
        "memory": {"percent": 78},
        "response_time": 1200,
    }

    behavioral_data = {
        "engagement_score": 25,
        "risk_score": 75,
        "features_used": ["openai"],
    }

    revenue_data = {"conversion_rate": 3.5, "churn_rate": 12, "mrr": 850}

    # Extract insights
    performance_insights = await insight_engine.extract_insights_from_performance_data(
        performance_data
    )
    behavioral_insights = await insight_engine.extract_insights_from_user_behavior(
        behavioral_data
    )
    revenue_insights = await insight_engine.extract_insights_from_revenue_data(
        revenue_data
    )

    all_insights = performance_insights + behavioral_insights + revenue_insights

    # Consolidate into memories
    memories = await memory_engine.consolidate_insights(all_insights)

    logger.info(
        f"✅ Extracted {len(all_insights)} insights and consolidated into {len(memories)} memories"
    )


if __name__ == "__main__":
    asyncio.run(main())
