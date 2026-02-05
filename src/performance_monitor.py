#!/usr/bin/env python3
"""
ZEJZL.NET Performance Monitoring System
Tracks system performance, detects bottlenecks, and provides health metrics
"""

import time
import asyncio
import logging
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None


@dataclass
class SystemHealth:
    status: str  # healthy, warning, critical
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    response_time: Optional[float] = None
    error_rate: Optional[float] = None
    uptime: Optional[float] = None


class PerformanceMonitor:
    """Monitor system performance and detect issues"""

    def __init__(self):
        self.metrics_history: List[PerformanceMetric] = []
        self.start_time = datetime.now()
        self.last_check = datetime.now()
        self.health_checks: List[SystemHealth] = []
        self.alert_thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "disk_warning": 85.0,
            "disk_critical": 95.0,
            "response_time_warning": 2000.0,  # ms
            "response_time_critical": 5000.0,  # ms
            "error_rate_warning": 5.0,  # %
            "error_rate_critical": 10.0,  # %
        }

    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk metrics
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # Process information
            current_process = psutil.Process()

            # Network metrics
            network = psutil.net_io_counters()

            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "frequency": psutil.cpu_freq()._asdict()
                    if psutil.cpu_freq()
                    else None,
                },
                "memory": {
                    "percent": memory_percent,
                    "available": memory.available,
                    "used": memory.used,
                    "total": memory.total,
                },
                "disk": {
                    "percent": disk_percent,
                    "free": disk.free,
                    "used": disk.used,
                    "total": disk.total,
                },
                "process": {
                    "pid": current_process.pid,
                    "memory_percent": current_process.memory_percent(),
                    "cpu_percent": current_process.cpu_percent(),
                    "threads": current_process.num_threads(),
                    "fds": current_process.num_fds()
                    if hasattr(current_process, "num_fds")
                    else None,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
                "uptime": (datetime.now() - self.start_time).total_seconds(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def check_health(self, metrics: Dict[str, Any]) -> SystemHealth:
        """Check system health based on metrics"""
        try:
            status = "healthy"

            # Check CPU
            cpu_percent = metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > self.alert_thresholds["cpu_critical"]:
                status = "critical"
            elif cpu_percent > self.alert_thresholds["cpu_warning"]:
                status = "warning"

            # Check Memory
            memory_percent = metrics.get("memory", {}).get("percent", 0)
            if memory_percent > self.alert_thresholds["memory_critical"]:
                status = "critical"
            elif memory_percent > self.alert_thresholds["memory_warning"]:
                status = "warning"

            # Check Disk
            disk_percent = metrics.get("disk", {}).get("percent", 0)
            if disk_percent > self.alert_thresholds["disk_critical"]:
                status = "critical"
            elif disk_percent > self.alert_thresholds["disk_warning"]:
                status = "warning"

            # Get process response time (mock - would come from actual app monitoring)
            response_time = metrics.get("response_time", 100.0)  # Mock 100ms

            # Get error rate (mock - would come from actual app monitoring)
            error_rate = metrics.get("error_rate", 0.0)

            health = SystemHealth(
                status=status,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                response_time=response_time,
                error_rate=error_rate,
                uptime=metrics.get("uptime", 0.0),
            )

            self.health_checks.append(health)

            # Keep only last 100 health checks
            if len(self.health_checks) > 100:
                self.health_checks = self.health_checks[-100:]

            return health

        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return SystemHealth(
                status="error", cpu_percent=0.0, memory_percent=0.0, disk_percent=0.0
            )

    def detect_bottlenecks(self, health: SystemHealth) -> List[str]:
        """Detect performance bottlenecks"""
        bottlenecks = []

        # CPU bottleneck
        if health.cpu_percent > self.alert_thresholds["cpu_warning"]:
            bottlenecks.append(f"High CPU usage: {health.cpu_percent:.1f}%")

        # Memory bottleneck
        if health.memory_percent > self.alert_thresholds["memory_warning"]:
            bottlenecks.append(f"High memory usage: {health.memory_percent:.1f}%")

        # Disk bottleneck
        if health.disk_percent > self.alert_thresholds["disk_warning"]:
            bottlenecks.append(f"High disk usage: {health.disk_percent:.1f}%")

        # Response time bottleneck
        if (
            health.response_time
            and health.response_time > self.alert_thresholds["response_time_warning"]
        ):
            bottlenecks.append(f"Slow response time: {health.response_time:.0f}ms")

        # Error rate bottleneck
        if (
            health.error_rate
            and health.error_rate > self.alert_thresholds["error_rate_warning"]
        ):
            bottlenecks.append(f"High error rate: {health.error_rate:.1f}%")

        return bottlenecks

    def calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends from historical data"""
        if len(self.health_checks) < 10:
            return {"error": "Insufficient data for trend analysis"}

        try:
            recent_checks = self.health_checks[-20:]  # Last 20 checks

            # Calculate averages
            avg_cpu = sum(check.cpu_percent for check in recent_checks) / len(
                recent_checks
            )
            avg_memory = sum(check.memory_percent for check in recent_checks) / len(
                recent_checks
            )
            avg_disk = sum(check.disk_percent for check in recent_checks) / len(
                recent_checks
            )

            # Calculate trends (compare to older data)
            if len(self.health_checks) >= 20:
                older_checks = (
                    self.health_checks[-40:-20]
                    if len(self.health_checks) >= 40
                    else self.health_checks[:-20]
                )

                if older_checks:
                    avg_cpu_old = sum(
                        check.cpu_percent for check in older_checks
                    ) / len(older_checks)
                    avg_memory_old = sum(
                        check.memory_percent for check in older_checks
                    ) / len(older_checks)
                    avg_disk_old = sum(
                        check.disk_percent for check in older_checks
                    ) / len(older_checks)

                    cpu_trend = avg_cpu - avg_cpu_old
                    memory_trend = avg_memory - avg_memory_old
                    disk_trend = avg_disk - avg_disk_old
                else:
                    cpu_trend = memory_trend = disk_trend = 0.0

            # Count status occurrences
            status_counts = {"healthy": 0, "warning": 0, "critical": 0}
            for check in recent_checks:
                status_counts[check.status] += 1

            return {
                "period": f"Last {len(recent_checks)} checks",
                "averages": {"cpu": avg_cpu, "memory": avg_memory, "disk": avg_disk},
                "trends": {
                    "cpu": cpu_trend if "cpu_trend" in locals() else 0.0,
                    "memory": memory_trend if "memory_trend" in locals() else 0.0,
                    "disk": disk_trend if "disk_trend" in locals() else 0.0,
                },
                "status_distribution": status_counts,
                "uptime_percentage": (
                    sum(1 for check in recent_checks if check.status == "healthy")
                    / len(recent_checks)
                )
                * 100,
            }

        except Exception as e:
            logger.error(f"Error calculating trends: {e}")
            return {"error": str(e)}

    async def start_monitoring(self, interval: int = 30):
        """Start continuous monitoring"""
        logger.info(f"Starting performance monitoring with {interval}s interval")

        while True:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()

                # Check health
                health = self.check_health(metrics)

                # Detect bottlenecks
                bottlenecks = self.detect_bottlenecks(health)

                # Log status
                logger.info(
                    f"Health: {health.status} | CPU: {health.cpu_percent:.1f}% | Memory: {health.memory_percent:.1f}% | Disk: {health.disk_percent:.1f}%"
                )

                # Log bottlenecks if any
                if bottlenecks:
                    logger.warning(
                        f"⚠️ Performance bottlenecks detected: {'; '.join(bottlenecks)}"
                    )

                # Save metrics to file
                await self.save_metrics(metrics, health, bottlenecks)

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Performance monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    async def save_metrics(
        self, metrics: Dict[str, Any], health: SystemHealth, bottlenecks: List[str]
    ):
        """Save metrics to file"""
        try:
            # Create monitoring directory
            monitor_dir = Path("monitoring")
            monitor_dir.mkdir(exist_ok=True)

            # Save current metrics
            with open(monitor_dir / "current_metrics.json", "w") as f:
                json.dump(
                    {
                        "metrics": metrics,
                        "health": asdict(health),
                        "bottlenecks": bottlenecks,
                        "timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            # Save historical data (append)
            with open(monitor_dir / "metrics_history.jsonl", "a") as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "status": health.status,
                            "cpu_percent": health.cpu_percent,
                            "memory_percent": health.memory_percent,
                            "disk_percent": health.disk_percent,
                            "response_time": health.response_time,
                            "error_rate": health.error_rate,
                            "bottlenecks": bottlenecks,
                        }
                    )
                    + "\n"
                )

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        try:
            if not self.health_checks:
                return {"error": "No performance data available"}

            trends = self.calculate_trends()

            # Get latest health check
            latest_health = self.health_checks[-1] if self.health_checks else None

            # Calculate uptime (healthy percentage over time)
            total_checks = len(self.health_checks)
            healthy_checks = sum(
                1 for check in self.health_checks if check.status == "healthy"
            )
            uptime_percentage = (
                (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            )

            report = {
                "summary": {
                    "monitoring_duration": str(datetime.now() - self.start_time),
                    "total_checks": total_checks,
                    "healthy_checks": healthy_checks,
                    "uptime_percentage": round(uptime_percentage, 2),
                    "latest_health": asdict(latest_health) if latest_health else None,
                },
                "trends": trends,
                "alerts": {
                    "current_bottlenecks": self.detect_bottlenecks(latest_health)
                    if latest_health
                    else [],
                    "thresholds": self.alert_thresholds,
                },
                "recommendations": self.generate_recommendations(latest_health, trends),
            }

            return report

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

    def generate_recommendations(
        self, health: SystemHealth, trends: Dict[str, Any]
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        if not health:
            return ["No health data available"]

        # CPU recommendations
        if health.cpu_percent > 80:
            recommendations.append(
                "Consider scaling up CPU resources or optimizing CPU-intensive operations"
            )

        # Memory recommendations
        if health.memory_percent > 80:
            recommendations.append(
                "Memory usage is high - consider adding more RAM or optimizing memory usage"
            )

        # Disk recommendations
        if health.disk_percent > 85:
            recommendations.append(
                "Disk space is running low - clean up files or add storage"
            )

        # Response time recommendations
        if health.response_time and health.response_time > 1000:
            recommendations.append(
                "Response times are slow - optimize database queries and API calls"
            )

        # Trend-based recommendations
        if "trends" in trends:
            if trends["trends"]["cpu"] > 5:
                recommendations.append(
                    "CPU usage is increasing trend - investigate growing resource demands"
                )

            if trends["trends"]["memory"] > 5:
                recommendations.append(
                    "Memory usage is increasing trend - check for memory leaks"
                )

            if trends["trends"]["disk"] > 5:
                recommendations.append(
                    "Disk usage is increasing trend - monitor log file growth"
                )

        # Uptime recommendations
        if "uptime_percentage" in trends and trends["uptime_percentage"] < 95:
            recommendations.append(
                "System uptime is below 95% - investigate reliability issues"
            )

        return recommendations if recommendations else ["System performance is optimal"]


# Performance monitoring instance
performance_monitor = PerformanceMonitor()


async def main():
    """Main performance monitoring function"""
    logger.info("🔍 Starting ZEJZL.NET Performance Monitoring")

    # Start monitoring in background
    monitor_task = asyncio.create_task(
        performance_monitor.start_monitoring(interval=60)
    )

    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(3600)  # Check every hour

            # Log performance report
            report = performance_monitor.get_performance_report()
            logger.info(
                f"📊 Performance Report: Uptime {report.get('summary', {}).get('uptime_percentage', 0)}%"
            )

            # Log recommendations if any issues
            recommendations = report.get("recommendations", [])
            if recommendations and recommendations != ["System performance is optimal"]:
                for rec in recommendations:
                    logger.warning(f"💡 Recommendation: {rec}")

    except KeyboardInterrupt:
        logger.info("Performance monitoring stopped by user")
    except Exception as e:
        logger.error(f"Performance monitoring error: {e}")
    finally:
        monitor_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
