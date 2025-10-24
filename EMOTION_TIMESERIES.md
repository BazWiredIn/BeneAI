# Emotion Time-Series System Documentation

## Overview

The BeneAI emotion time-series system aggregates real-time facial emotion data from Hume AI into structured 1-second intervals with synchronized speech transcription. This reduces context size for LLM coaching while preserving temporal patterns.

**Key Metrics:**
- **Context Reduction:** 94% (from 53 emotions → top 3)
- **Temporal Resolution:** 1-second intervals
- **LLM Update Frequency:** Every 5 seconds (5 intervals)
- **Frame Processing:** ~3 FPS (captures 3 emotion frames per second)

## Architecture

### Component Flow

```
Video Frame (30 FPS)
    ↓ [Throttle to 3 FPS]
Hume AI Face Analysis (53 emotions)
    ↓
IntervalAggregator (collects frames for 1 second)
    ↓ [Every 1 second]
SpeechMapper (adds word timestamps)
    ↓
TimeSeriesBuffer (collects 5 intervals)
    ↓ [Every 5 seconds]
LLMContextBuilder (formats for GPT-4)
    ↓
Coaching Advice
```

### Data Structure Evolution

#### 1. Raw Frame (from Hume AI)
```json
{
  "primary_emotion": "Concentration",
  "confidence": 0.72,
  "all_emotions": {
    "Concentration": 0.72,
    "Interest": 0.58,
    "Doubt": 0.43,
    ...46 more emotions
  },
  "investor_state": "evaluative",
  "timestamp": 1234567890.123
}
```

#### 2. 1-Second Interval (aggregated)
```json
{
  "timestamp": 5.5,
  "interval_start": 5.0,
  "interval_end": 6.0,
  "top_emotions": [
    {
      "name": "Concentration",
      "avg_score": 0.72,
      "ema_score": 0.68,
      "trend": "increasing"
    },
    {
      "name": "Interest",
      "avg_score": 0.58,
      "ema_score": 0.61,
      "trend": "stable"
    },
    {
      "name": "Doubt",
      "avg_score": 0.43,
      "ema_score": 0.45,
      "trend": "decreasing"
    }
  ],
  "investor_state": "evaluative",
  "frames_count": 3,
  "faces_detected": 3,
  "words": [
    {"word": "So", "timestamp": 5.1, "confidence": 0.95},
    {"word": "the", "timestamp": 5.3, "confidence": 0.98},
    {"word": "revenue", "timestamp": 5.6, "confidence": 0.92}
  ],
  "full_text": "So the revenue",
  "flags": {
    "high_confidence": true,
    "emotion_shift": false,
    "state_transition": false,
    "silence": false
  }
}
```

#### 3. LLM Context (5 intervals)
```json
{
  "time_window": {
    "duration_seconds": 5.0,
    "interval_count": 5,
    "start_time": 0.0,
    "end_time": 5.0
  },
  "intervals": [ /* 5 interval objects */ ],
  "summary": {
    "dominant_state": "evaluative",
    "total_words": 47,
    "total_frames": 15,
    "emotion_trends": {
      "Concentration": "increasing",
      "Interest": "stable",
      "Doubt": "decreasing"
    }
  },
  "patterns": {
    "state_transitions": [
      {
        "from_state": "receptive",
        "to_state": "evaluative",
        "timestamp": 3.5,
        "text_context": "What about costs?"
      }
    ],
    "emotion_shifts": [ /* ... */ ],
    "silence_periods": [ /* ... */ ],
    "engagement_trend": "increasing"
  }
}
```

## Components

### 1. IntervalAggregator (`interval_aggregator.py`)

**Purpose:** Aggregate ~3 emotion frames into 1-second intervals with EMA smoothing.

**Key Methods:**
- `add_frame(emotion_data, timestamp)`: Add a frame to current interval
- `interval_complete(current_time)`: Check if 1 second has elapsed
- `get_interval(current_time)`: Finalize and return interval data

