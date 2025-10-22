"""LLM Integration with OpenAI"""

import asyncio
from typing import AsyncGenerator
import openai
from .config import settings
from .prompts import SYSTEM_PROMPT, build_user_prompt, get_fallback_advice, determine_focus_area


# Configure OpenAI
openai.api_key = settings.openai_api_key


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

        # Call OpenAI API with streaming
        response = await asyncio.to_thread(
            openai.chat.completions.create,
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
        print(f"Error calling OpenAI API: {e}")

        # Return fallback advice
        emotion = parameters["emotion"]["label"]
        wpm = parameters["speech"]["wordsPerMinute"]
        filler_count = parameters["speech"]["fillerWords"]["total"]
        pause_freq = parameters["speech"]["pauseFrequency"]

        focus = determine_focus_area(emotion, wpm, filler_count, pause_freq)
        fallback = get_fallback_advice(focus)

        yield fallback


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
