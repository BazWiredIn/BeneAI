# BeneAI System Architecture

## Overview

BeneAI is a real-time AI-powered video call coaching system that analyzes facial expressions, speech patterns, and emotional tone to provide actionable advice during high-stakes meetings.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Chrome Extension                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Content Script (injected into video call page)          │  │
│  │  ┌────────────────┐  ┌─────────────────┐                │  │
│  │  │  Video Stream  │  │  Audio Stream   │                │  │
│  │  │   (WebRTC)     │  │   (WebRTC)      │                │  │
│  │  └───────┬────────┘  └────────┬────────┘                │  │
│  │          │                     │                          │  │
│  │          ▼                     ▼                          │  │
│  │  ┌────────────────┐  ┌─────────────────┐                │  │
│  │  │   MediaPipe    │  │  Web Audio API  │                │  │
│  │  │   Face Mesh    │  │  + Speech API   │                │  │
│  │  │  (468 points)  │  │                 │                │  │
│  │  └───────┬────────┘  └────────┬────────┘                │  │
│  │          │                     │                          │  │
│  │          ▼                     ▼                          │  │
│  │  ┌────────────────┐  ┌─────────────────┐                │  │
│  │  │    Emotion     │  │  Pacing/Tone    │                │  │
│  │  │   Detection    │  │   Analysis      │                │  │
│  │  │ (Rule-based)   │  │ (words/min,     │                │  │
│  │  │                │  │  pauses, etc)   │                │  │
│  │  └───────┬────────┘  └────────┬────────┘                │  │
│  │          │                     │                          │  │
│  │          └──────────┬──────────┘                          │  │
│  │                     ▼                                     │  │
│  │          ┌────────────────────┐                          │  │
│  │          │  Parameter Fusion  │                          │  │
│  │          │  (Aggregate data)  │                          │  │
│  │          └─────────┬──────────┘                          │  │
│  └────────────────────┼───────────────────────────────────┘  │
│                       │                                       │
│                       ▼                                       │
│            ┌────────────────────┐                            │
│            │  WebSocket Client  │                            │
│            └──────────┬─────────┘                            │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ WebSocket (wss://)
                        │ JSON Messages
                        │
┌───────────────────────┼───────────────────────────────────────┐
│                       ▼                                       │
│              Google Cloud Run                                 │
│            ┌────────────────────┐                            │
│            │  FastAPI Backend   │                            │
│            │  WebSocket Handler │                            │
│            └──────────┬─────────┘                            │
│                       │                                       │
│                       ▼                                       │
│            ┌────────────────────┐                            │
│            │   Request Queue    │                            │
│            │  (Batch & Cache)   │                            │
│            └──────────┬─────────┘                            │
│                       │                                       │
│                       ▼                                       │
│            ┌────────────────────┐                            │
│            │   LLM Integration  │                            │
│            │   (GPT-4 Turbo)    │                            │
│            └──────────┬─────────┘                            │
│                       │                                       │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ HTTPS API Call
                        │ Streaming Response
                        │
                        ▼
              ┌──────────────────┐
              │   OpenAI API     │
              │   GPT-4 Turbo    │
              └──────────┬───────┘
                        │
                        │ Streaming tokens
                        │
┌───────────────────────┼───────────────────────────────────────┐
│                       ▼                                       │
│              Google Cloud Run                                 │
│            ┌────────────────────┐                            │
│            │  Stream Response   │                            │
│            │   Back to Client   │                            │
│            └──────────┬─────────┘                            │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        │ WebSocket
                        │ Streaming advice
                        │
┌───────────────────────┼───────────────────────────────────────┐
│                       ▼                                       │
│                Chrome Extension                               │
│            ┌────────────────────┐                            │
│            │   Overlay UI       │                            │
│            │   - Corner widget  │                            │
│            │   - Advice panel   │                            │
│            │   - Real-time text │                            │
│            └────────────────────┘                            │
└───────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Chrome Extension (Client-Side)

#### Video Analysis (`extension/analysis/video-analyzer.js`)
- **Input:** Video stream from `chrome.tabCapture` API
- **Processing:**
  - Capture video frames at 5-10 fps (reduced for performance)
  - Pass to MediaPipe Face Mesh for landmark detection
  - Extract 468 3D facial landmarks
- **Output:** Landmark coordinates array

#### Emotion Detection (`extension/analysis/emotion-detector.js`)
- **Input:** Facial landmarks from MediaPipe
- **Processing:** Rule-based emotion detection using Action Units (AU)
  - **Smile Detection:** Mouth corner points (landmarks 61, 291) rise
  - **Frown Detection:** Mouth corner points drop, center drops (landmark 13)
  - **Surprise:** Eyebrows rise (landmarks 70, 300), eyes widen
  - **Neutral:** Default state when no strong signals
- **Output:** Emotion label (positive, negative, neutral, surprised, concerned)

#### Audio Analysis (`extension/analysis/audio-analyzer.js`)
- **Input:** Audio stream from `chrome.tabCapture` API
- **Processing:**
  - **Web Audio API:** Analyze volume, frequency, speech/silence detection
  - **Web Speech API:** Real-time speech-to-text transcription
  - **Metrics Calculation:**
    - Words per minute (from transcript)
    - Pause frequency (silence detection)
    - Filler words count ("um", "uh", "like", "you know")
    - Volume/energy levels
- **Output:** Speech metrics object

#### Parameter Fusion (`content.js`)
- **Input:** Emotion labels + Speech metrics
- **Processing:**
  - Aggregate data every 2-3 seconds
  - Create payload with timestamp
  - Handle missing/incomplete data gracefully
- **Output:** JSON payload sent via WebSocket

```javascript
// Example payload structure
{
  "timestamp": 1697745123456,
  "emotion": "concerned",
  "speech": {
    "wordsPerMinute": 180,
    "pauseFrequency": 0.15,
    "fillerWordCount": 3,
    "volumeLevel": 0.7,
    "recentTranscript": "um, so I think we should, like, consider..."
  }
}
```

#### WebSocket Client (`extension/utils/websocket.js`)
- **Connection:** Establish wss:// connection to Cloud Run backend
- **Send:** Parameter updates every 2-3 seconds
- **Receive:** Streaming advice from LLM
- **Error Handling:** Reconnect logic, fallback to cached advice

#### Overlay UI (`overlay.js`, `overlay.html`, `overlay.css`)
- **Corner Widget:** Compact indicator showing current state
  - Color-coded emotion (green=positive, yellow=neutral, red=concerned)
  - Icon representation
  - Click to expand
- **Advice Panel:** Expandable card with real-time suggestions
  - Streams text word-by-word as received from backend
  - Auto-hides after 10 seconds of no updates
  - Minimalist design to avoid distraction

### 2. Backend (Cloud Run)

#### FastAPI Application (`backend/main.py`)
- **Framework:** FastAPI with WebSocket support
- **Endpoints:**
  - `GET /`: Health check
  - `GET /ws`: WebSocket connection for real-time communication
- **Architecture:** Asynchronous event-driven

#### WebSocket Handler
- **Connection Management:** Track active connections
- **Message Parsing:** Validate incoming JSON payloads
- **Rate Limiting:** Prevent abuse (max 10 messages/second per client)
- **Error Handling:** Graceful degradation, send error messages to client

#### LLM Integration (`backend/llm.py`)
- **Provider:** OpenAI GPT-4-turbo
- **Mode:** Streaming responses
- **Implementation:**
  ```python
  async def get_coaching_advice(parameters):
      prompt = build_prompt(parameters)
      stream = openai.ChatCompletion.create(
          model="gpt-4-turbo",
          messages=[
              {"role": "system", "content": SYSTEM_PROMPT},
              {"role": "user", "content": prompt}
          ],
          stream=True
      )
      async for chunk in stream:
          yield chunk.choices[0].delta.content
  ```
- **Streaming:** Forward tokens to client in real-time via WebSocket

#### Prompt Engineering (`backend/prompts.py`)
- **System Prompt:** Define AI role as executive coach
- **User Prompt Template:**
  ```
  Current Situation:
  - Emotional state: {emotion}
  - Speech pace: {wpm} words/min (target: 120-150)
  - Filler words: {filler_count} in last 30 seconds
  - Pauses: {pause_freq} (target: 0.2-0.3)

  Provide ONE specific, actionable coaching tip (max 20 words).
  Focus on: {focus_area}
  ```
- **Focus Areas:** Rotate between emotional tone, pacing, clarity

#### Caching (`backend/cache.py`)
- **In-Memory Cache:** Store recent responses
- **Cache Key:** Hash of (emotion, speech_metrics)
- **TTL:** 5 minutes
- **Purpose:** Reduce OpenAI API calls for similar scenarios (save cost, reduce latency)

### 3. Data Flow

#### Happy Path (Normal Operation)

1. **Capture (0ms):** Extension captures video/audio from active call
2. **Video Processing (30-50ms):** MediaPipe detects facial landmarks
3. **Emotion Detection (10-20ms):** Rule-based classification
4. **Audio Processing (100-200ms):** Speech recognition + analysis
5. **Aggregation (10ms):** Combine parameters into JSON payload
6. **Send to Backend (20-50ms):** WebSocket message transmission
7. **Backend Processing (10ms):** Parse, validate, check cache
8. **LLM Request (300-500ms):** GPT-4 generates first token
9. **Stream Response (ongoing):** Tokens streamed back every 50-100ms
10. **UI Update (16ms):** Display advice in overlay, one word at a time

**Total Latency (to first word):** ~480-840ms
**Target:** <1000ms (achieved ✓)

#### Edge Cases

**No Face Detected:**
- Skip emotion analysis for this frame
- Send last known emotion state
- If >10 seconds with no face, send "disengaged" state

**Poor Audio Quality:**
- Increase volume threshold for speech detection
- Fallback to volume-only analysis (skip STT)

**Backend Unavailable:**
- Display cached advice based on state
- Show "Reconnecting..." indicator
- Store parameters locally, send batch when reconnected

**OpenAI Rate Limit:**
- Return cached response for similar state
- Fallback to rule-based advice (no LLM)
- Display error to user if persistent

## Technology Choices

### Why Chrome Extension?
- **Lowest Latency:** Direct access to video/audio streams via `tabCapture`
- **Platform Agnostic:** Works on any WebRTC-based platform (Meet, Zoom, Teams)
- **User Experience:** Seamless overlay on video call page

### Why MediaPipe?
- **On-Device:** Privacy-friendly, no server upload of video
- **Fast:** ~30ms per frame on modern hardware
- **Accurate:** 468 landmarks > sufficient for emotion detection
- **Browser Native:** Runs via WebAssembly, no installation

### Why Web Speech API?
- **Free:** No API costs
- **Fast:** ~100-200ms latency
- **Good Enough:** 80-90% accuracy sufficient for pacing analysis

### Why FastAPI + Cloud Run?
- **Fast Development:** FastAPI is quickest Python framework
- **WebSocket Support:** Built-in, easy to implement
- **Serverless:** No infrastructure management
- **Auto-Scaling:** Handles variable load
- **Cost:** Free tier covers development, minimal cost for demo

### Why GPT-4 Turbo?
- **Quality:** Best-in-class advice generation
- **Streaming:** Word-by-word display feels faster
- **Context Understanding:** Handles nuanced coaching scenarios
- **Cost:** ~$0.01 per request, acceptable for hackathon

## Performance Optimizations

### Client-Side
1. **Frame Rate Reduction:** Process 5-10 fps instead of 30fps (3-6x speedup)
2. **Skip Frames:** Only process every 3rd frame (negligible UX impact)
3. **Lazy Loading:** Load MediaPipe only when call detected
4. **Web Worker:** Run analysis in separate thread (avoid blocking UI)

### Server-Side
1. **Connection Pooling:** Maintain warm connection to OpenAI
2. **Caching:** Store responses for similar states (50% cache hit rate expected)
3. **Batching:** Aggregate rapid updates (send max 1 request per 2 seconds)
4. **Min Instances:** Set to 1 during demo to eliminate cold starts

### Network
1. **WebSocket:** Persistent connection avoids TCP handshake overhead
2. **Compression:** gzip compress JSON payloads (70% size reduction)
3. **Binary Protocol:** Consider MessagePack instead of JSON (future optimization)

## Security & Privacy

### What Leaves the Browser
- ✅ Aggregated metrics (emotion label, speech stats)
- ✅ Transcript text (last 30 seconds only)
- ✅ Anonymized (no user ID, no session ID for hackathon)

### What Stays Local
- ✅ Raw video frames (never uploaded)
- ✅ Raw audio (never uploaded)
- ✅ Facial landmarks (processed locally)

### Data Retention
- **Client:** No storage (all in-memory)
- **Server:** No database (all in-memory cache, cleared on restart)
- **OpenAI:** Per their policy (request deletion after hackathon)

## Scalability Considerations (Post-Hackathon)

### Current Limits (MVP)
- **Concurrent Users:** ~100 (Cloud Run default)
- **Requests/Second:** ~50 per instance
- **OpenAI Rate Limit:** Tier 2 = 10,000 requests/minute

### Future Scaling
1. **Database:** Add PostgreSQL/Firestore for user sessions
2. **Redis:** Distributed cache across instances
3. **Load Balancer:** Multiple Cloud Run regions
4. **WebSocket Gateway:** Dedicated WebSocket server (not FastAPI)
5. **LLM Optimization:** Fine-tuned smaller model (reduce cost by 90%)

## Monitoring & Debugging

### Metrics to Track
- **Latency:** Time from capture → advice display
- **Error Rate:** Failed WebSocket connections, API errors
- **Cache Hit Rate:** % of requests served from cache
- **API Cost:** OpenAI usage per day

### Logging
- **Client:** `console.log` with levels (debug, info, warn, error)
- **Server:** Structured logging (JSON format) to Cloud Run logs
- **Errors:** Sentry integration (future)

## Testing Strategy

### Unit Tests
- Emotion detection logic (given landmarks, assert emotion)
- Speech metrics calculation (given transcript, assert WPM)
- Prompt generation (given params, assert prompt format)

### Integration Tests
- WebSocket connection (can connect, send, receive)
- End-to-end (mock video/audio → receive advice)

### Manual Testing
- **Daily:** Test on real Google Meet call
- **Browser Testing:** Chrome only (Firefox future)
- **Performance:** Monitor latency with network throttling

## Deployment

### Extension
```bash
cd extension
zip -r beneai-extension.zip .
# Manual install via chrome://extensions
```

### Backend
```bash
cd backend
gcloud run deploy beneai-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 1 \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY
```

## Future Enhancements (Post-Hackathon)

1. **Multi-Person Detection:** Track all participants, not just user
2. **Historical Analysis:** Show trends over time
3. **Custom Coaching:** User-defined coaching goals
4. **Integrations:** Slack notifications, calendar integration
5. **Mobile App:** iOS/Android for viewing advice on phone
6. **Advanced Emotions:** Fear, anger, contempt (requires ML model)
7. **Voice Emotion:** Train model on audio features (Meyda.js features)
8. **Local LLM:** Run Llama 3 locally for privacy-conscious users
