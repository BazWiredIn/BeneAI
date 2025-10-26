"""
Lens Studio HTTP endpoint for Spectacles frame uploads
"""
import logging
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.hume_client import get_hume_client
from app.llm import get_negotiation_coaching

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/spectacles/analyze")
async def analyze_spectacles_frame(request: Request):
    """
    Analyze frame from Spectacles via HTTPS
    
    Expected payload:
    {
        "image": "base64_encoded_jpeg",
        "timestamp": 1234567890
    }
    
    Returns:
    {
        "suggestion": "Maintain eye contact. They seem interested.",
        "emotion": "receptive",
        "confidence": 0.85
    }
    """
    try:
        # Parse request
        data = await request.json()
        image_base64 = data.get("image")
        timestamp = data.get("timestamp", int(time.time() * 1000))
        
        if not image_base64:
            return JSONResponse(
                {"error": "Missing 'image' field"},
                status_code=400
            )
        
        logger.info(f"📱 [Spectacles] Received frame at {timestamp}")
        
        # Analyze with Hume AI
        hume = await get_hume_client()
        if not hume or not hume.connected:
            return JSONResponse(
                {"error": "Hume AI not available"},
                status_code=503
            )
        
        emotion_data = await hume.analyze_face(image_base64)
        
        if not emotion_data:
            return JSONResponse({
                "suggestion": "Waiting for clear view of face...",
                "emotion": "neutral",
                "confidence": 0
            })
        
        # Generate coaching suggestion
        investor_state = emotion_data.get("investor_state", "neutral")
        primary_emotion = emotion_data.get("primary_emotion", "neutral")
        confidence = emotion_data.get("confidence", 0)
        
        # Simple state-based suggestions (fast, no LLM needed for MVP)
        suggestions = {
            "skeptical": "They seem doubtful. Share a concrete example.",
            "evaluative": "They're thinking. Pause and let them process.",
            "receptive": "They're engaged. Ask a closing question.",
            "positive": "Great! Reinforce with confidence.",
            "neutral": "Continue presenting clearly."
        }
        
        suggestion = suggestions.get(investor_state, "Stay confident and clear.")
        
        logger.info(f"✅ [Spectacles] Response: {investor_state} -> \"{suggestion}\"")
        
        return JSONResponse({
            "suggestion": suggestion,
            "emotion": investor_state,
            "confidence": confidence,
            "primary_emotion": primary_emotion,
            "timestamp": timestamp
        })
        
    except Exception as e:
        logger.error(f"❌ [Spectacles] Error: {e}")
        return JSONResponse(
            {"error": "Internal server error", "suggestion": "System error. Keep going."},
            status_code=500
        )
