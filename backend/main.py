"""
BeneAI Backend - FastAPI Application
"""

import json
import os
import uuid
import time
import base64
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.llm import get_coaching_advice, get_negotiation_coaching
from app.cache import advice_cache
from app.hume_client import get_hume_client, close_hume_client
# Google Speech removed - using OpenAI Whisper for all transcription
from app.interval_aggregator import IntervalAggregator
from app.timeseries_buffer import TimeSeriesBuffer
from app.speech_mapper import SpeechMapper
from app.llm_context_builder import LLMContextBuilder
from app.prompts import INVESTOR_STATE_COLOR, INVESTOR_STATE_EMOJI
from app.session_logger import get_session_logger, close_session_logger
from app.lens_studio import router as lens_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BeneAI API",
    description="AI-powered video call coaching backend",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lens_router)
logger.info("✓ Lens Studio endpoint registered at /api/spectacles/analyze")

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()

        # Initialize time-series components for this client
        interval_aggregator = IntervalAggregator(alpha=0.3, interval_duration=1.0)
        timeseries_buffer = TimeSeriesBuffer(window_size=4, update_interval=4.0)  # LLM updates every 4 seconds (4 intervals)
        speech_mapper = SpeechMapper(silence_threshold=0.99)  # 0.99s pause threshold
        context_builder = LLMContextBuilder()

        self.active_connections[client_id] = {
            "websocket": websocket,
            "connected_at": time.time(),
            "last_message": time.time(),
            "last_frame_time": 0,  # For frame rate throttling
            # Time-series components
            "interval_aggregator": interval_aggregator,
            "timeseries_buffer": timeseries_buffer,
            "speech_mapper": speech_mapper,
            "context_builder": context_builder
        }
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")

        # Create per-client session logger
        session_logger = get_session_logger(client_id, output_dir=".")
        session_logger.start_new_session()
        logger.info(f"Started new logging session for {client_id[:8]} -> {session_logger.output_file.name}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            # Close and save session logger
            close_session_logger(client_id)
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id]["websocket"].send_text(
                json.dumps(message)
            )

manager = ConnectionManager()


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 80)
    logger.info("🚀 Starting BeneAI backend...")
    logger.info("=" * 80)

    # Log service configuration status
    logger.info("Service Configuration:")
    logger.info(f"  ✓ OpenAI API: {'Configured' if settings.openai_api_key else '✗ NOT CONFIGURED'}")
    logger.info(f"  ✓ Hume AI: {'Configured' if settings.hume_api_key else '✗ NOT CONFIGURED'}")
    logger.info(f"  ✓ Google Cloud Speech: {'Configured' if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else '✗ NOT CONFIGURED'}")
    logger.info("")

    # Initialize Hume client if configured
    if settings.hume_api_key:
        hume = await get_hume_client()
        if hume and hume.connected:
            logger.info("✓ Hume AI client ready")
        else:
            logger.warning("✗ Hume AI client failed to connect")
    else:
        logger.info("ℹ Hume AI not configured (optional)")

    # Test OpenAI client initialization
    try:
        from app.llm import get_openai_client
        client = get_openai_client()
        logger.info("✓ OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"✗ OpenAI client initialization failed: {e}")

    logger.info("=" * 80)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down BeneAI backend...")
    await close_hume_client()
    logger.info("Cleanup complete")


# Health check endpoint
@app.get("/")
async def health_check():
    """Health check endpoint"""
    hume = await get_hume_client()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "active_connections": len(manager.active_connections),
        "services": {
            "hume": bool(hume and hume.connected),
            "openai": bool(settings.openai_api_key)
        }
    }


