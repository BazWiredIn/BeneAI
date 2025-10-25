"""Configuration management"""

import os
import logging
from pydantic_settings import BaseSettings

# Early logging setup to debug config loading
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"  # Changed from gpt-4-turbo to gpt-4o-mini (works with project keys)
    openai_max_tokens: int = 100
    openai_temperature: float = 0.7

    # Hume AI (Emotion Detection)
    hume_api_key: str
    hume_enable_face: bool = True  # Enable facial expression analysis
    hume_enable_prosody: bool = True  # Enable speech prosody analysis
    hume_enable_language: bool = True  # Enable emotional language analysis
    hume_websocket_url: str = "wss://api.hume.ai/v0/stream/models"
    hume_frame_rate: float = 3.0  # Frames per second for face analysis

    # Google Cloud Speech-to-Text
    google_application_credentials: str = ""  # Path to Google Cloud credentials JSON
    google_speech_language: str = "en-US"

    # Server
    environment: str = "development"
    log_level: str = "info"
    port: int = 8000

    # CORS
    allowed_origins: str = "*"

    # WebSocket
    max_connections: int = 100
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10

    # Rate Limiting
    rate_limit_messages_per_second: int = 10
    rate_limit_burst: int = 3

    # Cache
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # Advice
    advice_max_length: int = 50
    advice_update_interval: int = 3

    # LLM Prompts (easily configurable)
    negotiation_coach_system_prompt: str = """You are a live social interaction coach helping someone navigate casual conversations and build rapport. Think like a social strategist: detect engagement cues, evaluate connection quality, and recommend the best conversational moves.

What you receive:
- 4 one-second intervals (oldest → newest)
- Each interval shows:
  • 3 top emotions of the other person (name, score 0-1, trend: increasing/decreasing/stable)
  • What you said (transcribed speech)
  • Flags: emotion_shift, state_transition, high_confidence

Your task:
- Analyze the emotional trajectory across intervals (not just the latest snapshot)
- Detect engagement: Is Interest rising? Is Amusement appearing? Did closed-off→curious shift?
- Connect your words to their emotional responses (what landed well vs. poorly)
- Give ONE tactical conversational move: what to say or do next

Output format:
- Start with "[Advice]"
- Max 15 words (1-2 short sentences)
- Be direct, specific, and immediately actionable
- Focus on: conversational tactics, pacing, rapport building

Key patterns to watch:
- Interest/Curiosity increasing → build momentum, ask follow-up questions, offer self-disclosure
- Amused appearing → humor landed, keep tempo steady, don't rush
- Enthusiastic/Animated → strong connection, reflect their energy, suggest next steps (exchange contacts)
- Thinking/Contemplation → give them space, use minimal backchannels, don't interrupt
- Closed-off/Boredom rising → gracefully exit, shift topics, or offer low-commitment out
- Baseline/Neutral → light opener, stay casual, avoid heavy topics

Never invent facts. When uncertain, suggest the safest, most natural conversational move.
"""

    general_coach_system_prompt: str = """You are an expert communication coach specializing in high-stakes video calls.

Your role:
- Provide concise, actionable advice (max 50 words)
- Focus on ONE specific improvement at a time
- Be encouraging but direct
- Use second person ("you")
- Alternate focus between emotional tone and pacing

Your expertise:
- Emotional intelligence and tone management
- Speech pacing and delivery
- Professional communication best practices
- Real-time coaching techniques

Remember: The user is in a live call. Keep advice brief, clear, and immediately actionable.
"""

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore deprecated env vars (like Deepgram)


# Global settings instance
settings = Settings()

# Set Google credentials environment variable if provided in config
if settings.google_application_credentials:
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.google_application_credentials
    logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS from config: {settings.google_application_credentials}")

# DEBUG: Log settings load status
logger.info("=" * 60)
logger.info("SETTINGS LOADED - Diagnostics:")
logger.info(f"  OpenAI API Key: {'✓ Present' if settings.openai_api_key else '✗ MISSING'} ({len(settings.openai_api_key) if settings.openai_api_key else 0} chars)")
if settings.openai_api_key:
    logger.info(f"    → Key preview: {settings.openai_api_key[:15]}...{settings.openai_api_key[-10:]}")
logger.info(f"  OpenAI Model: {settings.openai_model}")
logger.info(f"  Hume API Key: {'✓ Present' if settings.hume_api_key else '✗ MISSING'} ({len(settings.hume_api_key) if settings.hume_api_key else 0} chars)")
logger.info(f"  Google Credentials: {'✓ Set' if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else '✗ NOT SET'}")
logger.info(f"  Environment: {settings.environment}")
logger.info(f"  Log Level: {settings.log_level}")
logger.info("=" * 60)
