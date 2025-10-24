# BeneAI Quick Start Guide

## How to Run the Working System

### Option 1: Using `start_demo.sh` (Recommended)

This is the **only working method** right now.

```bash
# From project root
./start_demo.sh
```

This script will:
1. Start backend on `http://localhost:8000`
2. Start frontend on `http://localhost:8080`
3. Open your browser to `http://localhost:8080`

### Option 2: Manual Start

```bash
# Terminal 1: Start backend
cd backend
python main.py

# Terminal 2: Start frontend
cd frontend
python3 -m http.server 8080

# Browser: Open http://localhost:8080
```

---

## When You Press "Start Session" - What Happens?

**YES, you WILL be gathering data!** Here's the exact flow:

### 1. Initialization (1-2 seconds)
- ✅ **Webcam starts** → Requests camera permission
- ✅ **Video processor initializes** → Loads MediaPipe Face Mesh
- ✅ **Audio analyzer starts** → Initializes Web Speech API
- ✅ **WebSocket connects** → Connects to `ws://localhost:8000/ws`

### 2. Data Collection Begins (Continuous)
- 📹 **Video frames captured** at 30 FPS → Throttled to 3 FPS
- 📤 **Frames sent to backend** via WebSocket (Base64 JPEG, ~60KB each)
- 🤖 **Hume AI analyzes emotions** → Returns 48 emotion scores
- 🎯 **Investor state mapped** → skeptical/evaluative/receptive/positive/neutral
- 📊 **1-second intervals aggregated** → EMA smoothing applied
- 🗣️ **Speech transcribed** → Web Speech API converts audio to text
- 💾 **Buffered for 5 seconds** → Rolling window maintained
- 🧠 **GPT-4 generates coaching** → Every 4.5 seconds
- 💬 **Advice displayed** → Updates UI in real-time

### 3. What You'll See

**In the UI:**
- **Emotion label** → Shows current investor state (e.g., "Receptive")
- **Confidence bar** → Shows Hume AI detection confidence
- **Speech metrics** → Words/min, filler words, pause frequency
- **AI Coaching** → Real-time advice from GPT-4

**In the console (if you open DevTools):**
```
Connected to BeneAI backend
Received: connection
Welcome: Welcome to BeneAI coaching service
Video frame sent
Emotion detected: receptive (Joy: 0.85)
Interval complete: receptive, 3 frames analyzed
LLM coaching: "Great momentum! Investor is engaged..."
```

---

## What Data Is Being Collected?

### Sent to Backend:
1. **Video frames** (Base64 JPEG, 3 FPS)
2. **Transcribed speech** (text only, no audio files)
3. **Speech metrics** (WPM, filler words, pause frequency)

### Processed by Backend:
1. **Hume AI emotion analysis** → 48 emotion scores
2. **Investor state** → One of 6 states
3. **1-second intervals** → Aggregated with EMA smoothing
4. **5-second buffer** → Rolling window for LLM context
5. **GPT-4 coaching advice** → Generated every 4.5 seconds

### Displayed in UI:
1. **Current investor state** (e.g., "Receptive")
2. **Top 3 emotions** with trend arrows (↑↓→)
3. **Speech metrics** (WPM, filler words, pauses)
4. **Coaching advice** (1-2 sentences from GPT-4)

---

## Testing the Pipeline

### Quick Test (30 seconds)

1. Run `./start_demo.sh`
2. Open `http://localhost:8080`
3. Click **"Start Session"**
4. Allow camera and microphone access
5. Look at the camera and say something like:
   > "I think this is a great opportunity for growth"
6. Watch the UI update:
   - Emotion should show "Receptive" or "Positive"
   - Speech metrics should update
   - After 5 seconds, coaching advice appears

### Expected Behavior

**Immediate (0-1 seconds):**
- Webcam video appears
- Status shows "Active - Analyzing..."

**Within 1 second:**
- Emotion label updates (based on your facial expression)
- Confidence bar shows detection quality

**Within 5 seconds:**
- Speech metrics update (if you're speaking)
- Top emotions appear with trend arrows

**At 5 seconds:**
- First coaching advice appears
- Should say something relevant to your facial expression/speech

**Every 4.5 seconds after:**
- New coaching advice updates

---

## Troubleshooting

### "Failed to initialize audio"
- Grant microphone permission in browser
- Check browser console for errors

### "Connection failed" or "WebSocket error"
- Ensure backend is running: `curl http://localhost:8000/`
- Check `.env` file has `OPENAI_API_KEY` and `HUME_API_KEY`

### "No face detected"
- Ensure good lighting
- Face should be centered in camera
- Try moving closer to camera

### No coaching advice after 5 seconds
- Check backend logs for errors
- Verify OpenAI API key is valid
- Ensure at least one interval completed (check console logs)

---

## File Organization

```
BeneAI/
├── README.md                    # Project overview
├── USAGE_GUIDE.md              # Comprehensive usage guide (setup, testing, API)
├── DATA_FLOW.md                # Technical data flow documentation
├── EMOTION_TIMESERIES.md       # Time-series emotion system docs
├── QUICK_START.md              # This file (quick start)
├── start_demo.sh               # Demo startup script (WORKING)
│
├── frontend/
│   ├── index.html              # Main UI (press "Start Session" here)
│   ├── overlay.html            # Standalone overlay widget
│   ├── js/
│   │   ├── app.js              # Main application logic
│   │   ├── video-processor.js  # Video frame capture
│   │   ├── audio-analyzer.js   # Speech analysis
│   │   ├── websocket-client.js # Backend communication
│   │   └── config.js           # Configuration
│   └── css/
│       └── styles.css          # UI styles
│
├── backend/
│   ├── main.py                 # FastAPI + WebSocket server
│   ├── app/
│   │   ├── llm.py              # OpenAI GPT-4 integration
│   │   ├── hume_client.py      # Hume AI emotion detection
│   │   ├── interval_aggregator.py   # 1-second intervals
│   │   ├── timeseries_buffer.py     # 5-second buffer
│   │   ├── speech_mapper.py         # Speech-to-text alignment
│   │   ├── llm_context_builder.py   # LLM context formatting
│   │   └── prompts.py          # GPT-4 prompts
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # API keys (OPENAI_API_KEY, HUME_API_KEY)
```

---

## Next Steps

1. **Test the system:** Run `./start_demo.sh` and press "Start Session"
2. **Read technical docs:** Check `DATA_FLOW.md` for complete pipeline
3. **Understand the system:** Read `EMOTION_TIMESERIES.md` for design decisions
4. **Deploy (optional):** See `USAGE_GUIDE.md` for Cloud Run deployment

---

**Questions?** Check the other MD files or open an issue on GitHub.

**Pro tip:** Open DevTools Console (F12) to see real-time logs of data flowing through the system!