# Cache stats endpoint
@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    return advice_cache.stats()


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""

    client_id = str(uuid.uuid4())

    try:
        # Connect
        await manager.connect(websocket, client_id)

        # Send welcome message
        await manager.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "message": "Welcome to BeneAI coaching service",
            "server_version": "1.0.0",
            "timestamp": int(time.time() * 1000)
        })

        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)  # FIXED: was json.parse (JavaScript syntax)

            # Update last message time
            manager.active_connections[client_id]["last_message"] = time.time()

            # Handle message
            await handle_message(client_id, message)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected normally")

    except Exception as e:
        logger.error(f"Error in WebSocket for client {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_message(client_id: str, message: dict):
    """Handle incoming WebSocket messages"""

    msg_type = message.get("type")
    logger.debug(f"Received message type: {msg_type} from {client_id}")

    if msg_type == "ping":
        # Respond to ping
        await manager.send_message(client_id, {
            "type": "pong",
            "timestamp": int(time.time() * 1000)
        })

    elif msg_type == "video_frame":
        # Handle video frame for emotion detection
        await handle_video_frame(client_id, message.get("data"))

    elif msg_type == "audio_chunk":
        # Handle audio chunk for prosody analysis (Hume only)
        await handle_audio_chunk(client_id, message.get("data"))

    elif msg_type == "transcribed_text":
        # Handle transcribed text for language emotion analysis (Hume only)
        await handle_transcribed_text(client_id, message.get("data"))

    elif msg_type == "parameters":
        # Handle parameters update
        await handle_parameters(client_id, message["data"])

    elif msg_type == "speech_metrics":
        # Handle speech metrics from frontend
        await handle_speech_metrics(client_id, message.get("metrics", {}))

    elif msg_type == "disconnect":
        # Client wants to disconnect
        await manager.send_message(client_id, {
            "type": "disconnect_ack",
            "message": "Goodbye! Good luck with your call."
        })
        manager.disconnect(client_id)

    else:
        # Unknown message type
        await manager.send_message(client_id, {
            "type": "error",
            "error_code": "INVALID_MESSAGE",
            "message": f"Unknown message type: {msg_type}"
        })


async def process_completed_interval(client_id: str, current_time: float):
    """
    Process a completed 1-second interval and check if LLM update is needed

    Args:
        client_id: Client identifier
        current_time: Current timestamp
    """
    try:
        connection = manager.active_connections.get(client_id)
        if not connection:
            return

        aggregator = connection["interval_aggregator"]
        speech_mapper = connection["speech_mapper"]
        timeseries_buffer = connection["timeseries_buffer"]
        context_builder = connection["context_builder"]

        # Get completed interval from aggregator
        logger.info(f"⏱️  [Interval] Getting completed interval for {client_id[:8]}")
        interval_data = aggregator.get_interval(current_time)
        if not interval_data:
            logger.warning(f"⏱️  [Interval] No interval data returned from aggregator!")
            return

        logger.info(f"⏱️  [Interval] Interval created: [{interval_data['interval_start']:.2f}s - {interval_data['interval_end']:.2f}s]")
        logger.info(f"   State: {interval_data['investor_state']}")
        logger.info(f"   Top emotions: {[e['name'] for e in interval_data['top_emotions']]}")
        logger.info(f"   Words before speech mapping: {len(interval_data.get('words', []))}")

        # Update interval with speech data
        logger.info(f"⏱️  [Interval] Updating interval with speech data...")
        interval_data = speech_mapper.update_interval_with_speech(interval_data)

        logger.info(f"⏱️  [Interval] ✅ Interval complete!")
        logger.info(f"   State: {interval_data['investor_state']}")
        logger.info(f"   Words: {len(interval_data['words'])}")
        logger.info(f"   Text: \"{interval_data['full_text']}\"")

        # Send interval data to client for real-time display
        await manager.send_message(client_id, {
            "type": "interval_complete",
            "interval": interval_data,
            "timestamp": int(time.time() * 1000)
        })

        logger.info(f"Interval complete for {client_id}: {interval_data['investor_state']}, "
                   f"{len(interval_data['words'])} words")

        # Log interval to session logger
        session_logger = get_session_logger(client_id, output_dir=".")
        interval_number = timeseries_buffer.total_intervals + 1
        session_logger.log_interval(interval_data, interval_number)
        session_logger.auto_save()  # Auto-save after each interval

        # Add interval to time-series buffer
        should_trigger_llm = timeseries_buffer.add_interval(interval_data, current_time)

        # Check if we should trigger LLM update
        if should_trigger_llm:
            await trigger_llm_update(client_id)

    except Exception as e:
        logger.error(f"Error processing completed interval for {client_id}: {e}")


async def trigger_llm_update(client_id: str):
    """
    Trigger LLM coaching advice based on accumulated time-series data

    Args:
        client_id: Client identifier
    """
    try:
        connection = manager.active_connections.get(client_id)
        if not connection:
            return

        timeseries_buffer = connection["timeseries_buffer"]
        context_builder = connection["context_builder"]

        # Get context from buffer
        intervals = timeseries_buffer.get_context()
        if not intervals:
            return

        buffer_summary = timeseries_buffer.get_summary()
        emotion_trends = timeseries_buffer.get_emotion_trends()

        # Build LLM context
        context = context_builder.build_context(intervals, buffer_summary, emotion_trends)

        # Format for prompt
        formatted_context = context_builder.format_for_prompt(context)

        logger.info(f"Triggering LLM update for {client_id} with {len(intervals)} intervals")

        # DEBUG: Log speech data being sent to LLM
        total_words = 0
        for i, interval in enumerate(intervals):
            words = interval.get("words", [])
            text = interval.get("full_text", "")
            total_words += len(words)
            logger.info(f"  Interval {i+1}: {len(words)} words, text=\"{text}\"")
        logger.info(f"  TOTAL WORDS SENT TO LLM: {total_words}")

        logger.debug(f"LLM Context:\n{formatted_context}")

        # Generate negotiation coaching advice
        coaching_advice = await get_negotiation_coaching(context)

        # Get investor state info
        dominant_state = buffer_summary.get("dominant_state", "neutral")
        state_emoji = INVESTOR_STATE_EMOJI.get(dominant_state, "⚪")
        state_color = INVESTOR_STATE_COLOR.get(dominant_state, "#9ca3af")

        # Send to client
        await manager.send_message(client_id, {
            "type": "llm_context_update",
            "context": context,
            "formatted_text": formatted_context,
            "coaching_advice": coaching_advice,
            "investor_state": dominant_state,
            "state_emoji": state_emoji,
            "state_color": state_color,
            "timestamp": int(time.time() * 1000)
        })

        # Increment counter
        timeseries_buffer.increment_llm_updates()

        # Log LLM update to session logger
        session_logger = get_session_logger(client_id, output_dir=".")
        update_number = timeseries_buffer.llm_updates_sent
        session_logger.log_llm_update(
            context,
            formatted_context,
            coaching_advice,
            time.time(),
            update_number
        )
        session_logger.auto_save()  # Auto-save after LLM update

        logger.info(f"Coaching advice sent for {client_id}: {coaching_advice}")

    except Exception as e:
        logger.error(f"Error triggering LLM update for {client_id}: {e}")


async def handle_video_frame(client_id: str, frame_data: str):
    """Handle incoming video frame for emotion detection"""

    try:
        current_time = time.time()
        connection = manager.active_connections.get(client_id)

        if not connection:
            return

        # Note: Frame rate throttling is now handled entirely by frontend (2 FPS)
        # Backend processes all received frames immediately for lower latency
        connection["last_frame_time"] = current_time

        # Analyze with Hume AI
        logger.debug(f"Processing frame with Hume AI for {client_id}")
        hume = await get_hume_client()

        if not hume or not hume.connected:
            logger.warning(f"Hume AI not available for {client_id}")
            await manager.send_message(client_id, {
                "type": "emotion_error",
                "message": "Hume AI not available",
                "timestamp": int(time.time() * 1000)
            })
            return

        emotion_data = await hume.analyze_face(frame_data)

        # Handle no detection
        if not emotion_data:
            logger.warning(f"Hume analyze_face returned None for {client_id}")
            await manager.send_message(client_id, {
                "type": "emotion_error",
                "message": "Failed to detect emotions (Hume returned no data)",
                "timestamp": int(time.time() * 1000)
            })
            return

        # Check if face was detected
        if not emotion_data.get("primary_emotion"):
            logger.info(f"No face detected in frame for {client_id}. Hume response: {emotion_data.keys() if isinstance(emotion_data, dict) else type(emotion_data)}")
            await manager.send_message(client_id, {
                "type": "emotion_result",
                "detected": False,
                "message": "No face detected in frame",
                "timestamp": int(time.time() * 1000)
            })
            return

        # Send emotion result to client
        await manager.send_message(client_id, {
            "type": "emotion_result",
            "detected": True,
            "emotion": emotion_data["primary_emotion"],
            "confidence": emotion_data["confidence"],
            "all_emotions": emotion_data["all_emotions"],
            "investor_state": emotion_data["investor_state"],
            "top_emotions": emotion_data.get("top_emotions", []),
            "face_bbox": emotion_data.get("face_bbox"),
            "timestamp": int(time.time() * 1000),
            "service": "hume"
        })

        logger.info(f"Emotion detected for {client_id}: {emotion_data['investor_state']} "
                   f"({emotion_data['primary_emotion']}: {emotion_data['confidence']:.2f})")

        # Log emotion to session logger
        session_logger = get_session_logger(client_id, output_dir=".")
        session_logger.log_emotion(emotion_data, current_time)

        # Add frame to interval aggregator
        aggregator = connection["interval_aggregator"]
        aggregator.add_frame(emotion_data, current_time, face_detected=True)

        # Check if interval is complete
        if aggregator.interval_complete(current_time):
            await process_completed_interval(client_id, current_time)

    except Exception as e:
        logger.error(f"Error handling video frame for {client_id}: {e}")
        await manager.send_message(client_id, {
            "type": "emotion_error",
            "message": "Internal error processing frame",
            "timestamp": int(time.time() * 1000)
        })


async def transcribe_with_whisper(audio_base64: str, mime_type: str) -> dict:
    """
    Transcribe audio using OpenAI Whisper API (fallback for Google Speech)

    Args:
        audio_base64: Base64-encoded audio data
        mime_type: MIME type of audio

    Returns:
        Dictionary with transcription results (same format as Google Speech)
    """
    try:
        from app.llm import get_openai_client
        import io
        import tempfile

        # Decode audio
        audio_bytes = base64.b64decode(audio_base64)
        logger.info(f"🎙️  Whisper: Transcribing {len(audio_bytes)} bytes ({mime_type})")

        # Whisper API requires a file-like object
        # Create temporary file with proper extension
        ext_map = {
            "audio/webm": ".webm",
            "audio/webm;codecs=opus": ".webm",
            "audio/mp4": ".mp4",
            "audio/mp3": ".mp3",
            "audio/wav": ".wav"
        }
        ext = ext_map.get(mime_type, ".webm")

        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name

        try:
            # Call Whisper API
            client = get_openai_client()
            with open(tmp_file_path, "rb") as audio_file:
                response = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",  # Get word timestamps
                    timestamp_granularities=["word"]
                )

            # Parse response into Google Speech format
            words = []
            if hasattr(response, 'words') and response.words:
                for word_data in response.words:
                    words.append({
                        "word": word_data.word,
                        "start": word_data.start,
                        "end": word_data.end,
                        "confidence": 1.0  # Whisper doesn't provide confidence
                    })

            result = {
                "transcript": response.text.strip() if response.text else "",
                "words": words,
                "confidence": 1.0,
                "duration": words[-1]["end"] if words else 0.0,
                "word_count": len(words)
            }

            logger.info(f"✅ Whisper transcription: \"{result['transcript']}\" ({len(words)} words)")
            return result

        finally:
            # Clean up temp file
            import os
            try:
                os.unlink(tmp_file_path)
            except:
                pass

    except Exception as e:
        logger.error(f"❌ Error transcribing with Whisper: {e}")
        logger.exception("Full traceback:")
        return None


