#!/usr/bin/env python3
"""
Simple test script to verify connect/disconnect functionality
"""
import requests
import time

SERVER_URL = 'http://localhost:3001'

def test_webcam():
    print("=== Testing Webcam Connection ===")

    # Connect to webcam
    print("\n1. Connecting to webcam...")
    response = requests.post(f'{SERVER_URL}/api/connect', json={'source': 'webcam'})
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Get status
    print("\n2. Getting status...")
    response = requests.get(f'{SERVER_URL}/api/status')
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Disconnect
    print("\n3. Disconnecting...")
    response = requests.post(f'{SERVER_URL}/api/disconnect')
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Verify disconnected
    print("\n4. Verifying disconnection...")
    response = requests.get(f'{SERVER_URL}/api/status')
    print(f"   Response: {response.json()}")

def test_tello():
    print("\n\n=== Testing Tello Connection ===")

    # Connect to Tello
    print("\n1. Connecting to Tello...")
    response = requests.post(f'{SERVER_URL}/api/connect', json={'source': 'tello'})
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Get status
    print("\n2. Getting status...")
    response = requests.get(f'{SERVER_URL}/api/status')
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Disconnect
    print("\n3. Disconnecting...")
    response = requests.post(f'{SERVER_URL}/api/disconnect')
    print(f"   Response: {response.json()}")

    time.sleep(1)

    # Verify disconnected
    print("\n4. Verifying disconnection...")
    response = requests.get(f'{SERVER_URL}/api/status')
    print(f"   Response: {response.json()}")

if __name__ == '__main__':
    print("Tello Backend Disconnect Test")
    print("Make sure the server is running (python server.py)\n")

    try:
        # Test webcam
        test_webcam()

        # Ask before testing Tello
        input("\n\nPress Enter to test Tello connection (make sure you're on Tello WiFi), or Ctrl+C to skip...")
        test_tello()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
