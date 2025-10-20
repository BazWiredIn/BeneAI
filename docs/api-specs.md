# BeneAI API Specifications

## Overview

This document defines the WebSocket protocol and message formats for communication between the Chrome extension (client) and the FastAPI backend (server).

## WebSocket Connection

### Endpoint
```
wss://<cloud-run-url>/ws
```

**Local Development:**
```
ws://localhost:8000/ws
```

### Connection Flow

```
Client                          Server
  |                                |
  |-- WebSocket Handshake ------→ |
  |                                |
  |←-- Connection Accepted -------|
  |                                |
  |-- Authentication (future) ---→ |
  |                                |
  |←-- Welcome Message ------------|
  |                                |
  |-- Parameters Update ---------→ |
  |                                |
  |←-- Advice Stream (ongoing) ----|
  |                                |
  |-- Parameters Update ---------→ |
  |                                |
  |←-- Advice Stream (ongoing) ----|
  |                                |
  |-- Ping ----------------------→ |
  |←-- Pong ----------------------|
  |                                |
  |-- Close --------------------→  |
  |←-- Close Acknowledgment ------|
```

### Connection Lifecycle

#### 1. Connection Established
Server sends welcome message:
```json
{
  "type": "connection",
  "status": "connected",
  "message": "Welcome to BeneAI coaching service",
  "server_version": "1.0.0",
  "timestamp": 1697745123456
}
```

#### 2. Heartbeat (Keep-Alive)
**Client sends every 30 seconds:**
```json
{
  "type": "ping",
  "timestamp": 1697745123456
}
```

**Server responds:**
```json
{
  "type": "pong",
  "timestamp": 1697745123500
}
```

#### 3. Connection Closed
**Client initiates:**
```json
{
  "type": "disconnect",
  "reason": "user_stopped_call"
}
```

**Server responds:**
```json
{
  "type": "disconnect_ack",
  "message": "Goodbye! Good luck with your call."
}
```

## Message Types

### 1. Parameters Update (Client → Server)

Sent every 2-3 seconds with current analysis results.

```json
{
  "type": "parameters",
  "timestamp": 1697745123456,
  "data": {
    "emotion": {
      "label": "concerned",
      "confidence": 0.72,
      "landmarks_detected": true,
      "face_count": 1
    },
    "speech": {
      "wordsPerMinute": 185,
      "pauseFrequency": 0.12,
      "fillerWords": {
        "total": 5,
        "breakdown": {
          "um": 2,
          "uh": 1,
          "like": 2
        }
      },
      "volumeLevel": 0.68,
      "energyLevel": 0.71,
      "speakingTime": 45.2,
      "recentTranscript": "um, so I think we should, like, consider the, uh, the implications..."
    },
    "context": {
      "callDuration": 420,
      "platform": "google_meet",
      "participantCount": 3
    }
  }
}
```

#### Field Specifications

##### `emotion` Object
| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `label` | string | enum | One of: `positive`, `negative`, `neutral`, `concerned`, `surprised`, `disengaged` |
| `confidence` | float | 0.0-1.0 | Confidence in emotion detection |
| `landmarks_detected` | boolean | - | Whether face was detected in frame |
| `face_count` | integer | 0-10 | Number of faces detected (usually 1 for user) |

##### `speech` Object
| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `wordsPerMinute` | integer | 0-300 | Speaking rate (target: 120-150) |
| `pauseFrequency` | float | 0.0-1.0 | Ratio of silence to speech (target: 0.2-0.3) |
| `fillerWords.total` | integer | 0+ | Count of filler words in last 30 seconds |
| `fillerWords.breakdown` | object | - | Per-word filler counts |
| `volumeLevel` | float | 0.0-1.0 | Normalized volume (0=silent, 1=max) |
| `energyLevel` | float | 0.0-1.0 | Audio energy/intensity |
| `speakingTime` | float | 0.0+ | Seconds spent speaking in last 60s |
| `recentTranscript` | string | max 500 chars | Last 30 seconds of speech |

##### `context` Object (Optional)
| Field | Type | Description |
|-------|------|-------------|
| `callDuration` | integer | Seconds since call started |
| `platform` | string | `google_meet`, `zoom`, `teams`, `unknown` |
| `participantCount` | integer | Number of participants (if detectable) |

### 2. Advice Response (Server → Client)

#### Streaming Mode (Default)
Server streams advice word-by-word as tokens arrive from GPT-4.

**Start of stream:**
```json
{
  "type": "advice_start",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1697745124000
}
```

**Each token:**
```json
{
  "type": "advice_chunk",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunk": "Try ",
  "index": 0
}
```

```json
{
  "type": "advice_chunk",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunk": "slowing ",
  "index": 1
}
```

**End of stream:**
```json
{
  "type": "advice_complete",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_text": "Try slowing down - aim for 140 words per minute for clarity.",
  "timestamp": 1697745124500,
  "metadata": {
    "focus_area": "pacing",
    "cached": false,
    "latency_ms": 485
  }
}
```

