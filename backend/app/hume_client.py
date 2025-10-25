"""
Hume AI Client
Handles multi-modal emotion detection using Hume AI's Expression Measurement API
Supports: Facial Expression, Speech Prosody, and Emotional Language via WebSocket streaming
"""

import asyncio
import base64
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config, StreamFace, StreamLanguage
from hume.expression_measurement.stream.socket_client import StreamConnectOptions

from app.config import settings

logger = logging.getLogger(__name__)


class HumeClient:
    """Client for Hume AI Expression Measurement API via WebSocket streaming"""

    def __init__(self):
        self.api_key = settings.hume_api_key
        self.enable_face = settings.hume_enable_face
        self.enable_prosody = settings.hume_enable_prosody
        self.enable_language = settings.hume_enable_language

        # Initialize Hume client
        if self.api_key:
            self.client = AsyncHumeClient(api_key=self.api_key)
            logger.info("Hume AI client initialized successfully")
        else:
            self.client = None
            logger.warning("Hume API key not configured, client disabled")

        # WebSocket connection (managed per session)
        self.socket = None
        self.connected = False

        # Note: Hume requires separate connections for different model types
        # when mixing face/prosody with text. We'll create connections on-demand.

    async def connect(self) -> bool:
        """
        Establish WebSocket connection to Hume AI

        Returns:
            True if connected successfully, False otherwise
        """
        if not self.client:
            logger.error("Cannot connect: Hume client not initialized")
            return False

        try:
            # Configure models based on enabled features
            model_config = self._build_model_config()

            if not model_config:
                logger.error("No models enabled in configuration")
                return False

            # Create stream connection options
            stream_options = StreamConnectOptions(config=model_config)

            # Connect to WebSocket (store the context manager, not the entered value)
            logger.info("Connecting to Hume AI WebSocket...")
            connection_manager = self.client.expression_measurement.stream.connect(options=stream_options)
            self.socket = await connection_manager.__aenter__()
            self._connection_manager = connection_manager  # Store for proper cleanup

            self.connected = True
            logger.info("Successfully connected to Hume AI WebSocket")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Hume AI: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Hume AI WebSocket"""
        if self.socket:
            try:
                # Exit the context manager properly
                if hasattr(self, '_connection_manager'):
                    await self._connection_manager.__aexit__(None, None, None)
                logger.info("Disconnected from Hume AI WebSocket")
            except Exception as e:
                logger.error(f"Error disconnecting from Hume AI: {e}")
            finally:
                self.socket = None
                self.connected = False
                if hasattr(self, '_connection_manager'):
                    delattr(self, '_connection_manager')

    def _build_model_config(self) -> Optional[Config]:
        """
        Build model configuration based on enabled features

        Returns:
            Config object with enabled models
        """
        config_dict = {}

        if self.enable_face:
            config_dict["face"] = StreamFace()
            logger.debug("Facial Expression model enabled")

        if self.enable_prosody:
            # In SDK v0.12, prosody uses dict config, not a class
            config_dict["prosody"] = {}
            logger.debug("Speech Prosody model enabled")

        if self.enable_language:
            config_dict["language"] = StreamLanguage()
            logger.debug("Emotional Language model enabled")

        if not config_dict:
            return None

        return Config(**config_dict)

    async def analyze_face(self, image_data: str) -> Optional[Dict]:
        """
        Analyze facial expressions from base64 encoded image

        Args:
            image_data: Base64 encoded image string (with or without data URI prefix)

        Returns:
            Dictionary with facial emotion analysis:
            {
                "primary_emotion": str,
                "confidence": float,
                "all_emotions": dict,
                "face_bbox": dict,
                "investor_state": str,
                "top_emotions": list  # Top 5 emotions
            }
        """
        if not self.client:
            logger.warning("Cannot analyze face: Hume client not initialized")
            return None

        try:
            # Remove data URI prefix if present
            if "," in image_data and image_data.startswith("data:"):
                image_data = image_data.split(",", 1)[1]

            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_data)

            # Hume SDK v0.12 requires file path, so write to temp file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                tmp_file.write(image_bytes)
                tmp_path = tmp_file.name

            # Create a temporary connection with ONLY face model
            # (mixing face with language/prosody causes errors when sending images)
            logger.debug(f"Creating face-only connection for image analysis")
            face_config = Config(face=StreamFace())
            stream_options = StreamConnectOptions(config=face_config)

            async with self.client.expression_measurement.stream.connect(options=stream_options) as socket:
                try:
                    # Send image to Hume AI
                    logger.debug("Sending image to Hume AI for facial analysis")
                    result = await socket.send_file(tmp_path)

                    # Debug: Check what we got back
                    logger.debug(f"Result type: {type(result)}")
                    logger.debug(f"Has 'face' attr: {hasattr(result, 'face')}")
                    if hasattr(result, 'face'):
                        logger.debug(f"Face result: {result.face}")
                    if hasattr(result, 'error'):
                        logger.warning(f"API Error: {result.error}")
                finally:
                    # Clean up temp file
                    Path(tmp_path).unlink(missing_ok=True)

                # Parse facial expression results
                if not result or not hasattr(result, 'face'):
                    logger.warning(f"No facial data in Hume AI response. Result: {result}")
                    return None

                face_result = result.face
                if not face_result or not face_result.predictions:
                    logger.debug("No faces detected in image")
                    return None

                # Get first face (primary subject - investor in demo)
                first_face = face_result.predictions[0]

                # Extract emotions
                emotions_dict = {emotion.name: emotion.score for emotion in first_face.emotions}

                # Map to investor state FIRST
                investor_state = self._map_to_investor_state(emotions_dict)

                # Find primary emotion FROM the winning state category (not globally)
                primary_emotion = self._get_primary_emotion_for_state(emotions_dict, investor_state)

                # Get top 5 emotions
                top_emotions = sorted(emotions_dict.items(), key=lambda x: x[1], reverse=True)[:5]

                # Extract bounding box if available
                bbox = None
                if hasattr(first_face, 'bbox'):
                    bbox = {
                        "x": first_face.bbox.x,
                        "y": first_face.bbox.y,
                        "w": first_face.bbox.w,
                        "h": first_face.bbox.h
                    }

                result_data = {
                    "primary_emotion": primary_emotion[0],
                    "confidence": primary_emotion[1],
                    "all_emotions": emotions_dict,
                    "face_bbox": bbox,
                    "investor_state": investor_state,
                    "top_emotions": [{"name": name, "score": score} for name, score in top_emotions],
                    "num_faces": len(face_result.predictions)
                }

                logger.info(f"Facial analysis complete: {investor_state} ({primary_emotion[0]}: {primary_emotion[1]:.3f})")
                return result_data

        except Exception as e:
            logger.error(f"Error analyzing face with Hume AI: {e}")
            return None

    async def analyze_audio(self, audio_data: bytes) -> Optional[Dict]:
        """
        Analyze speech prosody from audio bytes

        Args:
            audio_data: Audio bytes (WAV, MP3, etc.)

        Returns:
            Dictionary with prosody analysis:
            {
                "primary_emotion": str,
                "confidence": float,
                "all_emotions": dict,
                "top_emotions": list
            }
        """
        if not self.connected or not self.socket:
            logger.warning("Cannot analyze audio: not connected to Hume AI")
            return None

        try:
            # Hume SDK v0.12 requires file path, so write to temp file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_path = tmp_file.name

            try:
                # Send audio to Hume AI
                logger.debug("Sending audio to Hume AI for prosody analysis")
                result = await self.socket.send_file(tmp_path)
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

            # Parse prosody results
            if not result or not hasattr(result, 'prosody'):
                logger.debug("No prosody data in Hume AI response")
                return None

            prosody_result = result.prosody
            if not prosody_result or not prosody_result.predictions:
                logger.debug("No prosody detected in audio")
                return None

            # Get first prediction
            first_prediction = prosody_result.predictions[0]

            # Extract emotions
            emotions_dict = {emotion.name: emotion.score for emotion in first_prediction.emotions}

            # Find primary emotion
            primary_emotion = max(emotions_dict.items(), key=lambda x: x[1])

            # Get top 5 emotions
            top_emotions = sorted(emotions_dict.items(), key=lambda x: x[1], reverse=True)[:5]

            result_data = {
                "primary_emotion": primary_emotion[0],
                "confidence": primary_emotion[1],
                "all_emotions": emotions_dict,
                "top_emotions": [{"name": name, "score": score} for name, score in top_emotions]
            }

            logger.info(f"Prosody analysis complete: {primary_emotion[0]} ({primary_emotion[1]:.3f})")
            return result_data

        except Exception as e:
            logger.error(f"Error analyzing audio with Hume AI: {e}")
            return None

    async def analyze_text(self, text: str) -> Optional[Dict]:
        """
        Analyze emotional language from text

        Args:
            text: Text to analyze

        Returns:
            Dictionary with language emotion analysis:
            {
                "predictions": list of {
                    "text": str,
                    "primary_emotion": str,
                    "confidence": float,
                    "emotions": dict
                }
            }
        """
        if not self.client:
            logger.warning("Cannot analyze text: Hume client not initialized")
            return None

        try:
            # Create a temporary connection with ONLY language model
            # (mixing face/prosody with text causes errors in Hume API)
            logger.debug(f"Creating language-only connection for text analysis")
            language_config = Config(language=StreamLanguage())
            stream_options = StreamConnectOptions(config=language_config)

            async with self.client.expression_measurement.stream.connect(options=stream_options) as socket:
                # Send text to Hume AI
                logger.debug(f"Sending text to Hume AI for language analysis: {text[:50]}...")
                result = await socket.send_text(text)

                # Debug: Check what we got back
                logger.debug(f"Result type: {type(result)}")
                logger.debug(f"Result attributes: {dir(result) if result else 'None'}")

                # Parse language results
                if not result or not hasattr(result, 'language'):
                    logger.warning(f"No language data in Hume AI response. Result: {result}")
                    return None

                language_result = result.language
                if not language_result or not language_result.predictions:
                    logger.debug("No predictions in language analysis")
                    return None

                # Parse each word/phrase prediction
                predictions = []
                for prediction in language_result.predictions:
                    emotions_dict = {emotion.name: emotion.score for emotion in prediction.emotions}
                    primary_emotion = max(emotions_dict.items(), key=lambda x: x[1])

                    predictions.append({
                        "text": prediction.text,
                        "primary_emotion": primary_emotion[0],
                        "confidence": primary_emotion[1],
                        "emotions": emotions_dict
                    })

                logger.info(f"Language analysis complete: {len(predictions)} predictions")
                return {"predictions": predictions}

        except Exception as e:
            logger.error(f"Error analyzing text with Hume AI: {e}")
            logger.exception("Full traceback:")  # This will show the full error
            return None

    def _get_primary_emotion_for_state(self, emotions: Dict[str, float], state: str) -> tuple:
        """
        Get the highest scoring emotion that belongs to the given state category

        This ensures the displayed primary emotion matches the state.
        For example, if state is "enthusiastic", only show Joy/Excitement/Admiration,
        not Confusion even if Confusion has a higher raw score.

        Args:
            emotions: Dictionary of all emotion scores
            state: The determined engagement state for social interactions

        Returns:
            Tuple of (emotion_name, score)
        """
        # Define which emotions belong to each social interaction state
        state_emotions = {
            "closed-off": [
                "Anger", "Fear", "Anxiety (negative)", "Distress", "Contempt",
                "Disgust", "Boredom", "Awkwardness", "Disapproval", "Sadness",
                "Doubt", "Pain"
            ],
            "baseline": [
                "Calmness", "Aesthetic Appreciation", "Contemplation"
            ],
            "curious": [
                "Interest", "Curiosity", "Concentration", "Realization",
                "Surprise (positive)"
            ],
            "amused": [
                "Amusement", "Joy", "Satisfaction", "Entrancement"
            ],
            "enthusiastic": [
                "Joy", "Excitement", "Admiration", "Triumph", "Ecstasy",
                "Surprise (positive)"
            ],
            "thinking": [
                "Contemplation", "Concentration", "Confusion", "Realization"
            ],
            "neutral": []  # For neutral, use global max
        }

        # Get emotions for this state
        relevant_emotions = state_emotions.get(state, [])

        if not relevant_emotions:
            # Neutral or unknown state - use global max
            return max(emotions.items(), key=lambda x: x[1])

        # Find highest scoring emotion from this state's category
        filtered_emotions = {
            name: score for name, score in emotions.items()
            if name in relevant_emotions
        }

        if filtered_emotions:
            return max(filtered_emotions.items(), key=lambda x: x[1])
        else:
            # Fallback: if no emotions from category found, use global max
            return max(emotions.items(), key=lambda x: x[1])

    def _map_to_investor_state(self, emotions: Dict[str, float]) -> str:
        """
        Map Hume's 53 emotions to social interaction states

        Social Interaction States:
        - closed-off: Disengaged, uncomfortable, wants to exit
        - baseline: Neutral, just met, scanning environment
        - curious: Interested, engaged, asking/answering questions
        - amused: Humor landed, lighthearted, positive micro-expressions
        - enthusiastic: Strong positive connection, animated, excited
        - thinking: Processing, contemplating, considering response

        Args:
            emotions: Dictionary of emotion names to scores

        Returns:
            Social interaction state string
        """
        # Hume provides 53 emotions - we'll map the most relevant ones

        # Closed-off indicators (disengaged, uncomfortable, wants to exit)
        closed_off_score = (
            emotions.get("Anger", 0) * 0.7 +
            emotions.get("Fear", 0) * 0.6 +
            emotions.get("Anxiety (negative)", 0) * 0.6 +
            emotions.get("Distress", 0) * 0.5 +
            emotions.get("Contempt", 0) * 0.5 +
            emotions.get("Disgust", 0) * 0.4 +
            emotions.get("Boredom", 0) * 0.6 +           # High weight for disengagement
            emotions.get("Awkwardness", 0) * 0.7 +       # High weight for social discomfort
            emotions.get("Disapproval", 0) * 0.3 +
            emotions.get("Sadness", 0) * 0.3 +
            emotions.get("Doubt", 0) * 0.3 +
            emotions.get("Pain", 0) * 0.2
        )

        # Baseline indicators (neutral, calm, just met)
        baseline_score = (
            emotions.get("Calmness", 0) * 0.8 +
            emotions.get("Aesthetic Appreciation", 0) * 0.3 +
            emotions.get("Contemplation", 0) * 0.2        # Mild thinking without strong engagement
        )

        # Curious indicators (interested, engaged in conversation)
        curious_score = (
            emotions.get("Interest", 0) * 0.9 +           # PRIMARY indicator
            emotions.get("Curiosity", 0) * 0.9 +          # PRIMARY indicator
            emotions.get("Concentration", 0) * 0.5 +      # Focused attention
            emotions.get("Realization", 0) * 0.5 +        # "Aha" moments in conversation
            emotions.get("Surprise (positive)", 0) * 0.4
        )

        # Amused indicators (humor landed, lighthearted)
        amused_score = (
            emotions.get("Amusement", 0) * 0.9 +          # PRIMARY indicator
            emotions.get("Joy", 0) * 0.5 +                # Mild joy (strong joy goes to enthusiastic)
            emotions.get("Satisfaction", 0) * 0.6 +
            emotions.get("Entrancement", 0) * 0.4
        )

        # Enthusiastic indicators (strong positive connection, excited)
        enthusiastic_score = (
            emotions.get("Joy", 0) * 0.9 +                # PRIMARY indicator
            emotions.get("Excitement", 0) * 0.9 +         # PRIMARY indicator
            emotions.get("Admiration", 0) * 0.7 +
            emotions.get("Triumph", 0) * 0.5 +
            emotions.get("Ecstasy", 0) * 0.6 +
            emotions.get("Surprise (positive)", 0) * 0.5
        )

        # Thinking indicators (processing, contemplating response)
        thinking_score = (
            emotions.get("Contemplation", 0) * 0.8 +
            emotions.get("Concentration", 0) * 0.7 +
            emotions.get("Confusion", 0) * 0.4 +          # Mild confusion as thinking through something
            emotions.get("Realization", 0) * 0.3
        )

        # Determine dominant state
        states = {
            "closed-off": closed_off_score,
            "baseline": baseline_score,
            "curious": curious_score,
            "amused": amused_score,
            "enthusiastic": enthusiastic_score,
            "thinking": thinking_score
        }

        dominant_state = max(states.items(), key=lambda x: x[1])

        # DEBUG: Log emotion score calculations
        logger.debug(f"   🎭 Emotion → State Mapping:")
        logger.debug(f"      Closed-off: {closed_off_score:.3f}")
        logger.debug(f"      Baseline: {baseline_score:.3f}")
        logger.debug(f"      Curious: {curious_score:.3f}")
        logger.debug(f"      Amused: {amused_score:.3f}")
        logger.debug(f"      Enthusiastic: {enthusiastic_score:.3f}")
        logger.debug(f"      Thinking: {thinking_score:.3f}")
        logger.debug(f"      → Dominant: {dominant_state[0]} ({dominant_state[1]:.3f})")

        # Log top 5 raw emotions for debugging
        top_5_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:5]
        logger.debug(f"      Top 5 raw emotions: {', '.join([f'{name}={score:.2f}' for name, score in top_5_emotions])}")

        # Return state only if confidence is above threshold
        if dominant_state[1] > 0.10:  # Lowered from 0.15 for faster state changes
            logger.info(f"   🎭 Engagement state: {dominant_state[0]} (score: {dominant_state[1]:.3f})")
            return dominant_state[0]
        else:
            logger.info(f"   🎭 Engagement state: baseline (all scores below threshold 0.10)")
            return "baseline"


# Global client instance (lazy initialization)
_hume_client: Optional[HumeClient] = None


async def get_hume_client() -> Optional[HumeClient]:
    """
    Get or create global Hume client instance

    Returns:
        HumeClient instance or None if disabled
    """
    global _hume_client

    if not settings.hume_api_key:
        logger.debug("Hume API key not configured")
        return None

    if _hume_client is None:
        _hume_client = HumeClient()

        # Connect on first use
        if not _hume_client.connected:
            await _hume_client.connect()

    return _hume_client


async def close_hume_client():
    """Close global Hume client connection"""
    global _hume_client

    if _hume_client:
        await _hume_client.disconnect()
        _hume_client = None
