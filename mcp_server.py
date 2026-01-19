#!/usr/bin/env python3
"""
Tello Drone MCP Server

This MCP server allows AI assistants to control a Tello drone through natural language.
It provides tools for flight control, camera operations, and status monitoring.
"""

import asyncio
import json
from typing import Any, Optional
from djitellopy import Tello
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio
import base64
import cv2
import time

# Global Tello instance
tello: Optional[Tello] = None
connected = False
streaming = False
frame_read = None

# Create MCP server
app = Server("tello-drone")

def ensure_connected() -> tuple[bool, str]:
    """Ensure Tello is connected. Returns (success, message)"""
    global tello, connected

    if connected and tello is not None:
        return True, "Already connected"

    try:
        tello = Tello()
        tello.connect()

        # Set high resolution for Tello EDU
        try:
            tello.send_control_command("setresolution high")
            time.sleep(0.3)
        except:
            pass

        connected = True
        battery = tello.get_battery()
        return True, f"Connected successfully. Battery: {battery}%"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def ensure_streaming() -> tuple[bool, str]:
    """Ensure video stream is active. Returns (success, message)"""
    global tello, streaming, frame_read

    if not connected or tello is None:
        return False, "Not connected to Tello. Please connect first."

    if streaming and frame_read is not None:
        return True, "Already streaming"

    try:
        # Set video quality
        tello.set_video_bitrate(tello.BITRATE_5MBPS)
        tello.set_video_fps(tello.FPS_30)

        tello.streamon()
        time.sleep(2)

        frame_read = tello.get_frame_read()
        time.sleep(1)

        streaming = True
        return True, "Video stream started"
    except Exception as e:
        return False, f"Failed to start stream: {str(e)}"

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Tello drone control tools"""
    return [
        Tool(
            name="connect",
            description="Connect to the Tello drone. Must be called before any other commands.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="get_status",
            description="Get current drone status including battery, temperature, height, and flight time.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="takeoff",
            description="Take off and hover at a safe altitude. The drone will automatically rise to about 1 meter.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="land",
            description="Land the drone safely at its current position.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="emergency_stop",
            description="EMERGENCY: Immediately stop all motors. The drone will fall! Only use in emergencies.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="move_up",
            description="Move the drone up by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move up in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="move_down",
            description="Move the drone down by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move down in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="move_forward",
            description="Move the drone forward by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move forward in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="move_back",
            description="Move the drone backward by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move backward in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="move_left",
            description="Move the drone left by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move left in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="move_right",
            description="Move the drone right by a specified distance (20-500 cm).",
            inputSchema={
                "type": "object",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Distance to move right in centimeters (20-500)",
                        "minimum": 20,
                        "maximum": 500
                    }
                },
                "required": ["distance"]
            }
        ),
        Tool(
            name="rotate_clockwise",
            description="Rotate the drone clockwise (turn right) by a specified angle (1-360 degrees).",
            inputSchema={
                "type": "object",
                "properties": {
                    "angle": {
                        "type": "integer",
                        "description": "Angle to rotate in degrees (1-360)",
                        "minimum": 1,
                        "maximum": 360
                    }
                },
                "required": ["angle"]
            }
        ),
        Tool(
            name="rotate_counterclockwise",
            description="Rotate the drone counter-clockwise (turn left) by a specified angle (1-360 degrees).",
            inputSchema={
                "type": "object",
                "properties": {
                    "angle": {
                        "type": "integer",
                        "description": "Angle to rotate in degrees (1-360)",
                        "minimum": 1,
                        "maximum": 360
                    }
                },
                "required": ["angle"]
            }
        ),
        Tool(
            name="flip",
            description="Perform a flip in the specified direction (left, right, forward, back).",
            inputSchema={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Direction to flip",
                        "enum": ["left", "right", "forward", "back"]
                    }
                },
                "required": ["direction"]
            }
        ),
        Tool(
            name="start_video_stream",
            description="Start the video stream from the drone's camera. Required before capturing photos.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="stop_video_stream",
            description="Stop the video stream to save battery.",
            inputSchema={
                "type": "object",
                "properties": {},
            }
        ),
        Tool(
            name="capture_photo",
            description="Capture a photo from the drone's camera. Video stream must be active. Returns the photo as base64-encoded image.",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Optional description of what you want to capture"
                    }
                },
            }
        ),
        Tool(
            name="set_speed",
            description="Set the drone's flight speed (10-100 cm/s). Lower speeds are safer for indoor flight.",
            inputSchema={
                "type": "object",
                "properties": {
                    "speed": {
                        "type": "integer",
                        "description": "Speed in cm/s (10-100)",
                        "minimum": 10,
                        "maximum": 100
                    }
                },
                "required": ["speed"]
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for drone control"""
    global tello, connected, streaming, frame_read

    try:
        # Connection command
        if name == "connect":
            success, message = ensure_connected()
            return [TextContent(type="text", text=message)]

        # All other commands require connection
        if not connected or tello is None:
            return [TextContent(
                type="text",
                text="❌ Not connected to Tello. Please call 'connect' first."
            )]

        # Status command
        if name == "get_status":
            battery = tello.get_battery()
            temp = tello.get_temperature()
            height = tello.get_height()
            flight_time = tello.get_flight_time()

            status_text = f"""📊 Tello Status:
• Battery: {battery}%
• Temperature: {temp}°C
• Height: {height} cm
• Flight Time: {flight_time}s
• Streaming: {'Yes' if streaming else 'No'}"""

            return [TextContent(type="text", text=status_text)]

        # Flight control commands
        elif name == "takeoff":
            tello.takeoff()
            return [TextContent(type="text", text="✅ Takeoff complete. Drone is hovering.")]

        elif name == "land":
            tello.land()
            return [TextContent(type="text", text="✅ Landing complete. Drone is on the ground.")]

        elif name == "emergency_stop":
            tello.emergency()
            return [TextContent(type="text", text="🚨 EMERGENCY STOP activated. Motors stopped.")]

        # Movement commands
        elif name == "move_up":
            distance = arguments.get("distance", 30)
            tello.move_up(distance)
            return [TextContent(type="text", text=f"✅ Moved up {distance} cm")]

        elif name == "move_down":
            distance = arguments.get("distance", 30)
            tello.move_down(distance)
            return [TextContent(type="text", text=f"✅ Moved down {distance} cm")]

        elif name == "move_forward":
            distance = arguments.get("distance", 30)
            tello.move_forward(distance)
            return [TextContent(type="text", text=f"✅ Moved forward {distance} cm")]

        elif name == "move_back":
            distance = arguments.get("distance", 30)
            tello.move_back(distance)
            return [TextContent(type="text", text=f"✅ Moved back {distance} cm")]

        elif name == "move_left":
            distance = arguments.get("distance", 30)
            tello.move_left(distance)
            return [TextContent(type="text", text=f"✅ Moved left {distance} cm")]

        elif name == "move_right":
            distance = arguments.get("distance", 30)
            tello.move_right(distance)
            return [TextContent(type="text", text=f"✅ Moved right {distance} cm")]

        elif name == "rotate_clockwise":
            angle = arguments.get("angle", 90)
            tello.rotate_clockwise(angle)
            return [TextContent(type="text", text=f"✅ Rotated clockwise {angle}°")]

        elif name == "rotate_counterclockwise":
            angle = arguments.get("angle", 90)
            tello.rotate_counter_clockwise(angle)
            return [TextContent(type="text", text=f"✅ Rotated counter-clockwise {angle}°")]

        elif name == "flip":
            direction = arguments.get("direction", "forward")
            tello.flip(direction[0])  # Uses first letter: l, r, f, b
            return [TextContent(type="text", text=f"✅ Flipped {direction}")]

        elif name == "set_speed":
            speed = arguments.get("speed", 50)
            tello.set_speed(speed)
            return [TextContent(type="text", text=f"✅ Speed set to {speed} cm/s")]

        # Video commands
        elif name == "start_video_stream":
            success, message = ensure_streaming()
            return [TextContent(type="text", text=f"{'✅' if success else '❌'} {message}")]

        elif name == "stop_video_stream":
            if streaming:
                tello.streamoff()
                if frame_read:
                    frame_read.stop()
                    frame_read = None
                streaming = False
                return [TextContent(type="text", text="✅ Video stream stopped")]
            else:
                return [TextContent(type="text", text="Video stream is not active")]

        elif name == "capture_photo":
            if not streaming or frame_read is None:
                return [TextContent(
                    type="text",
                    text="❌ Video stream not active. Please call 'start_video_stream' first."
                )]

            # Capture multiple frames and pick the sharpest one
            best_frame = None
            best_score = 0

            for i in range(5):
                frame = frame_read.frame
                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

                    if laplacian_var > best_score:
                        best_score = laplacian_var
                        best_frame = frame.copy()

                time.sleep(0.033)

            if best_frame is None:
                return [TextContent(type="text", text="❌ No frames available")]

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', best_frame, [
                cv2.IMWRITE_JPEG_QUALITY, 95
            ])

            # Convert to base64
            image_base64 = base64.b64encode(buffer).decode('utf-8')

            description = arguments.get("description", "Photo from Tello drone")

            return [
                TextContent(
                    type="text",
                    text=f"📸 Photo captured (sharpness score: {best_score:.1f})"
                ),
                ImageContent(
                    type="image",
                    data=image_base64,
                    mimeType="image/jpeg"
                )
            ]

        else:
            return [TextContent(type="text", text=f"❌ Unknown command: {name}")]

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return [TextContent(
            type="text",
            text=f"❌ Error executing {name}: {str(e)}\n\nDetails:\n{error_details}"
        )]

async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    print("Starting Tello Drone MCP Server...", flush=True)
    asyncio.run(main())
