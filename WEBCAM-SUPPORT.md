# Webcam Support Added to Tello App

## Backend Changes

I've updated the backend (`tello-backend/server.py`) to support **both Tello drone and local webcam** as camera sources. This allows you to test the app without the drone!

### New Features:

1. **Dual Camera Support**: Connect to either Tello or webcam
2. **Automatic Source Detection**: Backend tracks which source is active
3. **Unified API**: Same endpoints work for both sources
4. **Quality Settings**: Webcam configured for 1280x720 @ 30fps

### API Changes:

#### Connect Endpoint
```javascript
// Connect to Tello (default)
POST /api/connect
{
  "source": "tello"
}

// Connect to Webcam (new!)
POST /api/connect
{
  "source": "webcam"
}
```

#### Status Endpoint
Now returns the active source:
```javascript
{
  "success": true,
  "source": "webcam",  // or "tello" or null
  "status": { ... }
}
```

### Backend is Ready!

The backend now supports:
✅ Connecting to webcam
✅ Streaming from webcam
✅ Capturing photos from webcam
✅ All existing Tello functionality preserved

## Frontend Updates Needed

To add the camera selector UI, update your `tello-frontend/src/App.js`:

### 1. Add State for Camera Source

```javascript
const [cameraSource, setCameraSource] = useState('tello'); // 'tello' or 'webcam'
```

### 2. Update Connect Function

```javascript
const connectDrone = async (source = 'tello') => {
  setLoading(true);
  setStatus(`Connecting to ${source === 'webcam' ? 'webcam' : 'Tello drone'}...`);

  try {
    const response = await fetch(`${SERVER_URL}/api/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ source })
    });

    const data = await response.json();

    if (data.success) {
      setConnected(true);
      setCameraSource(data.source || source);
      if (source === 'webcam') {
        setStatus('✅ Connected to webcam!');
      } else {
        setStatus(`✅ Connected to Tello drone!${data.battery ? ` Battery: ${data.battery}%` : ''}`);
      }
      getDroneStatus();
    } else {
      setStatus(`❌ Connection failed: ${data.error}`);
    }
  } catch (error) {
    setStatus(`❌ Error: ${error.message}`);
  } finally {
    setLoading(false);
  }
};
```

### 3. Add Camera Selector UI

Add this before the "Connect to Drone" button:

```javascript
{!connected && (
  <div className="mb-4">
    <label className="block text-sm font-medium mb-2">Camera Source:</label>
    <div className="flex gap-3">
      <button
        onClick={() => setCameraSource('tello')}
        className={`px-4 py-2 rounded-lg font-medium transition-all ${
          cameraSource === 'tello'
            ? 'bg-blue-600 text-white'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
        }`}
      >
        🚁 Tello Drone
      </button>
      <button
        onClick={() => setCameraSource('webcam')}
        className={`px-4 py-2 rounded-lg font-medium transition-all ${
          cameraSource === 'webcam'
            ? 'bg-blue-600 text-white'
            : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
        }`}
      >
        📷 Webcam
      </button>
    </div>
  </div>
)}
```

### 4. Update Connect Button

```javascript
<button
  onClick={() => connectDrone(cameraSource)}
  disabled={loading}
  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:opacity-50 rounded-lg font-medium transition-all shadow-lg hover:shadow-blue-500/50"
>
  Connect to {cameraSource === 'webcam' ? 'Webcam' : 'Drone'}
</button>
```

### 5. Update Setup Warning (Optional)

Update the setup instructions to mention webcam option:

```javascript
{!connected && (
  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-6 flex items-start gap-3">
    <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
    <div className="text-sm text-yellow-200">
      <p className="font-semibold mb-1">Two Ways to Connect:</p>
      <ul className="list-disc list-inside space-y-1 text-yellow-300/80">
        <li><strong>Tello Drone:</strong> Connect to Tello WiFi network (TELLO-XXXXXX)</li>
        <li><strong>Webcam:</strong> Use your laptop/phone camera for testing</li>
      </ul>
    </div>
  </div>
)}
```

### 6. Update Battery Display (Optional)

Only show battery for Tello:

```javascript
{droneStatus && cameraSource === 'tello' && (
  <div className="flex items-center gap-4 text-sm">
    <div className="flex items-center gap-1 bg-green-500/20 px-3 py-1 rounded-full">
      <Battery className="w-4 h-4 text-green-400" />
      <span>{droneStatus.battery}%</span>
    </div>
  </div>
)}
```

## Complete Frontend Example

Here's a minimal complete implementation you can add to your App.js:

```javascript
// Add to state (top of component)
const [cameraSource, setCameraSource] = useState('tello');

