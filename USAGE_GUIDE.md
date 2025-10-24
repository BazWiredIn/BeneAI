# BeneAI Usage Guide

**AI-Powered Real-Time Video Call Coaching System**

This guide explains how to set up, run, and test the complete video-to-advice overlay pipeline.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Setup Instructions](#setup-instructions)
4. [Testing the Pipeline](#testing-the-pipeline)
5. [Pipeline Architecture](#pipeline-architecture)
6. [WebSocket API Reference](#websocket-api-reference)
7. [Troubleshooting](#troubleshooting)

---

## System Overview

BeneAI analyzes video calls in real-time to provide coaching advice for high-stakes meetings (investor pitches, negotiations, interviews). The system:

1. **Captures video frames** from your webcam or video call
2. **Detects emotions** using Hume AI's facial expression analysis
3. **Aggregates data** into 1-second intervals with emotional smoothing
4. **Generates coaching advice** using GPT-4 based on emotional trends (every 4-5 seconds)
5. **Displays insights** in a non-intrusive overlay widget

**Key Features:**
- Real-time emotion detection (48 Hume emotions → 6 investor states)
- Exponential moving average (EMA) for smooth emotion tracking
- Context-aware LLM coaching based on 5-second windows
- Beautiful overlay UI with minimizable widget

---

## Prerequisites

### Required Software

- **Python 3.11+** (for backend)
- **Node.js 18+** (optional, for frontend development)
- **Modern browser** (Chrome/Edge recommended for WebRTC)

### Required API Keys

1. **OpenAI API Key** - For GPT-4 coaching advice
   - Get it at: https://platform.openai.com/api-keys
   - Recommended tier: Tier 2+ ($50 budget for testing)

2. **Hume AI API Key** - For emotion detection
   - Get it at: https://beta.hume.ai/
   - Free tier available for testing

### Python Dependencies

All dependencies are in `backend/requirements.txt`:

```bash
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets>=13.1,<14.0

# AI Services
openai==1.3.5
hume==0.12.1

# Configuration
python-dotenv==1.0.0
pydantic>=2.10.0,<3.0.0
pydantic-settings>=2.6.0
```

---

## Setup Instructions

### 1. Clone and Navigate to Repository

```bash
git clone <repository-url>
cd BeneAI
```

### 2. Set Up Backend

#### a. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### b. Install Dependencies

```bash
pip install -r requirements.txt
```

#### c. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env

# OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=100
OPENAI_TEMPERATURE=0.7

# Hume AI Configuration
HUME_API_KEY=your-hume-api-key-here
HUME_ENABLE_FACE=true
HUME_ENABLE_PROSODY=true
HUME_ENABLE_LANGUAGE=true
HUME_FRAME_RATE=3.0

# Server Configuration
ENVIRONMENT=development
LOG_LEVEL=info
PORT=8000
ALLOWED_ORIGINS=*

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=300
```

#### d. Start the Backend Server

```bash
# From backend/ directory
uvicorn main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Starting BeneAI backend...
INFO:     Hume AI client ready
```

### 3. Set Up Frontend

#### a. Configure Backend URL

Edit `frontend/overlay.html` (line 292):

```javascript
const BACKEND_URL = 'ws://localhost:8000/ws';
```

For production/Cloud Run deployment:

```javascript
const BACKEND_URL = 'wss://your-backend-url.run.app/ws';
```

#### b. Open Frontend in Browser

Simply open `frontend/overlay.html` in your browser:

```bash
# From project root
open frontend/overlay.html  # macOS
# or
start frontend/overlay.html  # Windows
# or drag file to browser
```

---

## Testing the Pipeline

### Test 1: Backend Health Check

Verify the backend is running:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "active_connections": 0,
  "services": {
    "hume": true,
    "openai": true
  }
}
```

### Test 2: WebSocket Connection

Test WebSocket connectivity:

```bash
# From backend/ directory
python test_websocket.py
```

Expected output:

```
==================================================
BeneAI WebSocket Connection Test
==================================================

Connecting to ws://localhost:8000/ws...
✓ Connected to WebSocket!

✓ Received welcome message:
   Type: connection
   Status: connected
   Message: Welcome to BeneAI coaching service
   Version: 1.0.0

Sending ping...
✓ Sent ping

✓ Received pong:
   Type: pong
   Timestamp: 1234567890

==================================================
✅ WebSocket is working perfectly!
==================================================
```

### Test 3: Frontend Overlay Connection

1. Open `frontend/overlay.html` in Chrome
2. Open browser DevTools (F12) → Console
3. Look for connection logs:

```
Connected to BeneAI backend
Received: connection
Welcome: Welcome to BeneAI coaching service
```

4. Check the overlay widget (bottom-right corner):
   - Should show green "Connected" status dot
   - Investor State should show "Waiting..."

### Test 4: Send Test Video Frame

You can test video frame processing using the browser console:

```javascript
// In browser console on overlay.html
const canvas = document.createElement('canvas');
canvas.width = 640;
canvas.height = 480;
const ctx = canvas.getContext('2d');
ctx.fillStyle = 'blue';
ctx.fillRect(0, 0, 640, 480);
const frameData = canvas.toDataURL('image/jpeg', 0.8);

// Send frame via WebSocket (assuming ws is connected)
ws.send(JSON.stringify({
    type: 'video_frame',
    timestamp: Date.now(),
    data: frameData
}));
```

Check backend logs for:

```
INFO: Processing frame with Hume AI for <client-id>
INFO: Emotion detected for <client-id>: interested (Joy: 0.85)
```

### Test 5: Full Pipeline Test (with Webcam)

#### a. Create a Test HTML Page

Create `frontend/test-webcam.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>BeneAI Webcam Test</title>
</head>
<body>
    <h1>BeneAI Webcam Test</h1>
    <video id="video" width="640" height="480" autoplay></video>
    <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>
    <div id="status">Initializing...</div>

    <script src="js/websocket-client.js"></script>
    <script>
        const CONFIG = { BACKEND_URL: 'ws://localhost:8000/ws' };

        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const status = document.getElementById('status');

        const ws = new WebSocketClient();

        // Start webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                video.srcObject = stream;
                status.textContent = 'Webcam started';

                // Connect to backend
                ws.connect().then(() => {
                    status.textContent = 'Connected to backend';
                    startCapture();
                });
            });

        function startCapture() {
            setInterval(() => {
                // Draw video frame to canvas
                ctx.drawImage(video, 0, 0, 640, 480);

                // Convert to base64
                const frameData = canvas.toDataURL('image/jpeg', 0.8);

                // Send to backend
                ws.sendVideoFrame(frameData);

                status.textContent = 'Sending frames...';
            }, 333); // ~3 FPS (matches HUME_FRAME_RATE)
        }

        // Listen for emotion results
        ws.onEmotion((data) => {
            console.log('Emotion detected:', data.investor_state, data.primary_emotion);
            status.textContent = `Detected: ${data.investor_state} (${data.primary_emotion})`;
        });

        // Listen for coaching advice
        ws.onCoaching((data) => {
            console.log('Coaching advice:', data.coaching_advice);
            alert(`Coaching: ${data.coaching_advice}`);
        });
    </script>
</body>
</html>
```

#### b. Run Test

1. Open `test-webcam.html` in Chrome
2. Allow webcam access
3. Watch browser console for logs:
   - Video frames being sent (every ~330ms)
   - Emotion results (with Hume data)
   - Interval completions (every 1 second)
   - LLM context updates (every 4-5 seconds)

#### c. Expected Flow

```
[0.0s] Webcam started
[0.1s] Connected to backend
[0.3s] Frame sent → Hume AI analysis
[0.5s] Emotion detected: interested (Joy: 0.78)
[1.0s] Interval complete: interested (3 frames analyzed)
[1.3s] Frame sent → Hume AI analysis
[1.5s] Emotion detected: focused (Concentration: 0.82)
[2.0s] Interval complete: focused (3 frames analyzed)
...
[5.0s] LLM context update triggered
[5.5s] Coaching advice: "Great momentum! The investor is engaged..."
```

### Test 6: Verify Overlay Updates

1. Open `frontend/overlay.html` alongside the webcam test
2. Both should connect to the same backend
3. The overlay should update in real-time:
   - **Investor State** changes color and emoji
   - **Top Emotions** show EMA scores with trend arrows (↑↓→)
   - **Coaching Advice** updates every 4-5 seconds with new suggestions

---

## Pipeline Architecture

### Data Flow Diagram

```
┌─────────────────┐
│   Video Call    │
│   (Webcam)      │
└────────┬────────┘
         │ 30 FPS
         ▼
┌─────────────────┐
│  Frame Capture  │ ← Chrome Extension / HTML5
│  (640x480 JPEG) │
└────────┬────────┘
         │ 3 FPS (throttled)
         ▼
┌─────────────────┐
│  WebSocket      │ ← Base64 encoded frame
│  to Backend     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              BACKEND (FastAPI)                  │
├─────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐  │
│  │  1. Hume AI Face Detection               │  │
│  │     - 48 emotion scores                  │  │
│  │     - Face bounding box                  │  │
│  │     - Primary emotion + confidence       │  │
│  └──────────────┬───────────────────────────┘  │
│                 │ 300-500ms                     │
│                 ▼                               │
│  ┌──────────────────────────────────────────┐  │
│  │  2. Investor State Mapping               │  │
│  │     48 emotions → 6 states:              │  │
│  │     • interested    (🟢 green)           │  │
│  │     • skeptical     (🟡 yellow)          │  │
│  │     • concerned     (🟠 orange)          │  │
│  │     • confused      (🔴 red)             │  │
│  │     • bored         (🔵 blue)            │  │
│  │     • neutral       (⚪ gray)            │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│                 ▼                               │
│  ┌──────────────────────────────────────────┐  │
│  │  3. Interval Aggregator (1-second)       │  │
│  │     - EMA smoothing (alpha=0.3)          │  │
│  │     - Tracks top 5 emotions              │  │
│  │     - Counts frames analyzed             │  │
│  │     - Calculates trends (↑↓→)            │  │
│  └──────────────┬───────────────────────────┘  │
│                 │ Every 1.0 second              │
│                 ▼                               │
│  ┌──────────────────────────────────────────┐  │
│  │  4. Time-Series Buffer (5-second window) │  │
│  │     - Stores last 5 intervals            │  │
│  │     - Calculates dominant state          │  │
│  │     - Detects state changes              │  │
│  │     - Triggers LLM every 4.5 seconds     │  │
│  └──────────────┬───────────────────────────┘  │
│                 │ Every 4.5 seconds             │
│                 ▼                               │
│  ┌──────────────────────────────────────────┐  │
│  │  5. LLM Context Builder                  │  │
│  │     - Formats interval data for GPT-4    │  │
│  │     - Includes emotion trends            │  │
│  │     - Adds state transition history      │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│                 ▼                               │
│  ┌──────────────────────────────────────────┐  │
│  │  6. GPT-4 Negotiation Coaching          │  │
│  │     - Analyzes investor behavior         │  │
│  │     - Generates 1-2 sentence advice      │  │
│  │     - Tailored to current state          │  │
│  └──────────────┬───────────────────────────┘  │
│                 │ 300-500ms                     │
└─────────────────┼───────────────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  WebSocket      │ ← llm_context_update
         │  to Frontend    │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Overlay UI     │
         │  - State badge  │
         │  - Emotions     │
         │  - Coaching     │
         └─────────────────┘
```

### Time-Series Emotion Smoothing

BeneAI uses **Exponential Moving Average (EMA)** to smooth emotion scores over time:

```
EMA(t) = α × new_score + (1 - α) × EMA(t-1)

where α = 0.3 (30% weight to new data)
```

**Why EMA?**
- Reduces jitter from frame-to-frame variations
- Responds faster than simple moving average
- Better captures emotional transitions

**Example:**

```
Frame 1: Joy=0.9  → EMA_joy = 0.9
Frame 2: Joy=0.3  → EMA_joy = 0.3×0.3 + 0.7×0.9 = 0.72
Frame 3: Joy=0.4  → EMA_joy = 0.3×0.4 + 0.7×0.72 = 0.62
Frame 4: Joy=0.8  → EMA_joy = 0.3×0.8 + 0.7×0.62 = 0.67
```

### Investor State Mapping

Hume AI returns 48 emotions. We map these to 6 **investor states**:

| State | Color | Emoji | Key Emotions | User Goal |
|-------|-------|-------|--------------|-----------|
| **Interested** | 🟢 Green | 💚 | Joy, Interest, Excitement, Admiration | Keep going! |
| **Skeptical** | 🟡 Yellow | 🤔 | Contemplation, Doubt, Confusion (mild) | Address concerns |
| **Concerned** | 🟠 Orange | 😟 | Anxiety, Distress, Disapproval | Reassure immediately |
| **Confused** | 🔴 Red | 😕 | Confusion, Surprise (negative), Realization | Clarify point |
| **Bored** | 🔵 Blue | 😐 | Boredom, Tiredness, Distraction | Change approach |
| **Neutral** | ⚪ Gray | 😶 | Calmness, Concentration (low arousal) | Baseline state |

Mapping logic in `backend/app/prompts.py:get_investor_state()`.

---

## WebSocket API Reference

### Message Types: Client → Server

#### 1. `ping` - Heartbeat

```json
{
  "type": "ping",
  "timestamp": 1234567890
}
```

#### 2. `video_frame` - Send video frame for emotion detection

```json
{
  "type": "video_frame",
  "timestamp": 1234567890,
  "data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response:** `emotion_result` (see below)

#### 3. `audio_chunk` - Send audio for prosody analysis (optional)

```json
{
  "type": "audio_chunk",
  "timestamp": 1234567890,
  "data": "data:audio/webm;base64,GkXfo..."
}
```

**Response:** `prosody_result`

#### 4. `transcribed_text` - Send speech-to-text for language analysis

```json
{
  "type": "transcribed_text",
  "data": {
    "text": "I think this is a great opportunity",
    "timestamp": 1234567890,
    "start_time": 1234567880,
    "end_time": 1234567890,
    "words": [
      {"word": "I", "timestamp": 1234567880, "confidence": 0.99},
      {"word": "think", "timestamp": 1234567881, "confidence": 0.98}
    ]
  }
}
```

**Response:** `language_result`

#### 5. `disconnect` - Close connection

```json
{
  "type": "disconnect"
}
```

**Response:** `disconnect_ack`

---

### Message Types: Server → Client

#### 1. `connection` - Welcome message

```json
{
  "type": "connection",
  "status": "connected",
  "message": "Welcome to BeneAI coaching service",
  "server_version": "1.0.0",
  "timestamp": 1234567890
}
```

#### 2. `pong` - Heartbeat response

```json
{
  "type": "pong",
  "timestamp": 1234567890
}
```

#### 3. `emotion_result` - Emotion detection result

```json
{
  "type": "emotion_result",
  "detected": true,
  "emotion": "Joy",
  "confidence": 0.85,
  "investor_state": "interested",
  "top_emotions": [
    {"name": "Joy", "score": 0.85},
    {"name": "Interest", "score": 0.72},
    {"name": "Excitement", "score": 0.68}
  ],
  "all_emotions": {
    "Joy": 0.85,
    "Sadness": 0.02,
    "Anger": 0.01,
    ...
  },
  "face_bbox": {
    "x": 120,
    "y": 80,
    "width": 200,
    "height": 250
  },
  "timestamp": 1234567890,
  "service": "hume"
}
```

#### 4. `interval_complete` - 1-second interval aggregation

```json
{
  "type": "interval_complete",
  "interval": {
    "start_time": 1234567000,
    "end_time": 1234567001,
    "investor_state": "interested",
    "frames_analyzed": 3,
    "faces_detected": 3,
    "top_emotions": [
      {
        "name": "Joy",
        "ema_score": 0.82,
        "raw_score": 0.85,
        "trend": "increasing"
      },
      {
        "name": "Interest",
        "ema_score": 0.71,
        "raw_score": 0.72,
        "trend": "stable"
      }
    ],
    "words": ["great", "opportunity", "excited"],
    "speaking": true,
    "silence_duration": 0.0
  },
  "timestamp": 1234567890
}
```

**Trend values:** `"increasing"`, `"decreasing"`, `"stable"`

#### 5. `llm_context_update` - Coaching advice (every 4-5 seconds)

```json
{
  "type": "llm_context_update",
  "context": {
    "intervals": [ /* last 5 intervals */ ],
    "dominant_state": "interested",
    "state_duration": 4.5,
    "emotion_trends": {
      "Joy": "increasing",
      "Interest": "stable",
      "Confusion": "decreasing"
    },
    "speaking_ratio": 0.8,
    "total_words": 45
  },
  "formatted_text": "Last 5 seconds: Investor is 'interested'...",
  "coaching_advice": "Great momentum! The investor is highly engaged. Continue with your current approach and maintain this energy.",
  "investor_state": "interested",
  "state_emoji": "💚",
  "state_color": "#10b981",
  "timestamp": 1234567890
}
```

#### 6. `emotion_error` - Error detecting emotion

```json
{
  "type": "emotion_error",
  "message": "No face detected",
  "timestamp": 1234567890
}
```

#### 7. `error` - General error

```json
{
  "type": "error",
  "error_code": "INVALID_MESSAGE",
  "message": "Unknown message type: foo"
}
```

---

## Troubleshooting

### Issue: Backend won't start

**Error:** `ImportError: No module named 'fastapi'`

**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

---

### Issue: "Hume AI client failed to connect"

**Error in logs:** `WARNING: Hume AI client failed to connect`

**Solution:**
1. Check your `.env` file has valid `HUME_API_KEY`
2. Test Hume API key:
   ```bash
   curl -H "X-Hume-Api-Key: YOUR_KEY" https://api.hume.ai/v0/batch/jobs
   ```
3. Check Hume account quota (free tier limits)

---

### Issue: WebSocket connection refused

**Error:** `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution:**
1. Ensure backend is running: `ps aux | grep uvicorn`
2. Check port 8000 is not blocked:
   ```bash
   curl http://localhost:8000/
   ```
3. Check firewall settings

---

### Issue: Overlay not updating

**Symptoms:** Widget shows "Waiting..." forever

**Solution:**
1. Open browser DevTools → Console
2. Check for WebSocket connection errors
3. Verify backend URL in `overlay.html` (line 292)
4. Check backend logs for incoming messages
5. Test with webcam test page (see Test 5)

---

### Issue: "No face detected" errors

**Symptoms:** Backend logs show "No face detected" repeatedly

**Solution:**
1. Check lighting (face should be well-lit)
2. Ensure face is centered in frame
3. Check webcam is working (test with Photo Booth / Camera app)
4. Try different frame rate (adjust `HUME_FRAME_RATE` in `.env`)
5. Test with a photo:
   ```bash
   python backend/test_with_photo.py
   ```

---

### Issue: LLM not generating advice

**Symptoms:** No `llm_context_update` messages after 5 seconds

**Solution:**
1. Check OpenAI API key in `.env`
2. Check OpenAI account has credits:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_OPENAI_KEY"
   ```
3. Check backend logs for LLM errors
4. Verify at least 1 interval has completed (check logs for "Interval complete")

---

### Issue: High latency (>1 second)

**Symptoms:** Coaching advice feels delayed

**Solution:**
1. Reduce frame rate: `HUME_FRAME_RATE=2.0` (in `.env`)
2. Lower image quality in frontend:
   ```javascript
   const frameData = canvas.toDataURL('image/jpeg', 0.6); // was 0.8
   ```
3. Disable prosody/language if not needed:
   ```
   HUME_ENABLE_PROSODY=false
   HUME_ENABLE_LANGUAGE=false
   ```
4. Check network latency:
   ```bash
   ping api.hume.ai
   ping api.openai.com
   ```

---

### Issue: WebSocket disconnects randomly

**Symptoms:** Overlay shows "Disconnected" status

**Solution:**
1. Increase ping interval in `backend/app/config.py`:
   ```python
   websocket_ping_interval: int = 60  # was 30
   websocket_ping_timeout: int = 20   # was 10
   ```
2. Check for network instability
3. Add auto-reconnect in frontend (already implemented in `overlay.html`)

---

## Advanced: Production Deployment

### Deploy Backend to Google Cloud Run

```bash
# From backend/ directory
gcloud run deploy beneai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,HUME_API_KEY=$HUME_API_KEY
```

### Update Frontend for Production

Edit `frontend/overlay.html`:

```javascript
const BACKEND_URL = 'wss://beneai-backend-xxx.run.app/ws';
```

---

## Performance Benchmarks

Expected latencies (with good internet):

| Component | Latency |
|-----------|---------|
| Frame capture | 10-30ms |
| WebSocket send | 5-20ms |
| Hume AI face detection | 300-500ms |
| Interval aggregation | <5ms |
| LLM coaching generation | 500-800ms |
| WebSocket receive | 5-20ms |
| **Total (frame → emotion)** | **350-600ms** |
| **Total (context → advice)** | **550-900ms** |

---

## FAQ

**Q: Can I use this with Zoom/Google Meet/Teams?**

A: Yes! The system captures raw webcam feed, which works with any platform. For a Chrome extension version, see `extension/` directory (in development).

**Q: Does this work offline?**

A: No. Hume AI and OpenAI require internet. Future versions may support local models (MediaPipe + Llama).

**Q: How much does it cost to run?**

A: Approximately:
- Hume AI: Free tier (1000 requests/month) or $0.0001/frame
- OpenAI: ~$0.01 per coaching request (GPT-4-turbo)
- For a 30-min call: ~$0.50-$1.00 total

**Q: Can I customize the coaching prompts?**

A: Yes! Edit `backend/app/prompts.py` → `NEGOTIATION_COACHING_PROMPT`

**Q: Can I add custom investor states?**

A: Yes! Edit `backend/app/prompts.py` → `get_investor_state()` and add to `INVESTOR_STATE_EMOJI` / `INVESTOR_STATE_COLOR`

---

## Support

For issues, questions, or feedback:

1. Check troubleshooting section above
2. Review backend logs: `tail -f backend/logs/app.log`
3. Enable debug mode in `.env`: `LOG_LEVEL=debug`
4. Open GitHub issue with logs and error messages

---

**Happy Coaching!** 🚀

Built with ❤️ for better conversations.
