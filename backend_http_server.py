#!/usr/bin/env python3
"""
Tello Backend HTTP API Server - Runs in Kubernetes

This Flask server runs in K8s and provides REST API endpoints that communicate
with the Tello Proxy Service on the Mac.

Architecture:
    Frontend (K8s) → This Server (K8s) → Tello Proxy (Mac) → Tello Drone

Usage:
    python3 backend_http_server.py

Accessible at:
    http://localhost:3001/api/*
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from tello_proxy_adapter import create_tello

app = Flask(__name__)
CORS(app)

# Global Tello instance (will be TelloProxyAdapter)
tello = None
connected = False

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get server and drone status"""
    global tello, connected

    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')

    if not connected or tello is None:
        return jsonify({
            'success': True,
            'connected': False,
            'proxy_url': proxy_url,
            'message': 'Not connected to Tello'
        })

    try:
        battery = tello.get_battery()
        temp = tello.get_temperature()
        height = tello.get_height()
        flight_time = tello.get_flight_time()

        return jsonify({
            'success': True,
            'connected': True,
            'proxy_url': proxy_url,
            'battery': battery,
            'temperature': temp,
            'height': height,
            'flight_time': flight_time
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to Tello via proxy"""
    global tello, connected

    if connected and tello is not None:
        return jsonify({
            'success': True,
            'message': 'Already connected',
            'battery': tello.get_battery()
        })

    try:
        print("Connecting to Tello via proxy...")
        tello = create_tello()
        tello.connect()
        connected = True

        battery = tello.get_battery()
        print(f"✅ Connected! Battery: {battery}%")

        return jsonify({
            'success': True,
            'message': 'Connected to Tello via proxy',
            'battery': battery
        })
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from Tello"""
    global tello, connected

    tello = None
    connected = False

    return jsonify({
        'success': True,
        'message': 'Disconnected'
    })

@app.route('/api/battery', methods=['GET'])
def get_battery():
    """Get battery level"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({
            'success': False,
            'error': 'Not connected'
        }), 400

    try:
        battery = tello.get_battery()
        return jsonify({
            'success': True,
            'battery': battery
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/command', methods=['POST'])
def send_command():
    """Send a command to Tello"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({
            'success': False,
            'error': 'Not connected'
        }), 400

    data = request.get_json() or {}
    command = data.get('command', '').strip()

    if not command:
        return jsonify({
            'success': False,
            'error': 'Missing command'
        }), 400

    try:
        response = tello.send_control_command(command)
        return jsonify({
            'success': True,
            'command': command,
            'response': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'command': command,
            'error': str(e)
        }), 500