**Algorithm:**
1. Collect frames for 1 second (typically 3 frames at 3 FPS)
2. Calculate average score for each emotion across frames
3. Update EMA for all emotions: `EMA = α * avg + (1-α) * prev_EMA`
4. Select top 3 emotions by EMA score
5. Calculate trend (increasing/decreasing/stable) vs previous interval
6. Map to investor state (skeptical/evaluative/receptive/positive)

**Configuration:**
```python
IntervalAggregator(
    alpha=0.3,              # EMA smoothing factor (0.0-1.0)
    interval_duration=1.0   # Interval length in seconds
)
```

**Investor State Mapping:**
```python
# Weighted combinations of Hume's 53 emotions
skeptical   = Doubt(0.5) + Contempt(0.4) + Disapproval(0.4) + ...
evaluative  = Concentration(0.6) + Contemplation(0.5) + Realization(0.4) + ...
receptive   = Interest(0.5) + Curiosity(0.5) + Surprise(0.4) + ...
positive    = Admiration(0.6) + Excitement(0.5) + Joy(0.5) + ...
```

### 2. TimeSeriesBuffer (`timeseries_buffer.py`)

**Purpose:** Maintain a rolling 5-second window of intervals and trigger LLM updates.

**Key Methods:**
- `add_interval(interval_data, current_time)`: Add interval, returns True if LLM update needed
- `get_context()`: Get current buffer contents (5 intervals)
- `get_summary()`: Get buffer statistics
- `get_emotion_trends()`: Analyze emotion trends across buffer

**Triggering Logic:**
LLM update is triggered when:
1. Buffer is full (5 intervals = 5 seconds)
2. AND one of:
   - Time since last update ≥ 5 seconds
   - Significant emotion shift detected
   - Investor state transition occurred

**Example Usage:**
```python
buffer = TimeSeriesBuffer(window_size=5, update_interval=5.0)

# Add intervals as they complete
should_update = buffer.add_interval(interval_data, current_time)

if should_update:
    # Trigger LLM coaching update
    context = buffer.get_context()
    summary = buffer.get_summary()
    trends = buffer.get_emotion_trends()
```

### 3. SpeechMapper (`speech_mapper.py`)

**Purpose:** Synchronize speech transcription with emotion intervals.

**Key Methods:**
- `add_word(word, timestamp, confidence)`: Add individual word
- `add_transcript_segment(text, start_time, end_time)`: Add phrase segment
- `map_to_interval(interval_start, interval_end)`: Get words in interval
- `update_interval_with_speech(interval_data)`: Populate speech fields

**Word Alignment:**
```python
# Option 1: Word-level timestamps from speech API
speech_mapper.add_word("Hello", 5.1, confidence=0.95)
speech_mapper.add_word("world", 5.5, confidence=0.92)

# Option 2: Segment-level (estimates word times)
speech_mapper.add_transcript_segment(
    "Hello world",
    start_time=5.0,
    end_time=6.0
)

# Map to interval
words, full_text, is_silence = speech_mapper.map_to_interval(5.0, 6.0)
# words: [{"word": "Hello", "timestamp": 5.1, ...}, ...]
# full_text: "Hello world"
# is_silence: False
```

**Silence Detection:**
- Interval with no words = silence
- Gap ≥ 0.5s between words = silence

### 4. LLMContextBuilder (`llm_context_builder.py`)

**Purpose:** Format time-series data into structured context for GPT-4.

**Key Methods:**
- `build_context(intervals, buffer_summary, emotion_trends)`: Build structured context
- `format_for_prompt(context)`: Convert to human-readable text

**Output Example:**
```
=== PARTICIPANT ANALYSIS (Last 5 seconds) ===

Dominant State: EVALUATIVE
Engagement Trend: increasing
Words Spoken: 47

State Transitions:
  • receptive → evaluative at 3.5s
    Said: "What about costs?"

Interval Timeline:

[1.0s] EVALUATIVE
  Emotions: Concentration(0.68), Interest(0.61)
  Said: "So the revenue model is"

[2.0s] EVALUATIVE
  Emotions: Concentration(0.72), Doubt(0.45)
  Said: "interesting but what about"

[3.0s] RECEPTIVE
  Emotions: Interest(0.65), Curiosity(0.58)
  Said: "the customer acquisition"

...
```