async def handle_audio_chunk(client_id: str, audio_data: dict):
    """
    Handle incoming audio chunk for speech-to-text transcription

    Args:
        client_id: Client identifier
        audio_data: Dictionary containing:
            - audio: base64-encoded audio
            - mimeType: MIME type of audio
            - duration: Duration in seconds
            - chunkNumber: Sequential chunk number
    """
    # DEBUG: Entry logging
    logger.info(f"🎤 === handle_audio_chunk called for {client_id[:8]} ===")
    logger.info(f"   ✅ AUDIO CHUNK RECEIVED FROM FRONTEND!")
    logger.debug(f"   Audio data keys: {list(audio_data.keys()) if audio_data else 'None'}")

    try:
        # Use OpenAI Whisper for all transcription (more accurate than Google Speech)
        logger.info(f"🎙️  Using OpenAI Whisper for transcription")

        # Extract audio data
        audio_base64 = audio_data.get("audio", "")
        mime_type = audio_data.get("mimeType", "audio/webm")
        duration = audio_data.get("duration", 0)
        chunk_number = audio_data.get("chunkNumber", 0)

        # ENHANCED LOGGING: Show actual data
        audio_bytes_length = len(audio_base64)
        logger.info(f"📦 Audio chunk #{chunk_number}: base64={audio_bytes_length} chars, duration={duration}s, mime={mime_type}")

        # Decode to check actual byte size
        try:
            decoded_bytes = base64.b64decode(audio_base64)
            actual_size = len(decoded_bytes)

            # DIAGNOSTIC: Check if audio size is reasonable for speech
            expected_min_size = duration * 5000  # ~5KB per second for compressed audio
            expected_max_size = duration * 50000  # ~50KB per second for high quality

            if actual_size < expected_min_size:
                logger.warning(f"⚠️  Audio chunk #{chunk_number} is very small ({actual_size} bytes for {duration}s)")
                logger.warning(f"   Expected minimum: ~{expected_min_size:.0f} bytes")
                logger.warning(f"   This suggests mostly silence or very low microphone volume")
                logger.warning(f"   💡 Try speaking LOUDER or check microphone settings!")
            elif actual_size > expected_max_size:
                logger.info(f"📊 Audio chunk #{chunk_number} is large ({actual_size} bytes) - good signal strength")
            else:
                logger.info(f"✅ Audio chunk #{chunk_number} size looks good ({actual_size} bytes for {duration}s)")
            logger.info(f"   → Decoded size: {actual_size} bytes ({actual_size/1024:.2f} KB)")

            # Log first few bytes to verify it's not empty/corrupted
            logger.debug(f"   → First 20 bytes: {decoded_bytes[:20].hex() if actual_size > 0 else 'EMPTY'}")
        except Exception as decode_err:
            logger.error(f"   ❌ Failed to decode base64 audio: {decode_err}")

        if not audio_base64:
            logger.warning(f"❌ No audio data in chunk from {client_id[:8]}")
            return

        # Transcribe with OpenAI Whisper
        logger.info(f"🔄 Starting Whisper transcription for chunk #{chunk_number} from {client_id[:8]} ({duration}s)")
        transcription = await transcribe_with_whisper(audio_base64, mime_type)

        # ENHANCED LOGGING: Check transcription result
        if not transcription:
            logger.warning(f"❌ Whisper returned None for chunk #{chunk_number} (possible silence or error)")
            return

        if not transcription.get("transcript"):
            logger.info(f"🔇 Empty transcript for chunk #{chunk_number} - likely silence or background noise")
            logger.debug(f"   Transcription object: {transcription}")
            return

        # SUCCESS - we got text!
        logger.info(f"✅ Transcription SUCCESS for chunk #{chunk_number}!")
        logger.info(f"   Transcript: \"{transcription['transcript']}\"")

        # Get connection data
        connection = manager.active_connections.get(client_id)
        if not connection:
            logger.error(f"❌ Connection not found for {client_id[:8]} - cannot add words to speech mapper!")
            return

        speech_mapper = connection["speech_mapper"]
        current_time = time.time()

        # Add words to speech mapper with actual timestamps from Google Speech/Whisper
        words = transcription.get("words", [])
        logger.info(f"🗣️  [SpeechMapper] Adding {len(words)} words to speech mapper for {client_id[:8]}")

        for i, word_data in enumerate(words):
            # Timestamps are relative to chunk start
            # Convert to absolute time
            absolute_time = current_time - duration + word_data["start"]

            logger.info(f"   Word {i+1}/{len(words)}: \"{word_data['word']}\" @ {absolute_time:.2f}s (confidence: {word_data['confidence']:.2f})")

            speech_mapper.add_word(
                word=word_data["word"],
                timestamp=absolute_time,
                confidence=word_data["confidence"]
            )

        logger.info(f"🗣️  [SpeechMapper] ✅ Added {len(words)} words to mapper")
        logger.info(f"   Full transcript: \"{transcription['transcript']}\"")

        # Optionally send transcription back to frontend for display
        await manager.send_message(client_id, {
            "type": "transcription_result",
            "transcript": transcription["transcript"],
            "word_count": len(words),
            "confidence": transcription["confidence"],
            "chunk_number": chunk_number,
            "timestamp": int(time.time() * 1000)
        })

    except Exception as e:
        logger.error(f"Error handling audio chunk for {client_id}: {e}")


