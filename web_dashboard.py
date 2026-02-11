#!/usr/bin/env python3
"""
ZEJZL.NET Web Dashboard
Real-time monitoring and control interface for the AI framework
"""

import asyncio
import json
import logging
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import asdict
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import Optional
import traceback
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
logger_env = logging.getLogger(__name__)
logger_env.info(
    f"Environment loaded - GROK_API_KEY present: {bool(os.environ.get('GROK_API_KEY'))}"
)

# Import our framework
from ai_framework import AsyncMessageBus
from base import get_ai_provider_bus
from src.magic import FairyMagic
from src.usage_analytics import UsageAnalytics

try:
    from src.multimodal_processing import multimodal_processor
    from src.multimodal_ai import (
        create_multimodal_message,
        MultiModalContent,
        ModalityType,
    )
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

# Import Community Vault
try:
    from community_vault import CommunityVault
except ImportError:
    CommunityVault = None

# Import Payment System (safe import)
payment_manager = None
payment_router = None
SubscriptionTier = None

try:
    # Import only if dependencies are available
    import stripe
    from src.payments import (
        payment_manager as pm,
        payment_router as pr,
        SubscriptionTier as st,
    )

    payment_manager = pm
    payment_router = pr
    SubscriptionTier = st
    logger.info("Payment system loaded successfully")
except ImportError as e:
    logger.warning(f"Payment system not available: {e}")
except Exception as e:
    logger.error(f"Payment system import error: {e}")

# Import Pantheon Swarm
try:
    from pantheon_swarm import (
        PantheonSwarm,
        BudgetExhaustedError,
        PermissionDeniedError,
    )
except ImportError:
    PantheonSwarm = None
    BudgetExhaustedError = None
    PermissionDeniedError = None
    logger.warning("PantheonSwarm not available - swarm features disabled")

from telemetry import get_telemetry
from src.performance import record_metric
from src.logging_debug import debug_monitor, logger as debug_logger

# Initialize analytics globally
analytics = UsageAnalytics()

# Initialize community vault
vault = CommunityVault()

logger = logging.getLogger(__name__)

app = FastAPI(title="ZEJZL.NET Dashboard", version="1.0.0")

# --- Pydantic request models for validation ---

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field(default="grok-4-1-fast-reasoning")
    consensus: bool = Field(default=False)
    stream: bool = Field(default=False)

class ChatRLMRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    provider: str = Field(default="grok-4-1-fast-reasoning")
    use_real_agents: bool = Field(default=True)

class ChatSwarmRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    budget: int = Field(default=10000, ge=100, le=1000000)
    provider: str = Field(default="grok-4-1-fast-reasoning")

class OfflineToggleRequest(BaseModel):
    enabled: bool = Field(default=False)

# --- Global exception handlers (production-safe) ---

IS_PRODUCTION = os.getenv("ENVIRONMENT", "production") != "development"

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without exposing internal details."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    # In production, only return field names and error types, not raw input
    if IS_PRODUCTION:
        safe_errors = [
            {"field": ".".join(str(l) for l in e.get("loc", [])), "type": e.get("type", "unknown")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={"error": "Validation error", "details": safe_errors},
        )
    # In development, return full details
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "details": exc.errors()},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all handler: log real error, return generic message."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True,
    )
    if IS_PRODUCTION:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )

# Security: Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware

# Configure allowed origins (restrictive by default)
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
if not allowed_origins or allowed_origins == [""]:
    # Default to production origins only
    allowed_origins = [
        "https://zejzl-net.vercel.app",
        "https://zejzl.net",
    ]
    # Add localhost for development
    if os.getenv("ENVIRONMENT", "production") == "development":
        allowed_origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
        ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=3600,
)

logger.info(f"🔒 CORS configured for origins: {', '.join(allowed_origins)}")

# Security: Import authentication system
from src.auth import authenticate, optional_authenticate, RequireAuth, OptionalAuth, verify_api_key

