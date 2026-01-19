from flask import Flask, jsonify, send_file, request, Response
from flask_cors import CORS
from flask_sock import Sock
import cv2
import numpy as np
import base64
import threading
import time
import os
from djitellopy import Tello

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# Global variables
tello = None
connected = False
streaming = False
frame_read = None
stop_stream = False
camera_source = None  # 'tello' or 'webcam'
webcam = None  # OpenCV VideoCapture object for webcam
latest_frame = None  # Shared frame cache to avoid multiple webcam reads
frame_lock = threading.Lock()  # Thread lock for frame access

# Directories
PHOTOS_DIR = 'photos'
VIDEOS_DIR = 'videos'

# Create directories if they don't exist
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

# WebSocket clients
ws_clients = []

def video_stream_worker():
    """Background thread that reads frames and sends to WebSocket clients"""
    global frame_read, streaming, stop_stream, camera_source, webcam, latest_frame, frame_lock

    print(f"Video stream worker started (source: {camera_source})")
    frame_count = 0
    error_count = 0
    last_log_time = time.time()

    while streaming and not stop_stream:
        try:
            frame = None

            # Get frame from appropriate source
            if camera_source == 'webcam' and webcam is not None:
                ret, frame = webcam.read()
                if not ret:
                    frame = None
                else:
                    # Cache the frame for other consumers (MJPEG, photo capture)
                    with frame_lock:
                        latest_frame = frame.copy() if frame is not None else None
            elif camera_source == 'tello' and frame_read is not None and not frame_read.stopped:
                frame = frame_read.frame
                # Cache Tello frames too for consistency
                with frame_lock:
                    latest_frame = frame.copy() if frame is not None else None

            if frame is not None and len(ws_clients) > 0:
                # NO sharpening - raw frames for best quality
                # Encode frame with high quality JPEG
                encode_param = [
                    cv2.IMWRITE_JPEG_QUALITY, 95,
                    cv2.IMWRITE_JPEG_OPTIMIZE, 1
                ]
                _, buffer = cv2.imencode('.jpg', frame, encode_param)
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')

                frame_count += 1

                # Log every 3 seconds instead of every 30 frames
                current_time = time.time()
                if current_time - last_log_time >= 3.0:
                    fps = frame_count / (current_time - last_log_time + 0.001)
                    print(f"Streaming: {frame_count} frames, FPS: {fps:.1f}, Clients: {len(ws_clients)}")
                    last_log_time = current_time
                    frame_count = 0

                # Send to all connected WebSocket clients
                disconnected_clients = []
                for client in ws_clients:
                    try:
                        if client.connected:
                            client.send(jpg_as_text)
                    except Exception as e:
                        print(f"Error sending to client: {e}")
                        disconnected_clients.append(client)

                # Remove disconnected clients
                for client in disconnected_clients:
                    if client in ws_clients:
                        ws_clients.remove(client)

                error_count = 0
            elif frame is None:
                error_count += 1
                if error_count % 30 == 0:
                    print(f"Warning: No frame available (count: {error_count})")

            # Smaller delay for smoother video (targeting ~30 FPS)
            time.sleep(0.033)
        except Exception as e:
            print(f"Error in video stream worker: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)
    
    print(f"Video stream worker stopped")

@app.route('/api/connect', methods=['POST'])
def connect():
    global tello, connected, camera_source, webcam

    try:
        data = request.json or {}
        source = data.get('source', 'tello')  # 'tello' or 'webcam'

        if connected:
            return jsonify({'success': True, 'message': f'Already connected to {camera_source}'})

        if source == 'webcam':
            print("Connecting to webcam...")
            # Try to open default webcam (0)
            webcam = cv2.VideoCapture(0)

            if not webcam.isOpened():
                return jsonify({'success': False, 'error': 'Could not open webcam. Make sure your camera is not in use by another application.'})

            # Set webcam properties for better quality
            webcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            webcam.set(cv2.CAP_PROP_FPS, 30)

            connected = True
            camera_source = 'webcam'
            print("Connected to webcam!")
            return jsonify({'success': True, 'source': 'webcam'})

        else:  # tello
            print("Connecting to Tello EDU...")
            tello = Tello()
            tello.connect()

            # TELLO EDU: Set high resolution immediately after connecting
            try:
                print("Setting Tello EDU to high resolution mode...")
                response = tello.send_control_command("setresolution high")
                print(f"  Resolution command response: {response}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Could not set resolution: {e}")

            connected = True
            camera_source = 'tello'
            battery = tello.get_battery()
            print(f"Connected! Battery: {battery}%")
            return jsonify({'success': True, 'source': 'tello', 'battery': battery})

    except Exception as e:
        print(f"Connection error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    global tello, connected, camera_source, webcam

    if not connected:
        return jsonify({
            'success': True,
            'source': None,
            'status': {
                'battery': 'N/A',
                'wifi': 'N/A',
                'temperature': 'N/A',
                'height': 'N/A',
                'tof': 'N/A'
            }
        })

    if camera_source == 'webcam':
        return jsonify({
            'success': True,
            'source': 'webcam',
            'status': {
                'battery': 'N/A',
                'wifi': 'Webcam',
                'temperature': 'N/A',
                'height': 'N/A',
                'tof': 'N/A'
            }
        })

    # Tello status
    try:
        battery = tello.get_battery()
        temp = tello.get_temperature()
        height = tello.get_height()

        return jsonify({
            'success': True,
            'source': 'tello',
            'status': {
                'battery': str(battery),
                'wifi': 'Connected',
                'temperature': str(temp),
                'height': str(height),
                'tof': 'N/A'
            }
        })
    except Exception as e:
        print(f"Status error: {e}")
        return jsonify({
            'success': True,
            'source': 'tello',
            'status': {
                'battery': 'N/A',
                'wifi': 'N/A',
                'temperature': 'N/A',
                'height': 'N/A',
                'tof': 'N/A'
            }
        })

@app.route('/api/start-stream', methods=['POST'])
def start_stream():
    global tello, streaming, frame_read, stop_stream, camera_source, webcam

    try:
        if not connected:
            return jsonify({'success': False, 'error': 'Not connected. Please connect to a camera source first.'})
        
        if streaming:
            return jsonify({'success': True, 'message': 'Stream already running'})

        print(f"Starting video stream (source: {camera_source})...")

        if camera_source == 'webcam':
            # Webcam is already opened, just start streaming
            print(f"[start-stream] Webcam object: {webcam}")
            print(f"[start-stream] Webcam opened: {webcam.isOpened() if webcam else 'N/A'}")

            if webcam is None or not webcam.isOpened():
                print("[start-stream] ERROR: Webcam not available")
                return jsonify({'success': False, 'error': 'Webcam not available'})

            # Test read from webcam
            print("[start-stream] Testing webcam frame capture...")
            ret, test_frame = webcam.read()
            print(f"[start-stream] Read result: ret={ret}, frame={test_frame is not None if test_frame is not None else 'None'}")

            if not ret or test_frame is None:
                print("[start-stream] ERROR: Could not read from webcam")
                return jsonify({'success': False, 'error': 'Could not read from webcam'})

            print(f"[start-stream] ✅ SUCCESS: Webcam active, resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")

            # Initialize the cached frame
            with frame_lock:
                latest_frame = test_frame.copy()

            streaming = True
            stop_stream = False

            # Start background thread
            print("[start-stream] Starting background worker thread...")
            thread = threading.Thread(target=video_stream_worker, daemon=True)
            thread.start()
            print(f"[start-stream] ✅ Webcam stream started successfully (thread alive: {thread.is_alive()})")

            return jsonify({'success': True, 'source': 'webcam'})

        else:  # tello
            print("=== Configuring video quality settings ===")

            # Set bitrate to maximum for best quality
            try:
                tello.set_video_bitrate(tello.BITRATE_5MBPS)
                print("✓ Video bitrate: 5Mbps")
                time.sleep(0.2)
            except Exception as e:
                print(f"Could not set bitrate: {e}")

            # Set FPS
            try:
                tello.set_video_fps(tello.FPS_30)
                print("✓ Video FPS: 30")
                time.sleep(0.2)
            except Exception as e:
                print(f"Could not set FPS: {e}")

            # Start video stream
            print("\nStarting video stream...")
            tello.streamon()
            time.sleep(3)  # Wait for stream to initialize

            print("Getting frame reader...")
            frame_read = tello.get_frame_read()

            # Wait and check resolution
            time.sleep(0.5)
            test_frame = frame_read.frame
            if test_frame is None:
                print("ERROR: No frames from Tello!")
                return jsonify({'success': False, 'error': 'No video frames from drone'})
            else:
                print(f"SUCCESS: Got test frame, shape: {test_frame.shape}")
                print(f"Frame dimensions: Width={test_frame.shape[1]}, Height={test_frame.shape[0]}")
                print(f"Frame size in bytes: {test_frame.nbytes}")

                # Check if we got high resolution
                if test_frame.shape[1] == 1280:
                    print("✓ HIGH RESOLUTION MODE ACTIVE (1280×720)")
                elif test_frame.shape[1] == 960:
                    print("⚠ Resolution: 960×720)")
                    print("  Note: Tello EDU firmware may not support 1280×720 via djitellopy")
        
        streaming = True
        stop_stream = False
        
        # Start background thread to process frames
        thread = threading.Thread(target=video_stream_worker, daemon=True)
        thread.start()
        print(f"Video stream thread started (thread alive: {thread.is_alive()})")
        
        print("Video stream started successfully")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Start stream error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stop-stream', methods=['POST'])
def stop_stream_endpoint():
    global tello, streaming, frame_read, stop_stream, camera_source, webcam

    try:
        print("Stopping video stream...")
        stop_stream = True
        streaming = False

        if camera_source == 'tello' and tello is not None:
            tello.streamoff()

        if frame_read is not None:
            frame_read.stop()
            frame_read = None

        time.sleep(0.5)  # Wait for worker to stop

        print("Video stream stopped")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Stop stream error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    global tello, connected, streaming, frame_read, stop_stream, camera_source, webcam, latest_frame, frame_lock

    try:
        print(f"Disconnecting from {camera_source}...")

        # Stop streaming first if active
        if streaming:
            stop_stream = True
            streaming = False
            time.sleep(0.5)

        # Clean up based on source
        if camera_source == 'tello':
            if tello is not None:
                try:
                    tello.streamoff()
                except:
                    pass
                try:
                    tello.end()
                except:
                    pass
            if frame_read is not None:
                try:
                    frame_read.stop()
                except:
                    pass
                frame_read = None
            tello = None

        elif camera_source == 'webcam':
            if webcam is not None:
                webcam.release()
                webcam = None

        # Clear WebSocket clients
        ws_clients.clear()

        # Clear cached frame
        with frame_lock:
            latest_frame = None

        # Reset state
        connected = False
        camera_source = None

        print("Disconnected successfully")
        return jsonify({'success': True})

    except Exception as e:
        print(f"Disconnect error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# Flight Control Endpoints (Tello only)
@app.route('/api/takeoff', methods=['POST'])
def takeoff():
    global tello, connected, camera_source

    try:
        if not connected or camera_source != 'tello':
            return jsonify({'success': False, 'error': 'Tello drone not connected'})

        print("Taking off...")
        tello.takeoff()
        print("✓ Takeoff complete")
        return jsonify({'success': True, 'message': 'Drone has taken off'})

    except Exception as e:
        print(f"Takeoff error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/land', methods=['POST'])
def land():
    global tello, connected, camera_source

    try:
        if not connected or camera_source != 'tello':
            return jsonify({'success': False, 'error': 'Tello drone not connected'})

        print("Landing...")
        tello.land()
        print("✓ Landing complete")
        return jsonify({'success': True, 'message': 'Drone has landed'})

    except Exception as e:
        print(f"Landing error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/move', methods=['POST'])
def move():
    global tello, connected, camera_source

    try:
        if not connected or camera_source != 'tello':
            return jsonify({'success': False, 'error': 'Tello drone not connected'})

        data = request.json
        direction = data.get('direction')  # 'up', 'down', 'left', 'right', 'forward', 'back'
        distance = data.get('distance', 30)  # Default 30cm

        # Validate distance (20-500 cm)
        if distance < 20 or distance > 500:
            return jsonify({'success': False, 'error': 'Distance must be between 20-500 cm'})

        print(f"Moving {direction} {distance}cm...")

        if direction == 'up':
            tello.move_up(distance)
        elif direction == 'down':
            tello.move_down(distance)
        elif direction == 'left':
            tello.move_left(distance)
        elif direction == 'right':
            tello.move_right(distance)
        elif direction == 'forward':
            tello.move_forward(distance)
        elif direction == 'back':
            tello.move_back(distance)
        else:
            return jsonify({'success': False, 'error': f'Invalid direction: {direction}'})

        print(f"✓ Moved {direction} {distance}cm")
        return jsonify({'success': True, 'message': f'Moved {direction} {distance}cm'})

    except Exception as e:
        print(f"Move error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rotate', methods=['POST'])
def rotate():
    global tello, connected, camera_source

    try:
        if not connected or camera_source != 'tello':
            return jsonify({'success': False, 'error': 'Tello drone not connected'})

        data = request.json
        direction = data.get('direction')  # 'left' or 'right'
        angle = data.get('angle', 45)  # Default 45 degrees

        # Validate angle (1-360 degrees)
        if angle < 1 or angle > 360:
            return jsonify({'success': False, 'error': 'Angle must be between 1-360 degrees'})

        print(f"Rotating {direction} {angle}°...")

        if direction == 'left':
            tello.rotate_counter_clockwise(angle)
        elif direction == 'right':
            tello.rotate_clockwise(angle)
        else:
            return jsonify({'success': False, 'error': f'Invalid direction: {direction}'})

        print(f"✓ Rotated {direction} {angle}°")
        return jsonify({'success': True, 'message': f'Rotated {direction} {angle}°'})

    except Exception as e:
        print(f"Rotate error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/capture', methods=['POST'])
def capture_photo():
    global tello, frame_read, camera_source, webcam, latest_frame, frame_lock

    try:
        data = request.json
        filename = data.get('filename', 'photo.jpg')
        filepath = os.path.join(PHOTOS_DIR, filename)

        if not connected:
            return jsonify({'success': False, 'error': 'Not connected to camera source'})

        print(f"Capturing photo from {camera_source}: {filename}")

        # Get multiple frames and pick the sharpest one
        best_frame = None
        best_score = 0

        for i in range(5):  # Capture 5 frames
            frame = None

            # Use cached frame to avoid multiple reads from webcam
            with frame_lock:
                if latest_frame is not None:
                    frame = latest_frame.copy()

            if frame is not None:
                # Calculate sharpness score using Laplacian variance
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

                if laplacian_var > best_score:
                    best_score = laplacian_var
                    best_frame = frame.copy()

            time.sleep(0.033)  # Wait for next frame

        if best_frame is None:
            return jsonify({'success': False, 'error': 'No frame available'})

        print(f"Best frame sharpness score: {best_score:.2f}")

        # Save with maximum quality JPEG
        cv2.imwrite(filepath, best_frame, [
            cv2.IMWRITE_JPEG_QUALITY, 100,
            cv2.IMWRITE_JPEG_OPTIMIZE, 1,
            cv2.IMWRITE_JPEG_PROGRESSIVE, 0
        ])

        # Log file info
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath) / 1024
            print(f"✓ Photo saved: {filepath}")
            print(f"  Size: {file_size:.1f} KB, Dimensions: {best_frame.shape[1]}×{best_frame.shape[0]}")

        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        print(f"Capture error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/photo/<filename>', methods=['GET'])
def get_photo(filename):
    try:
        filepath = os.path.join(PHOTOS_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Photo not found'}), 404
    except Exception as e:
        print(f"Get photo error: {e}")
        return jsonify({'error': str(e)}), 500

def generate_mjpeg():
    """Generator function for MJPEG stream"""
    global frame_read, streaming, camera_source, webcam, latest_frame, frame_lock

    print(f"[MJPEG] Stream client connected (source: {camera_source})")
    frame_count = 0
    empty_frame_count = 0

    try:
        while streaming:
            frame = None

            # Use cached frame instead of reading directly from webcam
            # This prevents segmentation fault from multiple simultaneous reads
            with frame_lock:
                if latest_frame is not None:
                    frame = latest_frame.copy()
                else:
                    empty_frame_count += 1
                    if empty_frame_count % 30 == 1:  # Log every 30 empty frames
                        print(f"[MJPEG] WARNING: latest_frame is None (count: {empty_frame_count})")

            if frame is not None:
                # Encode to JPEG with higher quality, no processing
                _, buffer = cv2.imencode('.jpg', frame, [
                    cv2.IMWRITE_JPEG_QUALITY, 95
                ])

                frame_bytes = buffer.tobytes()
                frame_count += 1

                if frame_count % 100 == 0:
                    print(f"MJPEG: Streamed {frame_count} frames")

                # Yield frame in multipart format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n'
                       b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                       frame_bytes + b'\r\n')

                time.sleep(0.033)  # ~30 FPS
            else:
                time.sleep(0.01)

    except GeneratorExit:
        print("MJPEG stream client disconnected (normal)")
    except Exception as e:
        print(f"MJPEG stream error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"MJPEG stream ended. Total frames sent: {frame_count}")

@app.route('/api/video-feed')
def video_feed():
    """MJPEG video feed endpoint for HTML5 video tag"""
    print(f"[video-feed] Request received - streaming: {streaming}, source: {camera_source}")

    if not streaming:
        print("[video-feed] ERROR: Stream not active")
        return jsonify({'error': 'Stream not active'}), 400

    # Check if we have a valid source
    if camera_source == 'webcam':
        if webcam is None:
            print("[video-feed] ERROR: Webcam object is None")
            return jsonify({'error': 'Webcam not initialized'}), 400
        if not webcam.isOpened():
            print("[video-feed] ERROR: Webcam is not opened")
            return jsonify({'error': 'Webcam not available'}), 400
        print("[video-feed] ✅ Webcam is ready, starting MJPEG stream")
    elif camera_source == 'tello':
        if frame_read is None:
            print("[video-feed] ERROR: Tello frame_read is None")
            return jsonify({'error': 'Tello stream not active'}), 400
        print("[video-feed] ✅ Tello is ready, starting MJPEG stream")
    else:
        print(f"[video-feed] ERROR: Unknown camera source: {camera_source}")
        return jsonify({'error': 'Unknown camera source'}), 400

    response = Response(generate_mjpeg(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@sock.route('/video')
def video_socket(ws):
    """WebSocket endpoint for video streaming"""
    print("WebSocket client connected")
    ws_clients.append(ws)
    
    try:
        # Keep connection alive - don't call receive() with timeout
        while True:
            # Just wait for client to send something (or disconnect)
            message = ws.receive()
            if message is None:
                break
            # Echo back to confirm connection (optional)
            # ws.send('pong')
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)
        print("WebSocket client disconnected")

if __name__ == '__main__':
    print("Tello Python Backend Server")
    print("Make sure you are connected to the Tello WiFi network")
    print("Starting server on http://localhost:3001")
    app.run(host='0.0.0.0', port=3001, debug=False, threaded=True)