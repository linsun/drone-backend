# Webcam Live Feed Debugging Guide

## Changes Made

I've added comprehensive debugging output to the backend server to help diagnose why the webcam live feed isn't working.

### Updated Functions

1. **`/api/video-feed` endpoint** (line 639)
   - Added detailed logging for stream status
   - Better error messages for webcam/tello state
   - Shows exactly which checks are failing

2. **`/api/start-stream` endpoint** (line 246)
   - Added debug output for webcam object state
   - Logs test frame capture results
   - Shows resolution and thread status
   - Initializes `latest_frame` cache with test frame

3. **`generate_mjpeg()` function** (line 605)
   - Tracks empty frame count
   - Logs when `latest_frame` is None
   - Better visibility into MJPEG generation

## How to Debug

### Step 1: Test Webcam Access

First, verify your webcam works:

```bash
cd /path/to/tello-backend
python test_webcam.py
```

Expected output:
```
Testing webcam access...
✅ Webcam opened successfully!
✅ Resolution: 1280x720
✅ FPS: 30.0

Testing frame capture (5 frames)...
  Frame 1: ✅ (720, 1280, 3)
  Frame 2: ✅ (720, 1280, 3)
  ...
✅ Webcam is working correctly!
```

If this fails, the issue is with webcam access, not the streaming code.

### Step 2: Start Backend with Debugging

```bash
cd /path/to/tello-backend
python server.py
```

Watch the console output carefully.

### Step 3: Test Webcam Connection

1. In the frontend, select "Webcam" mode
2. Click "Connect"

**Expected Backend Output:**
```
Connecting to webcam...
Connected to webcam!
```

**If you see an error**, check:
- Is another app using the webcam? (Zoom, Skype, etc.)
- Do you have camera permissions enabled?
- Is the webcam physically connected?

### Step 4: Start Camera Stream

Click "Start Camera" in the frontend.

**Expected Backend Output:**
```
Starting video stream (source: webcam)...
[start-stream] Webcam object: <cv2.VideoCapture ...>
[start-stream] Webcam opened: True
[start-stream] Testing webcam frame capture...
[start-stream] Read result: ret=True, frame=True
[start-stream] ✅ SUCCESS: Webcam active, resolution: 1280x720
[start-stream] Starting background worker thread...
[start-stream] ✅ Webcam stream started successfully (thread alive: True)
Video stream worker started (source: webcam)
```

**Common Issues:**

| Backend Output | Problem | Solution |
|---------------|---------|----------|
| `Webcam object: None` | Webcam not connected | Check `/api/connect` was successful |
| `Webcam opened: False` | Webcam closed unexpectedly | Restart backend, check permissions |
| `Read result: ret=False` | Can't read frames | Check webcam isn't in use by another app |
| `thread alive: False` | Worker thread failed | Check for Python errors above |

### Step 5: Check MJPEG Stream

When the frontend displays the video, watch for:

**Expected Backend Output:**
```
[video-feed] Request received - streaming: True, source: webcam
[video-feed] ✅ Webcam is ready, starting MJPEG stream
[MJPEG] Stream client connected (source: webcam)
Streaming: 90 frames, FPS: 30.2, Clients: 0
[MJPEG] Streamed 100 frames
```

**Common Issues:**

| Backend Output | Problem | Solution |
|---------------|---------|----------|
| `Stream not active` | Streaming flag is False | Click "Start Camera" again |
| `Webcam not initialized` | Webcam object is None | Reconnect to webcam |
| `Webcam not available` | Webcam closed | Restart backend |
| `latest_frame is None` | Worker thread not populating frames | Check worker thread errors |

### Step 6: Frontend Console Check

Open browser DevTools (F12) → Console tab

**Expected:**
```javascript
Setting MJPEG source: http://localhost:3001/api/video-feed?t=1234567890
```

**Common Issues:**

| Console Output | Problem | Solution |
|---------------|---------|----------|
| `404 Not Found` | Backend not running | Start backend server |
| `400 Bad Request` | Stream not started | Check backend logs |
| `CORS error` | Cross-origin blocked | Backend should have CORS enabled (it does) |
| Image loads but is blank | Frames not being sent | Check backend MJPEG logs |

## Architecture Overview

```
Frontend (React)
    ↓
  [img] tag with src="/api/video-feed"
    ↓
Backend (Flask)
    ↓
  /api/video-feed endpoint
    ↓
  generate_mjpeg() generator
    ↓
  latest_frame (cached frame)
    ↑
  video_stream_worker() thread
    ↑
  webcam.read() (OpenCV)
```

The key points:
1. **Webcam is opened once** when `/api/connect` is called
2. **Worker thread** continuously reads frames and caches them
3. **MJPEG generator** reads from the cache (not directly from webcam)
4. **This prevents** segmentation faults from multiple simultaneous reads

## Known Working Configurations

✅ **Works with:**
- macOS with built-in webcam
- Linux with USB webcam
- Tello drone (original functionality)

⚠️ **May have issues with:**
- Windows with certain webcam drivers
- Virtual cameras (OBS, Snap Camera, etc.)
- Remote desktop sessions (no camera access)

## Testing Checklist

- [ ] Webcam test script passes
- [ ] Backend starts without errors
- [ ] Webcam connects successfully
- [ ] Stream starts, shows resolution
- [ ] Worker thread is alive
- [ ] MJPEG endpoint returns video
- [ ] Frontend displays live feed
- [ ] Photo capture works

## Still Not Working?

If you've gone through all the steps and it still doesn't work:

1. **Check Backend Logs**: Look for any Python exceptions or errors
2. **Check Frontend Console**: Look for network errors or failed requests
3. **Check Network Tab**: Open DevTools → Network, filter by "video-feed", see the response
4. **Test with curl**:
   ```bash
   # After starting stream
   curl -I http://localhost:3001/api/video-feed
   ```
   Should return `200 OK` and `Content-Type: multipart/x-mixed-replace`

5. **Compare with Tello**: Does Tello streaming work? If yes, it's webcam-specific.

## Next Steps

If webcam access works but MJPEG doesn't stream:
- The issue is in `generate_mjpeg()` or the worker thread
- Check if `latest_frame` is being populated
- Verify the worker thread is running and not crashing

If MJPEG streams but frontend doesn't display:
- The issue is in the frontend `<img>` tag
- Try opening `http://localhost:3001/api/video-feed` directly in browser
- Check CORS headers

## Summary of Changes

The debugging additions will help you see:
- ✅ When webcam is opened/closed
- ✅ When frames are being read
- ✅ When the worker thread starts
- ✅ When MJPEG clients connect
- ✅ Frame counts and FPS
- ✅ When `latest_frame` is empty
- ✅ Exact error conditions

With this detailed logging, you should be able to pinpoint exactly where the webcam streaming fails!