#### Cached Response Mode
If response is served from cache, sent as single complete message.

```json
{
  "type": "advice_complete",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "full_text": "Take a deep breath and pause before continuing.",
  "timestamp": 1697745124100,
  "metadata": {
    "focus_area": "emotional_regulation",
    "cached": true,
    "latency_ms": 25
  }
}
```

### 3. Error Messages (Server → Client)

```json
{
  "type": "error",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please wait 5 seconds.",
  "retry_after": 5,
  "timestamp": 1697745123456
}
```

#### Error Codes
| Code | Description | Client Action |
|------|-------------|---------------|
| `RATE_LIMIT_EXCEEDED` | Too many messages from client | Wait `retry_after` seconds |
| `INVALID_MESSAGE` | Malformed JSON or missing fields | Fix message format |
| `OPENAI_ERROR` | OpenAI API failure | Display fallback advice |
| `SERVER_OVERLOAD` | Server at capacity | Retry with exponential backoff |
| `AUTHENTICATION_REQUIRED` | (Future) Auth token missing | Prompt user to log in |

### 4. Status Updates (Server → Client)

```json
{
  "type": "status",
  "status": "processing",
  "message": "Analyzing your speech patterns...",
  "timestamp": 1697745123500
}
```

#### Status Types
- `connected`: Connection established
- `processing`: Analyzing parameters
- `waiting_for_llm`: Waiting for GPT-4 response
- `streaming`: Streaming advice
- `error`: Error occurred
- `reconnecting`: Server is reconnecting to OpenAI

## Request/Response Examples

### Example 1: User Speaking Too Fast

**Client sends:**
```json
{
  "type": "parameters",
  "timestamp": 1697745123456,
  "data": {
    "emotion": {
      "label": "neutral",
      "confidence": 0.85,
      "landmarks_detected": true,
      "face_count": 1
    },
    "speech": {
      "wordsPerMinute": 195,
      "pauseFrequency": 0.08,
      "fillerWords": {
        "total": 2,
        "breakdown": {"um": 1, "uh": 1}
      },
      "volumeLevel": 0.72,
      "energyLevel": 0.78,
      "speakingTime": 52.0,
      "recentTranscript": "so what I'm thinking is we should move forward with this plan and execute immediately"
    }
  }
}
```

**Server streams:**
```json
{"type": "advice_start", "request_id": "abc123", "timestamp": 1697745123600}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "Slow ", "index": 0}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "down ", "index": 1}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "to ", "index": 2}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "140 ", "index": 3}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "WPM. ", "index": 4}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "Pause ", "index": 5}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "between ", "index": 6}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "key ", "index": 7}
{"type": "advice_chunk", "request_id": "abc123", "chunk": "points.", "index": 8}
{"type": "advice_complete", "request_id": "abc123", "full_text": "Slow down to 140 WPM. Pause between key points.", "timestamp": 1697745124100, "metadata": {"focus_area": "pacing", "cached": false, "latency_ms": 500}}
```

### Example 2: User Looks Concerned

**Client sends:**
```json
{
  "type": "parameters",
  "timestamp": 1697745200000,
  "data": {
    "emotion": {
      "label": "concerned",
      "confidence": 0.79,
      "landmarks_detected": true,
      "face_count": 1
    },
    "speech": {
      "wordsPerMinute": 135,
      "pauseFrequency": 0.22,
      "fillerWords": {
        "total": 7,
        "breakdown": {"um": 3, "uh": 2, "like": 2}
      },
      "volumeLevel": 0.55,
      "energyLevel": 0.58,
      "speakingTime": 38.5,
      "recentTranscript": "um, I'm not sure, like, if we can actually, uh, make this work in time"
    }
  }
}
```

**Server response:**
```json
{"type": "advice_start", "request_id": "def456", "timestamp": 1697745200100}
{"type": "advice_chunk", "request_id": "def456", "chunk": "Take ", "index": 0}
{"type": "advice_chunk", "request_id": "def456", "chunk": "a ", "index": 1}
{"type": "advice_chunk", "request_id": "def456", "chunk": "breath. ", "index": 2}
{"type": "advice_chunk", "request_id": "def456", "chunk": "Project ", "index": 3}
{"type": "advice_chunk", "request_id": "def456", "chunk": "confidence - ", "index": 4}
{"type": "advice_chunk", "request_id": "def456", "chunk": "say ", "index": 5}
{"type": "advice_chunk", "request_id": "def456", "chunk": "\"we'll ", "index": 6}
{"type": "advice_chunk", "request_id": "def456", "chunk": "find ", "index": 7}
{"type": "advice_chunk", "request_id": "def456", "chunk": "a ", "index": 8}
{"type": "advice_chunk", "request_id": "def456", "chunk": "way.\"", "index": 9}
{"type": "advice_complete", "request_id": "def456", "full_text": "Take a breath. Project confidence - say \"we'll find a way.\"", "timestamp": 1697745200600, "metadata": {"focus_area": "emotional_tone", "cached": false, "latency_ms": 500}}
```

