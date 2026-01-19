#!/bin/bash

# Set environment variable to fix macOS camera permission issue
export OPENCV_AVFOUNDATION_SKIP_AUTH=1

echo "Starting Tello Backend Server with macOS camera fix..."
echo "Environment: OPENCV_AVFOUNDATION_SKIP_AUTH=1"
echo ""

# Run the server
python server.py