## Integration in main.py

### Connection Setup
```python
# Each WebSocket client gets their own components
self.active_connections[client_id] = {
    "websocket": websocket,
    "interval_aggregator": IntervalAggregator(alpha=0.3, interval_duration=1.0),
    "timeseries_buffer": TimeSeriesBuffer(window_size=5, update_interval=5.0),
    "speech_mapper": SpeechMapper(silence_threshold=0.5),
    "context_builder": LLMContextBuilder()
}
```

### Video Frame Processing
```python
async def handle_video_frame(client_id, frame_data):
    # 1. Analyze with Hume AI (53 emotions)
    emotion_data = await hume.analyze_face(frame_data)

    # 2. Add to interval aggregator
    aggregator.add_frame(emotion_data, current_time, face_detected=True)

    # 3. Check if interval complete (1 second elapsed)
    if aggregator.interval_complete(current_time):
        await process_completed_interval(client_id, current_time)
```

### Interval Completion
```python
async def process_completed_interval(client_id, current_time):
    # 1. Get completed interval
    interval_data = aggregator.get_interval(current_time)

    # 2. Add speech data
    interval_data = speech_mapper.update_interval_with_speech(interval_data)

    # 3. Send to client for display
    await send_message(client_id, {
        "type": "interval_complete",
        "interval": interval_data
    })

    # 4. Add to buffer and check if LLM update needed
    should_trigger_llm = timeseries_buffer.add_interval(interval_data, current_time)

    if should_trigger_llm:
        await trigger_llm_update(client_id)
```

### LLM Update
```python
async def trigger_llm_update(client_id):
    # 1. Get 5-second context
    intervals = timeseries_buffer.get_context()
    summary = timeseries_buffer.get_summary()
    trends = timeseries_buffer.get_emotion_trends()

    # 2. Build structured context
    context = context_builder.build_context(intervals, summary, trends)
    formatted_text = context_builder.format_for_prompt(context)

    # 3. Send to LLM (or client for display)
    await send_message(client_id, {
        "type": "llm_context_update",
        "context": context,
        "formatted_text": formatted_text
    })
```

## Visualization Tool

**File:** `visualize_emotions.py`

### Usage
```bash
# Generate plots from recorded session
python visualize_emotions.py session_data.json

# Save plots to file
python visualize_emotions.py session_data.json --output ./plots/

# Include trend analysis
python visualize_emotions.py session_data.json --trends
```

### Features
1. **Emotion Timeline:** Shows top 3 emotions over time with EMA smoothing
2. **Investor State Timeline:** Color-coded bars showing state changes
3. **Speech Alignment:** Word-level text displayed under intervals
4. **Trend Analysis:** Stacked area chart of increasing/decreasing/stable emotions
5. **Summary Statistics:** State distribution, transitions, silence periods

### Example Data Format
```json
{
  "intervals": [
    {
      "timestamp": 1.0,
      "top_emotions": [...],
      "investor_state": "evaluative",
      "full_text": "So the revenue",
      ...
    },
    ...
  ]
}
```

## Tuning Parameters

### EMA Alpha (smoothing factor)
- **Current:** 0.3
- **Effect:** Controls responsiveness vs stability
- **Lower (0.1-0.2):** More stable, slower to react to changes
- **Higher (0.4-0.6):** More responsive, tracks changes faster

### Frame Rate
- **Current:** 3 FPS
- **Effect:** Frames per second sent to Hume AI
- **Lower (1-2 FPS):** Reduces API cost, less granular
- **Higher (5-10 FPS):** More granular, higher cost

### Interval Duration
- **Current:** 1.0 seconds
- **Effect:** Temporal resolution of aggregation
- **Shorter (0.5s):** More granular, more intervals
- **Longer (2.0s):** Less granular, smoother

