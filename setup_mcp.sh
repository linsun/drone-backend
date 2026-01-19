#!/bin/bash

# Setup script for Tello MCP Server with Claude Desktop

echo "🚁 Tello MCP Server Setup for Claude Desktop"
echo "=============================================="
echo ""

# Get the absolute path to mcp_server.py
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MCP_SERVER_PATH="$SCRIPT_DIR/mcp_server.py"

echo "MCP Server location: $MCP_SERVER_PATH"
echo ""

# Detect OS and set config file location
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CONFIG_FILE="$HOME/.config/Claude/claude_desktop_config.json"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please manually add the MCP server to your Claude Desktop config."
    exit 1
fi

echo "Claude Desktop config: $CONFIG_FILE"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠️  Claude Desktop config file not found."
    echo "Creating directory and config file..."

    mkdir -p "$(dirname "$CONFIG_FILE")"

    # Create new config with just the Tello server
    cat > "$CONFIG_FILE" <<EOF
{
  "mcpServers": {
    "tello-drone": {
      "command": "python3",
      "args": [
        "$MCP_SERVER_PATH"
      ],
      "env": {
        "OPENCV_AVFOUNDATION_SKIP_AUTH": "1"
      }
    }
  }
}
EOF

    echo "✅ Created new config file with Tello MCP server"
else
    echo "✅ Config file exists"
    echo ""
    echo "⚠️  IMPORTANT: You need to manually add the Tello server to your config."
    echo ""
    echo "Add this to the 'mcpServers' section of $CONFIG_FILE:"
    echo ""
    cat <<EOF
    "tello-drone": {
      "command": "python3",
      "args": [
        "$MCP_SERVER_PATH"
      ],
      "env": {
        "OPENCV_AVFOUNDATION_SKIP_AUTH": "1"
      }
    }
EOF
    echo ""
    echo "Example full config:"
    echo ""
    cat <<EOF
{
  "mcpServers": {
    "tello-drone": {
      "command": "python3",
      "args": [
        "$MCP_SERVER_PATH"
      ],
      "env": {
        "OPENCV_AVFOUNDATION_SKIP_AUTH": "1"
      }
    }
  }
}
EOF
fi

echo ""
echo "=============================================="
echo "Next steps:"
echo ""
echo "1. ✅ Make sure you've edited: $CONFIG_FILE"
echo "2. 🔄 Restart Claude Desktop completely"
echo "3. 📡 Connect to your Tello WiFi (TELLO-XXXXXX)"
echo "4. 💬 In Claude Desktop, say: 'Connect to my Tello drone'"
echo "5. 🚁 Start flying with natural language!"
echo ""
echo "For more info, see: MCP-TESTING-GUIDE.md"
echo "=============================================="
