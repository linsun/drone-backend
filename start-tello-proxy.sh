#!/bin/bash

# Start Tello Proxy Service on Mac
# This service runs natively and provides HTTP API for Tello drone control

set -e

echo "🚁 Tello Proxy Service Launcher"
echo "================================"
echo ""

# Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Check Tello WiFi connection
echo "🔍 Checking Tello connectivity..."
if ping -c 1 -W 2 192.168.10.1 >/dev/null 2>&1; then
    echo "✅ Tello reachable at 192.168.10.1"
else
    echo "⚠️  Cannot reach Tello at 192.168.10.1"
    echo "   Please connect to Tello WiFi (TELLO-XXXXXX)"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Check dependencies
echo "📦 Checking dependencies..."
MISSING_DEPS=()

python3 -c "import flask" 2>/dev/null || MISSING_DEPS+=("flask")
python3 -c "import flask_cors" 2>/dev/null || MISSING_DEPS+=("flask-cors")
python3 -c "import mcp" 2>/dev/null || MISSING_DEPS+=("mcp")
python3 -c "import cv2" 2>/dev/null || MISSING_DEPS+=("opencv-python")
python3 -c "import djitellopy" 2>/dev/null || MISSING_DEPS+=("djitellopy")

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "Installing missing dependencies: ${MISSING_DEPS[*]}"
    pip3 install flask flask-cors mcp opencv-python djitellopy
fi
echo "✅ Dependencies OK"
echo ""

# Check if port 5000 is available
if lsof -Pi :50000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 50000 is already in use"
    echo ""
    lsof -i :50000
    echo ""
    read -p "Kill the process using port 50000? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti :50000)
        kill $PID
        echo "✅ Killed process $PID"
        sleep 1
    else
        exit 1
    fi
fi
echo ""

# Start the proxy service
echo "🚀 Starting Tello Proxy Service with MCP + Video Support..."
echo "   Service will run on http://0.0.0.0:50000"
echo "   REST API + MCP Tools + Video Streaming available"
echo "   Press Ctrl+C to stop"
echo ""

python3 tello-proxy-mcp-video.py
