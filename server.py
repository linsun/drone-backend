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
    global frame_read, streaming, stop_stream

    print("Video stream worker started")
    frame_count = 0
    error_count = 0
    last_log_time = time.time()

    while streaming and not stop_stream:
        try:
            if frame_read is not None and frame_read.stopped is False:
                frame = frame_read.frame

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
            else:
                if frame_read is None:
                    print("Warning: frame_read is None")
                elif frame_read.stopped:
                    print("Warning: frame_read is stopped")
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in video stream worker: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(0.1)
    
    print(f"Video stream worker stopped")

@app.route('/api/connect', methods=['POST'])
def connect():
    global tello, connected

    try:
        if not connected:
            print("Connecting to Tello EDU...")
            tello = Tello()
            tello.connect()

            # TELLO EDU: Set high resolution immediately after connecting
            # This needs to be done BEFORE starting the video stream
            try:
                print("Setting Tello EDU to high resolution mode...")
                response = tello.send_control_command("setresolution high")
                print(f"  Resolution command response: {response}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Could not set resolution: {e}")

            connected = True
            battery = tello.get_battery()
            print(f"Connected! Battery: {battery}%")
            return jsonify({'success': True})
        else:
            return jsonify({'success': True, 'message': 'Already connected'})
    except Exception as e:
        print(f"Connection error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def get_status():
    global tello, connected
    
    if not connected or tello is None:
        return jsonify({
            'success': True,
            'status': {
                'battery': 'N/A',
                'wifi': 'N/A',
                'temperature': 'N/A',
                'height': 'N/A',
                'tof': 'N/A'
            }
        })
    
    try:
        battery = tello.get_battery()
        temp = tello.get_temperature()
        height = tello.get_height()
        
        return jsonify({
            'success': True,
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
    global tello, streaming, frame_read, stop_stream
    
    try:
        if not connected or tello is None:
            return jsonify({'success': False, 'error': 'Not connected to Tello'})
        
        if streaming:
            return jsonify({'success': True, 'message': 'Stream already running'})
        
        print("Starting video stream...")
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
                print("⚠ Resolution: 960×720")
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
    global tello, streaming, frame_read, stop_stream
    
    try:
        print("Stopping video stream...")
        stop_stream = True
        streaming = False
        
        if tello is not None:
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

@app.route('/api/capture', methods=['POST'])
def capture_photo():
    global tello, frame_read

    try:
        data = request.json
        filename = data.get('filename', 'photo.jpg')
        filepath = os.path.join(PHOTOS_DIR, filename)

        if not connected or tello is None:
            return jsonify({'success': False, 'error': 'Not connected to Tello'})

        print(f"Capturing photo (Tello EDU optimized): {filename}")

        # Note: The take_picture() SDK command for 5MP photos is not supported
        # in standard djitellopy. We're using optimized video frame capture instead.

        # Fallback: If high-res photo fails, grab from video stream
        if frame_read is None:
            return jsonify({'success': False, 'error': 'Video stream not active and high-res photo failed'})

        print(f"Capturing from video stream (fallback): {filename}")

        # Get multiple frames and pick the sharpest one
        best_frame = None
        best_score = 0

        for i in range(5):  # Capture 5 frames
            frame = frame_read.frame
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
    global frame_read, streaming

    print("MJPEG stream client connected")
    frame_count = 0

    try:
        while streaming and frame_read is not None and not frame_read.stopped:
            frame = frame_read.frame

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
    if not streaming or frame_read is None:
        return jsonify({'error': 'Stream not active'}), 400

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