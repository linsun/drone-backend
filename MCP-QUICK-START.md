# Tello MCP Server - Quick Start

## What You Can Do

Control your Tello drone by talking to Claude in natural language! 🚁✨

## Setup (One-Time)

```bash
cd ~/src/github.com/linsun/tello-backend

# Run setup helper
./setup_mcp.sh

# Follow the instructions to add Tello to Claude Desktop config
# Then restart Claude Desktop
```

## Before Flying

1. ✅ Turn on Tello drone
2. ✅ Connect to Tello WiFi (TELLO-XXXXXX)
3. ✅ Open Claude Desktop

## Example Commands

Just talk to Claude naturally:

### Basic Flight
```
"Connect to my Tello drone"
"Take off"
"Move up 50 centimeters"
"Rotate 90 degrees clockwise"
"Land"
```

### Photo Mission
```
"Connect to the drone and start the video stream"
"Take off and take a photo"
"Move forward 100cm and take another photo"
"Compare the two photos - what changed?"
"Land the drone"
```

### Survey Pattern
```
"Fly a square pattern: take off, move forward 100cm,
rotate 90 degrees, repeat 4 times, then land"
```

### Status Check
```
"What's my drone's battery level?"
"Show me the current status"
```

### Advanced
```
"Set speed to 30 cm/s for safer indoor flying"
"Move up 50cm, forward 100cm, then take a photo"
"Do a flip forward" (only if safe!)
```

## Available Tools (17 total)

| Category | Tools |
|----------|-------|
| **Connection** | connect, get_status |
| **Flight** | takeoff, land, emergency_stop |
| **Move** | move_up, move_down, move_forward, move_back, move_left, move_right |
| **Rotate** | rotate_clockwise, rotate_counterclockwise |
| **Camera** | start_video_stream, stop_video_stream, capture_photo |
| **Advanced** | flip, set_speed |

## Safety

⚠️ **Always:**
- Fly in open space (2m × 2m minimum)
- Keep battery > 20%
- Be ready to say "emergency stop" (drone will fall!)
- Start with small movements (20-30cm)

## Testing Without Claude Desktop

```bash
# Test that MCP server works
cd ~/src/github.com/linsun/tello-backend
python3 test_mcp_standalone.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Not connected" | Make sure you're on Tello WiFi |
| Claude doesn't see tools | Restart Claude Desktop, check config |
| Commands timeout | Stay within 10m of drone |
| Video stream fails | Call "start video stream" first |

## Files

- **mcp_server.py** - The MCP server (runs automatically via Claude)
- **setup_mcp.sh** - Setup helper script
- **MCP-TESTING-GUIDE.md** - Full documentation
- **test_mcp_standalone.py** - Standalone test script

## Example Session

```
You: Connect to my Tello drone

Claude: ✅ I've connected to your Tello drone.
Battery is at 85%.

You: Take off and move to a height of about 1.5 meters

Claude: ✅ The drone has taken off and is hovering.
✅ Moved up 50 cm (now at approximately 1.5m).

You: Start the video and take a photo

Claude: ✅ Video stream started.
📸 Photo captured (sharpness score: 245.3)
[Photo appears inline showing the view from drone]

You: Perfect! Now land

Claude: ✅ Landing complete. Drone is on the ground.
```

## Quick Commands

### Basic Setup
```bash
cd ~/src/github.com/linsun/tello-backend
./setup_mcp.sh
```

### Test Server
```bash
python3 test_mcp_standalone.py
```

### Claude Desktop Config Location
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Required Config
```json
{
  "mcpServers": {
    "tello-drone": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"],
      "env": {
        "OPENCV_AVFOUNDATION_SKIP_AUTH": "1"
      }
    }
  }
}
```

## Tips

💡 **Pro Tips:**
- Use specific measurements (e.g., "50cm" not "a bit")
- Ask Claude to check status before/after flights
- Have Claude take photos at key points
- Use lower speeds indoors (20-30 cm/s)
- Let Claude plan complex flight patterns

🎯 **Best Use Cases:**
- Automated inspection flights
- Multi-angle photography
- Systematic area surveys
- Hands-free drone operation
- Complex flight patterns

---

**Need Help?** See `MCP-TESTING-GUIDE.md` for full documentation!
