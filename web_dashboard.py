#!/usr/bin/env python3
"""
ZEJZL.NET Web Dashboard
Real-time monitoring and control interface for the AI framework
"""

import asyncio
import json
import logging
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn

# Import our framework
from ai_framework import AsyncMessageBus
from base import get_ai_provider_bus
from src.magic import FairyMagic
from src.usage_analytics import UsageAnalytics
try:
    from src.multimodal_processing import multimodal_processor
    from src.multimodal_ai import create_multimodal_message, MultiModalContent, ModalityType
except ImportError:
    multimodal_processor = None
    create_multimodal_message = None
    MultiModalContent = None
    ModalityType = None

# Import MCP components
try:
    from src.mcp_registry import MCPServerRegistry
    from src.mcp_security import get_security_manager
    from src.mcp_agent_integration import MCPAgentInterface, initialize_mcp
except ImportError:
    MCPServerRegistry = None
    get_security_manager = None
    MCPAgentInterface = None
    initialize_mcp = None
from telemetry import get_telemetry
from src.performance import record_metric
from src.logging_debug import debug_monitor, logger as debug_logger

logger = logging.getLogger(__name__)

app = FastAPI(title="ZEJZL.NET Dashboard", version="1.0.0")

# Templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

class DashboardServer:
    """Web dashboard for ZEJZL.NET monitoring and control"""

    def __init__(self):
        self.bus: AsyncMessageBus = None
        self.magic: FairyMagic = None
        self.connected_clients = set()

        # MCP components
        self.mcp_registry: MCPServerRegistry = None
        self.mcp_agent_interface: MCPAgentInterface = None
        self.mcp_security_manager = None

    async def initialize(self):
        """Initialize the dashboard with framework components"""
        try:
            self.bus = await get_ai_provider_bus()
            self.magic = self.bus.magic

            # Initialize MCP components
            await self._initialize_mcp_system()

            # Initialize multi-modal providers
            await self._initialize_multimodal_providers()

            logger.info("Dashboard initialized with AI framework, MCP system, and multi-modal support")
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

    async def _initialize_mcp_system(self):
        """Initialize MCP system components"""
        try:
            if initialize_mcp and MCPAgentInterface:
                self.mcp_agent_interface = await initialize_mcp()
                self.mcp_registry = self.mcp_agent_interface.registry
                logger.info("MCP system initialized successfully")

            if get_security_manager:
                self.mcp_security_manager = get_security_manager()
                logger.info("MCP security manager initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize MCP system: {e}")

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
                "mcp_servers": len(dashboard.mcp_registry.configs) if dashboard.mcp_registry else 0,
                "mcp_connected": len([s for s in dashboard.mcp_registry.status.values() if s.connected]) if dashboard.mcp_registry else 0,
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

@app.post("/api/multimodal/analyze-pdf")
async def analyze_pdf_endpoint(request: Request):
    """Analyze a PDF document with AI"""
    try:
        data = await request.json()
        pdf_data = data.get("pdf_data")  # base64 encoded PDF
        query = data.get("query", "Summarize this document")
        provider = data.get("provider", "gpt4vision")

        if not pdf_data:
            return {"success": False, "error": "No PDF data provided"}

        # For now, we'll treat PDF as text content (placeholder until full PDF processing)
        # TODO: Implement proper PDF content extraction and multi-modal analysis
        pdf_content = MultiModalContent(
            modality=ModalityType.DOCUMENT,
            content=f"[PDF Analysis Request] Query: {query}",
            encoding="text",
            metadata={"format": "pdf", "base64_size": len(pdf_data)}
        )

        # Create multi-modal message
        multimodal_msg = create_multimodal_message([pdf_content])

        # Process through multi-modal system
        response = await multimodal_processor.process_multimodal_message(multimodal_msg, provider)

        # Format response
        if isinstance(response, MultiModalMessage):
            text_response = response.get_text_content()
        else:
            text_response = response.response or "No analysis generated"

        return {
            "success": True,
            "analysis": text_response,
            "provider": provider,
            "document_type": "pdf",
            "note": "PDF processing is in development - currently returns basic analysis"
        }
    except Exception as e:
        logger.error(f"PDF analysis endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/multimodal/extract-pdf-text")
