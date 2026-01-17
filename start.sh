#!/bin/bash
# Quick start script for zejzl.net

echo "🚀 zejzl.net Quick Start"
echo "========================"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "Start Redis with: redis-server"
    exit 1
fi

echo "✓ Redis is running"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.installed
fi

echo "✓ Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found, copying from .env.example"
    cp .env.example .env
    echo "📝 Please edit .env with your API keys"
fi

echo ""
echo "Starting zejzl.net..."
echo "========================"
echo ""

# Run the main script
python main.py