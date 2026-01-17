#!/usr/bin/env python3
"""
Telemetry and Performance Tracking for ZEJZL.NET
Tracks metrics for AI providers, agents, and system performance
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime
import json

logger = logging.getLogger("Telemetry")


@dataclass
class MetricSnapshot:
    """A single metric measurement"""
    timestamp: float
    value: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a component"""
    name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_response_time: float = 0.0
    min_response_time: Optional[float] = None
    max_response_time: Optional[float] = None
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_call_timestamp: Optional[float] = None

    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if self.successful_calls == 0:
            return 0.0
        return self.total_response_time / self.successful_calls

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def p95_response_time(self) -> float:
        """Calculate 95th percentile response time"""
        if not self.recent_response_times:
            return 0.0
        sorted_times = sorted(self.recent_response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "average_response_time": self.average_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "p95_response_time": self.p95_response_time,
            "success_rate": self.success_rate,
            "error_count_by_type": dict(self.error_count_by_type),
            "last_call_timestamp": self.last_call_timestamp
        }


class TelemetryCollector:
    """
    Collects and aggregates telemetry data
    """

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.custom_metrics: Dict[str, List[MetricSnapshot]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self.start_time = time.time()

    async def record_call(self, component: str, response_time: float,
                         success: bool, error_type: Optional[str] = None):
        """Record a function call with timing"""
        async with self._lock:
            if component not in self.metrics:
                self.metrics[component] = PerformanceMetrics(name=component)

            metrics = self.metrics[component]
            metrics.total_calls += 1
            metrics.last_call_timestamp = time.time()

            if success:
                metrics.successful_calls += 1
                metrics.total_response_time += response_time
                metrics.recent_response_times.append(response_time)

                # Update min/max
                if metrics.min_response_time is None or response_time < metrics.min_response_time:
                    metrics.min_response_time = response_time
                if metrics.max_response_time is None or response_time > metrics.max_response_time:
                    metrics.max_response_time = response_time
            else:
                metrics.failed_calls += 1
                if error_type:
                    metrics.error_count_by_type[error_type] += 1

    async def record_metric(self, name: str, value: float, metadata: Optional[Dict] = None):
        """Record a custom metric"""
        async with self._lock:
            snapshot = MetricSnapshot(
                timestamp=time.time(),
                value=value,
                metadata=metadata or {}
            )
            self.custom_metrics[name].append(snapshot)

            # Keep only last 1000 snapshots per metric
            if len(self.custom_metrics[name]) > 1000:
                self.custom_metrics[name] = self.custom_metrics[name][-1000:]

    async def get_metrics(self, component: Optional[str] = None) -> Dict:
        """Get metrics for a component or all components"""
        async with self._lock:
            if component:
                if component in self.metrics:
                    return self.metrics[component].to_dict()
                return {}

            return {
                name: metrics.to_dict()
                for name, metrics in self.metrics.items()
            }

    async def get_summary(self) -> Dict:
        """Get summary of all metrics"""
        async with self._lock:
            uptime = time.time() - self.start_time

            total_calls = sum(m.total_calls for m in self.metrics.values())
            total_successful = sum(m.successful_calls for m in self.metrics.values())
            total_failed = sum(m.failed_calls for m in self.metrics.values())

            return {
                "uptime_seconds": uptime,
                "total_calls": total_calls,
                "total_successful": total_successful,
                "total_failed": total_failed,
                "overall_success_rate": (total_successful / total_calls * 100) if total_calls > 0 else 0,
                "components_tracked": len(self.metrics),
                "custom_metrics_tracked": len(self.custom_metrics)
            }

    async def get_report(self) -> str:
        """Generate a human-readable report"""
        summary = await self.get_summary()
        all_metrics = await self.get_metrics()

        lines = [
            "="*70,
            "ZEJZL.NET Performance Report",
            "="*70,
            f"\nUptime: {summary['uptime_seconds']:.1f}s",
            f"Total Calls: {summary['total_calls']}",
            f"Success Rate: {summary['overall_success_rate']:.1f}%",
            f"Components Tracked: {summary['components_tracked']}",
            "\n" + "="*70,
            "Component Metrics:",
            "="*70
        ]

        for name, metrics in all_metrics.items():
            lines.extend([
                f"\n{name}:",
                f"  Total Calls: {metrics['total_calls']}",
                f"  Success Rate: {metrics['success_rate']:.1f}%",
                f"  Avg Response Time: {metrics['average_response_time']:.3f}s",
                f"  P95 Response Time: {metrics['p95_response_time']:.3f}s",
                f"  Min/Max: {metrics['min_response_time']:.3f}s / {metrics['max_response_time']:.3f}s"
            ])

            if metrics['error_count_by_type']:
                lines.append("  Errors:")
                for error_type, count in metrics['error_count_by_type'].items():
                    lines.append(f"    - {error_type}: {count}")

        lines.append("\n" + "="*70)
        return "\n".join(lines)

    async def export_json(self, filepath: str):
        """Export metrics to JSON file"""
        data = {
            "summary": await self.get_summary(),
            "metrics": await self.get_metrics(),
            "custom_metrics": {
                name: [asdict(snapshot) for snapshot in snapshots[-100:]]
                for name, snapshots in self.custom_metrics.items()
            },
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    async def reset(self):
        """Reset all metrics"""
        async with self._lock:
            self.metrics.clear()
            self.custom_metrics.clear()
            self.start_time = time.time()
            logger.info("Telemetry metrics reset")


# Global telemetry collector
_global_telemetry: Optional[TelemetryCollector] = None


def get_telemetry() -> TelemetryCollector:
    """Get global telemetry collector instance"""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = TelemetryCollector()
    return _global_telemetry


class telemetry_track:
    """
    Decorator to automatically track function performance
    """

    def __init__(self, component_name: str):
        self.component_name = component_name

    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            telemetry = get_telemetry()
            start_time = time.time()
            success = False
            error_type = None

            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_type = type(e).__name__
                raise
            finally:
                response_time = time.time() - start_time
                await telemetry.record_call(
                    self.component_name,
                    response_time,
                    success,
                    error_type
                )

        return wrapper
