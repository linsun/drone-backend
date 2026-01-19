# Tello Drone MCP Server

This MCP server allows you to control your Tello drone using natural language through Claude or other AI assistants that support the Model Context Protocol.

## Features

The MCP server provides tools for:

### 🚁 Flight Control
- **takeoff** - Take off and hover
- **land** - Land safely
- **emergency_stop** - Emergency motor stop
- **move_up/down/forward/back/left/right** - Precise movement (20-500 cm)
- **rotate_clockwise/counterclockwise** - Turn the drone (1-360°)
- **flip** - Perform flips in any direction
- **set_speed** - Adjust flight speed (10-100 cm/s)

### 📷 Camera Control
- **start_video_stream** - Start camera streaming
- **stop_video_stream** - Stop streaming to save battery
- **capture_photo** - Capture high-quality photos (returns image to Claude)

### 📊 Status Monitoring
- **connect** - Connect to the Tello drone
- **get_status** - Check battery, temperature, height, etc.

## Installation

### 1. Install Python Dependencies

```bash
cd tello-backend

# Make sure venv is activated
source venv/bin/activate

# Install MCP SDK
pip install mcp
```

### 2. Configure Claude Desktop (or other MCP client)

#### For Claude Desktop:

1. Open your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the Tello MCP server configuration:

```json
{
  "mcpServers": {
    "tello-drone": {
      "command": "/Users/linsun/src/github.com/linsun/tello-backend/venv/bin/python3.12",
      "args": ["/Users/linsun/src/github.com/linsun/tello-backend/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/linsun/src/github.com/linsun/tello-backend/venv/lib/python3.12/site-packages"
      }
    }
  }
}
```

**Important**: Replace the paths with your actual paths!

3. Restart Claude Desktop

#### For Claude Code CLI:

Create or edit `~/.config/claude/config.json`:

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

## Usage

### Before Starting

1. **Connect to Tello WiFi**: Connect your computer to the Tello's WiFi network (TELLO-XXXXXX)
2. **Launch Claude**: Open Claude Desktop or start a Claude Code session

### Example Commands

You can now control your drone using natural language! Here are some examples:

#### Getting Started
```
"Connect to my Tello drone"
"What's the battery level?"
"Start the video stream"
```

#### Basic Flight
```
"Take off"
"Move up 50 cm"
"Rotate right 90 degrees"
"Take a photo"
"Land"
```

#### Advanced Flight Patterns
```
"Fly in a square pattern: go forward 100cm, turn right 90 degrees, repeat 4 times"
"Take off, go up 1 meter, rotate 360 degrees slowly, then land"
"Move to the left 50cm and take a photo"
```

#### Camera Operations
```
"Start the camera and take a photo"
"Rotate 45 degrees right and capture what you see"
"Take photos while rotating 360 degrees in 45 degree increments"
```

#### Safety
```
"What's my current height?"
"Emergency stop!"
"Land immediately"
```

## Safety Features

- ✅ **Connection Check**: All commands check if drone is connected
- ✅ **Range Limits**: Movement constrained to safe ranges (20-500 cm)
- ✅ **Emergency Stop**: Quick access to emergency motor stop
- ✅ **Status Monitoring**: Always check battery before extended flights
- ✅ **Error Handling**: Detailed error messages for troubleshooting

## Command Reference

### Flight Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `connect` | - | Connect to Tello |
| `get_status` | - | Get battery, temp, height |
| `takeoff` | - | Take off and hover |
| `land` | - | Land safely |
| `emergency_stop` | - | Stop all motors (EMERGENCY) |
| `move_up` | distance (20-500cm) | Move up |
| `move_down` | distance (20-500cm) | Move down |
| `move_forward` | distance (20-500cm) | Move forward |
| `move_back` | distance (20-500cm) | Move backward |
| `move_left` | distance (20-500cm) | Move left |
| `move_right` | distance (20-500cm) | Move right |
| `rotate_clockwise` | angle (1-360°) | Turn right |
| `rotate_counterclockwise` | angle (1-360°) | Turn left |
| `flip` | direction (left/right/forward/back) | Perform flip |
| `set_speed` | speed (10-100 cm/s) | Set flight speed |

### Camera Commands

| Command | Parameters | Description |
|---------|-----------|-------------|
| `start_video_stream` | - | Start camera |
| `stop_video_stream` | - | Stop camera |
| `capture_photo` | description (optional) | Capture photo |