async def extract_pdf_text_endpoint(request: Request):
    """Extract text content from a PDF"""
    try:
        data = await request.json()
        pdf_data = data.get("pdf_data")  # base64 encoded PDF

        if not pdf_data:
            return {"success": False, "error": "No PDF data provided"}

        # Decode base64 PDF data
        try:
            pdf_bytes = base64.b64decode(pdf_data)
        except Exception as e:
            return {"success": False, "error": f"Invalid base64 PDF data: {e}"}

        # Extract text using our PDF processing
        extracted_text = MultiModalContent._extract_pdf_text(pdf_bytes)
        page_count = MultiModalContent._get_pdf_page_count(pdf_bytes)

        return {
            "success": True,
            "text": extracted_text,
            "page_count": page_count,
            "text_length": len(extracted_text),
            "has_content": bool(extracted_text.strip())
        }
    except Exception as e:
        logger.error(f"PDF text extraction endpoint error: {e}")
        return {"success": False, "error": str(e)}


# MCP Status Endpoints
@app.get("/api/mcp/status")
async def get_mcp_status():
    """Get MCP system status"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        servers = dashboard.mcp_registry.get_all_servers()
        stats = dashboard.mcp_registry.get_registry_stats()

        return {
            "success": True,
            "servers": servers,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP status endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/mcp/servers")
async def get_mcp_servers():
    """Get detailed MCP server information"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        servers = dashboard.mcp_registry.get_all_servers()

        return {
            "success": True,
            "servers": servers,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP servers endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/mcp/security")
async def get_mcp_security_status():
    """Get MCP security status"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        metrics = dashboard.mcp_security_manager.get_security_metrics()

        return {
            "success": True,
            "security": metrics,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP security endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/mcp/tool-call")
async def call_mcp_tool(request: Request):
    """Call an MCP tool through the web interface"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        data = await request.json()
        server_name = data.get("server_name")
        tool_name = data.get("tool_name")
        arguments = data.get("arguments", {})
        agent_name = data.get("agent_name", "web_dashboard")

        # Call the tool through the registry
        result = await dashboard.mcp_registry.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            agent_name=agent_name
        )

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP tool call endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/tools")
async def get_mcp_tools(server_name: str = None):
    """Get MCP tools"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        tools = dashboard.mcp_registry.list_tools(server_name)

        return {
            "success": True,
            "tools": tools,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP tools endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/resources")
async def get_mcp_resources(server_name: str = None):
    """Get MCP resources"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        resources = dashboard.mcp_registry.list_resources(server_name)

        return {
            "success": True,
            "resources": resources,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP resources endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/mcp/resource/read")
async def read_mcp_resource(request: Request):
    """Read an MCP resource through the web interface"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        data = await request.json()
        server_name = data.get("server_name")
        uri = data.get("uri")
        agent_name = data.get("agent_name", "web_dashboard")

        # Read the resource through the registry
        result = await dashboard.mcp_registry.read_resource(
            server_name=server_name,
            uri=uri,
            agent_name=agent_name
        )

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP resource read endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/mcp/server/connect/{server_name}")
async def connect_mcp_server(server_name: str):
    """Connect to an MCP server"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        await dashboard.mcp_registry._connect_server(server_name)

        return {
            "success": True,
            "message": f"Connected to {server_name}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP server connect error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/mcp/server/disconnect/{server_name}")
async def disconnect_mcp_server(server_name: str):
    """Disconnect from an MCP server"""
    try:
        if not dashboard.mcp_registry:
            return {"success": False, "error": "MCP not available"}

        await dashboard.mcp_registry._disconnect_server(server_name)

        return {
            "success": True,
            "message": f"Disconnected from {server_name}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP server disconnect error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/agents")
async def get_mcp_agents():
    """Get MCP agent activity statistics"""
    try:
        if not dashboard.mcp_agent_interface:
            return {"success": False, "error": "MCP Agent Interface not available"}

        agents = dashboard.mcp_agent_interface.get_all_agent_stats()

        return {
            "success": True,
            "agents": agents,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP agents endpoint error: {e}")
        return {"success": False, "error": str(e)}

# Security Validation Endpoints
@app.get("/api/security/overview")
async def get_security_overview():
    """Get security overview and statistics"""
    try:
        from src.security_validator import security_validator

        report = security_validator.get_security_report()
        pending_approvals = security_validator.get_pending_approvals()

        return {
            "success": True,
            "data": {
                "report": report,
                "pending_approvals": pending_approvals,
                "total_validations": report.get("total_operations", 0),
                "pending_count": len(pending_approvals),
                "blocked_count": sum(1 for op in pending_approvals if op.get("status") == "denied")
            }
        }
    except Exception as e:
        logger.error(f"Security overview endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/security/validate")
async def validate_operation(request: Request):
    """Validate an operation for security"""
    try:
        from src.security_validator import security_validator

        data = await request.json()
        operation = data.get("operation", "")
        context = data.get("context", {})
        user = data.get("user", "web_user")

        if not operation:
            return {"success": False, "error": "Operation required"}

        result = security_validator.validate_operation(operation, context, user)

        return {
            "success": True,
            "data": {
                "is_safe": result.is_safe,
                "risk_level": result.risk_level.value,
                "approval_required": result.approval_required.value,
                "violations": result.violations,
                "recommendations": result.recommendations,
                "requires_user_approval": result.requires_user_approval,
                "requires_admin_approval": result.requires_admin_approval,
                "can_proceed": result.can_proceed
            }
        }
    except Exception as e:
        logger.error(f"Security validation endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/security/approvals")
async def get_pending_approvals(user_id: str = None):
    """Get pending approval requests"""
    try:
        from src.security_validator import security_validator

        approvals = security_validator.get_pending_approvals(user_id)

        return {
            "success": True,
            "data": approvals
        }
    except Exception as e:
        logger.error(f"Pending approvals endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/security/approve")
async def approve_operation(request: Request):
    """Approve or deny a pending operation"""
    try:
        from src.security_validator import security_validator

        data = await request.json()
        approval_id = data.get("approval_id")
        approved = data.get("approved", False)
        admin_user = data.get("admin_user")

        if not approval_id:
            return {"success": False, "error": "Approval ID required"}

        success = security_validator.approve_operation(approval_id, approved, admin_user)

        return {
            "success": success,
            "message": f"Operation {'approved' if approved else 'denied'}"
        }
    except Exception as e:
        logger.error(f"Approve operation endpoint error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/security/request-approval")
async def request_user_approval(request: Request):
    """Request user approval for an operation"""
    try:
        from src.security_validator import security_validator

        data = await request.json()
        operation = data.get("operation", "")
        validation_data = data.get("validation", {})
        user_id = data.get("user_id", "web_user")

        if not operation:
            return {"success": False, "error": "Operation required"}

        # Convert dict back to ValidationResult
        from src.security_validator import ValidationResult, RiskLevel, ApprovalRequirement

        validation = ValidationResult(
            is_safe=validation_data.get("is_safe", False),
            risk_level=RiskLevel(validation_data.get("risk_level", "medium_risk")),
            approval_required=ApprovalRequirement(validation_data.get("approval_required", "user_confirm")),
            violations=validation_data.get("violations", []),
            recommendations=validation_data.get("recommendations", []),
            requires_user_approval=validation_data.get("requires_user_approval", True),
            requires_admin_approval=validation_data.get("requires_admin_approval", False),
            can_proceed=validation_data.get("can_proceed", False)
        )

        approved = await security_validator.request_user_approval(operation, validation, user_id)

        return {
            "success": True,
            "approved": approved,
            "message": "Approval request submitted"
        }
    except Exception as e:
        logger.error(f"Request approval endpoint error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "web_dashboard:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )