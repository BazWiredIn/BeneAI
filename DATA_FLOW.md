# BeneAI Data Flow: Frames & Audio → Coaching Advice

**Complete Technical Documentation of the Real-Time Pipeline**

This document traces the exact path of data from video frames and audio input through emotion detection, aggregation, time-series buffering, LLM processing, and finally to actionable coaching advice in the UI.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Stage 1: Video Frame Capture](#stage-1-video-frame-capture)
3. [Stage 2: Hume AI Emotion Detection](#stage-2-hume-ai-emotion-detection)
4. [Stage 3: Investor State Mapping](#stage-3-investor-state-mapping)
5. [Stage 4: 1-Second Interval Aggregation](#stage-4-1-second-interval-aggregation)
6. [Stage 5: Speech-to-Text Integration](#stage-5-speech-to-text-integration)
7. [Stage 6: 5-Second Time-Series Buffering](#stage-6-5-second-time-series-buffering)
8. [Stage 7: LLM Context Building](#stage-7-llm-context-building)
9. [Stage 8: GPT-4 Coaching Generation](#stage-8-gpt-4-coaching-generation)
10. [Stage 9: UI Overlay Display](#stage-9-ui-overlay-display)
11. [Complete Example Flow](#complete-example-flow)
12. [Data Structures Reference](#data-structures-reference)
13. [Performance Metrics](#performance-metrics)

---

## High-Level Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW PIPELINE                          │
└───────────────────────────────────────────────────────────────────────┘

📹 Video Frame (30 FPS)
    │
    ├─► [Throttle to 3 FPS] ──────────────────────────────────┐
    │                                                           │
    ▼                                                           │
🌐 WebSocket Send (Base64 JPEG)                                │
    │ ~10-20ms                                                  │
    ▼                                                           │
🤖 Hume AI Face Detection                                       │
    │ ~300-500ms                                                │
    │ ↳ Returns: 48 emotions + bounding box                    │
    ▼                                                           │
🎯 Investor State Mapping (48 → 6 states)                       │
    │ <1ms                                                      │
    │ ↳ Produces: skeptical/evaluative/receptive/positive      │
    ▼                                                           │
📊 Interval Aggregator (EMA smoothing)                          │
    │ Collects ~3 frames → 1-second interval                   │
    │ <5ms per frame                                            │
    │                                                           │
    │ ◄─────────────────────────────────────────────────────────┤
    │                                                           │
    │ 🎤 Speech-to-Text (Web Speech API)                       │
    │     │ Continuous recognition                              │
    │     ▼                                                      │
    │ 🗣️ SpeechMapper (word timestamps)                        │
    │     │ Maps words to intervals                             │
    │     ▼                                                      │
    └──► Enriched Interval                                      │
         │ {emotions, state, words, flags}                      │
         │ Every 1.0 second                                     │
         ▼                                                       │
    ⏰ TimeSeriesBuffer (rolling 5-second window)               │
         │ Stores last 5 intervals                              │
         │ Triggers LLM every 4.5 seconds                       │
         ▼                                                       │
    📝 LLM Context Builder                                       │
         │ Formats intervals + trends + patterns                │
         │ <5ms                                                  │
         ▼                                                       │
    🧠 GPT-4 Coaching (OpenAI API)                               │
         │ Negotiation coach prompt                             │
         │ ~500-800ms                                            │
         │ ↳ Returns: 1-2 sentence advice                       │
         ▼                                                       │
    💬 WebSocket Send to Frontend                                │
         │ ~5-20ms                                               │
         ▼                                                       │
    🎨 Overlay UI Update                                         │
         │ Display: state badge + emotions + advice             │
         │ <5ms render                                           │
         ▼                                                       │
    ✅ USER SEES COACHING ADVICE
```

**Total Latency Breakdown:**
- Frame → Emotion Result: **~350-600ms**
- Context → Coaching Advice: **~550-900ms**
- **Overall:** User sees advice 4-5 seconds after emotional state emerges

---

## Stage 1: Video Frame Capture

### Frontend: JavaScript WebRTC

**Location:** `frontend/test-webcam.html` or Chrome Extension

```javascript
// Capture from webcam
const video = document.getElementById('video');
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

// Set canvas size
canvas.width = 640;
canvas.height = 480;

// Capture loop (throttled to 3 FPS for Hume AI)
setInterval(() => {
    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, 640, 480);

    // Convert to JPEG base64 (quality: 0.8 = ~60KB per frame)
    const frameData = canvas.toDataURL('image/jpeg', 0.8);

    // Send to backend via WebSocket
    ws.sendVideoFrame(frameData);
}, 333); // ~3 FPS (every 333ms)
```

**Output Format:**
```javascript
{
  "type": "video_frame",
  "timestamp": 1234567890123,
  "data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Key Parameters:**
- **Resolution:** 640×480 (VGA, good balance for face detection)
- **Format:** JPEG (efficient compression)
- **Quality:** 0.8 (reduces size while maintaining emotion clarity)
- **Frame Rate:** 3 FPS (matches `HUME_FRAME_RATE` in config)
- **Typical Size:** 40-80 KB per frame

---

## Stage 2: Hume AI Emotion Detection

### Backend: WebSocket Handler

**Location:** `backend/main.py:333` → `handle_video_frame()`

```python
async def handle_video_frame(client_id: str, frame_data: str):
    """Handle incoming video frame for emotion detection"""

    # 1. Frame rate throttling
    current_time = time.time()
    connection = manager.active_connections.get(client_id)
    last_frame_time = connection["last_frame_time"]

    min_interval = 1.0 / settings.hume_frame_rate  # 1/3 = 0.333s

    if current_time - last_frame_time < min_interval:
        logger.debug("Skipping frame (throttling)")
        return  # Drop frame

    connection["last_frame_time"] = current_time

    # 2. Send to Hume AI
    hume = await get_hume_client()
    emotion_data = await hume.analyze_face(frame_data)

    # 3. Process response
    if not emotion_data or not emotion_data.get("primary_emotion"):
        # No face detected
        await manager.send_message(client_id, {
            "type": "emotion_result",
            "detected": False,
            "message": "No face detected"
        })
        return

    # 4. Send result to client
    await manager.send_message(client_id, {
        "type": "emotion_result",
        "detected": True,
        "emotion": emotion_data["primary_emotion"],
        "confidence": emotion_data["confidence"],
        "all_emotions": emotion_data["all_emotions"],  # All 48 emotions
        "investor_state": emotion_data["investor_state"],
        "top_emotions": emotion_data.get("top_emotions", []),
        "face_bbox": emotion_data.get("face_bbox"),
        "timestamp": int(time.time() * 1000),
        "service": "hume"
    })
```

**Hume AI Response Format:**

```python
{
    "primary_emotion": "Joy",
    "confidence": 0.847,
    "all_emotions": {
        "Admiration": 0.234,
        "Adoration": 0.123,
        "Amusement": 0.456,
        "Anxiety": 0.089,
        "Awe": 0.178,
        "Awkwardness": 0.045,
        "Boredom": 0.023,
        "Calmness": 0.567,
        "Concentration": 0.723,
        "Confusion": 0.034,
        "Contemplation": 0.512,
        "Contempt": 0.012,
        "Contentment": 0.689,
        "Craving": 0.056,
        "Determination": 0.678,
        "Disappointment": 0.028,
        "Disapproval": 0.019,
        "Disgust": 0.007,
        "Distress": 0.015,
        "Doubt": 0.082,
        "Ecstasy": 0.134,
        "Embarrassment": 0.021,
        "Empathic Pain": 0.011,
        "Entrancement": 0.089,
        "Envy": 0.004,
        "Excitement": 0.712,
        "Fear": 0.018,
        "Guilt": 0.009,
        "Horror": 0.003,
        "Interest": 0.789,
        "Joy": 0.847,
        "Love": 0.234,
        "Nostalgia": 0.045,
        "Pain": 0.006,
        "Pride": 0.456,
        "Realization": 0.123,
        "Relief": 0.234,
        "Romance": 0.067,
        "Sadness": 0.019,
        "Sarcasm": 0.034,
        "Satisfaction": 0.678,
        "Desire": 0.089,
        "Shame": 0.008,
        "Surprise (negative)": 0.045,
        "Surprise (positive)": 0.234,
        "Sympathy": 0.156,
        "Tiredness": 0.067,
        "Triumph": 0.345
    },
    "top_emotions": [
        {"name": "Joy", "score": 0.847},
        {"name": "Interest", "score": 0.789},
        {"name": "Concentration", "score": 0.723}
    ],
    "investor_state": "receptive",  # ← See Stage 3
    "face_bbox": {
        "x": 120,
        "y": 80,
        "width": 200,
        "height": 250
    }
}
```

---

## Stage 3: Investor State Mapping

### Backend: Emotion → Investor State

**Location:** `backend/app/prompts.py` → `get_investor_state()` (implied)

Hume AI returns 48 emotions. We map these to **6 investor states** for clarity:

| Investor State | Color | Emoji | Key Emotions (High Scores) | Interpretation |
|----------------|-------|-------|----------------------------|----------------|
| **positive** | 🟢 Green | 💚 | Joy, Excitement, Interest, Admiration, Pride | Investor is excited, approving |
| **receptive** | 🟢 Green | 🤝 | Interest, Concentration, Contemplation, Satisfaction | Investor is engaged, thinking |
| **evaluative** | 🟡 Yellow | 🤔 | Contemplation, Doubt, Concentration (neutral) | Investor is analyzing, unsure |
| **skeptical** | 🔴 Red | 😬 | Doubt, Disapproval, Contempt, Confusion | Investor has concerns, doubts |
| **neutral** | ⚪ Gray | 😶 | Calmness, low arousal across all emotions | Baseline state, not engaged |

**Mapping Logic (Pseudocode):**

```python
def get_investor_state(emotions: dict) -> str:
    """
    Map 48 Hume emotions to 6 investor states

    Priority order:
    1. Check for strong negative emotions (skeptical)
    2. Check for strong positive emotions (positive)
    3. Check for engagement markers (receptive)
    4. Check for evaluation markers (evaluative)
    5. Default to neutral
    """

    # Skeptical: high doubt/disapproval/contempt
    if (emotions.get("Doubt", 0) > 0.6 or
        emotions.get("Disapproval", 0) > 0.5 or
        emotions.get("Contempt", 0) > 0.4):
        return "skeptical"

    # Positive: high joy/excitement/interest
    if (emotions.get("Joy", 0) > 0.7 or
        emotions.get("Excitement", 0) > 0.7 or
        (emotions.get("Interest", 0) > 0.7 and emotions.get("Joy", 0) > 0.5)):
        return "positive"

    # Receptive: high interest/concentration
    if (emotions.get("Interest", 0) > 0.6 or
        emotions.get("Concentration", 0) > 0.6):
        return "receptive"

    # Evaluative: high contemplation/doubt (moderate)
    if (emotions.get("Contemplation", 0) > 0.5 or
        emotions.get("Doubt", 0) > 0.3):
        return "evaluative"

    # Default
    return "neutral"
```

**Output Added to Response:**

```python
emotion_data["investor_state"] = get_investor_state(emotion_data["all_emotions"])
```

---

## Stage 4: 1-Second Interval Aggregation

### Backend: IntervalAggregator Class

**Location:** `backend/app/interval_aggregator.py`

The `IntervalAggregator` collects ~3 frames per second and produces **1-second intervals** with:
- Top 3 emotions (averaged + EMA smoothed)
- Dominant investor state
- Trend indicators (↑↓→)
- Metadata flags

#### Step 4.1: Add Frame to Interval

```python
# In handle_video_frame() after Hume analysis
aggregator = connection["interval_aggregator"]
aggregator.add_frame(emotion_data, current_time, face_detected=True)

# Check if interval is complete (1 second elapsed)
if aggregator.interval_complete(current_time):
    await process_completed_interval(client_id, current_time)
```

**IntervalAggregator.add_frame():**

```python
def add_frame(self, emotion_data: dict, timestamp: float, face_detected: bool = True):
    """Add a frame to the current interval"""

    # Initialize interval if needed
    if self.current_interval_start is None:
        self.current_interval_start = timestamp

    # Store frame data
    self.current_interval_frames.append({
        "timestamp": timestamp,
        "emotions": emotion_data.get("all_emotions", {}),
        "state": emotion_data.get("investor_state"),
        "face_detected": face_detected,
        "confidence": emotion_data.get("confidence", 0.0)
    })

    # Track states for majority voting
    if emotion_data.get("investor_state"):
        self.current_interval_states.append(emotion_data["investor_state"])
```

#### Step 4.2: Finalize Interval (every 1 second)

```python
def get_interval(self, current_time: float) -> dict:
    """Finalize and return the current interval data"""

    # 1. Calculate average emotions across frames
    emotion_sums = defaultdict(float)
    emotion_counts = defaultdict(int)

    for frame in self.current_interval_frames:
        if frame["face_detected"]:
            for emotion_name, score in frame["emotions"].items():
                emotion_sums[emotion_name] += score
                emotion_counts[emotion_name] += 1

    emotion_averages = {
        name: emotion_sums[name] / emotion_counts[name]
        for name in emotion_sums
    }

    # 2. Update EMA for all emotions (smoothing across intervals)
    for emotion_name, avg_score in emotion_averages.items():
        if emotion_name not in self.ema_emotions:
            self.ema_emotions[emotion_name] = avg_score  # First time
        else:
            # EMA formula: new_ema = α × new_value + (1 - α) × old_ema
            self.ema_emotions[emotion_name] = (
                self.alpha * avg_score +
                (1 - self.alpha) * self.ema_emotions[emotion_name]
            )
            # α = 0.3 → 30% weight to new data, 70% to history

    # 3. Get top 3 emotions with trends
    top_emotions = self._get_top_emotions_with_trends(emotion_averages, n=3)

    # 4. Determine dominant investor state (majority vote)
    investor_state = self._get_dominant_state(self.current_interval_states)

    # 5. Generate metadata flags
    flags = {
        "high_confidence": self._check_high_confidence(),
        "emotion_shift": self._check_emotion_shift(),
        "state_transition": (investor_state != self.previous_state),
        "silence": False  # Will be set by SpeechMapper
    }

    # 6. Build interval data
    interval_data = {
        "timestamp": self.current_interval_start + 0.5,  # Middle of interval
        "interval_start": self.current_interval_start,
        "interval_end": current_time,
        "interval": f"{self.current_interval_start:.1f}-{current_time:.1f}s",
        "top_emotions": top_emotions,
        "investor_state": investor_state,
        "frames_count": len(self.current_interval_frames),
        "faces_detected": sum(1 for f in self.current_interval_frames if f["face_detected"]),
        "flags": flags,
        "words": [],  # ← Will be populated by SpeechMapper (Stage 5)
        "full_text": ""
    }

    # Reset for next interval
    self._reset_interval()

    return interval_data
```

#### Step 4.3: Calculate Emotion Trends

```python
def _calculate_trend(self, emotion_name: str, current_score: float) -> str:
    """Calculate trend for emotion (increasing/decreasing/stable)"""

    if self.previous_top_emotions is None:
        return "stable"  # First interval

    # Find emotion in previous interval
    prev_score = None
    for prev_emotion in self.previous_top_emotions:
        if prev_emotion["name"] == emotion_name:
            prev_score = prev_emotion["avg_score"]
            break

    if prev_score is None:
        return "new"  # Emotion wasn't in top 3 before

    # Calculate change
    diff = current_score - prev_score
    threshold = 0.05  # 5% threshold

    if diff > threshold:
        return "increasing"  # ↑
    elif diff < -threshold:
        return "decreasing"  # ↓
    else:
        return "stable"  # →
```

**Example Interval Output:**

```python
{
    "timestamp": 1234567890.5,
    "interval_start": 1234567890.0,
    "interval_end": 1234567891.0,
    "interval": "1234567890.0-1234567891.0s",
    "top_emotions": [
        {
            "name": "Joy",
            "avg_score": 0.847,      # Average across 3 frames
            "ema_score": 0.823,      # EMA smoothed
            "trend": "increasing"    # ↑
        },
        {
            "name": "Interest",
            "avg_score": 0.789,
            "ema_score": 0.791,
            "trend": "stable"        # →
        },
        {
            "name": "Concentration",
            "avg_score": 0.723,
            "ema_score": 0.715,
            "trend": "decreasing"    # ↓
        }
    ],
    "investor_state": "receptive",
    "frames_count": 3,
    "faces_detected": 3,
    "flags": {
        "high_confidence": True,
        "emotion_shift": True,
        "state_transition": False,
        "silence": False
    },
    "words": [],  # Empty until SpeechMapper processes
    "full_text": ""
}
```

---

## Stage 5: Speech-to-Text Integration

### Frontend: Web Speech API

**Location:** Browser (Chrome's built-in speech recognition)

```javascript
// Initialize Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = false;

recognition.onresult = (event) => {
    const resultIndex = event.resultIndex;
    const transcript = event.results[resultIndex][0].transcript;
    const confidence = event.results[resultIndex][0].confidence;
    const timestamp = Date.now() / 1000;  // Unix timestamp

    // Send to backend
    ws.sendTranscribedText(transcript, timestamp);
};

recognition.start();
```

**WebSocket Message:**

```json
{
  "type": "transcribed_text",
  "data": {
    "text": "I think this is a great opportunity",
    "timestamp": 1234567890.5,
    "start_time": 1234567888.0,
    "end_time": 1234567890.5
  }
}
```

### Backend: SpeechMapper Class

**Location:** `backend/app/speech_mapper.py`

The `SpeechMapper` synchronizes speech transcripts with emotion intervals.

#### Step 5.1: Receive Transcribed Text

```python
async def handle_transcribed_text(client_id: str, data: dict):
    """Handle transcribed text for language emotion analysis"""

    text = data.get("text")
    timestamp = data.get("timestamp", time.time())

    if not text:
        return

    connection = manager.active_connections.get(client_id)
    speech_mapper = connection["speech_mapper"]

    # Add transcript segment to speech mapper
    start_time = data.get("start_time", timestamp)
    end_time = data.get("end_time", timestamp)

    speech_mapper.add_transcript_segment(text, start_time, end_time)
```

**SpeechMapper.add_transcript_segment():**

```python
def add_transcript_segment(self, text: str, start_time: float, end_time: float, confidence: float = 1.0):
    """Add a full transcript segment with estimated word timestamps"""

    words = text.strip().split()
    if not words:
        return

    # Distribute timestamps evenly across words
    duration = end_time - start_time
    time_per_word = duration / len(words)

    for i, word in enumerate(words):
        word_timestamp = start_time + (i * time_per_word)
        self.add_word(word, word_timestamp, confidence)
```

#### Step 5.2: Map Words to Intervals

**Called in `process_completed_interval()`:**

```python
async def process_completed_interval(client_id: str, current_time: float):
    """Process a completed 1-second interval"""

    # Get completed interval from aggregator
    aggregator = connection["interval_aggregator"]
    interval_data = aggregator.get_interval(current_time)

    # Update interval with speech data
    speech_mapper = connection["speech_mapper"]
    interval_data = speech_mapper.update_interval_with_speech(interval_data)

    # Send interval to client and timeseries buffer
    await manager.send_message(client_id, {
        "type": "interval_complete",
        "interval": interval_data,
        "timestamp": int(time.time() * 1000)
    })
```

**SpeechMapper.update_interval_with_speech():**

```python
def update_interval_with_speech(self, interval_data: dict) -> dict:
    """Update an interval with speech data"""

    interval_start = interval_data["interval_start"]
    interval_end = interval_data["interval_end"]

    # Find words that fall within this interval
    interval_words = []
    remaining_words = []

    for word_data in self.pending_words:
        word_timestamp = word_data["timestamp"]

        if interval_start <= word_timestamp < interval_end:
            interval_words.append(word_data)
            self.total_words_mapped += 1
        elif word_timestamp >= interval_end:
            remaining_words.append(word_data)  # Keep for future intervals

    self.pending_words = remaining_words

    # Build full text
    full_text = " ".join(w["word"] for w in interval_words)

    # Detect silence (no words or long gaps)
    is_silence = len(interval_words) == 0

    # Update interval data
    interval_data["words"] = interval_words
    interval_data["full_text"] = full_text
    interval_data["flags"]["silence"] = is_silence

    return interval_data
```

**Enriched Interval Output:**

```python
{
    "timestamp": 1234567890.5,
    "investor_state": "receptive",
    "top_emotions": [...],
    "words": [
        {"word": "I", "timestamp": 1234567890.1, "confidence": 0.99},
        {"word": "think", "timestamp": 1234567890.3, "confidence": 0.98},
        {"word": "this", "timestamp": 1234567890.5, "confidence": 0.99},
        {"word": "is", "timestamp": 1234567890.7, "confidence": 0.99},
        {"word": "great", "timestamp": 1234567890.9, "confidence": 0.97}
    ],
    "full_text": "I think this is great",
    "flags": {
        "silence": False,
        "state_transition": False,
        ...
    }
}
```

---

## Stage 6: 5-Second Time-Series Buffering

### Backend: TimeSeriesBuffer Class

**Location:** `backend/app/timeseries_buffer.py`

The `TimeSeriesBuffer` maintains a **rolling 5-second window** of intervals and triggers LLM updates.

#### Step 6.1: Add Interval to Buffer

```python
async def process_completed_interval(client_id: str, current_time: float):
    """After speech mapping, add to time-series buffer"""

    # ... (previous code)

    timeseries_buffer = connection["timeseries_buffer"]

    # Add interval to buffer and check if LLM should be triggered
    should_trigger_llm = timeseries_buffer.add_interval(interval_data, current_time)

    if should_trigger_llm:
        await trigger_llm_update(client_id)
```

**TimeSeriesBuffer.add_interval():**

```python
def add_interval(self, interval_data: dict, current_time: float) -> bool:
    """Add a 1-second interval to the buffer"""

    if self.session_start is None:
        self.session_start = current_time

    # Add to rolling deque (max 5 intervals)
    self.intervals.append(interval_data)  # deque with maxlen=5
    self.total_intervals += 1

    # Check if we should trigger LLM update
    return self._should_trigger_llm_update(current_time)
```

#### Step 6.2: Trigger Conditions

```python
def _should_trigger_llm_update(self, current_time: float) -> bool:
    """Determine if LLM update should be triggered"""

    # 1. Don't update if buffer isn't full yet (need 5 intervals)
    if len(self.intervals) < self.window_size:  # window_size = 5
        return False

    # 2. First update once buffer is full (at 5 seconds)
    if self.last_llm_update is None:
        self.last_llm_update = current_time
        return True

    # 3. Check if enough time has elapsed (every 4.5 seconds)
    elapsed = current_time - self.last_llm_update
    if elapsed >= self.update_interval:  # update_interval = 4.5
        self.last_llm_update = current_time
        return True

    # 4. Check for significant emotion shift (early trigger)
    if self._has_significant_shift():
        self.last_llm_update = current_time
        return True

    # 5. Check for state transition (early trigger)
    if self._has_state_transition():
        self.last_llm_update = current_time
        return True

    return False
```

**Buffer State Example (after 5 seconds):**

```python
timeseries_buffer.intervals = [
    interval_1,  # 0-1s: receptive, "I think this is great"
    interval_2,  # 1-2s: receptive, "opportunity for growth"
    interval_3,  # 2-3s: positive, "excited about the potential"
    interval_4,  # 3-4s: positive, "revenue projections"
    interval_5   # 4-5s: positive, "scaling quickly"
]
```

#### Step 6.3: Get Buffer Summary

```python
def get_summary(self) -> dict:
    """Get summary statistics for the current buffer"""

    intervals_list = list(self.intervals)

    # Find dominant investor state (majority vote)
    state_counts = {}
    for interval in intervals_list:
        state = interval.get("investor_state", "neutral")
        state_counts[state] = state_counts.get(state, 0) + 1

    dominant_state = max(state_counts.items(), key=lambda x: x[1])[0]

    # Count total words
    total_words = sum(len(interval.get("words", [])) for interval in intervals_list)

    return {
        "buffer_size": 5,
        "time_span": 5.0,
        "dominant_state": dominant_state,  # e.g., "positive"
        "total_words": total_words,
        "total_frames": 15  # 3 frames/sec × 5 sec
    }
```

---

## Stage 7: LLM Context Building

### Backend: LLMContextBuilder Class

**Location:** `backend/app/llm_context_builder.py`

The `LLMContextBuilder` formats the 5-second buffer into a structured context for GPT-4.

```python
async def trigger_llm_update(client_id: str):
    """Trigger LLM coaching advice based on time-series data"""

    timeseries_buffer = connection["timeseries_buffer"]
    context_builder = connection["context_builder"]

    # Get context from buffer
    intervals = timeseries_buffer.get_context()  # List of 5 intervals
    buffer_summary = timeseries_buffer.get_summary()
    emotion_trends = timeseries_buffer.get_emotion_trends()

    # Build LLM context
    context = context_builder.build_context(intervals, buffer_summary, emotion_trends)

    # Format for prompt
    formatted_context = context_builder.format_for_prompt(context)

    # Generate coaching advice
    coaching_advice = await get_negotiation_coaching(context)

    # Send to client
    await manager.send_message(client_id, {
        "type": "llm_context_update",
        "context": context,
        "formatted_text": formatted_context,
        "coaching_advice": coaching_advice,
        "investor_state": buffer_summary["dominant_state"],
        ...
    })
```

**LLMContextBuilder.build_context():**

```python
def build_context(self, intervals: list, buffer_summary: dict, emotion_trends: dict) -> dict:
    """Build complete context for LLM from time-series data"""

    # Build interval summaries (compact format)
    interval_summaries = [
        self._build_interval_summary(interval)
        for interval in intervals
    ]

    # Analyze patterns across intervals
    patterns = self._analyze_patterns(intervals)

    # Build final context
    context = {
        "time_window": {
            "duration_seconds": 5.0,
            "interval_count": 5,
            "start_time": intervals[0]["interval_start"],
            "end_time": intervals[-1]["interval_end"]
        },
        "intervals": interval_summaries,
        "summary": {
            "dominant_state": buffer_summary["dominant_state"],  # "positive"
            "total_words": buffer_summary["total_words"],
            "total_frames": buffer_summary["total_frames"],
            "emotion_trends": emotion_trends  # {"Joy": "increasing", ...}
        },
        "patterns": patterns,  # State transitions, emotion shifts, etc.
        "flags": self._aggregate_flags(intervals)
    }

    return context
```

**Example Patterns Analysis:**

```python
def _analyze_patterns(self, intervals: list) -> dict:
    """Analyze patterns across intervals"""

    return {
        "state_transitions": [
            {
                "from_state": "receptive",
                "to_state": "positive",
                "timestamp": 1234567892.5,
                "text_context": "excited about the potential"
            }
        ],
        "emotion_shifts": [
            {
                "timestamp": 1234567893.5,
                "emotions": [
                    {"name": "Joy", "trend": "increasing", "score": 0.87}
                ],
                "text_context": "revenue projections"
            }
        ],
        "silence_periods": [],  # No silence in this window
        "engagement_trend": "increasing"
    }
```

**Formatted Text for Prompt:**

```python
def format_for_prompt(self, context: dict) -> str:
    """Format context into human-readable text for LLM"""

    return """
=== PARTICIPANT ANALYSIS (Last 5 seconds) ===

Dominant State: POSITIVE
Engagement Trend: increasing
Words Spoken: 23

State Transitions:
  • receptive → positive at 1234567892.5s
    Said: "excited about the potential"

Emotion Shifts:
  • Joy (increasing) at 1234567893.5s

Interval Timeline:

[1234567890.5s] RECEPTIVE
  Emotions: Joy(0.82), Interest(0.79)
  Said: "I think this is great"

[1234567891.5s] RECEPTIVE
  Emotions: Joy(0.85), Interest(0.81)
  Said: "opportunity for growth"

[1234567892.5s] POSITIVE
  Emotions: Joy(0.89), Excitement(0.76)
  Said: "excited about the potential"

[1234567893.5s] POSITIVE
  Emotions: Joy(0.92), Excitement(0.82)
  Said: "revenue projections"

[1234567894.5s] POSITIVE
  Emotions: Joy(0.94), Excitement(0.85)
  Said: "scaling quickly"
"""
```

---

## Stage 8: GPT-4 Coaching Generation

### Backend: OpenAI API Integration

**Location:** `backend/app/llm.py` → `get_negotiation_coaching()`

```python
async def get_negotiation_coaching(context: dict) -> str:
    """Generate negotiation coaching advice from context"""

    from app.prompts import NEGOTIATION_COACH_SYSTEM_PROMPT, build_negotiation_prompt

    # Build prompt from context
    user_prompt = build_negotiation_prompt(context)

    # Call OpenAI API
    response = await openai.ChatCompletion.acreate(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": NEGOTIATION_COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=100,
        temperature=0.7
    )

    advice = response.choices[0].message.content.strip()
    return advice
```

**System Prompt:**

```
You are a real-time negotiation coach helping a startup founder pitch to a YC-style investor.

Your role:
- Analyze the investor's emotional state and body language signals
- Provide brief, actionable coaching advice to help the founder succeed
- Focus on practical tactics: tone, pacing, posture, framing

Guidelines:
- Keep advice under 15 words (max 2 short sentences)
- Be direct and specific
- Focus on immediate next action
- Use confident, decisive language
- Match urgency to investor's emotional state

Investor States:
- SKEPTICAL (🔴): Investor doubts credibility/readiness → Suggest confidence, traction, examples
- EVALUATIVE (🟡): Investor analyzing/thinking → Suggest clarity, pacing, key wins
- RECEPTIVE (🟢): Investor interested/curious → Suggest building momentum, vision
- POSITIVE (🟢): Investor excited/approving → Suggest closing strong, next steps
```

**User Prompt (Built from Context):**

```
Investor Analysis (last 5 seconds):

Dominant State: POSITIVE
Engagement Trend: increasing
Recent transition: receptive → positive
Current emotions: Joy (0.94), Excitement (0.85), Interest (0.79)
Investor just said: "scaling quickly"

Provide ONE concise coaching tip (max 15 words) to help the founder address this situation:
```

**GPT-4 Response:**

```
"Capitalize on this momentum! Ask for commitment or outline next steps confidently."
```

---

## Stage 9: UI Overlay Display

### Frontend: Overlay HTML

**Location:** `frontend/overlay.html`

#### Step 9.1: Receive LLM Context Update

```javascript
// WebSocket message handler
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'llm_context_update') {
        updateCoachingAdvice(message);
    }
};
```

#### Step 9.2: Update UI Elements

```javascript
function updateCoachingAdvice(data) {
    const advice = data.coaching_advice;
    const state = data.investor_state;
    const emoji = data.state_emoji;
    const color = data.state_color;

    // 1. Update investor state badge
    document.getElementById('state-emoji').textContent = emoji;  // 💚
    document.getElementById('state-name').textContent = state;   // "positive"
    document.getElementById('investor-state').style.setProperty('--state-color', color);

    // 2. Update coaching advice with animation
    const adviceElement = document.getElementById('coaching-advice');
    adviceElement.textContent = advice;

    // 3. Re-trigger fade-in animation
    const coachingSection = adviceElement.closest('.coaching-section');
    coachingSection.style.animation = 'none';
    setTimeout(() => {
        coachingSection.style.animation = 'fadeIn 0.5s ease';
    }, 10);
}
```

#### Step 9.3: Display Top Emotions (from Intervals)

```javascript
function updateIntervalData(interval) {
    const topEmotions = interval.top_emotions || [];

    // Build HTML for emotions list
    const emotionsList = document.getElementById('emotions-list');
    emotionsList.innerHTML = topEmotions.slice(0, 3).map(emotion => {
        const trendIcon = getTrendIcon(emotion.trend);
        const trendClass = emotion.trend === 'increasing' ? 'up' :
                           emotion.trend === 'decreasing' ? 'down' : 'stable';

        return `
            <div class="emotion-item">
                <span class="emotion-name">${emotion.name}</span>
                <span class="emotion-trend">
                    <span>${emotion.ema_score.toFixed(2)}</span>
                    <span class="trend-icon ${trendClass}">${trendIcon}</span>
                </span>
            </div>
        `;
    }).join('');
}

function getTrendIcon(trend) {
    switch (trend) {
        case 'increasing': return '↑';
        case 'decreasing': return '↓';
        case 'stable': return '→';
        default: return '—';
    }
}
```

**Final UI Display:**

```
┌────────────────────────────────────────┐
│   🤖 BeneAI Coach                   − │
├────────────────────────────────────────┤
│  ┌──────────────────────────────────┐ │
│  │ 💚  Investor State               │ │
│  │     POSITIVE                     │ │
│  └──────────────────────────────────┘ │
│                                        │
│  TOP EMOTIONS                          │
│  Joy                    0.94 ↑         │
│  Excitement             0.85 ↑         │
│  Interest               0.79 →         │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ 💡 COACHING ADVICE               │ │
│  │                                  │ │
│  │ Capitalize on this momentum!     │ │
│  │ Ask for commitment or outline    │ │
│  │ next steps confidently.          │ │
│  └──────────────────────────────────┘ │
│                                        │
│  🟢 Connected                          │
└────────────────────────────────────────┘
```

---

## Complete Example Flow

### Timeline: 0-10 seconds of a pitch

```
Time    Event                           Data Flow
────────────────────────────────────────────────────────────────────────
0.0s    📹 Webcam starts                → Video stream at 30 FPS

0.3s    📸 Frame 1 captured             → Base64 JPEG (60KB)
        🌐 WebSocket send               → to backend (10ms)
        🤖 Hume AI analysis             → 48 emotions (400ms)
        ✅ Response: Joy=0.82           → investor_state = "receptive"
        📊 Add to interval #1           → EMA updated

0.6s    📸 Frame 2 captured
        🤖 Hume AI: Joy=0.85            → still "receptive"
        📊 Add to interval #1

0.9s    📸 Frame 3 captured
        🤖 Hume AI: Joy=0.87            → still "receptive"
        📊 Add to interval #1

1.0s    ⏱️ Interval #1 complete
        🗣️ Speech: "I think this is great"
        📤 Send interval_complete       → to frontend
        💾 Add to buffer (1/5)

        [Repeat for intervals #2-4...]

4.0s    ⏱️ Interval #4 complete
        🗣️ Speech: "revenue projections"
        💾 Add to buffer (4/5)

5.0s    ⏱️ Interval #5 complete
        🗣️ Speech: "scaling quickly"
        💾 Add to buffer (5/5)

        🚨 BUFFER FULL! Trigger LLM update

        📝 Build context
        ├─ Dominant state: POSITIVE
        ├─ Transition: receptive → positive
        ├─ Emotion trends: Joy ↑, Excitement ↑
        └─ Total words: 23

        🧠 Call GPT-4
        ├─ Prompt: "Investor is POSITIVE, engagement increasing..."
        └─ Response (500ms): "Capitalize on this momentum! Ask for commitment..."

        📤 Send llm_context_update

        🎨 Frontend updates overlay
        ├─ State badge: 💚 POSITIVE
        ├─ Top emotions: Joy (0.94) ↑
        └─ Advice: "Capitalize on this momentum!..."

        ✅ USER SEES COACHING ADVICE

9.5s    ⏱️ Interval #10 complete
        💾 Buffer now has intervals #6-10

        🚨 4.5 seconds elapsed → Trigger LLM update

        [Process repeats every 4.5 seconds...]
```

---

## Data Structures Reference

### 1. Video Frame (Client → Server)

```json
{
  "type": "video_frame",
  "timestamp": 1234567890123,
  "data": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

### 2. Hume AI Emotion Result (Hume → Backend)

```python
{
    "primary_emotion": "Joy",
    "confidence": 0.847,
    "all_emotions": {
        "Joy": 0.847,
        "Interest": 0.789,
        "Concentration": 0.723,
        ...  # All 48 emotions
    },
    "investor_state": "receptive",
    "top_emotions": [
        {"name": "Joy", "score": 0.847},
        {"name": "Interest", "score": 0.789},
        {"name": "Concentration", "score": 0.723}
    ],
    "face_bbox": {"x": 120, "y": 80, "width": 200, "height": 250}
}
```

### 3. 1-Second Interval (Aggregator Output)

```python
{
    "timestamp": 1234567890.5,
    "interval_start": 1234567890.0,
    "interval_end": 1234567891.0,
    "interval": "1234567890.0-1234567891.0s",
    "top_emotions": [
        {"name": "Joy", "avg_score": 0.847, "ema_score": 0.823, "trend": "increasing"},
        {"name": "Interest", "avg_score": 0.789, "ema_score": 0.791, "trend": "stable"},
        {"name": "Concentration", "avg_score": 0.723, "ema_score": 0.715, "trend": "decreasing"}
    ],
    "investor_state": "receptive",
    "frames_count": 3,
    "faces_detected": 3,
    "words": [
        {"word": "I", "timestamp": 1234567890.1, "confidence": 0.99},
        {"word": "think", "timestamp": 1234567890.3, "confidence": 0.98},
        ...
    ],
    "full_text": "I think this is great",
    "flags": {
        "high_confidence": True,
        "emotion_shift": False,
        "state_transition": False,
        "silence": False
    }
}
```

### 4. LLM Context (Builder Output)

```python
{
    "time_window": {
        "duration_seconds": 5.0,
        "interval_count": 5,
        "start_time": 1234567890.0,
        "end_time": 1234567895.0
    },
    "intervals": [
        # 5 interval summaries (compact format)
    ],
    "summary": {
        "dominant_state": "positive",
        "total_words": 23,
        "total_frames": 15,
        "emotion_trends": {
            "Joy": "increasing",
            "Excitement": "increasing",
            "Interest": "stable"
        }
    },
    "patterns": {
        "state_transitions": [
            {"from_state": "receptive", "to_state": "positive", "timestamp": 1234567892.5}
        ],
        "emotion_shifts": [...],
        "silence_periods": [],
        "engagement_trend": "increasing"
    },
    "flags": {
        "high_confidence_ratio": 1.0,
        "has_emotion_shifts": True,
        "has_state_transitions": True,
        "silence_ratio": 0.0
    }
}
```

### 5. LLM Context Update (Server → Client)

```json
{
  "type": "llm_context_update",
  "context": { /* Full context object */ },
  "formatted_text": "=== PARTICIPANT ANALYSIS (Last 5 seconds) ===\n...",
  "coaching_advice": "Capitalize on this momentum! Ask for commitment or outline next steps confidently.",
  "investor_state": "positive",
  "state_emoji": "💚",
  "state_color": "#10b981",
  "timestamp": 1234567895000
}
```

---

## Performance Metrics

### Latency Breakdown

| Stage | Component | Latency | Notes |
|-------|-----------|---------|-------|
| 1 | Frame capture | 10-30ms | Canvas.toDataURL() |
| 2 | WebSocket send | 5-20ms | Depends on network |
| 3 | Hume AI face detection | 300-500ms | API call to Hume |
| 4 | Investor state mapping | <1ms | Simple logic |
| 5 | Interval aggregation | <5ms | EMA calculation |
| 6 | Speech mapping | <1ms | Word timestamp matching |
| 7 | Buffer management | <1ms | Deque operations |
| 8 | Context building | <5ms | Data formatting |
| 9 | GPT-4 API call | 500-800ms | OpenAI API |
| 10 | WebSocket receive | 5-20ms | Network |
| 11 | UI render | <5ms | DOM updates |
| **TOTAL (frame → emotion)** | **350-600ms** | ✅ Real-time |
| **TOTAL (context → advice)** | **550-900ms** | ✅ Real-time |

### Throughput

- **Video frames:** 3 FPS (one frame every 333ms)
- **Intervals:** 1 per second
- **LLM updates:** 1 every 4.5 seconds
- **Data sent per second:** ~60 KB (one frame)
- **Data received per second:** ~2 KB (emotion results + intervals)

### Memory Usage

- **IntervalAggregator:** ~5 KB (current interval + EMA state)
- **TimeSeriesBuffer:** ~25 KB (5 intervals × ~5 KB each)
- **SpeechMapper:** ~2 KB (pending words queue)
- **Total per client:** ~32 KB

### Scalability

With current architecture:
- **100 concurrent users:** 3.2 MB RAM, 300 requests/sec to Hume
- **Cost per 30-min call:** ~$0.50-$1.00 (Hume + OpenAI)

---

## Key Insights

### Why 3 FPS for video?
- **Hume AI latency:** 300-500ms per frame
- **Emotion stability:** Faces don't change dramatically in 333ms
- **Cost:** 3 FPS = 180 frames/min vs 30 FPS = 1800 frames/min (10× cost reduction)
- **Result:** 3 FPS provides smooth emotional tracking at 1/10 the cost

### Why 1-second intervals?
- **EMA smoothing:** Aggregating 3 frames reduces jitter
- **Speech alignment:** Most words/phrases fit within 1 second
- **Responsiveness:** 1-second granularity feels real-time
- **Buffer size:** 5 intervals = 5 seconds of context (good for trend analysis)

### Why 4.5-second LLM updates?
- **Context window:** 5 intervals = comprehensive view without lag
- **Cost:** ~40 LLM calls per 30-min call vs 1800 (per-second) = 45× reduction
- **User experience:** 4-5 seconds feels like "thoughtful" advice, not spam
- **Early triggers:** State transitions trigger earlier updates when needed

### Why EMA with α=0.3?
- **Smoothing:** 70% weight to history reduces frame-to-frame noise
- **Responsiveness:** 30% weight to new data captures real shifts
- **Math:** After 3 intervals, new data contributes ~65% to EMA (responsive but smooth)

---

**End of Data Flow Documentation** 🚀

For questions, see `USAGE_GUIDE.md` or review source code:
- `backend/main.py` - WebSocket handlers
- `backend/app/interval_aggregator.py` - 1-second intervals
- `backend/app/timeseries_buffer.py` - 5-second buffering
- `backend/app/llm_context_builder.py` - Context formatting
- `backend/app/speech_mapper.py` - Speech-to-text alignment
- `frontend/overlay.html` - UI display