## Troubleshooting

### "Not connected to Tello"
- Make sure you're connected to the Tello WiFi network
- Try running: `"Connect to the drone"`

### "Video stream not active"
- Start streaming first: `"Start the video stream"`
- Wait a few seconds after starting the stream

### Commands not working
- Check that Claude Desktop/Code is running
- Verify the paths in your config file are correct
- Make sure the venv is properly configured
- Check console logs for errors

### Drone not responding
- Check battery level: `"What's the battery?"`
- Try reconnecting: Disconnect from chat, reconnect to Tello WiFi, then `"Connect to the drone"`
- Use emergency stop if needed: `"Emergency stop"`

## Best Practices

1. **Always check battery** before flying: `"What's my battery level?"`
2. **Start with small movements** to test: `"Move up 20cm"`
3. **Keep line of sight** with the drone
4. **Fly in open space** away from obstacles
5. **Monitor status regularly** during flight
6. **Land when battery is low** (below 20%)
7. **Use lower speeds indoors**: `"Set speed to 20"`

## Advanced Usage

### Creating Flight Patterns

You can ask Claude to execute complex flight patterns:

```
"Execute this flight pattern:
1. Take off
2. Move forward 100cm
3. Rotate clockwise 90 degrees
4. Move forward 100cm
5. Rotate clockwise 90 degrees
6. Move forward 100cm
7. Rotate clockwise 90 degrees
8. Move forward 100cm
9. Land"
```

### Photo Missions

```
"Take aerial photos of the room:
1. Take off
2. Capture a photo
3. Rotate 90 degrees
4. Capture a photo
5. Repeat until you've rotated 360 degrees
6. Land"
```

### Automated Inspection

```
"Inspect the ceiling:
1. Take off
2. Move up to 150cm
3. Capture photos while rotating around 360 degrees
4. Move down and land"
```

## Development

### Testing the MCP Server

You can test the server directly:

```bash
# From tello-backend directory
source venv/bin/activate
python mcp_server.py
```

Type JSON-RPC messages to test (mainly for debugging).

### Adding New Commands

To add new drone commands:

1. Add a new Tool definition in `list_tools()`
2. Add the command handler in `call_tool()`
3. Use the djitellopy Tello API

See the [djitellopy documentation](https://djitellopy.readthedocs.io/) for available commands.

## Limitations

- **Single connection**: Only one client can control the drone at a time
- **WiFi range**: Tello has limited WiFi range (~100m outdoors, less indoors)
- **Battery life**: Typically 10-13 minutes of flight time
- **Speed**: Movement commands execute sequentially, not simultaneously
- **Video resolution**: Limited to 960×720 (or 1280×720 on some Tello EDU models)

## Safety Warnings

⚠️ **IMPORTANT SAFETY NOTES**:

1. Never fly near people or animals
2. Keep away from obstacles (walls, furniture, etc.)
3. Do not fly outdoors in wind or rain
4. Always maintain visual line of sight
5. Know your emergency stop command
6. Check propellers before each flight
7. Fly in open, well-lit areas
8. Keep battery above 20% for safe landing

## License

This MCP server uses the djitellopy library and follows its license terms.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review djitellopy documentation
- Check MCP protocol documentation

## Example Session

Here's a complete example session:

```
You: "Connect to my Tello drone"
Claude: [Calls connect tool]
✅ Connected successfully. Battery: 85%

You: "What's the status?"
Claude: [Calls get_status tool]
📊 Tello Status:
• Battery: 85%
• Temperature: 22°C
• Height: 0 cm
• Flight Time: 0s
• Streaming: No

You: "Start the video stream"
Claude: [Calls start_video_stream tool]
✅ Video stream started

You: "Take off and take a photo"
Claude: [Calls takeoff tool]
✅ Takeoff complete. Drone is hovering.
[Calls capture_photo tool]
📸 Photo captured (sharpness score: 125.3)
[Shows the captured image]

You: "Rotate 90 degrees right and take another photo"
Claude: [Calls rotate_clockwise with angle=90]
✅ Rotated clockwise 90°
[Calls capture_photo tool]
📸 Photo captured (sharpness score: 132.1)
[Shows the captured image]

You: "Land safely"
Claude: [Calls land tool]
✅ Landing complete. Drone is on the ground.
```

Enjoy flying! 🚁