async def handle_speech_metrics(client_id: str, metrics: dict):
    """
    Handle speech metrics from frontend Web Speech API

    Args:
        client_id: Client identifier
        metrics: Speech metrics dict containing:
            - wordsPerMinute: int
            - recentTranscript: str (last 500 chars of transcript)
            - fillerWords: dict with total count
            - pauseFrequency: float
            - volumeLevel: float
    """
    try:
        connection = manager.active_connections.get(client_id)
        if not connection:
            return

        speech_mapper = connection["speech_mapper"]

        # Extract transcript
        transcript = metrics.get("recentTranscript", "")
        wpm = metrics.get("wordsPerMinute", 0)

        logger.debug(f"Received speech metrics from {client_id}: WPM={wpm}, transcript_length={len(transcript)}")

        # If we have new transcript text, process it
        if transcript:
            # Split into words and add to speech mapper
            words = transcript.split()
            current_time = time.time()

            # Add words with approximate timestamps
            # Note: Web Speech API doesn't provide word-level timestamps
            # so we distribute words evenly across the speaking period
            for i, word in enumerate(words[-10:]):  # Process last 10 words
                # Approximate timestamp (spread over last 2 seconds)
                word_time = current_time - (2.0 * (1 - i / max(len(words[-10:]), 1)))
                speech_mapper.add_word(word, word_time, confidence=1.0)

            logger.info(f"Processed {len(words)} words from {client_id}, WPM: {wpm}")
        else:
            logger.debug(f"No transcript from {client_id} (WPM: {wpm})")

    except Exception as e:
        logger.error(f"Error handling speech metrics for {client_id}: {e}")


