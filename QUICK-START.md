# Quick Start Guide

## Issues Fixed ✅

1. **macOS Camera Permission Error** - Fixed with environment variable
2. **No Disconnect Functionality** - Added `/api/disconnect` endpoint
3. **Video Feed 400 Error** - Fixed camera source validation
4. **Can't Switch Between Tello and Webcam** - Now fully supported!

---

## Start the Backend

```bash
cd ~/src/github.com/linsun/tello-backend

# Run with macOS camera fix
./run_server.sh
```

**Make sure:** You've granted camera access to Terminal/iTerm in **System Settings > Privacy & Security > Camera**

---

## Update Your Frontend

Apply the changes from `FRONTEND-DISCONNECT-CHANGES.md` to your `~/src/github.com/linsun/tello-frontend/src/App.js`:

1. Add the `disconnectCamera` function
2. Add the Disconnect button to your UI
3. Update the control section layout

Then start your frontend:

```bash
cd ~/src/github.com/linsun/tello-frontend
npm start
```

---

## Test Everything

### Test 1: Webcam Connection
1. Select "📷 Webcam" in the UI
2. Click "Connect" → should see "✅ Connected to webcam!"
3. Click "Start Stream" → should see live video
4. Click "Capture Photo" → should save photo
5. Click "Stop Stream"
6. Click "Disconnect"

### Test 2: Switch to Tello
1. Connect to Tello WiFi network
2. Select "🚁 Tello" in the UI
3. Click "Connect" → should see battery level
4. Click "Start Stream" → should see drone video
5. Fly the drone, take photos, etc.
6. Click "Disconnect"

### Test 3: Switch Back to Webcam
1. Select "📷 Webcam" in the UI
2. Click "Connect" → should work immediately!
3. No need to restart anything

---

## Files Changed

### Backend (`~/src/github.com/linsun/tello-backend/`)
- ✅ `server.py` - Added disconnect endpoint, fixed video feed validation
- ✅ `run_server.sh` - Script to run server with macOS camera fix
- 📄 `test_disconnect.py` - Test script for disconnect functionality
- 📄 `FIXES.md` - Detailed explanation of all fixes
- 📄 `FRONTEND-DISCONNECT-CHANGES.md` - Frontend code changes needed
- 📄 `QUICK-START.md` - This file!

### Frontend (`~/src/github.com/linsun/tello-frontend/src/`)
- ⏳ `App.js` - **YOU NEED TO UPDATE THIS** (see FRONTEND-DISCONNECT-CHANGES.md)

---

## Backend API

All endpoints now properly support both Tello and Webcam:

```bash
# Connect
curl -X POST http://localhost:3001/api/connect \
  -H "Content-Type: application/json" \
  -d '{"source": "webcam"}'

# Get Status
curl http://localhost:3001/api/status

# Start Stream
curl -X POST http://localhost:3001/api/start-stream

# Disconnect
curl -X POST http://localhost:3001/api/disconnect
```

---

## Environment Variable Explained

The `OPENCV_AVFOUNDATION_SKIP_AUTH=1` environment variable tells OpenCV to skip the automatic camera permission request. This is needed because:

1. macOS requires permission dialogs on the main thread
2. Flask runs OpenCV in a background thread
3. This causes the "can not spin main run loop from other thread" error
4. The workaround assumes you've already granted camera permission in System Settings

**Alternative:** You could modify the code to open the webcam once in the main thread before starting Flask, but the environment variable is simpler.

---

## Troubleshooting

### "Could not open webcam"
- Check System Settings > Privacy & Security > Camera
- Make sure Terminal/iTerm has camera access
- Close other apps using the camera (Zoom, FaceTime, etc.)

### "No video visible but photos work"
- Check browser console for WebSocket errors
- Make sure you clicked "Start Stream"
- Try refreshing the page

### "Can't connect to Tello"
- Make sure you're connected to Tello WiFi network
- Tello WiFi name is usually "TELLO-XXXXXX"
- Check that Tello is powered on (blinking yellow = ready)

### "Disconnect doesn't work"
- Make sure you applied the backend changes (server.py has `/api/disconnect` endpoint)
- Check backend logs for errors
- Try the test script: `python test_disconnect.py`

---

## What's Next?

Everything should work now! You can:

1. ✅ Connect to webcam for development/testing
2. ✅ Connect to Tello for flying
3. ✅ Switch between them without restarting
4. ✅ Take high-quality photos from both sources
5. ✅ Stream smooth video at ~30 FPS

The backend is ready. Just update your frontend with the disconnect button and you're all set! 🚀
