#!/usr/bin/env python3
"""
ZEJZL.NET Predictive Alerts and Forecasting System
Predicts future trends, generates alerts, and provides forecasting analytics
"""

import asyncio
import logging
import json
import os
import statistics
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
from pathlib import Path
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ForecastType(str, Enum):
    REVENUE = "revenue"
    USAGE = "usage"
    PERFORMANCE = "performance"
    CHURN = "churn"
    GROWTH = "growth"


class PredictionModel(str, Enum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    SEASONAL = "seasonal"
    ARIMA = "arima"
    MACHINE_LEARNING = "ml"


@dataclass
class Alert:
    id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str
    confidence: float  # 0-100
    predicted_impact: str  # "low", "medium", "high", "critical"
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    data_source: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    related_alerts: List[str] = field(default_factory=list)


@dataclass
class Forecast:
    id: str
    type: ForecastType
    model: PredictionModel
    time_horizon: int  # days into future
    predictions: List[Dict[str, Any]] = field(default_factory=list)
    confidence_interval: Tuple[float, float] = (0.0, 0.0)  # lower, upper bounds
    accuracy_score: float = 0.0  # 0-100
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Trend:
    id: str
    name: str
    description: str
    direction: str  # "increasing", "decreasing", "stable", "volatile"
    strength: float  # 0-100
    duration: int  # days
    significance: str  # "low", "medium", "high", "critical"
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)


