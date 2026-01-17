#!/usr/bin/env python3
"""
ZEJZL.NET Web Dashboard
Real-time monitoring and control interface for the AI framework
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# Import our framework
from ai_framework import AsyncMessageBus
from base import get_ai_provider_bus
from src.magic import FairyMagic
from src.usage_analytics import UsageAnalytics
from src.multimodal_processing import multimodal_processor
from src.multimodal_ai import create_multimodal_message, MultiModalContent, ModalityType
from telemetry import get_telemetry
from src.performance import record_metric
from src.logging_debug import debug_monitor, logger as debug_logger

logger = logging.getLogger(__name__)

app = FastAPI(title="ZEJZL.NET Dashboard", version="1.0.0")

# Templates and static files (we'll create these)
templates = Jinja2Templates(directory="web/templates")

class DashboardServer:
    """Web dashboard for ZEJZL.NET monitoring and control"""

    def __init__(self):
        self.bus: AsyncMessageBus = None
        self.magic: FairyMagic = None
        self.connected_clients = set()

    async def initialize(self):
        """Initialize the dashboard with framework components"""
        try:
            self.bus = await get_ai_provider_bus()
            self.magic = self.bus.magic

            # Initialize multi-modal providers
            await self._initialize_multimodal_providers()

            logger.info("Dashboard initialized with AI framework and multi-modal support")
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            # Create fallback instances for demo

    async def _initialize_multimodal_providers(self):
        """Initialize multi-modal AI providers"""
        try:
            # Import providers
            from src.multimodal_ai import GPT4VisionProvider, GeminiVisionProvider

            # Get API keys from environment
            import os
            openai_key = os.environ.get("OPENAI_API_KEY", "")
            gemini_key = os.environ.get("GEMINI_API_KEY", "")

            # Register providers if keys are available
            if openai_key:
                gpt4_provider = GPT4VisionProvider(openai_key)
                await gpt4_provider.initialize()
                multimodal_processor.register_multimodal_provider(gpt4_provider)
                logger.info("Registered GPT-4 Vision provider")

            if gemini_key:
                gemini_provider = GeminiVisionProvider(gemini_key)
                await gemini_provider.initialize()
                multimodal_processor.register_multimodal_provider(gemini_provider)
                logger.info("Registered Gemini Vision provider")

        except Exception as e:
            logger.warning(f"Failed to initialize multi-modal providers: {e}")
            # Continue without multi-modal support
            self.bus = AsyncMessageBus()
            await self.bus.start()
            self.magic = FairyMagic()

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Basic system info
            status = {
                "timestamp": datetime.now().isoformat(),
                "magic_system": {
                    "energy_level": self.magic.energy_level,
                    "max_energy": self.magic.max_energy,
                    "acorn_reserve": self.magic.acorn_reserve,
                    "is_shielded": self.magic.is_shielded,
                    "circuit_breakers": len(self.magic.circuit_breakers),
                    "healing_history": len(self.magic.healing_history)
                },
                "ai_providers": {},
                "metrics": {},
                "recent_activity": []
            }

            # Provider status
            if self.bus and hasattr(self.bus, 'providers'):
                for name, provider in self.bus.providers.items():
                    status["ai_providers"][name] = {
                        "model": getattr(provider, 'model', 'unknown'),
                        "status": "active"
                    }

            # Get basic telemetry data
            telemetry = get_telemetry()
            if telemetry:
                try:
                    summary_data = await telemetry.get_summary()
                    status["metrics"] = {
                        "total_calls": summary_data.get("total_calls", 0),
                        "avg_response_time": summary_data.get("avg_response_time", 0),
                        "success_rate": summary_data.get("success_rate", 0)
                    }
                except:
                    status["metrics"] = {"total_calls": 0, "avg_response_time": 0, "success_rate": 0}
                status["recent_activity"] = []  # Simplified for now

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "magic_system": {"energy_level": 0, "status": "error"}
            }

# Global dashboard instance
dashboard = DashboardServer()

@app.on_event("startup")
async def startup_event():
    """Initialize dashboard on startup"""
    debug_logger.info("Starting ZEJZL.NET Web Dashboard")
    await dashboard.initialize()
    debug_logger.info("Dashboard initialization complete")

@app.get("/", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/status")
async def get_status():
    """Get current system status"""
    return await dashboard.get_system_status()

@app.get("/api/personalities")
async def get_personalities():
    """Get available agent personalities"""
    try:
        from src.agent_personality import AGENT_PERSONALITIES
        return {
            "personalities": {
                name: {
                    "name": p.name,
                    "communication_style": p.communication_style.value,
                    "expertise_areas": p.expertise_areas,
                    "behavioral_traits": p.behavioral_traits,
                    "motivational_drivers": p.motivational_drivers
                } for name, p in AGENT_PERSONALITIES.items()
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/metrics")
async def get_metrics():
    """Get detailed metrics"""
    telemetry = get_telemetry()
    if telemetry:
        return await telemetry.get_metrics()
    return {}

@app.get("/api/debug/snapshot")
async def get_debug_snapshot():
    """Get current system debug snapshot"""
    snapshot = await debug_monitor.create_snapshot(dashboard.bus)
    return asdict(snapshot)

@app.get("/api/debug/logs")
async def get_recent_logs(lines: int = 50):
    """Get recent debug logs"""
    try:
        log_dir = Path.home() / ".zejzl" / "logs"
        log_file = log_dir / "debug.log"

        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return {"logs": all_lines[-lines:]}
        else:
            return {"logs": [], "message": "No debug logs found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/debug/performance")
async def get_performance_data():
    """Get performance monitoring data"""
    return {
        "performance_history": debug_monitor.performance_history[-100:],
        "active_requests": list(debug_monitor.active_requests.values()),
        "total_requests": len(debug_monitor.performance_history),
        "active_request_count": len(debug_monitor.active_requests)
    }

@app.post("/api/debug/log-level")
async def set_log_level(level: str):
    """Set logging level (DEBUG, INFO, WARNING, ERROR)"""
    try:
        import logging
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(numeric_level)

        debug_logger.info(f"Log level changed to {level}", new_level=level)
        return {"success": True, "level": level}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    try:
        import psutil
        import platform

        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                }
            },
            "zejzl": {
                "bus_status": "connected" if dashboard.bus else "disconnected",
                "magic_energy": dashboard.magic.energy_level if dashboard.magic else 0,
                "providers_count": len(dashboard.bus.providers) if dashboard.bus else 0,
                "active_requests": len(debug_monitor.active_requests)
            }
        }

        return health_data
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/magic/{action}")
async def magic_action(action: str, background_tasks: BackgroundTasks):
    """Perform magic system actions"""
    try:
        if action == "boost":
            result = await dashboard.magic.acorn_vitality_boost("web_dashboard", {"max_tokens": 1024})
            record_metric("dashboard_magic_boost", 1, {"source": "web"})
            return {"success": True, "result": result}

        elif action == "shield":
            dashboard.magic.is_shielded = not dashboard.magic.is_shielded
            return {"success": True, "shielded": dashboard.magic.is_shielded}

        elif action == "heal":
            result = await dashboard.magic.blue_spark_heal("dashboard_request", "Web interface healing")
            return {"success": True, "result": result}

        return {"success": False, "error": f"Unknown action: {action}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    dashboard.connected_clients.add(websocket)

    try:
        while True:
            # Send status updates every 5 seconds
            status = await dashboard.get_system_status()
            await websocket.send_json(status)
            await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        dashboard.connected_clients.remove(websocket)

@app.post("/api/chat")
async def chat_endpoint(request: Request, background_tasks: BackgroundTasks):
    """Handle chat requests from the web interface"""
    try:
        data = await request.json()
        message = data.get("message", "")
        provider = data.get("provider", "grok")
        consensus = data.get("consensus", False)
        stream = data.get("stream", False)

        if not message:
            return {"error": "No message provided"}

        # Send message through AI bus
        response = await dashboard.bus.send_message(
            content=message,
            provider_name=provider,
            stream=stream,
            consensus=consensus
        )

        # Record the interaction
        mode = "consensus" if consensus else "single"
        record_metric("dashboard_chat", 1, {"provider": provider, "mode": mode})

        return {
            "response": response,
            "provider": provider,
            "consensus": consensus,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {"error": str(e)}


# Analytics Endpoints
analytics = UsageAnalytics()

@app.get("/api/analytics/usage")
async def get_usage_analytics(days: int = 7):
    """Get usage analytics for the specified number of days"""
    try:
        report = await analytics.get_usage_report(days=days)
        return {
            "success": True,
            "data": {
                "period": report.period,
                "total_requests": report.total_requests,
                "total_tokens": report.total_tokens,
                "total_cost_usd": report.total_cost_usd,
                "avg_response_time": report.avg_response_time,
                "success_rate": report.success_rate,
                "provider_breakdown": report.provider_breakdown,
                "hourly_usage": report.hourly_usage[:24]  # Last 24 hours
            }
        }
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/costs")
async def get_cost_analytics(days: int = 30):
    """Get cost analysis for the specified number of days"""
    try:
        cost_analysis = await analytics.get_cost_analysis(days=days)
        return {
            "success": True,
            "data": {
                "period_days": cost_analysis.period_days,
                "total_cost": cost_analysis.total_cost,
                "avg_daily_cost": cost_analysis.avg_daily_cost,
                "avg_request_cost": cost_analysis.avg_request_cost,
                "most_expensive_provider": cost_analysis.most_expensive_provider,
                "cost_trend": cost_analysis.cost_trend,
                "projected_monthly_cost": cost_analysis.projected_monthly_cost
            }
        }
    except Exception as e:
        logger.error(f"Cost analytics endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/provider/{provider}")
async def get_provider_analytics(provider: str, days: int = 7):
    """Get detailed analytics for a specific provider"""
    try:
        provider_data = await analytics.get_provider_performance(provider, days=days)
        return {
            "success": True,
            "data": provider_data
        }
    except Exception as e:
        logger.error(f"Provider analytics endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/analytics/expensive-requests")
async def get_expensive_requests(limit: int = 10):
    """Get the most expensive individual requests"""
    try:
        expensive_requests = await analytics.get_top_expensive_requests(limit=limit)
        return {
            "success": True,
            "data": expensive_requests
        }
    except Exception as e:
        logger.error(f"Expensive requests endpoint error: {e}")
        return {"success": False, "error": str(e)}


# Multi-Modal Endpoints
@app.get("/api/multimodal/providers")
async def get_multimodal_providers():
    """Get available multi-modal providers and their capabilities"""
    try:
        providers = multimodal_processor.get_supported_providers()
        provider_info = multimodal_processor.get_provider_info()
        return {
            "success": True,
            "providers": providers,
            "details": provider_info
        }
    except Exception as e:
        logger.error(f"Multi-modal providers endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/multimodal/analyze-image")
async def analyze_image_endpoint(request: Request):
    """Analyze an image with AI"""
    try:
        data = await request.json()
        image_data = data.get("image_data")  # base64 encoded image
        query = data.get("query", "Describe this image in detail")
        provider = data.get("provider", "gpt4vision")

        if not image_data:
            return {"success": False, "error": "No image data provided"}

        # Create image content
        image_content = MultiModalContent.from_image_base64(image_data)

        # Analyze the image
        analysis = await multimodal_processor.process_image_analysis(image_content, query, provider)

        return {
            "success": True,
            "analysis": analysis,
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Image analysis endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/multimodal/chat")
async def multimodal_chat_endpoint(request: Request):
    """Multi-modal chat with text, images, and other content"""
    try:
        data = await request.json()
        message = data.get("message", "")
        provider = data.get("provider", "gpt4vision")
        attachments = data.get("attachments", [])  # List of {type: "image", data: "base64..."}

        if not message and not attachments:
            return {"success": False, "error": "No message or attachments provided"}

        # Build multi-modal content
        content = []
        if message:
            content.append(MultiModalContent.from_text(message))

        # Process attachments
        for attachment in attachments:
            attachment_type = attachment.get("type", "text")
            attachment_data = attachment.get("data", "")

            if attachment_type == "image":
                if attachment_data.startswith("data:image"):
                    # Handle data URL format
                    base64_data = attachment_data.split(",")[1] if "," in attachment_data else attachment_data
                    content.append(MultiModalContent.from_image_base64(base64_data))
                else:
                    # Assume direct base64
                    content.append(MultiModalContent.from_image_base64(attachment_data))
            elif attachment_type == "text":
                content.append(MultiModalContent.from_text(attachment_data))

        # Create multi-modal message
        multimodal_msg = create_multimodal_message(content, provider=provider)

        # Process through multi-modal system
        response = await multimodal_processor.process_multimodal_message(multimodal_msg, provider)

        # Format response
        if hasattr(response, 'get_text_content'):
            # MultiModalMessage response
            text_response = response.get_text_content()
            has_images = len(response.get_image_content()) > 0
            response_data = {
                "text": text_response,
                "has_images": has_images,
                "image_count": len(response.get_image_content())
            }
        else:
            # Traditional Message response
            response_data = {
                "text": response.response or "No response generated",
                "has_images": False,
                "image_count": 0
            }

        return {
            "success": True,
            "response": response_data,
            "provider": provider,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Multi-modal chat endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/multimodal/describe-image")
async def describe_image_endpoint(request: Request):
    """Generate detailed image description"""
    try:
        data = await request.json()
        image_data = data.get("image_data")
        style = data.get("style", "detailed")  # "brief", "detailed", "technical"
        provider = data.get("provider", "gpt4vision")

        if not image_data:
            return {"success": False, "error": "No image data provided"}

        # Create image content
        image_content = MultiModalContent.from_image_base64(image_data)

        # Generate description
        description = await multimodal_processor.generate_image_description(image_content, style, provider)

        return {
            "success": True,
            "description": description,
            "style": style,
            "provider": provider
        }
    except Exception as e:
        logger.error(f"Image description endpoint error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "web_dashboard:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )