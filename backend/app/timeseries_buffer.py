"""
Time-Series Buffer
Maintains a rolling 5-second window of 1-second intervals for LLM context
"""

import time
from typing import Dict, List, Optional
from collections import deque


class TimeSeriesBuffer:
    """
    Maintains a rolling window of emotion intervals for LLM context

    Collects 5 one-second intervals and triggers LLM updates when:
    - Buffer is full (5 seconds elapsed)
    - Significant emotion shift detected
    - Investor state transition occurs
    """

    def __init__(self, window_size: int = 5, update_interval: float = 5.0):
        """
        Initialize time-series buffer

        Args:
            window_size: Number of 1-second intervals to buffer (default 5)
            update_interval: Seconds between LLM updates (default 5.0)
        """
        self.window_size = window_size
        self.update_interval = update_interval

        # Rolling buffer of intervals
        self.intervals = deque(maxlen=window_size)

        # Timing
        self.last_llm_update = None
        self.session_start = None

        # Statistics
        self.total_intervals = 0
        self.llm_updates_sent = 0

    def add_interval(self, interval_data: Dict, current_time: float) -> bool:
        """
        Add a 1-second interval to the buffer

        Args:
            interval_data: Interval data from IntervalAggregator
            current_time: Current timestamp

        Returns:
            True if LLM update should be triggered
        """
        if self.session_start is None:
            self.session_start = current_time

        # Add interval to buffer
        self.intervals.append(interval_data)
        self.total_intervals += 1

        # Check if we should trigger LLM update
        return self._should_trigger_llm_update(current_time)

    def _should_trigger_llm_update(self, current_time: float) -> bool:
        """
        Determine if LLM update should be triggered

        Args:
            current_time: Current timestamp

        Returns:
            True if update should be sent
        """
        # Don't update if buffer isn't full yet
        if len(self.intervals) < self.window_size:
            return False

        # First update once buffer is full
        if self.last_llm_update is None:
            self.last_llm_update = current_time
            return True

        # Check if enough time has elapsed
        elapsed = current_time - self.last_llm_update
        if elapsed >= self.update_interval:
            self.last_llm_update = current_time
            return True

        # Check for significant emotion shift
        if self._has_significant_shift():
            self.last_llm_update = current_time
            return True

        # Check for state transition
        if self._has_state_transition():
            self.last_llm_update = current_time
            return True

        return False

    def _has_significant_shift(self) -> bool:
        """
        Check if there's a significant emotion shift in recent intervals

        Returns:
            True if significant shift detected
        """
        if len(self.intervals) < 2:
            return False

        # Check last 2 intervals for emotion_shift flag
        recent_intervals = list(self.intervals)[-2:]

        for interval in recent_intervals:
            if interval.get("flags", {}).get("emotion_shift", False):
                return True

        return False

    def _has_state_transition(self) -> bool:
        """
        Check if investor state has transitioned

        Returns:
            True if state transition detected
        """
        if len(self.intervals) < 2:
            return False

        # Check if any recent interval has state_transition flag
        recent_intervals = list(self.intervals)[-2:]

        for interval in recent_intervals:
            if interval.get("flags", {}).get("state_transition", False):
                return True

        return False

    def get_context(self) -> Optional[List[Dict]]:
        """
        Get current buffer contents for LLM context

        Returns:
            List of interval dictionaries, or None if buffer empty
        """
        if not self.intervals:
            return None

        return list(self.intervals)

    def get_summary(self) -> Dict:
        """
        Get summary statistics for the current buffer

        Returns:
            Dictionary with buffer statistics
        """
        if not self.intervals:
            return {
                "buffer_size": 0,
                "time_span": 0.0,
                "dominant_state": "neutral",
                "total_words": 0,
                "total_frames": 0
            }

        intervals_list = list(self.intervals)

        # Calculate time span
        first_interval = intervals_list[0]
        last_interval = intervals_list[-1]
        time_span = last_interval["interval_end"] - first_interval["interval_start"]

        # Find dominant investor state
        state_counts = {}
        for interval in intervals_list:
            state = interval.get("investor_state", "neutral")
            state_counts[state] = state_counts.get(state, 0) + 1

        dominant_state = max(state_counts.items(), key=lambda x: x[1])[0] if state_counts else "neutral"

        # Count total words and frames
        total_words = sum(len(interval.get("words", [])) for interval in intervals_list)
        total_frames = sum(interval.get("frames_count", 0) for interval in intervals_list)

        return {
            "buffer_size": len(self.intervals),
            "time_span": round(time_span, 1),
            "dominant_state": dominant_state,
            "total_words": total_words,
            "total_frames": total_frames,
            "total_intervals_processed": self.total_intervals,
            "llm_updates_sent": self.llm_updates_sent
        }

    def get_emotion_trends(self) -> Dict[str, str]:
        """
        Analyze emotion trends across the buffer

        Returns:
            Dictionary mapping emotion names to trend indicators
        """
        if len(self.intervals) < 2:
            return {}

        intervals_list = list(self.intervals)

        # Track emotion scores over time
        emotion_timeline = {}

        for interval in intervals_list:
            for emotion in interval.get("top_emotions", []):
                name = emotion["name"]
                score = emotion["avg_score"]

                if name not in emotion_timeline:
                    emotion_timeline[name] = []
                emotion_timeline[name].append(score)

        # Determine trends
        trends = {}
        for emotion_name, scores in emotion_timeline.items():
            if len(scores) < 2:
                trends[emotion_name] = "stable"
                continue

            # Compare first half to second half
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

            diff = second_half_avg - first_half_avg

            if diff > 0.05:
                trends[emotion_name] = "increasing"
            elif diff < -0.05:
                trends[emotion_name] = "decreasing"
            else:
                trends[emotion_name] = "stable"

        return trends

    def increment_llm_updates(self):
        """Increment the LLM updates counter"""
        self.llm_updates_sent += 1

    def reset_buffer(self):
        """Clear the buffer but keep session statistics"""
        self.intervals.clear()

    def reset_session(self):
        """Reset all state for new session"""
        self.intervals.clear()
        self.last_llm_update = None
        self.session_start = None
        self.total_intervals = 0
        self.llm_updates_sent = 0