async def handle_transcribed_text(client_id: str, data: dict):
    """Handle transcribed text for language emotion analysis (Hume only)"""

    if not settings.hume_enable_language:
        logger.debug(f"Language analysis disabled for {client_id}")
        return

    # Extract text and optional timing info
    text = data.get("text") if isinstance(data, dict) else data
    timestamp = data.get("timestamp", time.time()) if isinstance(data, dict) else time.time()

    if not text or len(text.strip()) == 0:
        return

    try:
        connection = manager.active_connections.get(client_id)
        if not connection:
            return

        # Add to speech mapper
        speech_mapper = connection["speech_mapper"]

        # Check if we have word-level timestamps or just a segment
        if isinstance(data, dict) and "words" in data:
            # Word-level timestamps provided
            for word_data in data["words"]:
                speech_mapper.add_word(
                    word_data["word"],
                    word_data["timestamp"],
                    word_data.get("confidence", 1.0)
                )
        else:
            # Segment-level only - estimate word timestamps
            start_time = data.get("start_time", timestamp) if isinstance(data, dict) else timestamp
            end_time = data.get("end_time", timestamp) if isinstance(data, dict) else timestamp
            speech_mapper.add_transcript_segment(text, start_time, end_time)

        # Get Hume client
        hume = await get_hume_client()
        if not hume or not hume.connected:
            logger.warning(f"Hume AI not available for language analysis")
            return

        # Analyze text
        logger.debug(f"Analyzing language emotions for {client_id}: {text[:50]}...")
        language_data = await hume.analyze_text(text)

        if not language_data or not language_data.get("predictions"):
            logger.debug(f"No language data detected for {client_id}")
            return

        # Send language result to client
        await manager.send_message(client_id, {
            "type": "language_result",
            "text": text,
            "predictions": language_data["predictions"],
            "timestamp": int(time.time() * 1000)
        })

        logger.info(f"Language analysis complete for {client_id}: {len(language_data['predictions'])} words")

    except Exception as e:
        logger.error(f"Error handling transcribed text for {client_id}: {e}")


