# Hume AI Integration Setup Guide

This guide explains how to set up and use Hume AI's Expression Measurement API in BeneAI for enhanced emotion detection.

## Overview

BeneAI now supports **Hume AI** as an alternative/primary emotion detection service, offering:

- **53 distinct emotions** (vs Luxand's 7) for more granular analysis
- **Multi-modal analysis**: Facial expressions, speech prosody, and emotional language
- **WebSocket streaming** for real-time processing
- **Better investor state mapping** with emotions like Admiration, Concentration, Contemplation, etc.

## Architecture

```
┌─────────────────┐
│  Chrome Ext     │
│  (Frontend)     │
└────────┬────────┘
         │ WebSocket
         │
┌────────▼────────┐
│  FastAPI        │
│  Backend        │
├─────────────────┤
│ ┌─────────────┐ │
│ │ Hume Client │ │ ← New!
│ └──────┬──────┘ │
│ ┌──────▼──────┐ │
│ │   Luxand    │ │ ← Fallback
│ └─────────────┘ │
└─────────────────┘
         │
    ┌────▼────┐
    │ OpenAI  │
    │  GPT-4  │
    └─────────┘
```

## Setup Instructions

### 1. Get Hume API Key

1. Sign up at [Hume AI Platform](https://platform.hume.ai/)
2. Navigate to API Keys section
3. Generate a new API key
4. Copy the key (starts with `hume-...`)

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `hume==0.6.1` - Hume AI Python SDK
- Other dependencies (FastAPI, OpenAI, etc.)

### 3. Configure Environment Variables

Update `backend/.env`:

```bash
# Hume AI Configuration
HUME_API_KEY=your-hume-api-key-here
HUME_ENABLE_FACE=true
HUME_ENABLE_PROSODY=true
HUME_ENABLE_LANGUAGE=true
HUME_WEBSOCKET_URL=wss://api.hume.ai/v0/stream/models
HUME_FRAME_RATE=3.0
HUME_USE_PRIMARY=false  # Set to 'true' to use Hume as primary (Luxand as fallback)
```

**Configuration Options:**

| Variable | Description | Default | Recommended |
|----------|-------------|---------|-------------|
| `HUME_API_KEY` | Your Hume API key | (required) | Get from Hume platform |
| `HUME_ENABLE_FACE` | Enable facial expression analysis | `true` | `true` |
| `HUME_ENABLE_PROSODY` | Enable speech prosody analysis | `true` | `true` for audio |
| `HUME_ENABLE_LANGUAGE` | Enable emotional language analysis | `true` | `true` for transcripts |
| `HUME_FRAME_RATE` | Video frames per second to analyze | `3.0` | `3.0` (hackathon) |
| `HUME_USE_PRIMARY` | Use Hume as primary vs fallback | `false` | `true` for better results |

### 4. Test the Integration

Run the test script to verify Hume API is working:

```bash
cd backend
python test_hume.py
```

**Expected Output:**
```
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

### 5. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Check health endpoint: http://localhost:8000

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "luxand": true,
    "hume": true,
    "openai": true
  }
}
```

## Usage

### WebSocket Message Types

The backend now accepts three types of data for emotion analysis:

#### 1. Video Frame (Facial Expression)

**Client → Server:**
```json
{
  "type": "video_frame",
  "data": "base64_encoded_image_data"
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
    {"name": "Joy", "score": 0.52}
  ],
  "service": "hume",
  "timestamp": 1234567890
}
```

#### 2. Audio Chunk (Speech Prosody) - NEW!

**Client → Server:**
```json
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio_data"
}
```

**Server → Client:**
```json
{
  "type": "prosody_result",
  "primary_emotion": "Excitement",
  "confidence": 0.82,
  "top_emotions": [
    {"name": "Excitement", "score": 0.82},
    {"name": "Joy", "score": 0.71}
  ],
  "timestamp": 1234567890
}
```

#### 3. Transcribed Text (Emotional Language) - NEW!

**Client → Server:**
```json
{
  "type": "transcribed_text",
  "data": "I think this is a great idea"
}
```

**Server → Client:**
```json
{
  "type": "language_result",
  "text": "I think this is a great idea",
  "predictions": [
    {
      "text": "great",
      "primary_emotion": "Admiration",
      "confidence": 0.74,
      "emotions": {"Admiration": 0.74, "Joy": 0.68, ...}
    }
  ],
  "timestamp": 1234567890
}
```

## Hume vs Luxand Comparison

| Feature | Luxand | Hume AI |
|---------|--------|---------|
| **Emotions** | 7 basic emotions | 53 granular emotions |
| **Modalities** | Face only | Face + Voice + Language |
| **Latency** | ~100-200ms | ~200-400ms |
| **Investor States** | Basic mapping | Advanced mapping |
| **Cost** | Pay per API call | Pay per API call |
| **Reliability** | High | High |

### Emotion Mapping Examples

**Luxand emotions:**
- happiness, neutral, anger, disgust, fear, sadness, surprise

**Hume emotions (53 total):**
- Admiration, Adoration, Aesthetic Appreciation, Amusement, Anger, Anxiety, Awe, Awkwardness, Boredom, Calmness, Concentration, Confusion, Contemplation, Contempt, Contentment, Craving, Desire, Determination, Disappointment, Disapproval, Disgust, Distress, Doubt, Ecstasy, Embarrassment, Empathic Pain, Entrancement, Envy, Excitement, Fear, Gratitude, Guilt, Horror, Interest, Joy, Love, Nostalgia, Pain, Pride, Realization, Relief, Romance, Sadness, Satisfaction, Shame, Surprise (negative), Surprise (positive), Sympathy, Tiredness, Triumph

## Investor State Mapping

Hume's 53 emotions are mapped to BeneAI's investor states:

### Skeptical
- **Emotions:** Doubt, Contempt, Disapproval, Disgust, Boredom, Distress
- **Use case:** Investor showing resistance or concern
- **Coaching:** "Address their concerns directly", "Provide evidence"

### Evaluative
- **Emotions:** Concentration, Contemplation, Confusion, Realization, Interest
- **Use case:** Investor analyzing your pitch
- **Coaching:** "Give them time to think", "Ask if they have questions"

### Receptive
- **Emotions:** Interest, Curiosity, Surprise (positive), Aesthetic Appreciation, Calmness
- **Use case:** Investor showing openness
- **Coaching:** "Continue with momentum", "Share more details"

### Positive
- **Emotions:** Admiration, Excitement, Joy, Satisfaction, Triumph, Amusement
- **Use case:** Investor is impressed
- **Coaching:** "Move towards close", "Discuss next steps"

## Frontend Integration (Optional)

To send audio and text data from the Chrome extension:

### Audio Streaming

```javascript
// In extension's audio-analyzer.js
async function sendAudioChunk(audioBlob) {
  const base64Audio = await blobToBase64(audioBlob);

  websocket.send(JSON.stringify({
    type: 'audio_chunk',
    data: base64Audio
  }));
}
```

### Text Analysis

```javascript
// After speech recognition
recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;

  websocket.send(JSON.stringify({
    type: 'transcribed_text',
    data: transcript
  }));
};
```

## Troubleshooting

### Connection Issues

**Problem:** `Failed to connect to Hume AI`

**Solutions:**
1. Verify API key is correct in `.env`
2. Check internet connection
3. Ensure firewall allows WebSocket connections
4. Check Hume API status: https://status.hume.ai/

### No Emotion Detection

**Problem:** `No face detected` or `No prosody detected`

**Solutions:**
1. Ensure video frame quality is sufficient (not too dark/blurry)
2. Check audio format is supported (WAV, MP3)
3. Verify base64 encoding is correct
4. Check logs for detailed error messages

### Rate Limiting

**Problem:** API requests failing with rate limit errors

**Solutions:**
1. Reduce `HUME_FRAME_RATE` (e.g., from 3.0 to 2.0)
2. Upgrade Hume API plan if needed
3. Implement client-side throttling

### High Latency

**Problem:** Emotion detection is slow

**Solutions:**
1. Use Hume as primary only (`HUME_USE_PRIMARY=true`)
2. Reduce frame rate (`HUME_FRAME_RATE=2.0`)
3. Disable unused models (prosody or language)
4. Check server location (Cloud Run region)

## API Limits

From Hume AI documentation:

- **WebSocket duration:** 1 minute inactivity timeout
- **Message payload size:**
  - Video: 5000ms (5 seconds)
  - Audio: 5000ms (5 seconds)
  - Image: 3,000 x 3,000 pixels
  - Text: 10,000 characters
- **Request rate:** 50 requests/second (handshake)

## Cost Considerations

Hume AI pricing (as of 2024):
- Pay per API call
- WebSocket connections are metered
- Check current pricing: https://hume.ai/pricing

**Optimization tips:**
- Use appropriate frame rate (3 FPS for hackathon)
- Only enable needed models (face, prosody, language)
- Cache results when possible
- Use Luxand as fallback to reduce Hume costs

## Next Steps

1. ✅ Get Hume API key
2. ✅ Update `.env` configuration
3. ✅ Run test script (`python test_hume.py`)
4. ✅ Start backend server
5. ✅ Test with Chrome extension
6. ⏭️ Optionally integrate audio/text streaming
7. ⏭️ Update prompts to leverage 53 emotions
8. ⏭️ Deploy to Cloud Run with Hume enabled

## Support

- **Hume Docs:** https://dev.hume.ai/docs
- **Hume SDK:** https://github.com/HumeAI/hume-python-sdk
- **BeneAI Issues:** Contact team

---

**Last updated:** January 2025
