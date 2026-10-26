#!/bin/bash
# Quick start script for zejzl.net

echo "[START] zejzl.net Quick Start"
echo "========================"

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "[ERROR] Redis is not running!"
    echo "Start Redis with: redis-server"
    exit 1
fi

echo "[OK] Redis is running"

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

echo "[OK] Dependencies installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "[WARNING] No .env file found, copying from .env.example"
    cp .env.example .env
    echo "[NOTE] Please edit .env with your API keys"
fi

echo ""
echo "Starting zejzl.net..."
echo "========================"
echo ""

# Run the main script
python main.py