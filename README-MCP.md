# 🚁 Tello Drone MCP Server

Control your Tello drone using natural language through Claude!

## Quick Start

### 1. Install Dependencies

```bash
cd tello-backend
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this (update the path to match your setup):

```json
{
  "mcpServers": {
    "tello-drone": {
      "command": "python",
      "args": ["/Users/linsun/src/github.com/linsun/tello-backend/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/linsun/src/github.com/linsun/tello-backend/venv/lib/python3.12/site-packages"
      }
    }
  }
}
```

### 3. Connect to Tello WiFi

Connect your computer to your Tello's WiFi network (TELLO-XXXXXX)

### 4. Restart Claude Desktop

Restart Claude Desktop to load the MCP server.

### 5. Start Flying!

In Claude Desktop, try:

```
"Connect to my Tello drone"
"What's the battery level?"
"Take off"
"Move up 50 cm"
"Capture a photo"
"Land"
```

## Available Commands

- **Flight**: takeoff, land, move (up/down/left/right/forward/back), rotate, flip
- **Camera**: start/stop video stream, capture photo
- **Status**: connect, get status (battery, temperature, height)
- **Safety**: emergency stop, set speed

## Full Documentation

See [MCP-SERVER-GUIDE.md](./MCP-SERVER-GUIDE.md) for:
- Complete command reference
- Safety guidelines
- Troubleshooting
- Advanced usage examples
- Flight patterns

## Safety First! ⚠️

- Always maintain visual line of sight
- Check battery before flying
- Fly in open, obstacle-free areas
- Keep away from people and animals
- Know how to use emergency stop

## Example Flight Mission

```
"Here's my flight plan:
1. Connect to the drone
2. Check the battery level
3. Take off
4. Move up 1 meter
5. Rotate 360 degrees while taking photos every 90 degrees
6. Land safely"
```

Claude will execute each step and show you the results!

## Troubleshooting

**MCP server not showing up in Claude?**
- Check the path in your config file is correct
- Make sure you restarted Claude Desktop
- Verify the venv path exists

**"Not connected" error?**
- Connect to Tello WiFi first
- Ask Claude to "Connect to the drone"

**Commands failing?**
- Check battery level
- Make sure you're in range
- Try reconnecting

For more help, see the [full guide](./MCP-SERVER-GUIDE.md).
