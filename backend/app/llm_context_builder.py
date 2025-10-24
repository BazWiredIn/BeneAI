"""
LLM Context Builder
Formats time-series emotion and speech data for GPT-4 coaching prompts
"""

from typing import Dict, List, Optional


class LLMContextBuilder:
    """
    Builds structured context from time-series intervals for LLM coaching

    Takes 5 one-second intervals and formats them into a compact,
    information-dense structure for GPT-4 to provide coaching advice.
    """

    def __init__(self):
        """Initialize context builder"""
        pass

    def build_context(
        self,
        intervals: List[Dict],
        buffer_summary: Dict,
        emotion_trends: Dict[str, str]
    ) -> Dict:
        """
        Build complete context for LLM from time-series data

        Args:
            intervals: List of 1-second interval dictionaries
            buffer_summary: Summary statistics from TimeSeriesBuffer
            emotion_trends: Emotion trends from TimeSeriesBuffer

        Returns:
            Formatted context dictionary for LLM
        """
        if not intervals:
            return self._build_empty_context()

        # Build interval summaries
        interval_summaries = [
            self._build_interval_summary(interval)
            for interval in intervals
        ]

        # Analyze patterns
        patterns = self._analyze_patterns(intervals)

        # Build final context
        context = {
            "time_window": {
                "duration_seconds": buffer_summary.get("time_span", 0),
                "interval_count": buffer_summary.get("buffer_size", 0),
                "start_time": intervals[0]["interval_start"],
                "end_time": intervals[-1]["interval_end"]
            },
            "intervals": interval_summaries,
            "summary": {
                "dominant_state": buffer_summary.get("dominant_state", "neutral"),
                "total_words": buffer_summary.get("total_words", 0),
                "total_frames": buffer_summary.get("total_frames", 0),
                "emotion_trends": emotion_trends
            },
            "patterns": patterns,
            "flags": self._aggregate_flags(intervals)
        }

        return context

    def _build_interval_summary(self, interval: Dict) -> Dict:
        """
        Build a compact summary of a single interval

        Args:
            interval: Interval data dictionary

        Returns:
            Compact interval summary
        """
        # Extract top 3 emotions
        top_emotions = interval.get("top_emotions", [])
        emotions_compact = [
            {
                "name": e["name"],
                "score": round(e["avg_score"], 2),
                "trend": e["trend"]
            }
            for e in top_emotions[:3]
        ]

        # Extract speech data
        words = interval.get("words", [])
        full_text = interval.get("full_text", "")

        # Build compact summary
        summary = {
            "timestamp": round(interval["timestamp"], 1),
            "investor_state": interval.get("investor_state", "neutral"),
            "emotions": emotions_compact,
            "speech": {
                "text": full_text,
                "word_count": len(words),
                "is_silence": interval.get("flags", {}).get("silence", False)
            },
            "flags": {
                "high_confidence": interval.get("flags", {}).get("high_confidence", False),
                "emotion_shift": interval.get("flags", {}).get("emotion_shift", False),
                "state_transition": interval.get("flags", {}).get("state_transition", False)
            }
        }

        return summary

    def _analyze_patterns(self, intervals: List[Dict]) -> Dict:
        """
        Analyze patterns across intervals

        Args:
            intervals: List of interval dictionaries

        Returns:
            Dictionary of detected patterns
        """
        patterns = {
            "state_transitions": self._find_state_transitions(intervals),
            "emotion_shifts": self._find_emotion_shifts(intervals),
            "silence_periods": self._find_silence_periods(intervals),
            "engagement_trend": self._calculate_engagement_trend(intervals)
        }

        return patterns

    def _find_state_transitions(self, intervals: List[Dict]) -> List[Dict]:
        """
        Find investor state transitions across intervals

        Args:
            intervals: List of intervals

        Returns:
            List of transition events
        """
        transitions = []

        for i in range(1, len(intervals)):
            prev_state = intervals[i - 1].get("investor_state", "neutral")
            curr_state = intervals[i].get("investor_state", "neutral")

            if prev_state != curr_state:
                transitions.append({
                    "from_state": prev_state,
                    "to_state": curr_state,
                    "timestamp": intervals[i]["timestamp"],
                    "text_context": intervals[i].get("full_text", "")
                })

        return transitions

    def _find_emotion_shifts(self, intervals: List[Dict]) -> List[Dict]:
        """
        Find significant emotion shifts

        Args:
            intervals: List of intervals

        Returns:
            List of emotion shift events
        """
        shifts = []

        for interval in intervals:
            if interval.get("flags", {}).get("emotion_shift", False):
                # Get top emotion with increasing/decreasing trend
                top_emotions = interval.get("top_emotions", [])
                shifting_emotions = [
                    e for e in top_emotions
                    if e.get("trend") in ["increasing", "decreasing"]
                ]

                if shifting_emotions:
                    shifts.append({
                        "timestamp": interval["timestamp"],
                        "emotions": [
                            {
                                "name": e["name"],
                                "trend": e["trend"],
                                "score": round(e["avg_score"], 2)
                            }
                            for e in shifting_emotions
                        ],
                        "text_context": interval.get("full_text", "")
                    })

        return shifts

    def _find_silence_periods(self, intervals: List[Dict]) -> List[Dict]:
        """
        Find periods of silence

        Args:
            intervals: List of intervals

        Returns:
            List of silence periods
        """
        silence_periods = []
        current_silence = None

        for interval in intervals:
            is_silence = interval.get("flags", {}).get("silence", False)

            if is_silence:
                if current_silence is None:
                    # Start new silence period
                    current_silence = {
                        "start_timestamp": interval["timestamp"],
                        "end_timestamp": interval["timestamp"],
                        "duration": 1.0,
                        "emotion_during_silence": interval.get("investor_state", "neutral")
                    }
                else:
                    # Extend current silence
                    current_silence["end_timestamp"] = interval["timestamp"]
                    current_silence["duration"] += 1.0
            else:
                if current_silence is not None:
                    # End silence period
                    silence_periods.append(current_silence)
                    current_silence = None

        # Add final silence period if still ongoing
        if current_silence is not None:
            silence_periods.append(current_silence)

        return silence_periods

    def _calculate_engagement_trend(self, intervals: List[Dict]) -> str:
        """
        Calculate overall engagement trend

        Args:
            intervals: List of intervals

        Returns:
            "increasing", "decreasing", or "stable"
        """
        if len(intervals) < 2:
            return "stable"

        # Map states to engagement scores
        state_scores = {
            "positive": 4,
            "receptive": 3,
            "evaluative": 2,
            "neutral": 1,
            "skeptical": 0
        }

        # Calculate average engagement for first and second half
        mid = len(intervals) // 2
        first_half = intervals[:mid]
        second_half = intervals[mid:]

        first_avg = sum(
            state_scores.get(i.get("investor_state", "neutral"), 1)
            for i in first_half
        ) / len(first_half)

        second_avg = sum(
            state_scores.get(i.get("investor_state", "neutral"), 1)
            for i in second_half
        ) / len(second_half)

        diff = second_avg - first_avg

        if diff > 0.5:
            return "increasing"
        elif diff < -0.5:
            return "decreasing"
        else:
            return "stable"

    def _aggregate_flags(self, intervals: List[Dict]) -> Dict:
        """
        Aggregate flags across all intervals

        Args:
            intervals: List of intervals

        Returns:
            Aggregated flags
        """
        total_intervals = len(intervals)

        high_confidence_count = sum(
            1 for i in intervals
            if i.get("flags", {}).get("high_confidence", False)
        )

        emotion_shift_count = sum(
            1 for i in intervals
            if i.get("flags", {}).get("emotion_shift", False)
        )

        state_transition_count = sum(
            1 for i in intervals
            if i.get("flags", {}).get("state_transition", False)
        )

        silence_count = sum(
            1 for i in intervals
            if i.get("flags", {}).get("silence", False)
        )

        return {
            "high_confidence_ratio": round(high_confidence_count / total_intervals, 2),
            "has_emotion_shifts": emotion_shift_count > 0,
            "has_state_transitions": state_transition_count > 0,
            "silence_ratio": round(silence_count / total_intervals, 2)
        }

    def _build_empty_context(self) -> Dict:
        """
        Build empty context when no intervals available

        Returns:
            Empty context structure
        """
        return {
            "time_window": {
                "duration_seconds": 0,
                "interval_count": 0,
                "start_time": 0,
                "end_time": 0
            },
            "intervals": [],
            "summary": {
                "dominant_state": "neutral",
                "total_words": 0,
                "total_frames": 0,
                "emotion_trends": {}
            },
            "patterns": {
                "state_transitions": [],
                "emotion_shifts": [],
                "silence_periods": [],
                "engagement_trend": "stable"
            },
            "flags": {
                "high_confidence_ratio": 0.0,
                "has_emotion_shifts": False,
                "has_state_transitions": False,
                "silence_ratio": 0.0
            }
        }

    def format_for_prompt(self, context: Dict) -> str:
        """
        Format context into human-readable text for LLM prompt

        Args:
            context: Context dictionary from build_context()

        Returns:
            Formatted text string for LLM prompt
        """
        lines = []

        # Header
        lines.append("=== PARTICIPANT ANALYSIS (Last 5 seconds) ===\n")

        # Overall summary
        summary = context["summary"]
        lines.append(f"Dominant State: {summary['dominant_state'].upper()}")
        lines.append(f"Engagement Trend: {context['patterns']['engagement_trend']}")
        lines.append(f"Words Spoken: {summary['total_words']}\n")

        # State transitions
        transitions = context["patterns"]["state_transitions"]
        if transitions:
            lines.append("State Transitions:")
            for t in transitions:
                lines.append(f"  • {t['from_state']} → {t['to_state']} at {t['timestamp']}s")
                if t['text_context']:
                    lines.append(f"    Said: \"{t['text_context']}\"")
            lines.append("")

        # Emotion shifts
        shifts = context["patterns"]["emotion_shifts"]
        if shifts:
            lines.append("Emotion Shifts:")
            for s in shifts:
                emotions_str = ", ".join(f"{e['name']} ({e['trend']})" for e in s['emotions'])
                lines.append(f"  • {emotions_str} at {s['timestamp']}s")
            lines.append("")

        # Silence periods
        silences = context["patterns"]["silence_periods"]
        if silences:
            lines.append("Silence Periods:")
            for s in silences:
                lines.append(f"  • {s['duration']}s silence ({s['emotion_during_silence']} state)")
            lines.append("")

        # Interval details
        lines.append("Interval Timeline:")
        for interval in context["intervals"]:
            timestamp = interval["timestamp"]
            state = interval["investor_state"]
            emotions = ", ".join(f"{e['name']}({e['score']})" for e in interval["emotions"][:2])
            text = interval["speech"]["text"] or "[silence]"

            lines.append(f"\n[{timestamp}s] {state.upper()}")
            lines.append(f"  Emotions: {emotions}")
            lines.append(f"  Said: \"{text}\"")

        return "\n".join(lines)