async def handle_parameters(client_id: str, parameters: dict):
    """Handle parameters update and generate advice"""

    try:
        # Check cache first
        cached_advice = advice_cache.get(parameters)

        if cached_advice:
            # Send cached response
            await manager.send_message(client_id, {
                "type": "advice_complete",
                "request_id": str(uuid.uuid4()),
                "full_text": cached_advice,
                "timestamp": int(time.time() * 1000),
                "metadata": {
                    "cached": True,
                    "latency_ms": 0
                }
            })
            return

        # Generate new advice
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Send advice start
        await manager.send_message(client_id, {
            "type": "advice_start",
            "request_id": request_id,
            "timestamp": int(time.time() * 1000)
        })

        # Stream advice
        full_advice = []
        index = 0

        async for chunk in get_coaching_advice(parameters):
            # Send chunk
            await manager.send_message(client_id, {
                "type": "advice_chunk",
                "request_id": request_id,
                "chunk": chunk,
                "index": index
            })

            full_advice.append(chunk)
            index += 1

        # Send complete
        full_text = "".join(full_advice)
        latency_ms = int((time.time() - start_time) * 1000)

        await manager.send_message(client_id, {
            "type": "advice_complete",
            "request_id": request_id,
            "full_text": full_text,
            "timestamp": int(time.time() * 1000),
            "metadata": {
                "cached": False,
                "latency_ms": latency_ms
            }
        })

        # Cache the advice
        advice_cache.set(parameters, full_text)

        logger.info(f"Advice generated for {client_id} in {latency_ms}ms")

    except Exception as e:
        logger.error(f"Error handling parameters for {client_id}: {e}")

        await manager.send_message(client_id, {
            "type": "error",
            "error_code": "SERVER_ERROR",
            "message": "Failed to generate advice. Please try again."
        })


# Run with: uvicorn main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