// Updated connectDrone function
const connectDrone = async (source = 'tello') => {
  setLoading(true);
  setStatus(`Connecting to ${source === 'webcam' ? 'webcam' : 'Tello drone'}...`);

  try {
    const response = await fetch(`${SERVER_URL}/api/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ source })
    });

    const data = await response.json();

    if (data.success) {
      setConnected(true);
      setCameraSource(data.source || source);
      setStatus(`✅ Connected to ${source === 'webcam' ? 'webcam' : 'Tello'}!`);
      getDroneStatus();
    } else {
      setStatus(`❌ Connection failed: ${data.error}`);
    }
  } catch (error) {
    setStatus(`❌ Error: ${error.message}`);
  } finally {
    setLoading(false);
  }
};

// UI (in your render/return section)
{!connected ? (
  <>
    {/* Camera Source Selector */}
    <div className="mb-4">
      <label className="block text-sm font-medium mb-2 text-slate-300">
        Select Camera Source:
      </label>
      <div className="flex gap-3">
        <button
          onClick={() => setCameraSource('tello')}
          className={`flex-1 px-4 py-3 rounded-lg font-medium transition-all shadow-lg ${
            cameraSource === 'tello'
              ? 'bg-blue-600 text-white shadow-blue-500/50'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl">🚁</span>
            <div className="text-left">
              <div className="font-semibold">Tello Drone</div>
              <div className="text-xs opacity-75">Requires WiFi connection</div>
            </div>
          </div>
        </button>
        <button
          onClick={() => setCameraSource('webcam')}
          className={`flex-1 px-4 py-3 rounded-lg font-medium transition-all shadow-lg ${
            cameraSource === 'webcam'
              ? 'bg-blue-600 text-white shadow-blue-500/50'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <span className="text-2xl">📷</span>
            <div className="text-left">
              <div className="font-semibold">Webcam</div>
              <div className="text-xs opacity-75">Test mode - no drone needed</div>
            </div>
          </div>
        </button>
      </div>
    </div>

    {/* Connect Button */}
    <button
      onClick={() => connectDrone(cameraSource)}
      disabled={loading}
      className="w-full px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-slate-700 disabled:to-slate-700 disabled:opacity-50 rounded-lg font-medium text-lg transition-all shadow-xl hover:shadow-blue-500/50"
    >
      Connect to {cameraSource === 'webcam' ? 'Webcam' : 'Tello Drone'}
    </button>
  </>
) : (
  // Your existing connected UI
  ...
)}
```

## Testing

### Test with Webcam:
1. Restart backend: `python server.py`
2. In frontend, select "Webcam"
3. Click "Connect to Webcam"
4. Click "Start Camera" - should see your webcam feed
5. Capture photos - should work normally

### Test with Tello:
1. Connect to Tello WiFi
2. In frontend, select "Tello Drone"
3. Click "Connect to Tello Drone"
4. Everything works as before

## Benefits

✅ **Test without drone** - develop and test UI without hardware
✅ **Demo-friendly** - show the app to people without flying
✅ **Debug easier** - test photo capture logic with webcam
✅ **Phone camera** - can use phone as camera source
✅ **Same codebase** - no separate test/prod builds needed

## Notes

- Webcam uses OpenCV's VideoCapture (device 0)
- Configured for 1280x720 @ 30fps (best quality)
- All photo capture features work the same
- Claude AI comparison works with webcam photos too
- Backend automatically handles source switching

Enjoy testing with your webcam! 📷✨
