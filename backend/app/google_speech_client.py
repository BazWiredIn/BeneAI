"""
Google Cloud Speech-to-Text Client
Handles speech-to-text transcription using Google Cloud Speech API
"""

import asyncio
import base64
import logging
from typing import Optional, Dict, List
from google.cloud import speech_v1
from google.cloud.speech_v1 import types
import os

from app.config import settings

logger = logging.getLogger(__name__)


class GoogleSpeechTranscriber:
    """Client for Google Cloud Speech-to-Text API"""

    def __init__(self):
        # Check for credentials
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            logger.warning("GOOGLE_APPLICATION_CREDENTIALS not set")
            self.client = None
        else:
            try:
                self.client = speech_v1.SpeechClient()
                logger.info("Google Cloud Speech client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Speech client: {e}")
                self.client = None

        # Configuration
        self.language_code = getattr(settings, 'google_speech_language', 'en-US')
        self.sample_rate = 16000  # Hz

    async def transcribe_audio(self, audio_base64: str, mime_type: str = "audio/webm") -> Optional[Dict]:
        """
        Transcribe audio chunk to text with word-level timestamps

        Args:
            audio_base64: Base64-encoded audio data
            mime_type: MIME type of audio (audio/webm, audio/mp4, etc.)

        Returns:
            Dictionary with transcription results:
            {
                "transcript": str,  # Full transcript text
                "words": [
                    {
                        "word": str,
                        "start": float,  # Seconds from start
                        "end": float,
                        "confidence": float
                    }
                ],
                "confidence": float,  # Overall confidence
                "duration": float  # Audio duration in seconds
            }
        """
        if not self.client:
            logger.warning("Google Cloud Speech client not initialized")
            return None

        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            logger.info(f"🎵 Decoded audio: {len(audio_bytes)} bytes from base64")

            # Map MIME type to Google encoding
            encoding_map = {
                "audio/webm": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "audio/webm;codecs=opus": speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                "audio/mp4": speech_v1.RecognitionConfig.AudioEncoding.MP3,
                "audio/mp3": speech_v1.RecognitionConfig.AudioEncoding.MP3,
                "audio/wav": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            }

            encoding = encoding_map.get(mime_type, speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS)
            logger.info(f"   MIME type: {mime_type} → Encoding: {encoding}")

            # Configure recognition
            config = speech_v1.RecognitionConfig(
                encoding=encoding,
                language_code=self.language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,  # Get word timestamps
                model="latest_long",  # Best accuracy for speech
            )

            audio = speech_v1.RecognitionAudio(content=audio_bytes)

            # Transcribe (run in thread pool to not block)
            logger.info(f"🌐 Calling Google Cloud Speech API...")
            logger.debug(f"   Config: language={self.language_code}, model=latest_long, encoding={encoding}")

            response = await asyncio.to_thread(
                self.client.recognize,
                config=config,
                audio=audio
            )

            logger.info(f"✅ Google API responded")

            # Parse response
            if not response.results:
                logger.warning("⚠️ No results in Google Speech response - audio likely silent or too short")
                logger.debug(f"   Raw response: {response}")
                return None

            # Get first result (best alternative)
            result = response.results[0]
            if not result.alternatives:
                logger.debug("No alternatives in Google Cloud Speech response")
                return None

            alternative = result.alternatives[0]

            # Extract words with timestamps
            words = []
            for word_info in alternative.words:
                # Convert duration to seconds
                start_seconds = word_info.start_time.total_seconds()
                end_seconds = word_info.end_time.total_seconds()

                words.append({
                    "word": word_info.word,
                    "start": start_seconds,
                    "end": end_seconds,
                    "confidence": word_info.confidence if hasattr(word_info, 'confidence') else alternative.confidence
                })

            # Calculate duration from last word
            duration = words[-1]["end"] if words else 0.0

            result_dict = {
                "transcript": alternative.transcript.strip(),
                "words": words,
                "confidence": alternative.confidence,
                "duration": duration,
                "word_count": len(words)
            }

            logger.info(f"Google Speech transcription: \"{result_dict['transcript']}\" ({len(words)} words, {duration:.2f}s)")
            return result_dict

        except Exception as e:
            logger.error(f"Error transcribing with Google Cloud Speech: {e}")
            logger.exception("Full traceback:")
            return None

    def is_available(self) -> bool:
        """Check if Google Cloud Speech client is available"""
        return self.client is not None


# Global client instance
_google_speech_client: Optional[GoogleSpeechTranscriber] = None


def get_google_speech_client() -> Optional[GoogleSpeechTranscriber]:
    """
    Get or create global Google Cloud Speech client instance

    Returns:
        GoogleSpeechTranscriber instance or None if disabled
    """
    global _google_speech_client

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.debug("GOOGLE_APPLICATION_CREDENTIALS not configured")
        return None

    if _google_speech_client is None:
        _google_speech_client = GoogleSpeechTranscriber()

    return _google_speech_client
