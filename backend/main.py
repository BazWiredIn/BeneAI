"""
BeneAI Backend - FastAPI Application
"""

import json
import uuid
import time
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import settings
from app.llm import get_coaching_advice
from app.cache import advice_cache
from app.hume_client import get_hume_client, close_hume_client


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

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = {
            "websocket": websocket,
            "connected_at": time.time(),
            "last_message": time.time(),
            "last_frame_time": 0  # For frame rate throttling
        }
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
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
    logger.info("Starting BeneAI backend...")

    # Initialize Hume client if configured
    if settings.hume_api_key:
        hume = await get_hume_client()
        if hume and hume.connected:
            logger.info("Hume AI client ready")
        else:
            logger.warning("Hume AI client failed to connect")
    else:
        logger.info("Hume AI not configured (optional)")


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
            message = json.parse(data)

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


async def handle_video_frame(client_id: str, frame_data: str):
    """Handle incoming video frame for emotion detection"""

    try:
        # Frame rate throttling (3-5 FPS)
        current_time = time.time()
        connection = manager.active_connections.get(client_id)

        if not connection:
            return

        last_frame_time = connection["last_frame_time"]

        # Use Hume frame rate for throttling
        min_interval = 1.0 / settings.hume_frame_rate

        # Skip frame if too soon
        if current_time - last_frame_time < min_interval:
            logger.debug(f"Skipping frame for {client_id} (throttling)")
            return

        # Update last frame time
        connection["last_frame_time"] = current_time

        # Analyze with Hume AI
        logger.debug(f"Processing frame with Hume AI for {client_id}")
        hume = await get_hume_client()

        if not hume or not hume.connected:
            await manager.send_message(client_id, {
                "type": "emotion_error",
                "message": "Hume AI not available",
                "timestamp": int(time.time() * 1000)
            })
            return

        emotion_data = await hume.analyze_face(frame_data)

        # Handle no detection
        if not emotion_data:
            await manager.send_message(client_id, {
                "type": "emotion_error",
                "message": "Failed to detect emotions",
                "timestamp": int(time.time() * 1000)
            })
            return

        # Check if face was detected
        if not emotion_data.get("primary_emotion"):
            await manager.send_message(client_id, {
                "type": "emotion_result",
                "detected": False,
                "message": "No face detected",
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

    except Exception as e:
        logger.error(f"Error handling video frame for {client_id}: {e}")
        await manager.send_message(client_id, {
            "type": "emotion_error",
            "message": "Internal error processing frame",
            "timestamp": int(time.time() * 1000)
        })


async def handle_audio_chunk(client_id: str, audio_data: str):
    """Handle incoming audio chunk for prosody analysis (Hume only)"""

    if not settings.hume_enable_prosody:
        logger.debug(f"Prosody analysis disabled for {client_id}")
        return

    try:
        # Get Hume client
        hume = await get_hume_client()
        if not hume or not hume.connected:
            logger.warning(f"Hume AI not available for audio analysis")
            return

        # Decode base64 audio data
        if "," in audio_data and audio_data.startswith("data:"):
            audio_data = audio_data.split(",", 1)[1]

        audio_bytes = base64.b64decode(audio_data)

        # Analyze prosody
        logger.debug(f"Analyzing audio prosody for {client_id}")
        prosody_data = await hume.analyze_audio(audio_bytes)

        if not prosody_data:
            logger.debug(f"No prosody data detected for {client_id}")
            return

        # Send prosody result to client
        await manager.send_message(client_id, {
            "type": "prosody_result",
            "primary_emotion": prosody_data["primary_emotion"],
            "confidence": prosody_data["confidence"],
            "all_emotions": prosody_data["all_emotions"],
            "top_emotions": prosody_data["top_emotions"],
            "timestamp": int(time.time() * 1000)
        })

        logger.info(f"Prosody detected for {client_id}: {prosody_data['primary_emotion']} "
                   f"({prosody_data['confidence']:.2f})")

    except Exception as e:
        logger.error(f"Error handling audio chunk for {client_id}: {e}")


async def handle_transcribed_text(client_id: str, text: str):
    """Handle transcribed text for language emotion analysis (Hume only)"""

    if not settings.hume_enable_language:
        logger.debug(f"Language analysis disabled for {client_id}")
        return

    if not text or len(text.strip()) == 0:
        return

    try:
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
