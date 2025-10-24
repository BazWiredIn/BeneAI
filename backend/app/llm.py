"""LLM Integration with OpenAI"""

import asyncio
import logging
from typing import AsyncGenerator
from openai import OpenAI
from .config import settings
from .prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
    NEGOTIATION_COACH_SYSTEM_PROMPT,
    build_negotiation_prompt
)

logger = logging.getLogger(__name__)

# Lazy client initialization to ensure settings are loaded first
_client = None


def get_openai_client() -> OpenAI:
    """
    Get or create OpenAI client (lazy initialization)

    This ensures settings.openai_api_key is loaded from .env before creating the client
    """
    global _client

    if _client is None:
        if not settings.openai_api_key:
            logger.error("OpenAI API key is missing! Check .env file has OPENAI_API_KEY set")
            raise ValueError("OpenAI API key not configured")

        logger.info(f"Creating OpenAI client (API key: {settings.openai_api_key[:10]}...{settings.openai_api_key[-4:]})")
        _client = OpenAI(api_key=settings.openai_api_key)

    return _client


async def get_coaching_advice(parameters: dict) -> AsyncGenerator[str, None]:
    """
    Get coaching advice from GPT-4 (streaming)

    Args:
        parameters: Dictionary with emotion and speech metrics

    Yields:
        Chunks of advice text as they arrive
    """

    try:
        # Build prompt
        user_prompt = build_user_prompt(parameters)

        # Get OpenAI client (lazy initialization)
        client = get_openai_client()

        # Call OpenAI API with streaming (using v1.x client)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature,
            stream=True
        )

        # Stream response
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        logger.error("No fallback advice - LLM call required")
        # Don't yield anything - let the error propagate or return empty
        return


async def get_coaching_advice_complete(parameters: dict) -> str:
    """
    Get complete coaching advice (non-streaming)

    Args:
        parameters: Dictionary with emotion and speech metrics

    Returns:
        Complete advice text
    """

    chunks = []
    async for chunk in get_coaching_advice(parameters):
        chunks.append(chunk)

    return "".join(chunks)


async def get_negotiation_coaching(context: dict) -> str:
    """
    Get negotiation coaching advice from GPT-4 (non-streaming, fast)

    Args:
        context: Time-series context from LLMContextBuilder

    Returns:
        Concise coaching advice (max 15 words)
    """

    try:
        # Build negotiation prompt
        user_prompt = build_negotiation_prompt(context)

        # DEBUG: Log API call details
        logger.info("🤖 [OpenAI] Preparing API call...")
        logger.info(f"  Model: {settings.openai_model}")
        logger.info(f"  API Key (first 10 chars): {settings.openai_api_key[:10]}...")
        logger.info(f"  API Key (last 4 chars): ...{settings.openai_api_key[-4:]}")
        logger.info(f"  Max Tokens: 30")
        logger.info(f"  Temperature: 0.7")

        # Get OpenAI client (lazy initialization)
        logger.info("🤖 [OpenAI] Getting OpenAI client...")
        client = get_openai_client()
        logger.info(f"🤖 [OpenAI] Client type: {type(client)}")

        # DEBUG: Log message payload
        messages = [
            {"role": "system", "content": NEGOTIATION_COACH_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        logger.info(f"🤖 [OpenAI] System prompt length: {len(NEGOTIATION_COACH_SYSTEM_PROMPT)} chars")
        logger.info(f"🤖 [OpenAI] User prompt length: {len(user_prompt)} chars")

        # Call OpenAI API (non-streaming for speed, using v1.x client)
        logger.info("🤖 [OpenAI] Calling API (chat.completions.create)...")

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=settings.openai_model,
            messages=messages,
            max_tokens=30,  # Keep it short (15 words ~= 20-30 tokens)
            temperature=0.7,
            stream=False
        )

        logger.info(f"🤖 [OpenAI] ✅ Response received!")
        logger.info(f"  Response type: {type(response)}")
        logger.info(f"  Response ID: {response.id if hasattr(response, 'id') else 'N/A'}")
        logger.info(f"  Model used: {response.model if hasattr(response, 'model') else 'N/A'}")
        logger.info(f"  Choices count: {len(response.choices) if hasattr(response, 'choices') else 0}")

        advice = response.choices[0].message.content.strip()
        logger.info(f"🤖 [OpenAI] ✅ Advice extracted: \"{advice}\"")
        logger.info(f"  Tokens used: {response.usage.total_tokens if hasattr(response, 'usage') else 'N/A'}")

        return advice

    except Exception as e:
        logger.error(f"❌ [OpenAI] Error calling API: {e}")
        logger.error(f"  Error type: {type(e).__name__}")
        logger.exception("Full traceback:")
        logger.error("❌ No fallback advice - LLM call failed and is required")

        # Return empty string or error message instead of fallback
        return "[LLM Error: Unable to generate advice]"
