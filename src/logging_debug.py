#!/usr/bin/env python3
"""
Enhanced Logging and Debugging System for ZEJZL.NET
Provides structured logging, debugging, monitoring, and observability features
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio
import sys
from functools import wraps
import traceback
import psutil
import os

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_entry, indent=2 if os.environ.get('LOG_PRETTY', '').lower() == 'true' else None)

class ZEJZLLogger:
    """Enhanced logging system for ZEJZL.NET"""

    def __init__(self, name: str = "zejzl"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

        # File handler for persistent logs
        log_dir = Path.home() / ".zejzl" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "zejzl.log")
        file_handler.setFormatter(StructuredFormatter())
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        # Performance log handler
        perf_handler = logging.FileHandler(log_dir / "performance.log")
        perf_handler.setFormatter(StructuredFormatter())
        perf_handler.setLevel(logging.INFO)
        self.perf_logger = logging.getLogger(f"{name}.performance")
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.setLevel(logging.INFO)

        # Debug log handler
        debug_handler = logging.FileHandler(log_dir / "debug.log")
        debug_handler.setFormatter(StructuredFormatter())
        debug_handler.setLevel(logging.DEBUG)
        self.debug_logger = logging.getLogger(f"{name}.debug")
        self.debug_logger.addHandler(debug_handler)
        self.debug_logger.setLevel(logging.DEBUG)

    def log_with_context(self, level: str, message: str, **context):
        """Log with additional context fields"""
        extra = {'extra_fields': context}
        log_method = getattr(self.logger, level)
        log_method(message, extra=extra)

    def info(self, message: str, **context):
        self.log_with_context('info', message, **context)

    def debug(self, message: str, **context):
        self.log_with_context('debug', message, **context)

    def warning(self, message: str, **context):
        self.log_with_context('warning', message, **context)

    def error(self, message: str, **context):
        self.log_with_context('error', message, **context)

    def critical(self, message: str, **context):
        self.log_with_context('critical', message, **context)

    def performance(self, operation: str, duration: float, **metrics):
        """Log performance metrics"""
        self.perf_logger.info(f"Performance: {operation}", extra={
            'extra_fields': {
                'operation': operation,
                'duration_ms': duration * 1000,
                'metrics': metrics
            }
        })

    def request_debug(self, request_id: str, operation: str, data: Any = None):
        """Debug logging for requests"""
        self.debug_logger.debug(f"Request {request_id}: {operation}", extra={
            'extra_fields': {
                'request_id': request_id,
                'operation': operation,
                'data': str(data) if data else None
            }
        })

# Global logger instance
logger = ZEJZLLogger()

@dataclass
class DebugSnapshot:
    """System state snapshot for debugging"""
    timestamp: datetime
    system_info: Dict[str, Any]
    agent_states: Dict[str, Any]
    magic_state: Dict[str, Any]
    active_requests: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    recent_logs: List[Dict[str, Any]]

class DebugMonitor:
    """Debug monitoring and system introspection"""

    def __init__(self):
        self.snapshots: List[DebugSnapshot] = []
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.request_counter = 0

    def start_request(self, operation: str, **metadata) -> str:
        """Start tracking a request"""
        request_id = f"req_{self.request_counter}"
        self.request_counter += 1

        self.active_requests[request_id] = {
            "operation": operation,
            "start_time": time.time(),
            "metadata": metadata,
            "status": "active"
        }

        logger.request_debug(request_id, f"STARTED: {operation}", metadata)
        return request_id

    def end_request(self, request_id: str, result: Any = None, error: Exception = None):
        """End tracking a request"""
        if request_id not in self.active_requests:
            logger.warning(f"Attempted to end unknown request: {request_id}")
            return

        request = self.active_requests[request_id]
        duration = time.time() - request["start_time"]
        request.update({
            "end_time": time.time(),
            "duration": duration,
            "result": str(result) if result else None,
            "error": str(error) if error else None,
            "status": "error" if error else "completed"
        })

        logger.performance(f"request_{request['operation']}", duration,
                          request_id=request_id, success=error is None)

        if error:
            logger.request_debug(request_id, f"FAILED: {error}", request)
        else:
            logger.request_debug(request_id, f"COMPLETED: {duration:.3f}s", result)

    def record_performance(self, operation: str, duration: float, **metrics):
        """Record performance metrics"""
        entry = {
            "timestamp": datetime.now(),
            "operation": operation,
            "duration": duration,
            "metrics": metrics
        }
        self.performance_history.append(entry)

        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

        logger.performance(operation, duration, **metrics)

    async def create_snapshot(self, bus=None) -> DebugSnapshot:
        """Create a comprehensive system snapshot"""
        try:
            # System information
            system_info = {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
                "disk_usage": psutil.disk_usage('/')._asdict(),
                "process_memory": psutil.Process().memory_info()._asdict(),
                "uptime": time.time() - psutil.boot_time()
            }

            # Agent states (simplified)
            agent_states = {}
            if bus and hasattr(bus, 'providers'):
                agent_states = {
                    name: {
                        "status": "active",
                        "model": getattr(provider, 'model', 'unknown'),
                        "last_used": getattr(provider, '_last_used', None)
                    } for name, provider in bus.providers.items()
                }

            # Magic state
            magic_state = {}
            if bus and hasattr(bus, 'magic'):
                magic = bus.magic
                magic_state = {
                    "energy_level": magic.energy_level,
                    "acorn_reserve": magic.acorn_reserve,
                    "is_shielded": magic.is_shielded,
                    "circuit_breakers": len(magic.circuit_breakers),
                    "healing_history_count": len(magic.healing_history)
                }

            # Active requests
            active_requests = list(self.active_requests.values())

            # Performance metrics
            performance_metrics = {
                "total_requests": len(self.performance_history),
                "avg_response_time": sum(p["duration"] for p in self.performance_history[-100:]) / max(len(self.performance_history[-100:]), 1),
                "error_rate": sum(1 for p in self.performance_history[-100:] if "error" in p.get("metrics", {})) / max(len(self.performance_history[-100:]), 1)
            }

            # Recent logs (last 50 entries from performance history)
            recent_logs = [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "operation": entry["operation"],
                    "duration": entry["duration"],
                    "metrics": entry.get("metrics", {})
                }
                for entry in self.performance_history[-50:]
            ]

            snapshot = DebugSnapshot(
                timestamp=datetime.now(),
                system_info=system_info,
                agent_states=agent_states,
                magic_state=magic_state,
                active_requests=active_requests,
                performance_metrics=performance_metrics,
                recent_logs=recent_logs
            )

            # Keep only last 10 snapshots
            self.snapshots.append(snapshot)
            if len(self.snapshots) > 10:
                self.snapshots = self.snapshots[-10:]

            logger.debug("Debug snapshot created", snapshot_count=len(self.snapshots))
            return snapshot

        except Exception as e:
            logger.error(f"Failed to create debug snapshot: {e}")
            return DebugSnapshot(
                timestamp=datetime.now(),
                system_info={"error": str(e)},
                agent_states={},
                magic_state={},
                active_requests=[],
                performance_metrics={},
                recent_logs=[]
            )

# Global debug monitor
debug_monitor = DebugMonitor()

# Decorators for automatic logging and monitoring
def log_execution(level: str = "info"):
    """Decorator to log function execution"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            request_id = debug_monitor.start_request(func_name)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                debug_monitor.record_performance(func_name, duration, success=True)
                logger.log_with_context(level, f"Function completed: {func_name}",
                                      function=func_name, duration=duration, success=True)

                debug_monitor.end_request(request_id, result=result)
                return result

            except Exception as e:
                duration = time.time() - start_time
                debug_monitor.record_performance(func_name, duration, success=False, error=str(e))
                logger.log_with_context("error", f"Function failed: {func_name}",
                                      function=func_name, duration=duration, error=str(e), traceback=traceback.format_exc())

                debug_monitor.end_request(request_id, error=e)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__qualname__}"
            request_id = debug_monitor.start_request(func_name)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                debug_monitor.record_performance(func_name, duration, success=True)
                logger.log_with_context(level, f"Function completed: {func_name}",
                                      function=func_name, duration=duration, success=True)

                debug_monitor.end_request(request_id, result=result)
                return result

            except Exception as e:
                duration = time.time() - start_time
                debug_monitor.record_performance(func_name, duration, success=False, error=str(e))
                logger.log_with_context("error", f"Function failed: {func_name}",
                                      function=func_name, duration=duration, error=str(e), traceback=traceback.format_exc())

                debug_monitor.end_request(request_id, error=e)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

