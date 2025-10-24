"""Prompt templates for GPT-4 coaching"""

from .config import settings

# ============================================================================
# NEGOTIATION COACH (for investor pitch demo)
# ============================================================================

# Load from config for easy customization
NEGOTIATION_COACH_SYSTEM_PROMPT = settings.negotiation_coach_system_prompt


def build_negotiation_prompt(context: dict) -> str:
    """
    Build negotiation coaching prompt from time-series context

    Args:
        context: Formatted context from LLMContextBuilder

    Returns:
        Complete prompt string for GPT-4
    """
    import logging
    logger = logging.getLogger(__name__)

    summary = context.get("summary", {})
    patterns = context.get("patterns", {})
    intervals = context.get("intervals", [])

    # Get emotion trajectory across intervals
    emotion_trajectory = []
    for i, interval in enumerate(intervals):
        emotions = interval.get("emotions", [])
        speech = interval.get("speech", {}).get("text", "")

        # Format emotions with trends
        emotion_str = ", ".join([
            f"{e['name']}({e['score']:.2f}, {e['trend']})"
            for e in emotions[:3]
        ])

        interval_summary = f"[Interval {i+1}] Emotions: {emotion_str}"
        if speech:
            interval_summary += f' | Founder said: "{speech}"'
        else:
            interval_summary += " | [silence]"

        emotion_trajectory.append(interval_summary)

    # Get emotion shifts and patterns
    emotion_shifts = patterns.get("emotion_shifts", [])
    shift_text = ""
    if emotion_shifts:
        recent_shift = emotion_shifts[-1]
        shift_emotions = ", ".join([
            f"{e['name']} ({e['trend']})"
            for e in recent_shift.get('emotions', [])
        ])
        shift_text = f"\nEmotion shift detected: {shift_emotions}"

    # Build prompt
    trajectory_text = "\n".join(emotion_trajectory)

    prompt = f"""Investor Emotion Analysis (last 4 seconds, 4 intervals oldest→newest):

{trajectory_text}{shift_text}

Based on this emotion trajectory, provide ONE tactical coaching move (max 15 words):"""

    # DEBUG: Log the complete prompt being sent to OpenAI
    logger.info("=" * 60)
    logger.info("PROMPT SENT TO OPENAI:")
    logger.info(prompt)
    logger.info("=" * 60)

    return prompt


# Emotion state to emoji mapping
INVESTOR_STATE_EMOJI = {
    "skeptical": "🔴",
    "evaluative": "🟡",
    "receptive": "🟢",
    "positive": "🟢",
    "neutral": "⚪"
}

# Emotion state to color mapping (for frontend)
INVESTOR_STATE_COLOR = {
    "skeptical": "#ef4444",      # red-500
    "evaluative": "#eab308",     # yellow-500
    "receptive": "#22c55e",      # green-500
    "positive": "#10b981",       # emerald-500
    "neutral": "#9ca3af"         # gray-400
}


# ============================================================================
# GENERAL COMMUNICATION COACH (legacy/alternative)
# ============================================================================

# Load from config for easy customization
SYSTEM_PROMPT = settings.general_coach_system_prompt


def build_user_prompt(parameters: dict) -> str:
    """Build user prompt from parameters"""

    emotion = parameters["emotion"]["label"]
    confidence = parameters["emotion"]["confidence"]
    speech = parameters["speech"]

    wpm = speech["wordsPerMinute"]
    pause_freq = speech["pauseFrequency"]
    filler_count = speech["fillerWords"]["total"]
    recent_transcript = speech.get("recentTranscript", "")

    # Determine focus area
    focus = determine_focus_area(emotion, wpm, filler_count, pause_freq)

    prompt = f"""Current situation:
- Emotional state: {emotion} (confidence: {confidence:.0%})
- Speech pace: {wpm} words/min (target: 120-150)
- Filler words: {filler_count} in last 30 seconds
- Pause frequency: {pause_freq:.0%} (target: 20-30%)

Focus on: {focus}

Provide ONE specific coaching tip (max 20 words)."""

    # Add transcript context if available
    if recent_transcript:
        prompt += f"\n\nRecent speech: \"{recent_transcript[:200]}...\""

    return prompt


# ============================================================================
# DEPRECATED: Fallback advice functions (no longer used - LLM only)
# ============================================================================
#
# def determine_focus_area(emotion: str, wpm: int, filler_count: int, pause_freq: float) -> str:
#     """Determine what to focus advice on"""
#     # REMOVED: No longer using hardcoded fallbacks
#     pass
#
# def get_fallback_advice(focus: str) -> str:
#     """Get fallback advice when API fails"""
#     # REMOVED: No longer using hardcoded fallbacks - LLM calls are required
#     pass