class PredictiveAnalyticsEngine:
    """Core predictive analytics engine"""

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.forecasts: Dict[str, Forecast] = {}
        self.trends: Dict[str, Trend] = {}
        self.initialize_database()

    def initialize_database(self):
        """Initialize predictive analytics database"""
        conn = sqlite3.connect("predictive_analytics.db")
        cursor = conn.cursor()

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                severity TEXT,
                category TEXT,
                confidence REAL,
                predicted_impact TEXT,
                created_at TEXT,
                expires_at TEXT,
                is_active BOOLEAN,
                data_source TEXT,
                metrics TEXT,
                recommendations TEXT,
                related_alerts TEXT
            )
        """)

        # Forecasts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecasts (
                id TEXT PRIMARY KEY,
                type TEXT,
                model TEXT,
                time_horizon INTEGER,
                predictions TEXT,
                confidence_interval TEXT,
                accuracy_score REAL,
                created_at TEXT,
                last_updated TEXT,
                metadata TEXT
            )
        """)

        # Trends table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trends (
                id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                direction TEXT,
                strength REAL,
                duration INTEGER,
                significance TEXT,
                data_points TEXT,
                detected_at TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Predictive analytics database initialized")

    async def generate_revenue_forecast(
        self, historical_data: List[Dict[str, Any]], days_ahead: int = 30
    ) -> Forecast:
        """Generate revenue forecast using multiple models"""
        if len(historical_data) < 7:
            # Not enough data for reliable forecast
            return self.create_mock_forecast(ForecastType.REVENUE, days_ahead)

        # Extract revenue values
        revenue_values = []
        dates = []
        for item in historical_data:
            if "revenue" in item:
                revenue_values.append(float(item["revenue"]))
                dates.append(item.get("date", datetime.now()))

        if len(revenue_values) < 7:
            return self.create_mock_forecast(ForecastType.REVENUE, days_ahead)

        # Try different models and select best
        forecasts = []

        # Linear regression forecast
        linear_forecast = self.linear_regression_forecast(revenue_values, days_ahead)
        forecasts.append(("linear", linear_forecast))

        # Exponential smoothing forecast
        exp_forecast = self.exponential_smoothing_forecast(revenue_values, days_ahead)
        forecasts.append(("exponential", exp_forecast))

        # Select best model based on fit
        best_model, best_predictions = self.select_best_forecast(
            forecasts, revenue_values
        )

        # Calculate confidence interval
        std_dev = statistics.stdev(revenue_values) if len(revenue_values) > 1 else 0
        confidence_interval = (
            max(0, statistics.mean(revenue_values) - 2 * std_dev),
            statistics.mean(revenue_values) + 2 * std_dev,
        )

        forecast = Forecast(
            id=str(uuid.uuid4()),
            type=ForecastType.REVENUE,
            model=PredictionModel(best_model),
            time_horizon=days_ahead,
            predictions=[
                {
                    "date": (datetime.now() + timedelta(days=i)).isoformat(),
                    "predicted_revenue": pred,
                    "day": i,
                }
                for i, pred in enumerate(best_predictions)
            ],
            confidence_interval=confidence_interval,
            accuracy_score=self.calculate_forecast_accuracy(
                revenue_values, best_predictions
            ),
            metadata={
                "historical_points": len(revenue_values),
                "model_used": best_model,
                "std_deviation": std_dev,
            },
        )

        self.forecasts[forecast.id] = forecast
        await self.save_forecast(forecast)

        return forecast

    def linear_regression_forecast(
        self, values: List[float], days_ahead: int
    ) -> List[float]:
        """Simple linear regression forecast"""
        if len(values) < 2:
            return [values[0]] * days_ahead if values else [0] * days_ahead

        # Calculate linear regression
        n = len(values)
        x = list(range(n))
        y = values

        # Calculate slope and intercept
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        intercept = y_mean - slope * x_mean

        # Generate predictions
        predictions = []
        for i in range(days_ahead):
            x_next = n + i
            y_next = slope * x_next + intercept
            predictions.append(max(0, y_next))  # Revenue can't be negative

        return predictions

    def exponential_smoothing_forecast(
        self, values: List[float], days_ahead: int, alpha: float = 0.3
    ) -> List[float]:
        """Exponential smoothing forecast"""
        if not values:
            return [0] * days_ahead

        # Simple exponential smoothing
        smoothed_values = [values[0]]
        for i in range(1, len(values)):
            smoothed = alpha * values[i] + (1 - alpha) * smoothed_values[-1]
            smoothed_values.append(smoothed)

        # Use last smoothed value as forecast
        last_smoothed = smoothed_values[-1]
        predictions = [last_smoothed] * days_ahead

        return predictions

    def select_best_forecast(
        self, forecasts: List[Tuple[str, List[float]]], actual_values: List[float]
    ) -> Tuple[str, List[float]]:
        """Select best forecast model based on accuracy"""
        best_model = "linear"
        best_predictions = forecasts[0][1]
        best_error = float("inf")

        for model_name, predictions in forecasts:
            # Calculate error (simplified - using last actual values)
            if len(predictions) >= len(actual_values):
                error = sum(
                    abs(predictions[i] - actual_values[i])
                    for i in range(len(actual_values))
                ) / len(actual_values)
            else:
                error = sum(
                    abs(predictions[i] - actual_values[i])
                    for i in range(len(predictions))
                ) / len(predictions)

            if error < best_error:
                best_error = error
                best_model = model_name
                best_predictions = predictions

        return best_model, best_predictions

    def calculate_forecast_accuracy(
        self, actual_values: List[float], predicted_values: List[float]
    ) -> float:
        """Calculate forecast accuracy score"""
        if len(predicted_values) < len(actual_values):
            predicted_values = predicted_values[: len(actual_values)]
        elif len(predicted_values) > len(actual_values):
            predicted_values = predicted_values[: len(actual_values)]

        if not actual_values or not predicted_values:
            return 0.0

        # Calculate Mean Absolute Percentage Error (MAPE)
        mape = sum(
            abs((actual - pred) / actual) * 100
            for actual, pred in zip(actual_values, predicted_values)
            if actual != 0
        ) / len(actual_values)

        # Convert to accuracy score (0-100)
        accuracy = max(0, 100 - mape)

        return accuracy

    async def generate_usage_forecast(
        self, usage_data: List[Dict[str, Any]], days_ahead: int = 30
    ) -> Forecast:
        """Generate usage forecast"""
        if len(usage_data) < 7:
            return self.create_mock_forecast(ForecastType.USAGE, days_ahead)

        # Extract usage values
        usage_values = []
        for item in usage_data:
            if "api_calls" in item:
                usage_values.append(float(item["api_calls"]))
            elif "usage" in item:
                usage_values.append(float(item["usage"]))

        if len(usage_values) < 7:
            return self.create_mock_forecast(ForecastType.USAGE, days_ahead)

        # Use exponential smoothing for usage (tends to be more volatile)
        predictions = self.exponential_smoothing_forecast(
            usage_values, days_ahead, alpha=0.5
        )

        # Calculate confidence interval
        std_dev = statistics.stdev(usage_values) if len(usage_values) > 1 else 0
        mean_usage = statistics.mean(usage_values)
        confidence_interval = (
            max(0, mean_usage - 2 * std_dev),
            mean_usage + 2 * std_dev,
        )

        forecast = Forecast(
            id=str(uuid.uuid4()),
            type=ForecastType.USAGE,
            model=PredictionModel.EXPONENTIAL,
            time_horizon=days_ahead,
            predictions=[
                {
                    "date": (datetime.now() + timedelta(days=i)).isoformat(),
                    "predicted_usage": pred,
                    "day": i,
                }
                for i, pred in enumerate(predictions)
            ],
            confidence_interval=confidence_interval,
            accuracy_score=75.0,  # Mock accuracy
            metadata={
                "historical_points": len(usage_values),
                "mean_usage": mean_usage,
                "volatility": std_dev / mean_usage if mean_usage > 0 else 0,
            },
        )

        self.forecasts[forecast.id] = forecast
        await self.save_forecast(forecast)

        return forecast

    async def generate_churn_forecast(
        self, churn_data: List[Dict[str, Any]], days_ahead: int = 30
    ) -> Forecast:
        """Generate churn forecast"""
        if len(churn_data) < 7:
            return self.create_mock_forecast(ForecastType.CHURN, days_ahead)

        # Extract churn rates
        churn_rates = []
        for item in churn_data:
            if "churn_rate" in item:
                churn_rates.append(float(item["churn_rate"]))
            elif "churned_customers" in item and "total_customers" in item:
                rate = (
                    float(item["churned_customers"])
                    / float(item["total_customers"])
                    * 100
                )
                churn_rates.append(rate)

        if len(churn_rates) < 7:
            return self.create_mock_forecast(ForecastType.CHURN, days_ahead)

        # Use linear regression for churn (tends to be more predictable)
        predictions = self.linear_regression_forecast(churn_rates, days_ahead)

        # Ensure predictions are within valid range (0-100%)
        predictions = [max(0, min(100, pred)) for pred in predictions]

        # Calculate confidence interval
        std_dev = statistics.stdev(churn_rates) if len(churn_rates) > 1 else 0
        mean_churn = statistics.mean(churn_rates)
        confidence_interval = (
            max(0, mean_churn - 2 * std_dev),
            min(100, mean_churn + 2 * std_dev),
        )

        forecast = Forecast(
            id=str(uuid.uuid4()),
            type=ForecastType.CHURN,
            model=PredictionModel.LINEAR,
            time_horizon=days_ahead,
            predictions=[
                {
                    "date": (datetime.now() + timedelta(days=i)).isoformat(),
                    "predicted_churn_rate": pred,
                    "day": i,
                }
                for i, pred in enumerate(predictions)
            ],
            confidence_interval=confidence_interval,
            accuracy_score=80.0,  # Mock accuracy
            metadata={
                "historical_points": len(churn_rates),
                "mean_churn_rate": mean_churn,
                "churn_volatility": std_dev,
            },
        )

        self.forecasts[forecast.id] = forecast
        await self.save_forecast(forecast)

        return forecast

    def create_mock_forecast(
        self, forecast_type: ForecastType, days_ahead: int
    ) -> Forecast:
        """Create mock forecast when insufficient data"""
        mock_predictions = []

        if forecast_type == ForecastType.REVENUE:
            base_value = 1000.0
            growth_rate = 0.05  # 5% growth
            for i in range(days_ahead):
                pred = base_value * (1 + growth_rate) ** i
                mock_predictions.append(
                    {
                        "date": (datetime.now() + timedelta(days=i)).isoformat(),
                        "predicted_revenue": pred,
                        "day": i,
                    }
                )
        elif forecast_type == ForecastType.USAGE:
            base_value = 100.0
            growth_rate = 0.03  # 3% growth
            for i in range(days_ahead):
                pred = base_value * (1 + growth_rate) ** i
                mock_predictions.append(
                    {
                        "date": (datetime.now() + timedelta(days=i)).isoformat(),
                        "predicted_usage": pred,
                        "day": i,
                    }
                )
        elif forecast_type == ForecastType.CHURN:
            base_rate = 5.0  # 5% churn rate
            for i in range(days_ahead):
                mock_predictions.append(
                    {
                        "date": (datetime.now() + timedelta(days=i)).isoformat(),
                        "predicted_churn_rate": base_rate,
                        "day": i,
                    }
                )
        else:
            # Generic forecast
            for i in range(days_ahead):
                mock_predictions.append(
                    {
                        "date": (datetime.now() + timedelta(days=i)).isoformat(),
                        "predicted_value": 100.0,
                        "day": i,
                    }
                )

        return Forecast(
            id=str(uuid.uuid4()),
            type=forecast_type,
            model=PredictionModel.LINEAR,
            time_horizon=days_ahead,
            predictions=mock_predictions,
            confidence_interval=(0.0, 0.0),
            accuracy_score=50.0,  # Mock accuracy
            metadata={"mock": True, "reason": "Insufficient historical data"},
        )

    async def detect_anomalies(
        self, data: List[Dict[str, Any]], threshold: float = 2.0
    ) -> List[Alert]:
        """Detect anomalies in data and generate alerts"""
        alerts = []

        if len(data) < 5:
            return alerts

        # Extract numeric values
        numeric_values = []
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_values.append(value)

        if len(numeric_values) < 5:
            return alerts

        # Calculate statistics
        mean = statistics.mean(numeric_values)
        std_dev = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0

        # Find anomalies
        anomalies = []
        for i, value in enumerate(numeric_values):
            z_score = (value - mean) / std_dev if std_dev != 0 else 0
            if abs(z_score) > threshold:
                anomalies.append(
                    {
                        "index": i,
                        "value": value,
                        "z_score": z_score,
                        "deviation": abs(z_score) * std_dev,
                    }
                )

        if anomalies:
            # Create alert for anomalies
            alert = Alert(
                id=str(uuid.uuid4()),
                title="Anomaly Detected in Data",
                description=f"Found {len(anomalies)} anomalous data points (threshold: {threshold}σ)",
                severity=AlertSeverity.WARNING
                if len(anomalies) < 3
                else AlertSeverity.CRITICAL,
                category="anomaly_detection",
                confidence=min(100, len(anomalies) * 20),
                predicted_impact="medium" if len(anomalies) < 3 else "high",
                data_source="predictive_analytics",
                metrics={
                    "anomaly_count": len(anomalies),
                    "threshold": threshold,
                    "mean": mean,
                    "std_dev": std_dev,
                    "anomalies": anomalies[:5],  # Sample anomalies
                },
                recommendations=[
                    "Investigate anomalous data points",
                    "Check for data quality issues",
                    "Monitor for recurring anomalies",
                ],
            )
            alerts.append(alert)

        return alerts

    async def generate_trend_alerts(self, trends: List[Trend]) -> List[Alert]:
        """Generate alerts based on trend analysis"""
        alerts = []

        for trend in trends:
            if trend.direction == "decreasing" and trend.strength > 70:
                alert = Alert(
                    id=str(uuid.uuid4()),
                    title=f"Strong Decreasing Trend: {trend.name}",
                    description=f"Detected strong decreasing trend in {trend.name} (strength: {trend.strength}%)",
                    severity=AlertSeverity.WARNING,
                    category="trend_analysis",
                    confidence=trend.strength,
                    predicted_impact="high",
                    data_source="trend_analysis",
                    metrics={
                        "trend_direction": trend.direction,
                        "trend_strength": trend.strength,
                        "duration": trend.duration,
                        "significance": trend.significance,
                    },
                    recommendations=[
                        f"Investigate causes of decreasing {trend.name}",
                        "Implement corrective measures",
                        "Monitor trend closely",
                    ],
                )
                alerts.append(alert)

            elif trend.direction == "volatile" and trend.strength > 60:
                alert = Alert(
                    id=str(uuid.uuid4()),
                    title=f"High Volatility Detected: {trend.name}",
                    description=f"High volatility detected in {trend.name} (strength: {trend.strength}%)",
                    severity=AlertSeverity.INFO,
                    category="trend_analysis",
                    confidence=trend.strength,
                    predicted_impact="medium",
                    data_source="trend_analysis",
                    metrics={
                        "trend_direction": trend.direction,
                        "trend_strength": trend.strength,
                        "duration": trend.duration,
                        "significance": trend.significance,
                    },
                    recommendations=[
                        f"Stabilize {trend.name} if possible",
                        "Investigate causes of volatility",
                        "Consider smoothing strategies",
                    ],
                )
                alerts.append(alert)

        return alerts

    async def generate_forecast_alerts(self, forecasts: List[Forecast]) -> List[Alert]:
        """Generate alerts based on forecast predictions"""
        alerts = []

        for forecast in forecasts:
            # Check for concerning predictions
            if forecast.type == ForecastType.REVENUE:
                # Check for revenue decline
                if len(forecast.predictions) >= 2:
                    first_pred = forecast.predictions[0].get("predicted_revenue", 0)
                    last_pred = forecast.predictions[-1].get("predicted_revenue", 0)

                    if last_pred < first_pred * 0.8:  # 20% decline
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            title="Revenue Decline Forecast",
                            description=f"Forecast predicts {((first_pred - last_pred) / first_pred * 100):.1f}% revenue decline over {forecast.time_horizon} days",
                            severity=AlertSeverity.WARNING,
                            category="revenue_forecast",
                            confidence=forecast.accuracy_score,
                            predicted_impact="high",
                            data_source="revenue_forecast",
                            metrics={
                                "initial_revenue": first_pred,
                                "final_revenue": last_pred,
                                "decline_percentage": (
                                    (first_pred - last_pred) / first_pred * 100
                                ),
                                "time_horizon": forecast.time_horizon,
                            },
                            recommendations=[
                                "Investigate revenue decline causes",
                                "Implement retention strategies",
                                "Focus on customer acquisition",
                            ],
                        )
                        alerts.append(alert)

            elif forecast.type == ForecastType.CHURN:
                # Check for high churn
                if forecast.predictions:
                    avg_churn = statistics.mean(
                        [p.get("predicted_churn_rate", 0) for p in forecast.predictions]
                    )

                    if avg_churn > 10:  # > 10% churn
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            title="High Churn Rate Forecast",
                            description=f"Forecast predicts average churn rate of {avg_churn:.1f}% over {forecast.time_horizon} days",
                            severity=AlertSeverity.CRITICAL
                            if avg_churn > 15
                            else AlertSeverity.WARNING,
                            category="churn_forecast",
                            confidence=forecast.accuracy_score,
                            predicted_impact="critical" if avg_churn > 15 else "high",
                            data_source="churn_forecast",
                            metrics={
                                "average_churn_rate": avg_churn,
                                "time_horizon": forecast.time_horizon,
                                "confidence_interval": forecast.confidence_interval,
                            },
                            recommendations=[
                                "Implement customer success program",
                                "Improve product value proposition",
                                "Address customer pain points",
                            ],
                        )
                        alerts.append(alert)

            elif forecast.type == ForecastType.USAGE:
                # Check for usage decline
                if len(forecast.predictions) >= 2:
                    first_usage = forecast.predictions[0].get("predicted_usage", 0)
                    last_usage = forecast.predictions[-1].get("predicted_usage", 0)

                    if last_usage < first_usage * 0.7:  # 30% decline
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            title="Usage Decline Forecast",
                            description=f"Forecast predicts {((first_usage - last_usage) / first_usage * 100):.1f}% usage decline over {forecast.time_horizon} days",
                            severity=AlertSeverity.INFO,
                            category="usage_forecast",
                            confidence=forecast.accuracy_score,
                            predicted_impact="medium",
                            data_source="usage_forecast",
                            metrics={
                                "initial_usage": first_usage,
                                "final_usage": last_usage,
                                "decline_percentage": (
                                    (first_usage - last_usage) / first_usage * 100
                                ),
                                "time_horizon": forecast.time_horizon,
                            },
                            recommendations=[
                                "Investigate usage decline causes",
                                "Improve user engagement",
                                "Add new features or improvements",
                            ],
                        )
                        alerts.append(alert)

        return alerts

    async def save_forecast(self, forecast: Forecast):
        """Save forecast to database"""
        conn = sqlite3.connect("predictive_analytics.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO forecasts 
            (id, type, model, time_horizon, predictions, confidence_interval, 
             accuracy_score, created_at, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                forecast.id,
                forecast.type.value,
                forecast.model.value,
                forecast.time_horizon,
                json.dumps(forecast.predictions),
                json.dumps(forecast.confidence_interval),
                forecast.accuracy_score,
                forecast.created_at.isoformat(),
                forecast.last_updated.isoformat(),
                json.dumps(forecast.metadata),
            ),
        )

        conn.commit()
        conn.close()

    async def save_alert(self, alert: Alert):
        """Save alert to database"""
        conn = sqlite3.connect("predictive_analytics.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO alerts 
            (id, title, description, severity, category, confidence, predicted_impact,
             created_at, expires_at, is_active, data_source, metrics, recommendations, related_alerts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alert.id,
                alert.title,
                alert.description,
                alert.severity.value,
                alert.category,
                alert.confidence,
                alert.predicted_impact,
                alert.created_at.isoformat(),
                alert.expires_at.isoformat() if alert.expires_at else None,
                alert.is_active,
                alert.data_source,
                json.dumps(alert.metrics),
                json.dumps(alert.recommendations),
                json.dumps(alert.related_alerts),
            ),
        )

        conn.commit()
        conn.close()

    async def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        conn = sqlite3.connect("predictive_analytics.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM alerts WHERE is_active = 1 
            ORDER BY created_at DESC
        """)

        alerts = []
        for row in cursor.fetchall():
            alert = Alert(
                id=row[0],
                title=row[1],
                description=row[2],
                severity=AlertSeverity(row[3]),
                category=row[4],
                confidence=row[5],
                predicted_impact=row[6],
                created_at=datetime.fromisoformat(row[7]),
                expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
                is_active=row[9],
                data_source=row[10],
                metrics=json.loads(row[11]),
                recommendations=json.loads(row[12]),
                related_alerts=json.loads(row[13]),
            )
            alerts.append(alert)

        conn.close()
        return alerts

    async def cleanup_expired_alerts(self):
        """Clean up expired alerts"""
        conn = sqlite3.connect("predictive_analytics.db")
        cursor = conn.cursor()

        # Mark expired alerts as inactive
        cursor.execute(
            """
            UPDATE alerts SET is_active = 0 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """,
            (datetime.now().isoformat(),),
        )

        conn.commit()
        conn.close()

        logger.info("Cleaned up expired alerts")


# Global predictive analytics engine
predictive_engine = PredictiveAnalyticsEngine()


async def main():
    """Main predictive analytics function"""
    logger.info("🔮 Starting ZEJZL.NET Predictive Analytics Engine")

    # Sample data for demonstration
    revenue_data = [
        {"date": "2026-01-01", "revenue": 1000},
        {"date": "2026-01-02", "revenue": 1050},
        {"date": "2026-01-03", "revenue": 1100},
        {"date": "2026-01-04", "revenue": 1080},
        {"date": "2026-01-05", "revenue": 1150},
        {"date": "2026-01-06", "revenue": 1200},
        {"date": "2026-01-07", "revenue": 1180},
    ]

    usage_data = [
        {"date": "2026-01-01", "api_calls": 100},
        {"date": "2026-01-02", "api_calls": 105},
        {"date": "2026-01-03", "api_calls": 110},
        {"date": "2026-01-04", "api_calls": 108},
        {"date": "2026-01-05", "api_calls": 115},
        {"date": "2026-01-06", "api_calls": 120},
        {"date": "2026-01-07", "api_calls": 118},
    ]

    churn_data = [
        {"date": "2026-01-01", "churned_customers": 5, "total_customers": 100},
        {"date": "2026-01-02", "churned_customers": 4, "total_customers": 105},
        {"date": "2026-01-03", "churned_customers": 6, "total_customers": 110},
        {"date": "2026-01-04", "churned_customers": 3, "total_customers": 115},
        {"date": "2026-01-05", "churned_customers": 7, "total_customers": 120},
        {"date": "2026-01-06", "churned_customers": 5, "total_customers": 125},
        {"date": "2026-01-07", "churned_customers": 4, "total_customers": 130},
    ]

    # Generate forecasts
    revenue_forecast = await predictive_engine.generate_revenue_forecast(
        revenue_data, 30
    )
    usage_forecast = await predictive_engine.generate_usage_forecast(usage_data, 30)
    churn_forecast = await predictive_engine.generate_churn_forecast(churn_data, 30)

    # Generate alerts
    anomaly_alerts = await predictive_engine.detect_anomalies(revenue_data)
    forecast_alerts = await predictive_engine.generate_forecast_alerts(
        [revenue_forecast, usage_forecast, churn_forecast]
    )

    all_alerts = anomaly_alerts + forecast_alerts

    # Save alerts
    for alert in all_alerts:
        await predictive_engine.save_alert(alert)

    logger.info(f"✅ Generated 3 forecasts and {len(all_alerts)} alerts")


if __name__ == "__main__":
    asyncio.run(main())