### Example 3: Using Filler Words

**Client sends:**
```json
{
  "type": "parameters",
  "timestamp": 1697745300000,
  "data": {
    "emotion": {
      "label": "neutral",
      "confidence": 0.88,
      "landmarks_detected": true,
      "face_count": 1
    },
    "speech": {
      "wordsPerMinute": 145,
      "pauseFrequency": 0.18,
      "fillerWords": {
        "total": 12,
        "breakdown": {"um": 5, "uh": 3, "like": 4}
      },
      "volumeLevel": 0.70,
      "energyLevel": 0.72,
      "speakingTime": 48.0,
      "recentTranscript": "so like, um, what I'm saying is, uh, we should, like, really focus on, um, the core features"
    }
  }
}
```

**Server response:**
```json
{"type": "advice_start", "request_id": "ghi789", "timestamp": 1697745300100}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "Reduce ", "index": 0}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "filler ", "index": 1}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "words. ", "index": 2}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "Pause ", "index": 3}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "instead ", "index": 4}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "of ", "index": 5}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "saying ", "index": 6}
{"type": "advice_chunk", "request_id": "ghi789", "chunk": "\"um.\"", "index": 7}
{"type": "advice_complete", "request_id": "ghi789", "full_text": "Reduce filler words. Pause instead of saying \"um.\"", "timestamp": 1697745300550, "metadata": {"focus_area": "clarity", "cached": false, "latency_ms": 450}}
```

## Rate Limiting

### Client-Side Throttling
- **Maximum send rate:** 1 message per 2 seconds
- **Burst allowance:** 3 messages in quick succession, then throttle
- **Implementation:** Use debounce/throttle on parameter updates

### Server-Side Limits
- **Per connection:** 10 messages per second
- **Violation response:**
  ```json
  {
    "type": "error",
    "error_code": "RATE_LIMIT_EXCEEDED",
    "message": "Slow down! Max 10 messages per second.",
    "retry_after": 1
  }
  ```

## Error Handling

### Client Responsibilities
1. **Reconnection Logic:**
   - On disconnect, wait 1 second, then reconnect
   - Exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
   - After 5 failed attempts, notify user

2. **Message Validation:**
   - Validate JSON before sending
   - Ensure required fields present
   - Handle server errors gracefully

3. **Fallback Behavior:**
   - If no response in 3 seconds, show cached advice
   - If server unavailable, show generic coaching tips
   - Never leave user without feedback

### Server Responsibilities
1. **Graceful Degradation:**
   - If OpenAI API fails, return cached response
   - If cache miss, return simple rule-based advice
   - Always respond, even with "try again later"

2. **Logging:**
   - Log all errors with context
   - Track error rates for monitoring
   - Alert on spike in error rate

## Security

### Authentication (Future)
```json
{
  "type": "auth",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "timestamp": 1697745123456
}
```

### Data Privacy
- **No PII:** Never send user names, emails, or identifiable info
- **Minimal Transcripts:** Only last 30 seconds, truncated to 500 chars
- **No Storage:** All data in-memory, cleared on disconnect

### Content Security
- **Input Validation:** Sanitize all user-provided text
- **Output Filtering:** Ensure LLM responses are appropriate
- **Rate Limiting:** Prevent abuse

## Testing

### Unit Tests
```python
# Test message parsing
def test_parse_parameters_message():
    message = '{"type": "parameters", "data": {...}}'
    parsed = parse_message(message)
    assert parsed["type"] == "parameters"
    assert "emotion" in parsed["data"]
```

### Integration Tests
```python
# Test WebSocket flow
async def test_websocket_advice_flow():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        # Send parameters
        await ws.send(json.dumps({...}))

        # Receive advice
        response = await ws.recv()
        assert json.loads(response)["type"] == "advice_start"
```

### Load Testing
```bash
# Simulate 100 concurrent connections
locust -f load_test.py --host ws://localhost:8000
```

## Versioning

### Current Version: 1.0.0

### Future Versions
- **1.1.0:** Add authentication
- **1.2.0:** Multi-person tracking
- **2.0.0:** Binary protocol (MessagePack) for efficiency

## Appendix

### Complete Message Type Reference

| Type | Direction | Description |
|------|-----------|-------------|
| `connection` | Server → Client | Connection established |
| `ping` | Client → Server | Keep-alive heartbeat |
| `pong` | Server → Client | Heartbeat response |
| `parameters` | Client → Server | Analysis results |
| `advice_start` | Server → Client | Start of advice stream |
| `advice_chunk` | Server → Client | Streaming advice token |
| `advice_complete` | Server → Client | End of advice stream |
| `error` | Server → Client | Error occurred |
| `status` | Server → Client | Status update |
| `disconnect` | Client → Server | Client disconnecting |
| `disconnect_ack` | Server → Client | Disconnect confirmed |

### Timestamp Format
All timestamps are Unix epoch in milliseconds (JavaScript `Date.now()`).

Example: `1697745123456` = October 19, 2023 11:52:03.456 PM UTC