@app.route('/api/takeoff', methods=['POST'])
def takeoff():
    """Take off"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    try:
        tello.takeoff()
        return jsonify({'success': True, 'message': 'Taking off'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/land', methods=['POST'])
def land():
    """Land"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    try:
        tello.land()
        return jsonify({'success': True, 'message': 'Landing'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/move', methods=['POST'])
def move():
    """Move in a direction"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    data = request.get_json() or {}
    direction = data.get('direction', '').lower()
    distance = int(data.get('distance', 30))

    if distance < 20 or distance > 500:
        return jsonify({'success': False, 'error': 'Distance must be 20-500 cm'}), 400

    try:
        if direction == "forward":
            tello.move_forward(distance)
        elif direction == "back":
            tello.move_back(distance)
        elif direction == "left":
            tello.move_left(distance)
        elif direction == "right":
            tello.move_right(distance)
        elif direction == "up":
            tello.move_up(distance)
        elif direction == "down":
            tello.move_down(distance)
        else:
            return jsonify({'success': False, 'error': f'Invalid direction: {direction}'}), 400

        return jsonify({'success': True, 'message': f'Moved {direction} {distance} cm'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rotate', methods=['POST'])
def rotate():
    """Rotate"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    data = request.get_json() or {}
    direction = data.get('direction', '').lower()
    angle = int(data.get('angle', 90))

    if angle < 1 or angle > 360:
        return jsonify({'success': False, 'error': 'Angle must be 1-360 degrees'}), 400

    try:
        if direction in ['cw', 'clockwise']:
            tello.rotate_clockwise(angle)
        elif direction in ['ccw', 'counterclockwise']:
            tello.rotate_counter_clockwise(angle)
        else:
            return jsonify({'success': False, 'error': f'Invalid direction: {direction}'}), 400

        return jsonify({'success': True, 'message': f'Rotated {direction} {angle}°'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/flip', methods=['POST'])
def flip():
    """Flip"""
    global tello, connected

    if not connected or tello is None:
        return jsonify({'success': False, 'error': 'Not connected'}), 400

    data = request.get_json() or {}
    direction = data.get('direction', '').lower()

    try:
        if direction in ['f', 'forward']:
            tello.flip_forward()
        elif direction in ['b', 'back']:
            tello.flip_back()
        elif direction in ['l', 'left']:
            tello.flip_left()
        elif direction in ['r', 'right']:
            tello.flip_right()
        else:
            return jsonify({'success': False, 'error': f'Invalid direction: {direction}'}), 400

        return jsonify({'success': True, 'message': f'Flipped {direction}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start_stream', methods=['POST'])
def start_stream():
    """Start video stream (via proxy)"""
    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')

    try:
        import requests
        response = requests.post(f'{proxy_url}/tello/start_stream', timeout=10)
        data = response.json()

        if data.get('success'):
            # Return proxy video URL
            return jsonify({
                'success': True,
                'message': 'Video stream started',
                'video_url': f'{proxy_url}/tello/video_feed'
            })
        else:
            return jsonify({
                'success': False,
                'error': data.get('error', 'Unknown error')
            }), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop_stream', methods=['POST'])
def stop_stream():
    """Stop video stream (via proxy)"""
    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')

    try:
        import requests
        response = requests.post(f'{proxy_url}/tello/stop_stream', timeout=10)
        data = response.json()

        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/video_feed')
def video_feed_proxy():
    """Proxy video feed from Mac proxy"""
    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')

    import requests
    from flask import Response

    def generate():
        try:
            response = requests.get(f'{proxy_url}/tello/video_feed', stream=True, timeout=30)
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        except Exception as e:
            print(f"Video feed error: {e}")

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/capture_photo', methods=['POST'])
def capture_photo():
    """Capture photo (via proxy)"""
    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')

    try:
        import requests
        response = requests.post(f'{proxy_url}/tello/capture_photo', timeout=10)
        data = response.json()

        return jsonify(data)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    proxy_url = os.getenv('TELLO_PROXY_URL', 'http://host.docker.internal:50000')
    http_port = int(os.getenv('HTTP_PORT', '3001'))

    print("=" * 60)
    print("🚀 Tello Backend HTTP Server Starting...")
    print("=" * 60)
    print(f"📡 Proxy URL: {proxy_url}")
    print(f"🌐 HTTP API: http://0.0.0.0:{http_port}/api/*")
    print("")
    print("Architecture:")
    print("  Frontend (K8s) → This Server (K8s) → Proxy (Mac) → Tello")
    print("")
    print("Available API Endpoints:")
    print("  GET  /api/status")
    print("  POST /api/connect")
    print("  POST /api/disconnect")
    print("  GET  /api/battery")
    print("  POST /api/command")
    print("  POST /api/takeoff")
    print("  POST /api/land")
    print("  POST /api/move")
    print("  POST /api/rotate")
    print("  POST /api/flip")
    print("  POST /api/start_stream       ← Start video")
    print("  POST /api/stop_stream        ← Stop video")
    print("  GET  /api/video_feed         ← Video stream (MJPEG)")
    print("  POST /api/capture_photo      ← Take photo")
    print("=" * 60)

    app.run(host='0.0.0.0', port=http_port, debug=False)
