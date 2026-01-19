#!/usr/bin/env python3
"""
Test script to verify MJPEG streaming works with webcam
This simulates what the frontend does
"""

import requests
import time
import cv2
import numpy as np

SERVER_URL = "http://localhost:3001"

print("=" * 60)
print("MJPEG Webcam Stream Test")
print("=" * 60)

# Step 1: Connect to webcam
print("\n1. Connecting to webcam...")
try:
    response = requests.post(f"{SERVER_URL}/api/connect",
                            json={"source": "webcam"})
    data = response.json()
    if data['success']:
        print("   ✅ Connected to webcam")
    else:
        print(f"   ❌ Failed to connect: {data.get('error')}")
        exit(1)
except Exception as e:
    print(f"   ❌ Connection error: {e}")
    exit(1)

time.sleep(1)

# Step 2: Start stream
print("\n2. Starting video stream...")
try:
    response = requests.post(f"{SERVER_URL}/api/start-stream")
    data = response.json()
    if data['success']:
        print("   ✅ Stream started")
    else:
        print(f"   ❌ Failed to start stream: {data.get('error')}")
        exit(1)
except Exception as e:
    print(f"   ❌ Start stream error: {e}")
    exit(1)

time.sleep(2)  # Wait for stream to initialize

# Step 3: Test MJPEG endpoint
print("\n3. Testing MJPEG endpoint...")
print("   Fetching video feed URL...")

try:
    response = requests.get(f"{SERVER_URL}/api/video-feed",
                          stream=True, timeout=5)

    if response.status_code != 200:
        print(f"   ❌ HTTP {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)

    print(f"   ✅ HTTP 200 OK")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")

    # Try to read a few frames
    print("\n4. Reading frames from MJPEG stream...")
    frame_count = 0
    bytes_buffer = b''

    for chunk in response.iter_content(chunk_size=1024):
        bytes_buffer += chunk

        # Look for JPEG frame boundaries
        a = bytes_buffer.find(b'\xff\xd8')  # JPEG start
        b = bytes_buffer.find(b'\xff\xd9')  # JPEG end

        if a != -1 and b != -1:
            jpg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:]

            # Decode JPEG
            try:
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMWRITE_JPEG_QUALITY)
                if frame is not None:
                    frame_count += 1
                    print(f"   Frame {frame_count}: ✅ {frame.shape} - {len(jpg)} bytes")
                else:
                    print(f"   Frame {frame_count}: ❌ Failed to decode")
            except Exception as e:
                print(f"   Frame decode error: {e}")

            if frame_count >= 5:
                print(f"\n✅ SUCCESS: Received {frame_count} valid frames!")
                break

    if frame_count == 0:
        print("\n   ❌ No frames received from stream")

except requests.exceptions.Timeout:
    print("   ❌ Request timed out - stream may not be sending data")
except Exception as e:
    print(f"   ❌ Stream error: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Stop stream
print("\n5. Stopping stream...")
try:
    response = requests.post(f"{SERVER_URL}/api/stop-stream")
    data = response.json()
    if data['success']:
        print("   ✅ Stream stopped")
    else:
        print(f"   ⚠️ Failed to stop: {data.get('error')}")
except Exception as e:
    print(f"   ⚠️ Stop error: {e}")

# Step 5: Disconnect
print("\n6. Disconnecting...")
try:
    response = requests.post(f"{SERVER_URL}/api/disconnect")
    data = response.json()
    if data['success']:
        print("   ✅ Disconnected")
    else:
        print(f"   ⚠️ Failed to disconnect: {data.get('error')}")
except Exception as e:
    print(f"   ⚠️ Disconnect error: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
