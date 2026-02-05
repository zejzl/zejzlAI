#!/usr/bin/env python3
"""
ZEJZL.NET Production Startup Script
Handles graceful startup with optional dependencies
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def check_dependencies():
    """Check which dependencies are available"""
    dependencies = {
        "stripe": False,
        "aiosqlite": False,
        "jwt": False,
        "passlib": False,
        "email_validator": False,
    }

    try:
        import stripe

        dependencies["stripe"] = True
        logger.info("✅ Stripe available")
    except ImportError:
        logger.warning("⚠️ Stripe not available - payment system disabled")

    try:
        import aiosqlite

        dependencies["aiosqlite"] = True
        logger.info("✅ aiosqlite available")
    except ImportError:
        logger.warning("⚠️ aiosqlite not available - user management disabled")

    try:
        import jwt

        dependencies["jwt"] = True
        logger.info("✅ JWT available")
    except ImportError:
        logger.warning("⚠️ JWT not available - authentication disabled")

    try:
        from passlib.context import CryptContext

        dependencies["passlib"] = True
        logger.info("✅ Passlib available")
    except ImportError:
        logger.warning("⚠️ Passlib not available - password hashing disabled")

    try:
        import email_validator

        dependencies["email_validator"] = True
        logger.info("✅ Email validator available")
    except ImportError:
        logger.warning("⚠️ Email validator not available")

    return dependencies


async def create_minimal_app():
    """Create minimal FastAPI app that works without optional dependencies"""
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="ZEJZL.NET Dashboard", version="1.0.0")

    # Mount static files
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return """
        <html>
            <head><title>ZEJZL.NET</title></head>
            <body>
                <h1>ZEJZL.NET Dashboard</h1>
                <p><a href="/blackboard">Go to Blackboard Dashboard</a></p>
                <p><a href="/billing">Billing Dashboard (if available)</a></p>
                <p><a href="/get-started">Get Started (if available)</a></p>
            </body>
        </html>
        """

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "1.0.0"}

    return app


async def main():
    """Main startup function"""
    logger.info("🚀 Starting ZEJZL.NET Dashboard")

    # Check dependencies
    deps = await check_dependencies()

    # Create app based on available dependencies
    if deps.get("stripe") and deps.get("aiosqlite"):
        logger.info("🎯 Full features available - starting complete app")
        # Import and start full app
        try:
            from web_dashboard import app

            logger.info("✅ Full app loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load full app: {e}")
            logger.info("🔄 Falling back to minimal app")
            app = await create_minimal_app()
    else:
        logger.info("🔄 Some dependencies missing - starting minimal app")
        app = await create_minimal_app()

    # Start server
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    logger.info(f"🌐 Server starting on port {port}")
    config = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