# Security: API Authentication Middleware
@app.middleware("http")
async def authenticate_api_requests(request: Request, call_next):
    """
    Middleware to authenticate all /api/* requests
    
    Public endpoints (no auth required):
    - /api/status
    - /api/health/*
    - / (homepage and static assets)
    """
    # Public endpoints that don't require authentication
    public_paths = [
        "/api/status",
        "/api/health",
        "/api/health/detailed",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    # Check if this is an API request that needs authentication
    if request.url.path.startswith("/api/"):
        # Skip authentication for public endpoints
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Require authentication for all other /api/* endpoints
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Authentication required",
                    "detail": "Include X-API-Key header or Authorization: Bearer token"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify the API key
        key_info = verify_api_key(api_key)
        if not key_info:
            logger.warning(f"Invalid API key attempted from {request.client.host}")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API key"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add key info to request state for use in endpoints
        request.state.auth_info = key_info
        request.state.authenticated = True
        
        logger.info(f"✓ API request authenticated: {key_info['description']} -> {request.url.path}")
    
    # Continue to endpoint
    response = await call_next(request)
    
    # Add security headers to all responses
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

logger.info("🔒 API authentication middleware enabled")

# Templates and static files
import os

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include payment router if available
if payment_router:
    app.include_router(payment_router)

# Include user management router (safe import)
user_db = None
onboarding_router = None

try:
    # Import only if dependencies are available
    import aiosqlite
    import jwt
    from passlib.context import CryptContext
    from src.user_management import onboarding_router as obr, user_db as udb

    user_db = udb
    app.include_router(obr)
    logger.info("User management system loaded successfully")
except ImportError as e:
    logger.warning(f"User management not available: {e}")
except Exception as e:
    logger.error(f"User management import error: {e}")

# Include user management router (safe import)
user_db = None
onboarding_router = None

try:
    # Import only if dependencies are available
    import aiosqlite
    import jwt
    from passlib.context import CryptContext
    from src.user_management import onboarding_router as obr, user_db as udb

    user_db = udb
    app.include_router(obr)
    logger.info("User management system loaded successfully")
except ImportError as e:
    logger.warning(f"User management not available: {e}")
except Exception as e:
    logger.error(f"User management import error: {e}")

# Include task management router (safe import)
task_router = None
try:
    from src.task_manager import task_manager, Task, TaskStatus, TaskPriority
    from fastapi import APIRouter
    from typing import List, Optional

    task_router = APIRouter(prefix="/api/tasks", tags=["task-management"])

    @task_router.get("/", response_model=List[dict])
    async def get_all_tasks():
        """Get all tasks"""
        return [task.__dict__ for task in task_manager.tasks.values()]

    @task_router.get("/{task_id}")
    async def get_task(task_id: str):
        """Get specific task"""
        task = task_manager.get_task(task_id)
        if task:
            return task.__dict__
        return {"error": "Task not found"}

    @task_router.post("/", response_model=dict)
    async def create_task(request):
        """Create new task"""
        task_data = await request.json()

        new_task = Task(id=f"task-{len(task_manager.tasks) + 1:03d}", **task_data)

        task_manager.tasks[new_task.id] = new_task
        await task_manager.save_data()

        return {"success": True, "task": new_task.__dict__}

    @task_router.put("/{task_id}", response_model=dict)
    async def update_task(task_id: str, request):
        """Update task"""
        update_data = await request.json()

        if task_id in task_manager.tasks:
            task_manager.update_task(task_id, **update_data)
            await task_manager.save_data()

            return {"success": True, "task": task_manager.get_task(task_id).__dict__}

        return {"error": "Task not found"}

    @task_router.get("/project/{project_id}/status")
    async def get_project_status(project_id: str):
        """Get project status with task breakdown"""
        status = task_manager.get_project_status(project_id)
        return status

    @task_router.get("/critical-path")
    async def get_critical_path():
        """Get critical path analysis"""
        critical_path = task_manager.calculate_critical_path()
        return {
            "critical_path": critical_path,
            "analysis": {
                "total_tasks": len(task_manager.tasks),
                "dependencies": len(task_manager.dependencies),
                "blocked_tasks": len(task_manager.get_blocked_tasks()),
            },
        }

    @task_router.get("/resource-allocation")
    async def get_resource_allocation():
        """Get resource allocation analysis"""
        return task_manager.get_resource_allocation()

    app.include_router(task_router)
    logger.info("Task management system loaded successfully")

except ImportError as e:
    logger.warning(f"Task management not available: {e}")
except Exception as e:
    logger.error(f"Task management import error: {e}")

# Include business analytics router (safe import)
business_analytics_router = None
try:
    from src.business_analytics import business_analytics
    from fastapi import APIRouter

    business_analytics_router = APIRouter(
        prefix="/api/analytics", tags=["business-analytics"]
    )

    @business_analytics_router.get("/revenue")
    async def get_revenue_metrics():
        """Get current revenue metrics"""
        metrics = await business_analytics.calculate_revenue_metrics()
        return {"success": True, "data": metrics}

    @business_analytics_router.get("/customer-segments")
    async def get_customer_segments():
        """Get customer segment analysis"""
        segments = business_analytics.analyze_customer_segments()
        return {"success": True, "data": segments}

    @business_analytics_router.get("/behavioral-insights")
    async def get_behavioral_insights():
        """Get behavioral insights"""
        insights = business_analytics.analyze_behavioral_patterns()
        return {"success": True, "data": insights}

    @business_analytics_router.get("/cohort-analysis")
    async def get_cohort_analysis():
        """Get cohort analysis"""
        await business_analytics.generate_business_intelligence_report()
        return {"success": True, "data": "Cohort analysis generated"}

    @business_analytics_router.post("/track-event")
    async def track_analytics_event(request):
        """Track analytics event"""
        event_data = await request.json()
        from src.business_analytics import EventType

        await business_analytics.track_event(
            event_data.get("user_id", "anonymous"),
            EventType(event_data.get("event_type", "api_call")),
            event_data.get("event_data", {}),
            event_data.get("revenue_impact", 0),
            event_data.get("session_id", None),
        )

        return {"success": True, "message": "Event tracked"}

    app.include_router(business_analytics_router)
    logger.info("Business analytics system loaded successfully")

except ImportError as e:
    logger.warning(f"Business analytics not available: {e}")
except Exception as e:
    logger.error(f"Business analytics import error: {e}")

# Include insight extraction router (safe import)
insight_router = None
try:
    from src.insight_engine import insight_engine, memory_engine
    from fastapi import APIRouter

    insight_router = APIRouter(prefix="/api/intelligence", tags=["insights"])

    @insight_router.get("/insights")
    async def get_insights():
        """Get all consolidated insights"""
        insights = list(insight_engine.insights.values())
        return {"success": True, "data": insights}

    @insight_router.get("/memories")
    async def get_memories():
        """Get consolidated memories"""
        memories = list(memory_engine.memories.values())
        return {"success": True, "data": memories}

    @insight_router.get("/patterns")
    async def get_patterns():
        """Get detected patterns"""
        patterns = list(insight_engine.patterns.values())
        return {"success": True, "data": patterns}

    @insight_router.post("/extract-insights")
    async def extract_insights(request):
        """Extract insights from performance data"""
        data = await request.json()

        # Extract insights from different data sources
        performance_insights = (
            await insight_engine.extract_insights_from_performance_data(
                data.get("performance_data", {})
            )
        )
        behavioral_insights = await insight_engine.extract_insights_from_user_behavior(
            data.get("behavioral_data", {})
        )
        revenue_insights = await insight_engine.extract_insights_from_revenue_data(
            data.get("revenue_data", {})
        )

        all_insights = performance_insights + behavioral_insights + revenue_insights

        # Consolidate into memories
        memories = await memory_engine.consolidate_insights(all_insights)

        return {
            "success": True,
            "data": {
                "insights_extracted": len(all_insights),
                "memories_created": len(memories),
                "insights": all_insights,
                "memories": memories,
            },
        }

    app.include_router(insight_router)
    logger.info("Insight extraction system loaded successfully")

except ImportError as e:
    logger.warning(f"Insight extraction not available: {e}")
except Exception as e:
    logger.error(f"Insight extraction import error: {e}")

# Include predictive analytics router (safe import)
predictive_router = None
try:
    from src.predictive_analytics import predictive_engine, AlertSeverity, ForecastType
    from fastapi import APIRouter

    predictive_router = APIRouter(
        prefix="/api/predictive", tags=["predictive-analytics"]
    )

    @predictive_router.get("/forecasts/revenue")
    async def get_revenue_forecast():
        """Get revenue forecast"""
        # Mock historical data
        revenue_data = [
            {"date": "2026-01-01", "revenue": 1000},
            {"date": "2026-01-02", "revenue": 1050},
            {"date": "2026-01-03", "revenue": 1100},
            {"date": "2026-01-04", "revenue": 1080},
            {"date": "2026-01-05", "revenue": 1150},
            {"date": "2026-01-06", "revenue": 1200},
            {"date": "2026-01-07", "revenue": 1180},
        ]

        forecast = await predictive_engine.generate_revenue_forecast(revenue_data, 30)
        return {"success": True, "data": forecast}

    @predictive_router.get("/forecasts/usage")
    async def get_usage_forecast():
        """Get usage forecast"""
        # Mock historical data
        usage_data = [
            {"date": "2026-01-01", "api_calls": 100},
            {"date": "2026-01-02", "api_calls": 105},
            {"date": "2026-01-03", "api_calls": 110},
            {"date": "2026-01-04", "api_calls": 108},
            {"date": "2026-01-05", "api_calls": 115},
            {"date": "2026-01-06", "api_calls": 120},
            {"date": "2026-01-07", "api_calls": 118},
        ]

        forecast = await predictive_engine.generate_usage_forecast(usage_data, 30)
        return {"success": True, "data": forecast}

    @predictive_router.get("/forecasts/churn")
    async def get_churn_forecast():
        """Get churn forecast"""
        # Mock historical data
        churn_data = [
            {"date": "2026-01-01", "churned_customers": 5, "total_customers": 100},
            {"date": "2026-01-02", "churned_customers": 3, "total_customers": 105},
            {"date": "2026-01-03", "churned_customers": 4, "total_customers": 110},
            {"date": "2026-01-04", "churned_customers": 6, "total_customers": 115},
            {"date": "2026-01-05", "churned_customers": 4, "total_customers": 120},
            {"date": "2026-01-06", "churned_customers": 2, "total_customers": 125},
            {"date": "2026-01-07", "churned_customers": 3, "total_customers": 130},
        ]

        forecast = await predictive_engine.generate_churn_forecast(churn_data, 30)
        return {"success": True, "data": forecast}

    @predictive_router.get("/alerts")
    async def get_alerts():
        """Get active predictive alerts"""
        alerts = await predictive_engine.get_active_alerts()
        return {"success": True, "data": alerts}

    app.include_router(predictive_router)
    logger.info("Predictive analytics system loaded successfully")

except ImportError as e:
    logger.warning(f"Predictive analytics not available: {e}")
except Exception as e:
    logger.error(f"Predictive analytics import error: {e}")


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

        # Pantheon Swarm (budget tracking + permission gates)
        self.swarm: PantheonSwarm = None

    async def initialize(self):
        """Initialize the dashboard with framework components"""
        try:
            self.bus = await get_ai_provider_bus()
            self.magic = self.bus.magic

            # Initialize Pantheon Swarm (budget tracking + permission gates)
            await self._initialize_swarm()

            # Initialize MCP components
            await self._initialize_mcp_system()

            # Initialize multi-modal providers
            await self._initialize_multimodal_providers()

            logger.info(
                "Dashboard initialized with AI framework, Pantheon Swarm, MCP system, and multi-modal support"
            )
        except Exception as e:
            logger.error(f"Failed to initialize dashboard: {e}")
            # Create fallback instances for demo

    async def _initialize_swarm(self):
        """Initialize Pantheon Swarm for budget-tracked multi-agent coordination"""
        try:
            if PantheonSwarm:
                self.swarm = PantheonSwarm(
                    pantheon_config_path="pantheon_config.json",
                    model="grok-4-1-fast-reasoning",
                    verbose=False,  # Set True for debugging
                )
                logger.info(
                    "✓ Pantheon Swarm initialized with budget tracking & permission gates"
                )
            else:
                logger.warning(
                    "PantheonSwarm not available - skipping swarm initialization"
                )
        except Exception as e:
            logger.error(f"Failed to initialize Pantheon Swarm: {e}")
            self.swarm = None

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
                    "healing_history": len(self.magic.healing_history),
                },
                "ai_providers": {},
                "metrics": {},
                "recent_activity": [],
            }

            # Provider status
            if self.bus and hasattr(self.bus, "providers"):
                for name, provider in self.bus.providers.items():
                    status["ai_providers"][name] = {
                        "model": getattr(provider, "model", "unknown"),
                        "status": "active",
                    }

            # Get basic telemetry data
            telemetry = get_telemetry()
            if telemetry:
                try:
                    summary_data = await telemetry.get_summary()
                    status["metrics"] = {
                        "total_calls": summary_data.get("total_calls", 0),
                        "avg_response_time": summary_data.get("avg_response_time", 0),
                        "success_rate": summary_data.get("success_rate", 0),
                    }
                except:
                    status["metrics"] = {
                        "total_calls": 0,
                        "avg_response_time": 0,
                        "success_rate": 0,
                    }
                status["recent_activity"] = []  # Simplified for now

            return status

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "magic_system": {"energy_level": 0, "status": "error"},
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


@app.get("/blackboard", response_class=HTMLResponse)
async def blackboard_page(request: Request):
    """Blackboard coordination dashboard"""
    try:
        with open("static/blackboard_dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>Blackboard Dashboard Not Found</h1><p>Please ensure blackboard_dashboard.html exists in the static/ directory.</p>",
            status_code=404,
        )


@app.get("/billing", response_class=HTMLResponse)
async def billing_page(request: Request):
    """Billing and revenue dashboard"""
    try:
        with open("static/billing_dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>Billing Dashboard Not Found</h1><p>Please ensure billing_dashboard.html exists in the static/ directory.</p>",
            status_code=404,
        )


@app.get("/get-started", response_class=HTMLResponse)
async def get_started_page(request: Request):
    """Onboarding and registration page"""
    try:
        with open("static/onboarding.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(
            "<h1>Onboarding Page Not Found</h1><p>Please ensure onboarding.html exists in the static/ directory.</p>",
            status_code=404,
        )


@app.websocket("/ws/blackboard")
async def blackboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time blackboard updates

    Pushes updates every 2 seconds for:
    - Blackboard state
    - Budget status
    - Audit log

    Replaces HTTP polling for instant updates
    """
    await websocket.accept()
    logger.info("WebSocket connection established for blackboard")

    try:
        while True:
            # Collect all dashboard data
            data = {
                "timestamp": datetime.now().isoformat(),
                "blackboard": {},
                "budget": {},
                "audit": {},
            }

            # Get blackboard state
            if dashboard.swarm:
                try:
                    blackboard_state = dashboard.swarm.get_blackboard_state()
                    data["blackboard"] = {
                        "success": True,
                        "entries": blackboard_state,
                        "key_count": len(blackboard_state),
                    }
                except Exception as e:
                    data["blackboard"] = {"success": False, "error": str(e)}

                # Get budget status
                try:
                    budget_file = (
                        Path(dashboard.swarm.coordinator.data_dir)
                        / "budget_tracking.json"
                    )
                    if budget_file.exists():
                        with open(budget_file, "r", encoding="utf-8") as f:
                            budget_data = json.load(f)

                        tasks = budget_data.get("tasks", {})
                        task_list = []
                        total_used = 0
                        total_limit = 0

                        for task_id, task_data in tasks.items():
                            tokens_used = task_data.get("tokens_used", 0)
                            budget_limit = task_data.get("budget_limit", 0)

                            task_list.append(
                                {
                                    "task_id": task_id,
                                    "tokens_used": tokens_used,
                                    "budget_limit": budget_limit,
                                    "percentage": (tokens_used / budget_limit * 100)
                                    if budget_limit > 0
                                    else 0,
                                    "status": task_data.get("status", "active"),
                                }
                            )

                            total_used += tokens_used
                            total_limit += budget_limit

                        data["budget"] = {
                            "success": True,
                            "tasks": sorted(
                                task_list, key=lambda x: x["percentage"], reverse=True
                            ),
                            "total_used": total_used,
                            "total_limit": total_limit,
                            "global_percentage": (total_used / total_limit * 100)
                            if total_limit > 0
                            else 0,
                        }
                    else:
                        data["budget"] = {
                            "success": True,
                            "tasks": [],
                            "total_used": 0,
                            "total_limit": 0,
                        }
                except Exception as e:
                    data["budget"] = {"success": False, "error": str(e)}

                # Get audit log (last 20 entries)
                try:
                    audit_file = (
                        Path(dashboard.swarm.coordinator.data_dir) / "audit_log.jsonl"
                    )
                    if audit_file.exists():
                        entries = []
                        with open(audit_file, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.strip():
                                    try:
                                        entry = json.loads(line)
                                        entries.append(entry)
                                    except json.JSONDecodeError:
                                        continue

                        entries.reverse()
                        data["audit"] = {
                            "success": True,
                            "entries": entries[:20],
                            "total_count": len(entries),
                        }
                    else:
                        data["audit"] = {
                            "success": True,
                            "entries": [],
                            "total_count": 0,
                        }
                except Exception as e:
                    data["audit"] = {"success": False, "error": str(e)}
            else:
                data["error"] = "Swarm not initialized"

            # Send update to client
            await websocket.send_json(data)

            # Wait 2 seconds before next update
            await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket connection closed for blackboard")


@app.get("/api/status")
async def get_status():
    """Get current system status"""
    return await dashboard.get_system_status()


@app.get("/api/debug/routes")
async def debug_routes():
    """Debug endpoint to show registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(
                {
                    "path": route.path,
                    "name": route.name if hasattr(route, "name") else None,
                }
            )
    return {
        "total_routes": len(app.routes),
        "routes": sorted(routes, key=lambda x: x["path"]),
        "swarm_count": len([r for r in routes if "swarm" in r["path"]]),
    }


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
                    "motivational_drivers": p.motivational_drivers,
                }
                for name, p in AGENT_PERSONALITIES.items()
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
            with open(log_file, "r", encoding="utf-8") as f:
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
        "active_request_count": len(debug_monitor.active_requests),
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


@app.get("/api/activity/recent")
async def get_recent_activity(limit: int = 10):
    """Get recent system activity"""
    try:
        activities = []

        # Get recent agent activities from memory
        if dashboard.bus and dashboard.bus.memory:
            try:
                recent_events = await dashboard.bus.memory.recall(limit=limit)
                for event in recent_events[-limit:]:
                    activities.append(
                        {
                            "type": "agent_activity",
                            "timestamp": event.get(
                                "timestamp", datetime.now().isoformat()
                            ),
                            "title": f"Agent {event.get('agent', 'Unknown')} Activity",
                            "description": event.get("type", "Activity"),
                            "icon": "bot",
                        }
                    )
            except Exception:
                pass

        # Get recent API calls from analytics
        try:
            usage_data = await analytics.get_usage_report(days=1)
            if usage_data.success and usage_data.data.total_requests > 0:
                activities.append(
                    {
                        "type": "api_activity",
                        "timestamp": datetime.now().isoformat(),
                        "title": f"{usage_data.data.total_requests} API Requests Today",
                        "description": f"Used {usage_data.data.total_tokens or 0} tokens",
                        "icon": "zap",
                    }
                )
        except Exception:
            pass

        # Get recent chat messages
        try:
            chat_history = await dashboard.bus.memory.recall(
                query={"type": "chat_message"}, limit=limit
            )
            for chat in chat_history[-3:]:  # Show last 3 chat messages
                activities.append(
                    {
                        "type": "chat_message",
                        "timestamp": chat.get("timestamp", datetime.now().isoformat()),
                        "title": "Chat Message",
                        "description": chat.get("content", "")[:50] + "..."
                        if len(chat.get("content", "")) > 50
                        else chat.get("content", ""),
                        "icon": "message-circle",
                    }
                )
        except Exception:
            pass

        # Get recent learning activities
        try:
            learning_cycles = await dashboard.bus.memory.recall(
                query={"type": "learning_cycle"}, limit=limit
            )
            for cycle in learning_cycles[-2:]:  # Show last 2 learning cycles
                activities.append(
                    {
                        "type": "learning_cycle",
                        "timestamp": cycle.get("timestamp", datetime.now().isoformat()),
                        "title": "Learning Cycle Completed",
                        "description": f"Found {cycle.get('insights', 0)} insights",
                        "icon": "brain",
                    }
                )
        except Exception:
            pass

        # Sort by timestamp (most recent first) and limit
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        activities = activities[:limit]

        # If no activities, add some default ones
        if not activities:
            activities = [
                {
                    "type": "system_startup",
                    "timestamp": datetime.now().isoformat(),
                    "title": "System Started",
                    "description": "ZEJZL.NET dashboard initialized",
                    "icon": "power",
                },
                {
                    "type": "info",
                    "timestamp": (
                        datetime.now().replace(second=0, microsecond=0)
                    ).isoformat(),
                    "title": "Dashboard Ready",
                    "description": "All systems operational",
                    "icon": "check-circle",
                },
            ]

        return {"success": True, "data": activities}

    except Exception as e:
        logger.error(f"Recent activity endpoint error: {e}")
        return {
            "success": True,
            "data": [
                {
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "title": "Activity Loading Error",
                    "description": "Unable to load recent activity",
                    "icon": "alert-triangle",
                }
            ],
        }


@app.get("/api/offline/status")
async def get_offline_status():
    """Get offline mode status and connectivity information"""
    try:
        connectivity = await dashboard.bus.check_connectivity()
        cache_stats = await dashboard.bus.get_cache_stats()

        return {
            "success": True,
            "data": {
                "offline_mode_enabled": dashboard.bus.offline_mode,
                "connectivity_status": dashboard.bus.connectivity_status,
                "is_online": connectivity,
                "cache_stats": cache_stats,
                "monitoring_active": dashboard.bus.connectivity_checker is not None
                and not dashboard.bus.connectivity_checker.done(),
            },
        }

    except Exception as e:
        logger.error(f"Offline status endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/offline/toggle")
async def toggle_offline_mode(request: Request):
    """Enable or disable offline mode"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)

        await dashboard.bus.enable_offline_mode(enabled)

        return {
            "success": True,
            "message": f"Offline mode {'enabled' if enabled else 'disabled'}",
            "offline_mode": dashboard.bus.offline_mode,
        }

    except Exception as e:
        logger.error(f"Toggle offline mode endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/cache/stats")
async def get_cache_statistics():
    """Get detailed cache statistics"""
    try:
        stats = await dashboard.bus.get_cache_stats()
        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"Cache stats endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/cache/clear")
async def clear_cache():
    """Clear all cached responses"""
    try:
        success = await dashboard.bus.offline_cache.clear()

        if success:
            # Also clear any in-memory caches
            dashboard.bus.conversation_cache.clear()

            return {"success": True, "message": "Cache cleared successfully"}
        else:
            return {"success": False, "error": "Failed to clear cache"}

    except Exception as e:
        logger.error(f"Clear cache endpoint error: {e}")
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
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
            },
            "zejzl": {
                "bus_status": "connected" if dashboard.bus else "disconnected",
                "magic_energy": dashboard.magic.energy_level if dashboard.magic else 0,
                "providers_count": len(dashboard.bus.providers) if dashboard.bus else 0,
                "mcp_servers": len(dashboard.mcp_registry.configs)
                if dashboard.mcp_registry
                else 0,
                "mcp_connected": len(
                    [s for s in dashboard.mcp_registry.status.values() if s.connected]
                )
                if dashboard.mcp_registry
                else 0,
                "active_requests": len(debug_monitor.active_requests),
            },
        }

        return health_data
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.post("/api/magic/{action}")
async def magic_action(action: str, background_tasks: BackgroundTasks):
    """Perform magic system actions"""
    try:
        if action == "boost":
            result = await dashboard.magic.acorn_vitality_boost(
                "web_dashboard", {"max_tokens": 1024}
            )
            record_metric("dashboard_magic_boost", 1, {"source": "web"})
            return {"success": True, "result": result}

        elif action == "shield":
            dashboard.magic.is_shielded = not dashboard.magic.is_shielded
            return {"success": True, "shielded": dashboard.magic.is_shielded}

        elif action == "heal":
            result = await dashboard.magic.blue_spark_heal(
                "dashboard_request", "Web interface healing"
            )
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
        chat_req = ChatRequest(**data)
        message = chat_req.message
        provider = chat_req.provider
        consensus = chat_req.consensus
        stream = chat_req.stream

        # Check for magic commands
        magic_commands = {
            "shield": "shield",
            "magic shield": "shield",
            "activate shield": "shield",
            "enable shield": "shield",
            "disable shield": "shield",
            "boost": "boost",
            "magic boost": "boost",
            "vitality boost": "boost",
            "acorn boost": "boost",
            "heal": "heal",
            "magic heal": "heal",
            "blue spark": "heal",
            "spark heal": "heal",
        }

        message_lower = message.lower().strip()
        if message_lower in magic_commands:
            # Handle magic command directly
            action = magic_commands[message_lower]
            magic_result = await magic_action(action, background_tasks)

            if magic_result.get("success"):
                # Format the response nicely
                if action == "shield":
                    status = (
                        "activated" if magic_result.get("shielded") else "deactivated"
                    )
                    response = f"[MAGIC] **Magic Shield {status.capitalize()}!**\n\n[SHIELD] The Fairy Magic shield has been {status} to protect against failures and ensure system stability."
                elif action == "boost":
                    boost_result = magic_result.get("result", {})
                    response = f"[BOOST] **Vitality Boost Applied!**\n\n[POWER] System performance enhanced with Acorn Vitality Boost!\n\n**Details:** {boost_result}"
                elif action == "heal":
                    heal_result = magic_result.get("result", {})
                    response = f"[HEAL] **Blue Spark Healing Complete!**\n\n[SUCCESS] System healed and optimized using Fairy Magic.\n\n**Healing Report:** {heal_result}"
                else:
                    response = f"[MAGIC] **Magic {action.capitalize()} Complete!**\n\nMagic action executed successfully."
            else:
                response = f"[ERROR] **Magic Failed**\n\n{action.capitalize()} action could not be completed: {magic_result.get('error', 'Unknown error')}"
        else:
            # Send message through AI bus
            response = await dashboard.bus.send_message(
                content=message,
                provider_name=provider,
                stream=stream,
                consensus=consensus,
            )

        # Record the interaction
        mode = "consensus" if consensus else "single"
        record_metric("dashboard_chat", 1, {"provider": provider, "mode": mode})

        return {
            "response": response,
            "provider": provider,
            "consensus": consensus,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return {"error": "Failed to process chat request" if IS_PRODUCTION else str(e)}


@app.post("/api/chat-rlm")
async def chat_rlm_endpoint(request: Request):
    """Handle RLM (Recursive Language Model) chat requests with Pantheon agents"""
    try:
        data = await request.json()
        rlm_req = ChatRLMRequest(**data)
        message = rlm_req.message
        provider = rlm_req.provider
        use_real_agents = rlm_req.use_real_agents

        # Initialize Pantheon RLM if not already done
        if not hasattr(dashboard, "_pantheon_rlm"):
            from pantheon_rlm_integration import ZejzlPantheonRLM

            dashboard._pantheon_rlm = ZejzlPantheonRLM(
                pantheon_config_path="pantheon_config.json",
                model=provider,
                use_real_agents=use_real_agents,
                verbose=False,  # Don't print debug in production
            )
            logger.info("[RLM] Initialized Pantheon RLM")

        # Process task through RLM
        logger.info(f"[RLM] Processing task: {message[:60]}...")
        response = await dashboard._pantheon_rlm.process_task_async(message)
        logger.info(f"[RLM] Task complete: {len(response)} chars")

        # Record the interaction
        record_metric(
            "dashboard_chat_rlm",
            1,
            {"provider": provider, "use_real_agents": use_real_agents},
        )

        return {
            "response": response,
            "provider": provider,
            "mode": "rlm",
            "real_agents": use_real_agents,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"[RLM] Chat endpoint error: {e}", exc_info=True)
        return {"error": f"RLM error: {str(e)}"}


@app.post("/api/chat-swarm")
async def chat_swarm_endpoint(request: Request):
    """Handle Pantheon Swarm chat requests with budget tracking and permission gates"""
    try:
        data = await request.json()
        swarm_req = ChatSwarmRequest(**data)
        message = swarm_req.message
        budget = swarm_req.budget
        provider = swarm_req.provider

        # Auto-detect required permissions from message
        permissions = []
        message_lower = message.lower()
        if any(
            kw in message_lower
            for kw in ["deploy", "update", "delete", "schema", "migration"]
        ):
            permissions.append("DATABASE")
        if any(
            kw in message_lower for kw in ["payment", "charge", "refund", "transaction"]
        ):
            permissions.append("PAYMENTS")
        if any(kw in message_lower for kw in ["email", "send", "notify", "alert"]):
            permissions.append("EMAIL")

        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized", "fallback_available": True},
                status_code=503,
            )

        # Process task through Pantheon Swarm
        logger.info(f"[SWARM] Processing task: {message[:60]}... (budget: {budget:,})")

        result = await dashboard.swarm.process_task(
            task=message,
            budget=budget,
            required_permissions=permissions if permissions else None,
        )

        if result["success"]:
            logger.info(
                f"[SWARM] Task complete: {result['estimated_tokens']:,} / {budget:,} tokens"
            )

            # Record the interaction
            record_metric(
                "dashboard_chat_swarm",
                1,
                {
                    "provider": provider,
                    "budget": budget,
                    "tokens_used": result["estimated_tokens"],
                },
            )

            return JSONResponse(
                {
                    "success": True,
                    "response": result["result"],
                    "mode": "swarm",
                    "task_id": result["task_id"],
                    "budget": {
                        "used": result["budget_status"]["used_tokens"],
                        "max": result["budget_status"]["max_tokens"],
                        "remaining": result["budget_status"]["remaining_tokens"],
                        "percentage": result["budget_status"]["usage_percentage"],
                        "status": result["budget_status"]["status"],
                    },
                    "execution_time": result["execution_time"],
                    "permissions_checked": permissions,
                    "timestamp": datetime.now().isoformat(),
                }
            )
        else:
            # Handle errors
            error_type = result.get("error", "unknown")
            status_code = (
                429
                if error_type == "budget_exhausted"
                else 403
                if error_type == "permission_denied"
                else 500
            )

            logger.warning(
                f"[SWARM] Task failed: {error_type} - {result.get('message')}"
            )

            return JSONResponse(
                {
                    "success": False,
                    "error": result.get("message", "Unknown error"),
                    "error_type": error_type,
                    "task_id": result.get("task_id"),
                    "budget_status": result.get("budget_status"),
                    "timestamp": datetime.now().isoformat(),
                },
                status_code=status_code,
            )

    except Exception as e:
        logger.error(f"[SWARM] Chat endpoint error: {e}", exc_info=True)
        return JSONResponse({"error": f"Swarm error: {str(e)}"}, status_code=500)


@app.get("/api/swarm/budget/{task_id}")
async def get_swarm_budget(task_id: str):
    """Get budget status for a Pantheon Swarm task"""
    try:
        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        status = dashboard.swarm.get_budget_status(task_id)
        return JSONResponse(status)

    except Exception as e:
        logger.error(f"[SWARM] Budget endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/swarm/blackboard")
async def get_swarm_blackboard():
    """Get current blackboard state (all keys)"""
    try:
        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        state = dashboard.swarm.get_blackboard_state()
        return JSONResponse(
            {"success": True, "entries": state, "state": state, "key_count": len(state)}
        )

    except Exception as e:
        logger.error(f"[SWARM] Blackboard endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/swarm/blackboard/{key}")
async def get_swarm_blackboard_key(key: str):
    """Get specific blackboard key value"""
    try:
        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        value = dashboard.swarm.get_blackboard_state(key)
        return JSONResponse({"success": True, "key": key, "value": value})

    except Exception as e:
        logger.error(f"[SWARM] Blackboard key endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/swarm/budget/global")
async def get_swarm_budget_global():
    """Get aggregated budget status across all tasks"""
    try:
        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        budget_file = (
            Path(dashboard.swarm.coordinator.data_dir) / "budget_tracking.json"
        )

        if not budget_file.exists():
            return JSONResponse(
                {"success": True, "tasks": [], "total_used": 0, "total_limit": 0}
            )

        with open(budget_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        tasks = data.get("tasks", {})
        task_list = []
        total_used = 0
        total_limit = 0

        for task_id, task_data in tasks.items():
            tokens_used = task_data.get("tokens_used", 0)
            budget_limit = task_data.get("budget_limit", 0)

            task_list.append(
                {
                    "task_id": task_id,
                    "tokens_used": tokens_used,
                    "budget_limit": budget_limit,
                    "percentage": (tokens_used / budget_limit * 100)
                    if budget_limit > 0
                    else 0,
                    "status": task_data.get("status", "active"),
                    "last_updated": task_data.get("last_updated", ""),
                }
            )

            total_used += tokens_used
            total_limit += budget_limit

        return JSONResponse(
            {
                "success": True,
                "tasks": sorted(task_list, key=lambda x: x["percentage"], reverse=True),
                "total_used": total_used,
                "total_limit": total_limit,
                "global_percentage": (total_used / total_limit * 100)
                if total_limit > 0
                else 0,
            }
        )

    except Exception as e:
        logger.error(f"[SWARM] Global budget endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/swarm/audit")
async def get_swarm_audit_log():
    """Get permission audit log entries"""
    try:
        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        audit_file = Path(dashboard.swarm.coordinator.data_dir) / "audit_log.jsonl"

        if not audit_file.exists():
            return JSONResponse({"success": True, "entries": []})

        entries = []
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        entries.reverse()

        return JSONResponse(
            {"success": True, "entries": entries[:100], "total_count": len(entries)}
        )

    except Exception as e:
        logger.error(f"[SWARM] Audit log endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/swarm/test-alert")
async def test_budget_alert(request: Request):
    """Test budget alert system with sample data"""
    try:
        data = await request.json()
        task_id = data.get("task_id", "test_task_alert")
        tokens_used = data.get("tokens_used", 8500)
        budget_limit = data.get("budget_limit", 10000)

        if not dashboard.swarm:
            return JSONResponse(
                {"error": "Pantheon Swarm not initialized"}, status_code=503
            )

        # Import alert manager
        from src.budget_alerts import send_budget_alert

        # Send test alert
        result = await send_budget_alert(
            task_id=task_id, tokens_used=tokens_used, budget_limit=budget_limit
        )

        return JSONResponse(
            {
                "success": True,
                "result": result,
                "message": f"Alert check complete: {result.get('alert_level', 'None')}",
            }
        )

    except Exception as e:
        logger.error(f"[SWARM] Test alert endpoint error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# Analytics Endpoints
analytics = UsageAnalytics()


@app.get("/api/analytics/usage")
async def get_analytics(days: int = 7):
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
                "hourly_usage": report.hourly_usage[:24],  # Last 24 hours
            },
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
                "projected_monthly_cost": cost_analysis.projected_monthly_cost,
            },
        }
    except Exception as e:
        logger.error(f"Cost analytics endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/analytics/provider/{provider}")
async def get_provider_analytics(provider: str, days: int = 7):
    """Get detailed analytics for a specific provider"""
    try:
        provider_data = await analytics.get_provider_performance(provider, days=days)
        return {"success": True, "data": provider_data}
    except Exception as e:
        logger.error(f"Provider analytics endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/analytics/expensive-requests")
async def get_expensive_requests(limit: int = 10):
    """Get the most expensive individual requests"""
    try:
        expensive_requests = await analytics.get_top_expensive_requests(limit=limit)
        return {"success": True, "data": expensive_requests}
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
        return {"success": True, "providers": providers, "details": provider_info}
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
        analysis = await multimodal_processor.process_image_analysis(
            image_content, query, provider
        )

        return {"success": True, "analysis": analysis, "provider": provider}
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
        attachments = data.get(
            "attachments", []
        )  # List of {type: "image", data: "base64..."}

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
                    base64_data = (
                        attachment_data.split(",")[1]
                        if "," in attachment_data
                        else attachment_data
                    )
                    content.append(MultiModalContent.from_image_base64(base64_data))
                else:
                    # Assume direct base64
                    content.append(MultiModalContent.from_image_base64(attachment_data))
            elif attachment_type == "text":
                content.append(MultiModalContent.from_text(attachment_data))

        # Create multi-modal message
        multimodal_msg = create_multimodal_message(content, provider=provider)

        # Process through multi-modal system
        response = await multimodal_processor.process_multimodal_message(
            multimodal_msg, provider
        )

        # Format response
        if hasattr(response, "get_text_content"):
            # MultiModalMessage response
            text_response = response.get_text_content()
            has_images = len(response.get_image_content()) > 0
            response_data = {
                "text": text_response,
                "has_images": has_images,
                "image_count": len(response.get_image_content()),
            }
        else:
            # Traditional Message response
            response_data = {
                "text": response.response or "No response generated",
                "has_images": False,
                "image_count": 0,
            }

        return {
            "success": True,
            "response": response_data,
            "provider": provider,
            "timestamp": datetime.now().isoformat(),
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
        description = await multimodal_processor.generate_image_description(
            image_content, style, provider
        )

        return {
            "success": True,
            "description": description,
            "style": style,
            "provider": provider,
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
            metadata={"format": "pdf", "base64_size": len(pdf_data)},
        )

        # Create multi-modal message
        multimodal_msg = create_multimodal_message([pdf_content])

        # Process through multi-modal system
        response = await multimodal_processor.process_multimodal_message(
            multimodal_msg, provider
        )

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
            "note": "PDF processing is in development - currently returns basic analysis",
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
            "has_content": bool(extracted_text.strip()),
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
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"MCP security endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/security/principals")
async def get_mcp_security_principals():
    """Get all security principals"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        principals = {}
        for id, principal in dashboard.mcp_security_manager.principals.items():
            principals[id] = {
                "id": principal.id,
                "name": principal.name,
                "type": principal.type,
                "security_level": principal.security_level.value,
                "permissions": [p.value for p in principal.permissions],
                "created_at": principal.created_at.isoformat(),
                "last_active": principal.last_active.isoformat(),
            }

        return {
            "success": True,
            "principals": principals,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"MCP security principals endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/mcp/security/principals")
async def create_mcp_security_principal(request: Request):
    """Create a new security principal"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        data = await request.json()
        principal_id = data.get("id")
        name = data.get("name")
        principal_type = data.get("type", "user")
        security_level = data.get("security_level", "USER")
        permissions = data.get("permissions", [])

        if not principal_id or not name:
            return {"success": False, "error": "Principal ID and name are required"}

        from src.mcp_security import SecurityLevel, Permission

        # Convert string to enum
        try:
            level = SecurityLevel(security_level.upper())
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid security level: {security_level}",
            }

        # Convert permissions
        permission_enums = []
        for perm in permissions:
            try:
                permission_enums.append(Permission(perm.upper()))
            except ValueError:
                return {"success": False, "error": f"Invalid permission: {perm}"}

        principal = await dashboard.mcp_security_manager.create_principal(
            principal_id, name, principal_type, level, set(permission_enums)
        )

        return {
            "success": True,
            "principal": {
                "id": principal.id,
                "name": principal.name,
                "type": principal.type,
                "security_level": principal.security_level.value,
                "permissions": [p.value for p in principal.permissions],
            },
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Create MCP security principal endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/security/tokens")
async def get_mcp_security_tokens():
    """Get all active access tokens"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        tokens = {}
        for token_str, token in dashboard.mcp_security_manager.tokens.items():
            tokens[token_str[:8] + "..."] = {
                "principal_id": token.principal_id,
                "expires_at": token.expires_at.isoformat(),
                "permissions": [p.value for p in token.permissions],
                "created_at": token.created_at.isoformat(),
            }

        return {
            "success": True,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"MCP security tokens endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/mcp/security/tokens")
async def create_mcp_security_token(request: Request):
    """Create a new access token"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        data = await request.json()
        principal_id = data.get("principal_id")
        expires_in = data.get("expires_in", 3600)
        permissions = data.get("permissions", [])

        if not principal_id:
            return {"success": False, "error": "Principal ID is required"}

        # Convert permissions
        permission_enums = []
        for perm in permissions:
            try:
                from src.mcp_security import Permission

                permission_enums.append(Permission(perm.upper()))
            except ValueError:
                return {"success": False, "error": f"Invalid permission: {perm}"}

        token = await dashboard.mcp_security_manager.create_token(
            principal_id,
            expires_in,
            set(permission_enums) if permission_enums else None,
        )

        if not token:
            return {
                "success": False,
                "error": "Failed to create token - principal not found",
            }

        return {
            "success": True,
            "token": token,
            "expires_in": expires_in,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Create MCP security token endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/mcp/security/tokens/{token_prefix}")
async def revoke_mcp_security_token(token_prefix: str):
    """Revoke an access token by prefix"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        # Find token by prefix
        target_token = None
        for token_str in dashboard.mcp_security_manager.tokens:
            if token_str.startswith(token_prefix):
                target_token = token_str
                break

        if not target_token:
            return {"success": False, "error": "Token not found"}

        success = await dashboard.mcp_security_manager.revoke_token(target_token)

        return {
            "success": success,
            "message": "Token revoked successfully"
            if success
            else "Failed to revoke token",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Revoke MCP security token endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/security/audit")
async def get_mcp_security_audit(
    limit: int = 100, principal_id: str = None, action: str = None
):
    """Get audit log events"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        events = await dashboard.mcp_security_manager.get_audit_events(
            limit=limit, principal_id=principal_id, action=action
        )

        audit_events = []
        for event in events:
            audit_events.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "principal_id": event.principal_id,
                    "action": event.action,
                    "resource": event.resource,
                    "success": event.success,
                    "details": event.details,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                }
            )

        return {
            "success": True,
            "events": audit_events,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"MCP security audit endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/mcp/security/rate-limits")
async def get_mcp_security_rate_limits():
    """Get rate limit rules and status"""
    try:
        if not dashboard.mcp_security_manager:
            return {"success": False, "error": "MCP Security not available"}

        rules = {}
        for name, rule in dashboard.mcp_security_manager.rate_rules.items():
            rules[name] = {
                "name": rule.name,
                "max_requests": rule.max_requests,
                "window_seconds": rule.window_seconds,
                "burst_limit": rule.burst_limit,
                "cooldown_seconds": rule.cooldown_seconds,
            }

        return {
            "success": True,
            "rules": rules,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"MCP security rate limits endpoint error: {e}")
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
            agent_name=agent_name,
        )

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
            server_name=server_name, uri=uri, agent_name=agent_name
        )

        return {
            "success": True,
            "result": result,
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
            "timestamp": datetime.now().isoformat(),
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
                "blocked_count": sum(
                    1 for op in pending_approvals if op.get("status") == "denied"
                ),
            },
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
                "can_proceed": result.can_proceed,
            },
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

        return {"success": True, "data": approvals}
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

        success = security_validator.approve_operation(
            approval_id, approved, admin_user
        )

        return {
            "success": success,
            "message": f"Operation {'approved' if approved else 'denied'}",
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

        approval_request = security_validator.request_approval(
            operation, validation_data, user_id
        )

        return {
            "success": True,
            "data": {
                "request_id": approval_request.id,
                "status": approval_request.status.value,
                "requires_approval": approval_request.requires_user_approval
                or approval_request.requires_admin_approval,
            },
        }

    except Exception as e:
        logger.error(f"Request approval endpoint error: {e}")
        return {"success": False, "error": str(e)}


# Community Vault API Endpoints


@app.get("/api/vault/categories")
async def get_vault_categories():
    """Get available vault categories"""
    try:
        categories = await vault.get_categories()
        return {"success": True, "data": categories}
    except Exception as e:
        logger.error(f"Vault categories endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/vault/stats")
async def get_vault_stats():
    """Get vault statistics"""
    try:
        stats = await vault.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Vault stats endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/vault/featured")
async def get_featured_items(limit: int = 10):
    """Get featured vault items"""
    try:
        items = await vault.get_featured_items(limit)
        return {"success": True, "data": [item.to_dict() for item in items]}
    except Exception as e:
        logger.error(f"Featured items endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/vault/search")
async def search_vault_items(
    q: str = "",
    category: str = None,
    author: str = None,
    tags: str = None,
    sort_by: str = "downloads",
    sort_order: str = "desc",
    limit: int = 20,
    offset: int = 0,
):
    """Search vault items"""
    try:
        # Parse tags if provided
        tag_list = tags.split(",") if tags else None

        items = await vault.search_items(
            query=q,
            category=category,
            author=author,
            tags=tag_list,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        return {
            "success": True,
            "data": [item.to_dict() for item in items],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(items) == limit,
            },
        }
    except Exception as e:
        logger.error(f"Vault search endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/vault/item/{item_id}")
async def get_vault_item(item_id: str):
    """Get a specific vault item"""
    try:
        item = await vault.get_item(item_id)
        if item:
            return {"success": True, "data": item.to_dict()}
        else:
            return {"success": False, "error": "Item not found"}
    except Exception as e:
        logger.error(f"Get vault item endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/vault/publish")
async def publish_vault_item(request: Request):
    """Publish a new vault item"""
    try:
        data = await request.json()
        item_data = data.get("item", {})
        author = data.get("author", "anonymous")

        # Basic validation
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            if field not in item_data:
                return {"success": False, "error": f"Missing required field: {field}"}

        success, result = await vault.publish_item(item_data, author=author)

        if success:
            return {"success": True, "data": {"item_id": result}}
        else:
            return {"success": False, "error": result}

    except Exception as e:
        logger.error(f"Publish vault item endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/vault/download/{item_id}")
async def download_vault_item(item_id: str, request: Request):
    """Download a vault item"""
    try:
        # Get client info for download tracking
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        content = await vault.download_item(
            item_id=item_id, ip_address=client_ip, user_agent=user_agent
        )

        if content:
            item = await vault.get_item(item_id)
            if item:
                return {
                    "success": True,
                    "data": {
                        "item": item.to_dict(),
                        "content": base64.b64encode(content).decode("utf-8"),
                        "content_type": item.content_type,
                    },
                }

        return {"success": False, "error": "Item not found or download failed"}

    except Exception as e:
        logger.error(f"Download vault item endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/vault/rate/{item_id}")
async def rate_vault_item(item_id: str, request: Request):
    """Rate a vault item"""
    try:
        data = await request.json()
        user_id = data.get("user_id", "anonymous")
        rating = data.get("rating", 0)
        review = data.get("review")

        if not 1 <= rating <= 5:
            return {"success": False, "error": "Rating must be between 1 and 5"}

        success = await vault.rate_item(item_id, user_id, rating, review)

        if success:
            return {"success": True, "message": "Rating submitted successfully"}
        else:
            return {"success": False, "error": "Failed to submit rating"}

    except Exception as e:
        logger.error(f"Rate vault item endpoint error: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/vault/item/{item_id}")
async def delete_vault_item(item_id: str, author: str = "admin"):
    """Delete a vault item (admin only)"""
    try:
        # In a real implementation, you'd check admin permissions
        # For now, we'll just check if the item exists
        item = await vault.get_item(item_id)
        if not item:
            return {"success": False, "error": "Item not found"}

        # For now, just return success (actual deletion would require more complex logic)
        return {"success": True, "message": "Item deletion not yet implemented"}

    except Exception as e:
        logger.error(f"Delete vault item endpoint error: {e}")
        return {"success": False, "error": str(e)}


# ===== SUBSCRIPTION & BILLING ENDPOINTS =====


@app.get("/api/subscriptions/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    try:
        if payment_manager:
            return {"success": True, "data": payment_manager.get_plans()}
        else:
            return {"success": False, "error": "Payment system not available"}
    except Exception as e:
        logger.error(f"Get subscription plans error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/subscriptions/create-checkout")
async def create_subscription_checkout(request: Request):
    """Create checkout session for subscription"""
    try:
        if not payment_manager:
            return {"success": False, "error": "Payment system not available"}

        data = await request.json()
        from src.payments import CreateCheckoutSessionRequest

        checkout_request = CreateCheckoutSessionRequest(**data)
        result = await payment_manager.create_checkout_session(checkout_request)
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Create checkout session error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/subscriptions/portal")
async def create_customer_portal(request: Request):
    """Create customer portal session for billing management"""
    try:
        if not payment_manager:
            return {"success": False, "error": "Payment system not available"}

        data = await request.json()
        from src.payments import CustomerPortalRequest

        portal_request = CustomerPortalRequest(**data)
        result = await payment_manager.create_customer_portal_session(portal_request)
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Create portal session error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/subscriptions/{subscription_id}")
async def get_user_subscription(subscription_id: str):
    """Get user's subscription details"""
    try:
        if not payment_manager:
            return {"success": False, "error": "Payment system not available"}

        subscription = await payment_manager.get_subscription(subscription_id)
        return {"success": True, "data": subscription}

    except Exception as e:
        logger.error(f"Get subscription error: {e}")
        return {"success": False, "error": str(e)}


@app.delete("/api/subscriptions/{subscription_id}")
async def cancel_user_subscription(subscription_id: str, request: Request):
    """Cancel user's subscription"""
    try:
        if not payment_manager:
            return {"success": False, "error": "Payment system not available"}

        data = await request.json()
        immediate = data.get("immediate", False)

        result = await payment_manager.cancel_subscription(subscription_id, immediate)
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Cancel subscription error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/subscriptions/webhook")
async def stripe_webhook_handler(request: Request):
    """Handle Stripe webhooks for subscription events"""
    try:
        if not payment_manager:
            return {"status": "ignored", "reason": "Payment system not available"}

        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        result = await payment_manager.handle_webhook(payload.decode(), sig_header)
        return result

    except Exception as e:
        logger.error(f"Webhook handler error: {e}")
        return {"status": "error", "error": str(e)}


@app.get("/api/billing/usage")
async def get_billing_usage(user_id: str = "demo"):
    """Get user's API usage for billing"""
    try:
        # This would typically fetch from a database
        # For demo, return mock data
        usage_data = {
            "user_id": user_id,
            "current_period_start": (datetime.now() - timedelta(days=30)).isoformat(),
            "current_period_end": datetime.now().isoformat(),
            "api_calls_used": 847,
            "api_calls_limit": 1000 if user_id == "demo" else None,
            "tokens_used": 125420,
            "cost_breakdown": {
                "chatgpt": {"calls": 342, "tokens": 52123, "cost": 2.45},
                "claude": {"calls": 287, "tokens": 48921, "cost": 3.12},
                "gemini": {"calls": 218, "tokens": 24376, "cost": 0.89},
            },
        }
        return {"success": True, "data": usage_data}

    except Exception as e:
        logger.error(f"Get billing usage error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/revenue/dashboard")
async def get_revenue_dashboard():
    """Get revenue analytics dashboard data"""
    try:
        # Mock revenue data - in production this would come from database
        revenue_data = {
            "current_mrr": 0,  # Monthly Recurring Revenue
            "current_arr": 0,  # Annual Recurring Revenue
            "total_customers": 0,
            "conversion_rate": 0,
            "churn_rate": 0,
            "mrr_growth": {"this_month": 0, "last_month": 0, "growth_percent": 0},
            "customer_breakdown": {
                "free": 1,  # demo user
                "pro": 0,
                "enterprise": 0,
            },
            "revenue_by_tier": {"free": 0, "pro": 0, "enterprise": 0},
            "monthly_revenue": [
                {"month": "Jan", "revenue": 0},
                {"month": "Feb", "revenue": 0},
                {"month": "Mar", "revenue": 0},
                {"month": "Apr", "revenue": 0},
                {"month": "May", "revenue": 0},
                {"month": "Jun", "revenue": 0},
            ],
        }
        return {"success": True, "data": revenue_data}

    except Exception as e:
        logger.error(f"Get revenue dashboard error: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "web_dashboard:app", host="0.0.0.0", port=8000, reload=False, log_level="info"
    )
