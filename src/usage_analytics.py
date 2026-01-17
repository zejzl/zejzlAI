"""
Usage Analytics Engine
Provides comprehensive analytics and reporting for AI provider usage, costs, and performance metrics.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import asyncio
import sqlite3
from pathlib import Path


@dataclass
class UsageReport:
    """Usage analytics report"""
    period: str  # "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_response_time: float
    success_rate: float
    provider_breakdown: Dict[str, Dict[str, Any]]
    hourly_usage: List[Dict[str, Any]]


@dataclass
class CostAnalysis:
    """Cost analysis for a specific period"""
    period_days: int
    total_cost: float
    avg_daily_cost: float
    avg_request_cost: float
    most_expensive_provider: str
    cost_trend: str  # "increasing", "decreasing", "stable"
    projected_monthly_cost: float


class UsageAnalytics:
    """Analytics engine for usage tracking and reporting"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".ai_framework.db")

    async def get_usage_report(self, days: int = 7) -> UsageReport:
        """Generate a comprehensive usage report for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Get basic metrics from daily_usage
            cursor.execute("""
                SELECT
                    SUM(total_requests) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(total_cost_usd) as cost,
                    AVG(avg_response_time) as avg_response_time,
                    AVG(success_rate) as success_rate
                FROM daily_usage
                WHERE date >= ? AND date <= ?
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            row = cursor.fetchone()
            total_requests = row[0] or 0
            total_tokens = row[1] or 0
            total_cost = row[2] or 0.0
            avg_response_time = row[3] or 0.0
            success_rate = row[4] or 0.0

            # Get provider breakdown
            provider_breakdown = await self._get_provider_breakdown(cursor, start_date, end_date)

            # Get hourly usage data
            hourly_usage = await self._get_hourly_usage(cursor, start_date, end_date)

            return UsageReport(
                period=f"{days} days",
                start_date=start_date,
                end_date=end_date,
                total_requests=total_requests,
                total_tokens=total_tokens,
                total_cost_usd=total_cost,
                avg_response_time=avg_response_time,
                success_rate=success_rate,
                provider_breakdown=provider_breakdown,
                hourly_usage=hourly_usage
            )
        finally:
            conn.close()

    async def get_cost_analysis(self, days: int = 30) -> CostAnalysis:
        """Analyze cost trends and provide cost insights"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Get cost data
            cursor.execute("""
                SELECT
                    SUM(total_cost_usd) as total_cost,
                    AVG(total_cost_usd) as avg_daily_cost,
                    COUNT(*) as days_with_data
                FROM daily_usage
                WHERE date >= ? AND date <= ?
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            row = cursor.fetchone()
            total_cost = row[0] or 0.0
            avg_daily_cost = row[1] or 0.0
            days_with_data = row[2] or 1

            # Get total requests for average cost per request
            cursor.execute("""
                SELECT SUM(total_requests) FROM daily_usage
                WHERE date >= ? AND date <= ?
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            total_requests = cursor.fetchone()[0] or 1
            avg_request_cost = total_cost / total_requests if total_requests > 0 else 0

            # Find most expensive provider
            cursor.execute("""
                SELECT provider, SUM(cost_usd) as total_cost
                FROM provider_usage
                WHERE date >= ? AND date <= ?
                GROUP BY provider
                ORDER BY total_cost DESC
                LIMIT 1
            """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            most_expensive_row = cursor.fetchone()
            most_expensive_provider = most_expensive_row[0] if most_expensive_row else "None"

            # Calculate cost trend (simplified)
            cost_trend = await self._calculate_cost_trend(cursor, days)

            # Project monthly cost
            projected_monthly_cost = avg_daily_cost * 30

            return CostAnalysis(
                period_days=days,
                total_cost=total_cost,
                avg_daily_cost=avg_daily_cost,
                avg_request_cost=avg_request_cost,
                most_expensive_provider=most_expensive_provider,
                cost_trend=cost_trend,
                projected_monthly_cost=projected_monthly_cost
            )
        finally:
            conn.close()

    async def get_provider_performance(self, provider: str, days: int = 7) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific provider"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    SUM(requests) as total_requests,
                    SUM(tokens) as total_tokens,
                    SUM(cost_usd) as total_cost,
                    AVG(avg_response_time) as avg_response_time,
                    SUM(success_count) as success_count,
                    SUM(error_count) as error_count
                FROM provider_usage
                WHERE provider = ? AND date >= ? AND date <= ?
            """, (provider, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

            row = cursor.fetchone()
            if not row or row[0] is None:
                return {"error": f"No data found for provider {provider}"}

            total_requests = row[0]
            total_tokens = row[1]
            total_cost = row[2] or 0
            avg_response_time = row[3] or 0
            success_count = row[4] or 0
            error_count = row[5] or 0

            success_rate = success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
            avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0

            return {
                "provider": provider,
                "period_days": days,
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
                "avg_response_time": avg_response_time,
                "success_rate": success_rate,
                "avg_cost_per_request": avg_cost_per_request,
                "avg_cost_per_token": avg_cost_per_token,
                "error_count": error_count
            }
        finally:
            conn.close()

    async def _get_provider_breakdown(self, cursor, start_date: datetime, end_date: datetime) -> Dict[str, Dict[str, Any]]:
        """Get usage breakdown by provider"""
        cursor.execute("""
            SELECT
                provider,
                SUM(requests) as requests,
                SUM(tokens) as tokens,
                SUM(cost_usd) as cost,
                AVG(avg_response_time) as avg_response_time,
                SUM(success_count) as success_count,
                SUM(error_count) as error_count
            FROM provider_usage
            WHERE date >= ? AND date <= ?
            GROUP BY provider
        """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        breakdown = {}
        for row in cursor.fetchall():
            provider = row[0]
            requests = row[1] or 0
            tokens = row[2] or 0
            cost = row[3] or 0
            avg_response_time = row[4] or 0
            success_count = row[5] or 0
            error_count = row[6] or 0

            success_rate = success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0

            breakdown[provider] = {
                "requests": requests,
                "tokens": tokens,
                "cost_usd": cost,
                "avg_response_time": avg_response_time,
                "success_rate": success_rate,
                "error_count": error_count
            }

        return breakdown

    async def _get_hourly_usage(self, cursor, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get hourly usage data"""
        cursor.execute("""
            SELECT
                hour,
                requests,
                tokens,
                cost_usd,
                peak_concurrent
            FROM hourly_usage
            WHERE substr(hour, 1, 10) >= ? AND substr(hour, 1, 10) <= ?
            ORDER BY hour
        """, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

        hourly_data = []
        for row in cursor.fetchall():
            hourly_data.append({
                "hour": row[0],
                "requests": row[1] or 0,
                "tokens": row[2] or 0,
                "cost_usd": row[3] or 0.0,
                "peak_concurrent": row[4] or 0
            })

        return hourly_data

    async def _calculate_cost_trend(self, cursor, days: int) -> str:
        """Calculate cost trend (simplified)"""
        # Get first half vs second half comparison
        mid_date = datetime.now() - timedelta(days=days//2)

        cursor.execute("""
            SELECT SUM(total_cost_usd) FROM daily_usage
            WHERE date >= ? AND date < ?
        """, (mid_date.strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d")))

        recent_cost = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT SUM(total_cost_usd) FROM daily_usage
            WHERE date >= ? AND date < ?
        """, ((mid_date - timedelta(days=days//2)).strftime("%Y-%m-%d"), mid_date.strftime("%Y-%m-%d")))

        older_cost = cursor.fetchone()[0] or 0

        if older_cost == 0:
            return "stable"

        ratio = recent_cost / older_cost
        if ratio > 1.1:
            return "increasing"
        elif ratio < 0.9:
            return "decreasing"
        else:
            return "stable"

    async def get_top_expensive_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most expensive individual requests"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    content,
                    provider,
                    token_usage_provider,
                    token_usage_model,
                    total_tokens,
                    cost_usd,
                    timestamp,
                    response_time
                FROM messages
                WHERE cost_usd > 0
                ORDER BY cost_usd DESC
                LIMIT ?
            """, (limit,))

            expensive_requests = []
            for row in cursor.fetchall():
                expensive_requests.append({
                    "id": row[0],
                    "content": row[1][:100] + "..." if len(row[1]) > 100 else row[1],
                    "provider": row[2],
                    "model": row[4] or row[2],
                    "tokens": row[5] or 0,
                    "cost_usd": row[6] or 0,
                    "timestamp": row[7],
                    "response_time": row[8]
                })

            return expensive_requests
        finally:
            conn.close()