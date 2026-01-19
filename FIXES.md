# Fixes Applied

## Issues Fixed

### 1. macOS Camera Permission Error
**Problem:**
```
OpenCV: not authorized to capture video (status 0), requesting...
OpenCV: can not spin main run loop from other thread
```

**Solution:**
Set environment variable before running the server:

```bash
export OPENCV_AVFOUNDATION_SKIP_AUTH=1
python server.py
```

Or use the provided script:
```bash
./run_server.sh
```

**Why this works:**
macOS requires camera permission dialogs to be shown from the main thread. This environment variable tells OpenCV to skip the automatic permission request, assuming you've already granted camera access to Terminal/iTerm in System Settings.

**Make sure:**
1. Go to System Settings > Privacy & Security > Camera
2. Enable access for your Terminal app (Terminal.app or iTerm.app)

---

### 2. No Disconnect Endpoint
**Problem:**
Could not switch from webcam to Tello drone - no way to disconnect.

**Solution:**
Added new `/api/disconnect` endpoint that:
- Stops any active streaming
- Releases webcam or disconnects from Tello
- Clears all state variables
- Allows you to reconnect to a different source

**Usage:**
```bash
curl -X POST http://localhost:3001/api/disconnect
```

Or from frontend (needs to be updated):
```javascript
const disconnect = async () => {
  const response = await fetch(`${SERVER_URL}/api/disconnect`, {
    method: 'POST'
  });
  const data = await response.json();
  if (data.success) {
    setConnected(false);
    setCameraSource(null);
  }
};
```

---

### 3. Video Feed 400 Error
**Problem:**
```
127.0.0.1 - - [18/Jan/2026 12:02:24] "GET /api/video-feed?t=1768755744045 HTTP/1.1" 400 -
```

**Solution:**
Fixed the `video_feed()` endpoint to properly check camera source:
- Changed from `if not streaming or frame_read is None`
- To properly check webcam vs Tello source
- Now validates the correct source is available

**Note:**
Your frontend is using WebSocket (`/video`) which works fine. The MJPEG endpoint (`/api/video-feed`) is an alternative method that some browsers prefer.

---

## Testing

### Test the disconnect functionality:
```bash
# In terminal 1: Start server with camera fix
cd tello-backend
./run_server.sh

# In terminal 2: Run test script
cd tello-backend
python test_disconnect.py
```

The test script will:
1. Connect to webcam
2. Get status
3. Disconnect
4. Verify disconnection
5. (Optional) Test same flow with Tello

---

## Frontend Updates Needed

Your `tello-frontend` folder appears to be empty. You'll need to add a disconnect button to your React frontend:

```javascript
// Add disconnect function
const disconnectCamera = async () => {
  try {
    // Stop stream first
    if (streaming) {
      await fetch(`${SERVER_URL}/api/stop-stream`, { method: 'POST' });
      setStreaming(false);
    }

    // Then disconnect
    const response = await fetch(`${SERVER_URL}/api/disconnect`, {
      method: 'POST'
    });

    const data = await response.json();
    if (data.success) {
      setConnected(false);
      setCameraSource(null);
      setStatus('Disconnected');
    }
  } catch (error) {
    setStatus(`Disconnect error: ${error.message}`);
  }
};

// Add button in UI (when connected)
{connected && (
  <button
    onClick={disconnectCamera}
    className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium"
  >
    Disconnect
  </button>
)}
```

---

## Summary

✅ **Fixed**: macOS camera permission issue (use `run_server.sh`)
✅ **Fixed**: Added disconnect endpoint
✅ **Fixed**: Video feed 400 error
⏳ **TODO**: Update frontend with disconnect button (frontend folder is empty)

The backend is fully functional now. You can:
1. Connect to webcam
2. Connect to Tello
3. Disconnect from either
4. Switch between them

The video streaming works via WebSocket. The MJPEG endpoint also works now if you want to use it.
