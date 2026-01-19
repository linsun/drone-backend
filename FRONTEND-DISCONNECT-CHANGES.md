# Frontend Changes for Disconnect Functionality

## Changes needed in your App.js

Add these changes to enable disconnect functionality and fix the camera switching issue.

### 1. Add Disconnect Function

Add this function to your App.js component:

```javascript
const disconnectCamera = async () => {
  setLoading(true);
  setStatus('Disconnecting...');

  try {
    // Stop stream first if active
    if (streaming) {
      await fetch(`${SERVER_URL}/api/stop-stream`, {
        method: 'POST'
      });
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
      setStatus('✅ Disconnected successfully');
      setBattery(null);
    } else {
      setStatus(`❌ Disconnect failed: ${data.error}`);
    }
  } catch (error) {
    setStatus(`❌ Disconnect error: ${error.message}`);
  } finally {
    setLoading(false);
  }
};
```

### 2. Update the UI - Add Disconnect Button

Find the section where you have the Connect button when connected, and add a Disconnect button:

```javascript
{connected ? (
  <div className="flex gap-2">
    {/* Show current source */}
    <div className="px-4 py-2 bg-slate-700 rounded-lg text-slate-300">
      {cameraSource === 'webcam' ? '📷 Webcam' : '🚁 Tello'}
    </div>

    {/* Disconnect button */}
    <button
      onClick={disconnectCamera}
      disabled={loading}
      className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-red-500/50"
    >
      Disconnect
    </button>
  </div>
) : (
  // ... existing camera source selector and connect button
)}
```

### 3. Optional: Add Battery State Reset

If you have a battery state variable, make sure to reset it on disconnect. Add this to your state declarations if not already present:

```javascript
const [battery, setBattery] = useState(null);
```

### 4. Full Example of Updated Control Section

Here's the complete control section with disconnect button:

```javascript
{/* Control Buttons */}
<div className="flex items-center gap-3">
  {!connected ? (
    <>
      {/* Camera Source Selector */}
      <div className="flex gap-2 mr-2">
        <button
          onClick={() => setCameraSource('tello')}
          className={`px-4 py-2 rounded-lg font-medium transition-all text-sm ${
            cameraSource === 'tello'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          🚁 Tello
        </button>
        <button
          onClick={() => setCameraSource('webcam')}
          className={`px-4 py-2 rounded-lg font-medium transition-all text-sm ${
            cameraSource === 'webcam'
              ? 'bg-blue-600 text-white shadow-lg'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          📷 Webcam
        </button>
      </div>

      {/* Connect Button */}
      <button
        onClick={() => connectDrone(cameraSource)}
        disabled={loading}
        className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-blue-500/50"
      >
        Connect
      </button>
    </>
  ) : (
    <>
      {/* Current Source Display */}
      <div className="px-4 py-2 bg-slate-700 rounded-lg text-slate-300 font-medium">
        {cameraSource === 'webcam' ? '📷 Webcam' : '🚁 Tello'}
        {cameraSource === 'tello' && battery && ` • ${battery}%`}
      </div>

      {/* Disconnect Button */}
      <button
        onClick={disconnectCamera}
        disabled={loading}
        className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-red-500/50"
      >
        Disconnect
      </button>

      {/* Start/Stop Stream Buttons */}
      {!streaming ? (
        <button
          onClick={startStream}
          disabled={loading}
          className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-green-500/50"
        >
          Start Stream
        </button>
      ) : (
        <button
          onClick={stopStream}
          disabled={loading}
          className="px-6 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-yellow-500/50"
        >
          Stop Stream
        </button>
      )}
    </>
  )}
</div>
```

### 5. Usage Flow

The user flow will now be:

1. **Select camera source** (Tello or Webcam)
2. **Click Connect** → connects to selected source
3. **Start Stream** → begins video streaming
4. **Stop Stream** → stops video streaming
5. **Click Disconnect** → disconnects from camera source
6. **Can now select different source** and reconnect

This allows switching between Tello and Webcam without restarting the app or server!

---

## Testing the Changes

1. Start the backend with camera fix:
   ```bash
   cd ~/src/github.com/linsun/tello-backend
   ./run_server.sh
   ```

2. Start your frontend:
   ```bash
   cd ~/src/github.com/linsun/tello-frontend
   npm start
   ```

3. Test the flow:
   - Connect to Webcam → should work with live video
   - Disconnect
   - Connect to Tello → should work if on Tello WiFi
   - Disconnect
   - Connect back to Webcam → should work again

---

## API Endpoints Summary

The backend now supports:

- `POST /api/connect` - Connect to camera source (body: `{source: 'tello' | 'webcam'}`)
- `POST /api/disconnect` - Disconnect from current source
- `GET /api/status` - Get current status
- `POST /api/start-stream` - Start video streaming
- `POST /api/stop-stream` - Stop video streaming
- `POST /api/capture` - Capture photo
- `GET /api/photo/<filename>` - Get captured photo
- WebSocket `/video` - Video stream frames

All endpoints properly handle both Tello and Webcam sources!
