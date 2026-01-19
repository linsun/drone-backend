# Tello MCP Server Testing Guide

## What is the MCP Server?

The Tello MCP (Model Context Protocol) Server allows AI assistants like Claude to control your Tello drone through natural language commands. Instead of writing code or using a UI, you can just talk to Claude and say things like:

- "Connect to the drone and take off"
- "Move forward 50cm and take a photo"
- "Rotate 90 degrees clockwise"
- "What's the battery level?"

## Prerequisites

1. **Tello Drone** - Powered on and ready
2. **WiFi Connection** - Connected to Tello WiFi network (TELLO-XXXXXX)
3. **Backend Dependencies** - Already installed via `requirements.txt`

## Configuration for Claude Desktop

To use the MCP server with Claude Desktop app, you need to add it to your configuration.

### 1. Find Your Claude Desktop Config File

**Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add Tello MCP Server to Config

Edit the config file and add the Tello server to the `mcpServers` section:

```json
{
  "mcpServers": {
    "tello-drone": {
      "command": "python3",
      "args": [
        "/Users/linsun/src/github.com/linsun/tello-backend/mcp_server.py"
      ],
      "env": {
        "OPENCV_AVFOUNDATION_SKIP_AUTH": "1"
      }
    }
  }
}
```

**Important:** Replace `/Users/linsun/src/github.com/linsun/tello-backend/mcp_server.py` with the actual path to your `mcp_server.py` file.

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server.

## Verifying MCP Server is Loaded

In Claude Desktop, you should see:
- A small 🔌 icon or indicator showing MCP servers are connected
- When you type a message, Claude will have access to Tello drone tools

## Testing the MCP Server

### Method 1: Using Claude Desktop (Recommended)

Once configured, you can control your drone through natural language in Claude Desktop:

**Example Conversation:**

```
You: Connect to my Tello drone

Claude: [Calls the 'connect' tool]
I've connected to your Tello drone. Battery is at 85%.

You: Take off and hover

Claude: [Calls 'takeoff' tool]
The drone has taken off and is now hovering safely.

You: Move up 50 centimeters

Claude: [Calls 'move_up' with distance=50]
The drone has moved up 50 cm.

You: Start the video stream and take a photo

Claude: [Calls 'start_video_stream' then 'capture_photo']
I've started the video stream and captured a photo. Here's what the drone sees:
[Photo appears inline]

You: Rotate 90 degrees clockwise and take another photo

Claude: [Calls 'rotate_clockwise' with angle=90, then 'capture_photo']
The drone has rotated 90° clockwise. Here's the new view:
[Photo appears inline]

You: Land the drone

Claude: [Calls 'land' tool]
The drone has landed safely.
```

### Method 2: Manual Testing with MCP Inspector

If you want to test the server directly without Claude Desktop:

```bash
# Install MCP inspector (one-time)
npm install -g @modelcontextprotocol/inspector

# Run the inspector
mcp-inspector python3 /Users/linsun/src/github.com/linsun/tello-backend/mcp_server.py
```

This opens a web interface where you can:
- See all available tools
- Manually call each tool
- View responses

### Method 3: Command-Line Testing

You can also test the server via stdin/stdout:

```bash
cd ~/src/github.com/linsun/tello-backend

# Run the server (it uses stdio)
python3 mcp_server.py
```

Then send MCP protocol messages (JSON) to stdin. This is advanced and not recommended for casual testing.

## Available MCP Tools

The server provides these tools:

### Connection
- **connect** - Connect to Tello drone (must be called first)
- **get_status** - Get battery, temperature, height, flight time

### Flight Control
- **takeoff** - Take off and hover
- **land** - Land safely
- **emergency_stop** - Emergency motor stop (drone will fall!)

### Movement (20-500 cm)
- **move_up** - Move up
- **move_down** - Move down
- **move_forward** - Move forward
- **move_back** - Move backward
- **move_left** - Move left
- **move_right** - Move right

### Rotation (1-360 degrees)
- **rotate_clockwise** - Turn right
- **rotate_counterclockwise** - Turn left

### Advanced
- **flip** - Flip in direction (left, right, forward, back)
- **set_speed** - Set flight speed (10-100 cm/s)

