#!/bin/bash

# Tello Drone MCP Server Launcher
# This script activates the virtual environment and runs the MCP server

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚁 Starting Tello Drone MCP Server..."
echo "📁 Working directory: $SCRIPT_DIR"

# Check if venv exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Check if MCP is installed
if ! python -c "import mcp" 2>/dev/null; then
    echo "❌ MCP package not found"
    echo "Installing MCP..."
    pip install mcp
fi

# Run the MCP server
echo "✅ Launching MCP server..."
echo ""
python "$SCRIPT_DIR/mcp_server.py"
