# Running and Testing Hume API Locally

This guide shows you how to install, configure, and test the Hume API integration on your local machine.

## Prerequisites

- Python 3.11+ installed
- Hume API key (get from https://platform.hume.ai/)
- Internet connection

---

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed hume-0.12.1 fastapi-0.104.1 uvicorn-0.24.0 ...
```

**If you see an error**, make sure you're using Python 3.11 or higher:
```bash
python --version  # Should show Python 3.11+
```

---

## Step 2: Get Hume API Key

1. Visit https://platform.hume.ai/
2. Sign up or log in
3. Go to **API Keys** section
4. Click **Create New Key**
5. Copy the key (format: `hume-xxxxx...`)

---

## Step 3: Configure Environment

Edit `backend/.env` and add your Hume API key:

```bash
# Add these lines to backend/.env

# Hume AI Configuration
HUME_API_KEY=your-actual-hume-api-key-here
HUME_ENABLE_FACE=true
HUME_ENABLE_PROSODY=true
HUME_ENABLE_LANGUAGE=true
HUME_USE_PRIMARY=true
```

**Important:** Replace `your-actual-hume-api-key-here` with your real key!

---

## Step 4: Test Hume Connection

Run the test script:

```bash
cd backend
python test_hume.py
```

### ✅ Expected Success Output

```
╔════════════════════════════════════════════════╗
║      Hume AI Integration Test Suite           ║
╚════════════════════════════════════════════════╝

=== Testing Hume AI Connection ===
✅ Successfully connected to Hume AI WebSocket
   - Facial Expression: Enabled
   - Speech Prosody: Enabled
   - Emotional Language: Enabled

=== Testing Investor State Mapping ===
✅ Skeptical scenario: skeptical
✅ Positive scenario: positive
✅ Evaluative scenario: evaluative
✅ Receptive scenario: receptive

=== Testing Emotional Language Analysis ===
Analyzing: "I'm really excited about this opportunity!"
✅ Language analysis successful (7 words)
   - "excited": Excitement (0.856)
   - "opportunity": Interest (0.623)
   ...
```

### ❌ Common Errors and Fixes

**Error: `No module named 'hume'`**
```
Fix: pip install -r requirements.txt
```

**Error: `HUME_API_KEY not set`**
```
Fix: Add HUME_API_KEY to backend/.env file
```

**Error: `Failed to connect to Hume AI`**
```
Fixes:
1. Check API key is valid
2. Check internet connection
3. Verify Hume API status: https://status.hume.ai/
```

---

## Step 5: Start Backend Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Starting BeneAI backend...
INFO:     Hume AI client ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Step 6: Test WebSocket Connection

### Method 1: Browser Health Check

Open browser to: **http://localhost:8000**

Expected JSON response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "active_connections": 0,
  "services": {
    "luxand": true,
    "hume": true,     ← Should be true!
    "openai": true
  }
}
```

### Method 2: cURL Test

```bash
curl http://localhost:8000
```

### Method 3: WebSocket Test (Advanced)

You can use a WebSocket client like **Postman** or **wscat**:

**Install wscat:**
```bash
npm install -g wscat
```

**Connect to WebSocket:**
```bash
wscat -c ws://localhost:8000/ws
```

**Send test message (after connecting):**
```json
{"type":"ping"}
```

**Expected response:**
```json
{"type":"pong","timestamp":1234567890}
```

---

## Step 7: Test with Frontend

### Terminal 1: Backend (already running)
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Terminal 2: Frontend Server
```bash
cd frontend
python -m http.server 8080
```

### Browser
1. Open: **http://localhost:8080**
2. Click **"Start Session"**
3. Allow camera/microphone access
4. You should see:
   - Video feed from your webcam
   - Real-time emotion detection
   - Investor state changes (skeptical/positive/etc.)
   - AI coaching advice

---

## Understanding the WebSocket Messages

### 1. Video Frame Analysis (Hume Facial Expression)

**Client → Server:**
```json
{
  "type": "video_frame",
  "data": "base64_encoded_image..."
}
```

**Server → Client:**
```json
{
  "type": "emotion_result",
  "detected": true,
  "emotion": "Admiration",
  "confidence": 0.78,
  "investor_state": "positive",
  "top_emotions": [
    {"name": "Admiration", "score": 0.78},
    {"name": "Interest", "score": 0.65},
    {"name": "Concentration", "score": 0.52}
  ],
  "service": "hume",
  "timestamp": 1234567890
}
```

### 2. Audio Analysis (Hume Prosody) - Optional

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio..."
}
```

**Server → Client:**
```json
{
  "type": "prosody_result",
  "primary_emotion": "Excitement",
  "confidence": 0.82,
  "top_emotions": [...]
}
```

### 3. Text Analysis (Hume Language) - Optional

**Client → Server:**
```json
{
  "type": "transcribed_text",
  "data": "I think this is a great opportunity"
}
```

**Server → Client:**
```json
{
  "type": "language_result",
  "text": "I think this is a great opportunity",
  "predictions": [
    {
      "text": "great",
      "primary_emotion": "Admiration",
      "confidence": 0.74
    }
  ]
}
```

---

## Hume vs Luxand

Your backend now has **TWO** emotion detection services:

### Configuration

**Use Hume as primary (recommended):**
```bash
HUME_USE_PRIMARY=true   # Hume first, Luxand as fallback
```

**Use Luxand as primary:**
```bash
HUME_USE_PRIMARY=false  # Luxand first, Hume as fallback
```

### Comparison

| Feature | Luxand | Hume |
|---------|--------|------|
| Emotions | 7 basic | **53 granular** |
| Modalities | Face only | Face + Voice + Text |
| Examples | happiness, sad | Admiration, Concentration, Triumph |
| Best for | Quick/simple | **Detailed investor analysis** |

---

## Troubleshooting

### Backend won't start

**Problem:** `ModuleNotFoundError: No module named 'hume'`

**Fix:**
```bash
cd backend
pip install -r requirements.txt
```

### Hume shows as disconnected

**Problem:** Health check shows `"hume": false`

**Fixes:**
1. Check `HUME_API_KEY` in `.env`
2. Restart backend server
3. Check logs for connection errors
4. Verify API key is valid at https://platform.hume.ai/

### Slow performance

**Problem:** Emotion detection is laggy

**Fixes:**
1. Reduce frame rate in `.env`:
   ```bash
   HUME_FRAME_RATE=2.0  # Lower = faster but less frequent
   ```
2. Disable unused models:
   ```bash
   HUME_ENABLE_PROSODY=false
   HUME_ENABLE_LANGUAGE=false
   ```

### No emotions detected

**Problem:** `No face detected` messages

**Fixes:**
1. Ensure good lighting (not too dark)
2. Face camera directly
3. Check video feed is working in frontend
4. Test with Luxand first (`HUME_USE_PRIMARY=false`)

---

## Next Steps

### ✅ You've successfully set up Hume AI!

Now you can:

1. **Test different emotions:**
   - Smile → Should detect "Joy", "Admiration"
   - Frown → Should detect "Sadness", "Disapproval"
   - Thinking → Should detect "Concentration", "Contemplation"

2. **Integrate with frontend:**
   - Update Chrome extension to use new emotion data
   - Leverage 53 emotions for better coaching

3. **Optimize prompts:**
   - Update `backend/app/prompts.py` to use granular emotions
   - Better investor state coaching

4. **Deploy to production:**
   - Push to Cloud Run with Hume enabled
   - Monitor API usage and costs

---

## Quick Command Reference

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Test Hume connection
python test_hume.py

# Start backend
uvicorn main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && python -m http.server 8080

# Check health
curl http://localhost:8000

# View logs
# Watch the terminal where uvicorn is running
```

---

## Support

- **Hume Docs:** https://dev.hume.ai/docs
- **Hume Status:** https://status.hume.ai/
- **BeneAI Docs:** See `HUME_SETUP.md` for detailed guide

**Happy testing! 🚀**
