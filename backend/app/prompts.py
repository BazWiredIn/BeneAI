"""Prompt templates for GPT-4 coaching"""

SYSTEM_PROMPT = """You are an expert communication coach specializing in high-stakes video calls.

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


def determine_focus_area(emotion: str, wpm: int, filler_count: int, pause_freq: float) -> str:
    """Determine what to focus advice on"""

    # Priority order: 1) pacing, 2) emotional tone, 3) clarity

    # Check pacing issues
    if wpm > 160:
        return "pacing - speaking too fast"
    elif wpm < 100 and wpm > 0:
        return "pacing - speaking too slowly"
    elif pause_freq < 0.1:
        return "pacing - not enough pauses"

    # Check emotional tone
    if emotion == "concerned":
        return "emotional_tone - projecting concern"
    elif emotion == "disengaged":
        return "emotional_tone - appearing disengaged"

    # Check clarity
    if filler_count > 8:
        return "clarity - too many filler words"

    # Default: general pacing
    return "pacing - speech delivery"


def get_fallback_advice(focus: str) -> str:
    """Get fallback advice when API fails"""

    fallback_map = {
        "pacing - speaking too fast": "Slow down to 140 words per minute. Pause between key points.",
        "pacing - speaking too slowly": "Increase your pace slightly. Aim for 140 words per minute.",
        "pacing - not enough pauses": "Add more pauses. Breathe between sentences.",
        "emotional_tone - projecting concern": "Take a breath. Project confidence - say 'we'll find a way.'",
        "emotional_tone - appearing disengaged": "Show engagement. Lean forward slightly and maintain eye contact.",
        "clarity - too many filler words": "Reduce filler words. Pause instead of saying 'um.'",
        "pacing - speech delivery": "Maintain steady pace at 140 WPM with natural pauses."
    }

    return fallback_map.get(focus, "Speak clearly at a steady pace with confidence.")