### Buffer Window Size
- **Current:** 5 intervals (5 seconds)
- **Effect:** Amount of context sent to LLM
- **Smaller (3):** Less context, faster updates
- **Larger (10):** More context, better patterns

### Update Interval
- **Current:** 5 seconds
- **Effect:** Minimum time between LLM updates
- **Shorter (3s):** More frequent advice, higher cost
- **Longer (10s):** Less frequent, lower cost

## Performance Characteristics

### Latency Breakdown
```
Video Frame Capture:        ~10-20ms
Hume AI Analysis:           ~100-200ms
Interval Aggregation:       ~1-5ms
Speech Mapping:             ~1-5ms
Context Building:           ~5-10ms
LLM Generation (GPT-4):     ~500-2000ms (streaming)
-------------------------------------------
Total (frame to advice):    ~620-2240ms
```

### Memory Usage (per client)
```
IntervalAggregator:         ~10 KB
TimeSeriesBuffer (5 int):   ~50 KB
SpeechMapper (pending):     ~5 KB
Context (JSON):             ~20 KB
-------------------------------------------
Total per client:           ~85 KB
```

### Context Size Reduction
```
Raw Hume Data (per frame):
  53 emotions × 3 FPS × 5 seconds = 795 emotion values

Aggregated Context:
  3 emotions × 5 intervals = 15 emotion values

Reduction: 98% (795 → 15)
```

## Testing & Validation

### Unit Tests
```bash
# Test interval aggregation
pytest backend/tests/test_interval_aggregator.py

# Test buffer logic
pytest backend/tests/test_timeseries_buffer.py

# Test speech mapping
pytest backend/tests/test_speech_mapper.py
```

### Manual Testing
```python
# Create test aggregator
aggregator = IntervalAggregator(alpha=0.3, interval_duration=1.0)

# Simulate frames
for i in range(3):
    emotion_data = {
        "all_emotions": {"Concentration": 0.7, "Interest": 0.6},
        "investor_state": "evaluative"
    }
    aggregator.add_frame(emotion_data, time.time())

# Get interval
if aggregator.interval_complete(time.time()):
    interval = aggregator.get_interval(time.time())
    print(json.dumps(interval, indent=2))
```

## Troubleshooting

### Issue: Intervals not completing
**Symptom:** No interval_complete messages
**Cause:** Not enough time elapsed or no frames added
**Fix:** Check that frames are being added with proper timestamps

### Issue: Empty speech data
**Symptom:** All intervals have `full_text: ""`
**Cause:** Speech transcription not being sent to backend
**Fix:** Verify frontend is sending `transcribed_text` messages

### Issue: Erratic emotion values
**Symptom:** Emotions jumping between extreme values
**Cause:** EMA alpha too high or face detection failing
**Fix:** Lower alpha to 0.2 or improve lighting conditions

### Issue: LLM updates too frequent
**Symptom:** Advice updates multiple times per second
**Cause:** Buffer triggering logic too sensitive
**Fix:** Increase `update_interval` or disable emotion_shift triggering

## Future Enhancements

1. **Adaptive EMA:** Adjust alpha based on face detection confidence
2. **Multi-person Support:** Track multiple faces with separate aggregators
3. **Emotion Clustering:** Group similar emotional states for simplification
4. **Predictive Triggers:** Use ML to predict when user needs advice
5. **A/B Testing Framework:** Compare different smoothing parameters
6. **Real-time Dashboard:** Live visualization during sessions
7. **Historical Analysis:** Compare current session to past sessions
8. **Export Formats:** CSV, Parquet for data science analysis

## References

- **Hume AI Documentation:** https://docs.hume.ai/
- **Exponential Moving Average:** https://en.wikipedia.org/wiki/Moving_average#Exponential_moving_average
- **Time-Series Analysis:** https://en.wikipedia.org/wiki/Time_series

## Version History

- **v1.0.0** (2025-01-XX): Initial implementation with 1-second intervals, EMA smoothing, and 5-second LLM updates