def log_ai_interaction(provider: str, operation: str = "ai_call"):
    """Decorator specifically for AI provider interactions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request_id = debug_monitor.start_request(f"{provider}.{operation}")

            # Log input parameters (sanitized)
            input_data = {
                "provider": provider,
                "operation": operation,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }

            logger.debug(f"AI call started: {provider}.{operation}", **input_data)

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Log success with metrics
                output_data = {
                    "provider": provider,
                    "operation": operation,
                    "duration": duration,
                    "success": True,
                    "response_length": len(str(result)) if result else 0
                }

                logger.info(f"AI call completed: {provider}.{operation} ({duration:.3f}s)", **output_data)
                debug_monitor.record_performance(f"{provider}.{operation}", duration,
                                               tokens=len(str(result)), success=True)

                debug_monitor.end_request(request_id, result=f"Response: {len(str(result))} chars")
                return result

            except Exception as e:
                duration = time.time() - start_time

                error_data = {
                    "provider": provider,
                    "operation": operation,
                    "duration": duration,
                    "error": str(e),
                    "error_type": type(e).__name__
                }

                logger.error(f"AI call failed: {provider}.{operation}", **error_data)
                debug_monitor.record_performance(f"{provider}.{operation}", duration,
                                               success=False, error=str(e))

                debug_monitor.end_request(request_id, error=e)
                raise

        return wrapper
    return decorator

# Initialize logging
def setup_logging(level: str = "INFO", pretty: bool = False):
    """Setup logging configuration"""
    os.environ['LOG_PRETTY'] = str(pretty).lower()

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(numeric_level)

    # Set up our custom logger
    global logger
    logger = ZEJZLLogger()

    logger.info("Enhanced logging system initialized", log_level=level, pretty=pretty)

# Export functions and classes
__all__ = [
    'logger',
    'debug_monitor',
    'log_execution',
    'log_ai_interaction',
    'setup_logging',
    'DebugSnapshot'
]