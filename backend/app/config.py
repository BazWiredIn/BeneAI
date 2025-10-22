"""Configuration management"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-turbo"
    openai_max_tokens: int = 100
    openai_temperature: float = 0.7

    # Hume AI (Emotion Detection)
    hume_api_key: str
    hume_enable_face: bool = True  # Enable facial expression analysis
    hume_enable_prosody: bool = True  # Enable speech prosody analysis
    hume_enable_language: bool = True  # Enable emotional language analysis
    hume_websocket_url: str = "wss://api.hume.ai/v0/stream/models"
    hume_frame_rate: float = 3.0  # Frames per second for face analysis

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

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
