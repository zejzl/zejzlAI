#!/bin/bash
# Docker entrypoint for ZEJZL.NET

echo "🐳 ZEJZL.NET Docker Container Starting"
echo "====================================="

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    echo "Redis not ready, waiting..."
    sleep 2
done
echo "✓ Redis is ready"

# Create data directories
mkdir -p /app/data
mkdir -p /app/logs

# Check if .env exists, create from template if not
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please mount your .env file with API keys for full functionality"
fi

# Run health check
echo "Running initial health check..."
python -c "
import asyncio
from ai_framework import AsyncMessageBus

async def health_check():
    try:
        bus = AsyncMessageBus()
        await bus.start()
        print('✓ AI Framework initialized successfully')
        await bus.stop()
    except Exception as e:
        print(f'❌ Health check failed: {e}')
        exit(1)

asyncio.run(health_check())
"

echo ""
echo "🚀 Starting ZEJZL.NET..."
echo "========================"
echo ""

# Execute the main command
exec "$@"