### Camera
- **start_video_stream** - Start camera stream
- **stop_video_stream** - Stop camera stream
- **capture_photo** - Take photo (returns image to Claude)

## Example Test Scenarios

### Scenario 1: Basic Flight

```
1. "Connect to the drone"
2. "What's the battery level?"
3. "Take off"
4. "Move up 30 cm"
5. "Rotate 180 degrees"
6. "Land"
```

### Scenario 2: Photo Survey

```
1. "Connect to the drone and start the video stream"
2. "Take off"
3. "Take a photo of what's in front"
4. "Rotate 90 degrees clockwise and take another photo"
5. "Rotate 90 degrees clockwise and take another photo"
6. "Rotate 90 degrees clockwise and take another photo"
7. "Now I have 4 photos from all directions - land the drone"
```

### Scenario 3: Inspection Flight

```
1. "Connect and take off"
2. "Move forward 100 cm and take a photo"
3. "Move up 50 cm and take another photo"
4. "Move back to starting position" (move back 100cm, move down 50cm)
5. "Land"
```

## Safety Tips

⚠️ **IMPORTANT SAFETY GUIDELINES:**

1. **Indoor Flying**
   - Clear a space of at least 2m × 2m × 2m
   - Remove fragile items
   - Close windows and doors
   - Keep pets and people away

2. **Battery**
   - Don't fly with battery < 20%
   - Have spare batteries charged

3. **Emergency**
   - Be ready to use `emergency_stop` (but drone will fall!)
   - Have a manual controller nearby
   - Know how to manually land

4. **Starting Out**
   - Use `set_speed` to reduce speed (e.g., 20 cm/s)
   - Start with small movements (20-30 cm)
   - Test in a safe, open area

5. **MCP Control**
   - Always monitor what Claude is doing
   - Review commands before Claude executes them
   - Be ready to intervene

## Troubleshooting

### "Not connected to Tello"
- Make sure you're on Tello WiFi network
- Tello must be powered on
- Try calling `connect` tool explicitly

### "Video stream not active"
- Call `start_video_stream` before `capture_photo`
- Wait a few seconds after starting stream

### "MCP server not showing in Claude Desktop"
- Check config file syntax (valid JSON)
- Verify file path is correct
- Restart Claude Desktop completely
- Check Claude Desktop logs

### "Command failed / Timeout"
- Tello is out of range (stay within 10m)
- Battery too low
- Drone is on the ground (needs takeoff first)

## MCP Server Logs

The server prints logs to stderr, which you can see in Claude Desktop's logs:

**macOS Logs Location:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

Look for:
```
Starting Tello Drone MCP Server...
```

## Advanced: Custom Commands

You can ask Claude to combine multiple tools:

```
You: "Fly a square pattern: take off, move forward 100cm,
      rotate 90 degrees, repeat 4 times, then land"

Claude: [Executes sequence of tools]:
- takeoff
- move_forward 100
- rotate_clockwise 90
- move_forward 100
- rotate_clockwise 90
- move_forward 100
- rotate_clockwise 90
- move_forward 100
- rotate_clockwise 90
- land
```

## Comparison: MCP Server vs Web UI

| Feature | MCP Server (Claude) | Web UI |
|---------|-------------------|--------|
| Control Method | Natural language | Click buttons |
| Photo Viewing | Inline in chat | Side-by-side comparison |
| Automation | Easy (just describe) | Manual steps |
| Precision | Exact (specify cm/degrees) | Preset movements |
| Camera Source | Tello only | Tello OR Webcam |
| Best For | Flying missions, exploration | Testing, development, comparison |

**Recommendation:** Use both!
- **MCP Server** - For actual drone flights and photo missions
- **Web UI** - For testing, development, and side-by-side photo comparison

## Getting Help

If you see errors in Claude Desktop when using MCP tools:
1. Check the MCP logs (see above)
2. Verify Tello WiFi connection
3. Test the server manually: `python3 mcp_server.py`
4. Check that all dependencies are installed

## Summary

1. ✅ Add MCP server to Claude Desktop config
2. ✅ Restart Claude Desktop
3. ✅ Connect to Tello WiFi
4. ✅ Tell Claude: "Connect to my Tello drone"
5. ✅ Start flying with natural language!

Enjoy controlling your Tello drone with AI! 🚁✨
