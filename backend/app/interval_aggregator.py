"""
Interval Aggregator
Aggregates emotion data into 1-second intervals for time-series analysis
"""

import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class IntervalAggregator:
    """
    Aggregates emotion frames into 1-second intervals

    Collects ~3 frames per second and produces:
    - Top 3 emotions (averaged + EMA)
    - Investor state for the interval
    - Metadata flags
    """

    def __init__(self, alpha: float = 0.3, interval_duration: float = 1.0):
        """
        Initialize interval aggregator

        Args:
            alpha: DEPRECATED - no longer used (EMA removed)
            interval_duration: Duration of each interval in seconds (default 1.0)
        """
        self.interval_duration = interval_duration

        # Current interval state
        self.current_interval_start = None
        self.current_interval_frames = []
        self.current_interval_states = []

        # Previous interval for comparison
        self.previous_top_emotions = None
        self.previous_state = None

        # Session tracking
        self.interval_count = 0

    def add_frame(
        self,
        emotion_data: Dict,
        timestamp: float,
        face_detected: bool = True
    ) -> None:
        """
        Add a frame to the current interval

        Args:
            emotion_data: Dict with 'all_emotions', 'investor_state', etc.
            timestamp: Unix timestamp when frame was captured
            face_detected: Whether face was successfully detected
        """
        # Initialize interval if needed
        if self.current_interval_start is None:
            self.current_interval_start = timestamp

        # Add frame to current interval
        self.current_interval_frames.append({
            "timestamp": timestamp,
            "emotions": emotion_data.get("all_emotions", {}),
            "state": emotion_data.get("investor_state"),
            "face_detected": face_detected,
            "confidence": emotion_data.get("confidence", 0.0)
        })

        # Track states
        if emotion_data.get("investor_state"):
            self.current_interval_states.append(emotion_data["investor_state"])

    def interval_complete(self, current_time: float) -> bool:
        """
        Check if current interval is complete (1 second elapsed)

        Args:
            current_time: Current timestamp

        Returns:
            True if interval should be finalized
        """
        if self.current_interval_start is None:
            return False

        elapsed = current_time - self.current_interval_start
        return elapsed >= self.interval_duration

    def get_interval(self, current_time: float) -> Optional[Dict]:
        """
        Finalize and return the current interval data

        Args:
            current_time: Current timestamp for interval end

        Returns:
            Dictionary with interval data, or None if no frames
        """
        if not self.current_interval_frames:
            return None

        # Calculate interval timestamp (middle of interval)
        interval_timestamp = self.current_interval_start + (self.interval_duration / 2)

        # Aggregate emotions across frames
        emotion_sums = defaultdict(float)
        emotion_counts = defaultdict(int)

        for frame in self.current_interval_frames:
            if not frame["face_detected"]:
                continue

            for emotion_name, score in frame["emotions"].items():
                emotion_sums[emotion_name] += score
                emotion_counts[emotion_name] += 1

        # Calculate averages (simple average per interval, no EMA)
        emotion_averages = {}
        for emotion_name in emotion_sums:
            if emotion_counts[emotion_name] > 0:
                emotion_averages[emotion_name] = (
                    emotion_sums[emotion_name] / emotion_counts[emotion_name]
                )

        # Get top 3 emotions with trends (simple average, no EMA)
        top_emotions = self._get_top_emotions_with_trends(
            emotion_averages,
            n=3
        )

        # Determine dominant investor state for interval
        investor_state = self._get_dominant_state(self.current_interval_states)

        # Generate metadata flags
        flags = self._generate_flags(investor_state)

        # Build interval data
        interval_data = {
            "timestamp": interval_timestamp,
            "interval_start": self.current_interval_start,
            "interval_end": current_time,
            "interval": f"{self.current_interval_start:.1f}-{current_time:.1f}s",
            "top_emotions": top_emotions,
            "investor_state": investor_state,
            "frames_count": len(self.current_interval_frames),
            "faces_detected": sum(1 for f in self.current_interval_frames if f["face_detected"]),
            "flags": flags,
            "words": [],  # Will be populated by SpeechMapper
            "full_text": ""  # Will be populated by SpeechMapper
        }

        # Update previous state
        self.previous_top_emotions = top_emotions
        self.previous_state = investor_state

        # Reset for next interval
        self._reset_interval()
        self.interval_count += 1

        return interval_data

    def _get_top_emotions_with_trends(
        self,
        current_averages: Dict[str, float],
        n: int = 3
    ) -> List[Dict]:
        """
        Get top N emotions with trend indicators (using simple average, no EMA)

        Args:
            current_averages: Current interval emotion averages
            n: Number of top emotions to return

        Returns:
            List of emotion dictionaries with trends
        """
        # Sort by average score (no EMA)
        sorted_emotions = sorted(
            current_averages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]

        top_emotions = []
        for emotion_name, avg_score in sorted_emotions:
            # Determine trend
            trend = self._calculate_trend(emotion_name, avg_score)

            top_emotions.append({
                "name": emotion_name,
                "avg_score": round(avg_score, 3),
                "trend": trend
            })

        return top_emotions

    def _calculate_trend(self, emotion_name: str, current_score: float) -> str:
        """
        Calculate trend for emotion (increasing/decreasing/stable)

        Args:
            emotion_name: Name of emotion
            current_score: Current interval average score

        Returns:
            "increasing", "decreasing", or "stable"
        """
        if self.previous_top_emotions is None:
            return "stable"

        # Find emotion in previous interval
        prev_score = None
        for prev_emotion in self.previous_top_emotions:
            if prev_emotion["name"] == emotion_name:
                prev_score = prev_emotion["avg_score"]
                break

        if prev_score is None:
            return "new"  # Emotion wasn't in top 3 before

        # Calculate change
        diff = current_score - prev_score

        # Threshold for considering it a real trend
        threshold = 0.05

        if diff > threshold:
            return "increasing"
        elif diff < -threshold:
            return "decreasing"
        else:
            return "stable"

    def _get_dominant_state(self, states: List[str]) -> str:
        """
        Get the most common investor state in the interval

        Args:
            states: List of states from frames

        Returns:
            Most common state, or "neutral" if none
        """
        if not states:
            return "neutral"

        # Count occurrences
        state_counts = defaultdict(int)
        for state in states:
            state_counts[state] += 1

        # Return most common
        return max(state_counts.items(), key=lambda x: x[1])[0]

    def _generate_flags(self, current_state: str) -> Dict[str, bool]:
        """
        Generate metadata flags for the interval

        Args:
            current_state: Current investor state

        Returns:
            Dictionary of boolean flags
        """
        flags = {
            "high_confidence": self._check_high_confidence(),
            "emotion_shift": self._check_emotion_shift(),
            "state_transition": self._check_state_transition(current_state),
            "silence": False  # Will be set by SpeechMapper
        }

        return flags

    def _check_high_confidence(self) -> bool:
        """Check if frames in interval have high confidence"""
        if not self.current_interval_frames:
            return False

        # At least 80% of frames should have face detected
        detected = sum(1 for f in self.current_interval_frames if f["face_detected"])
        return (detected / len(self.current_interval_frames)) >= 0.8

    def _check_emotion_shift(self) -> bool:
        """Check if there was a significant emotion shift"""
        if self.previous_top_emotions is None or len(self.previous_top_emotions) < 3:
            return False

        # Check if any emotion shows "increasing" or "decreasing" trend
        # This will be calculated when we get top emotions
        return False  # Will be updated based on trends

    def _check_state_transition(self, current_state: str) -> bool:
        """Check if investor state changed from previous interval"""
        if self.previous_state is None:
            return False

        return current_state != self.previous_state

    def _reset_interval(self) -> None:
        """Reset state for next interval"""
        self.current_interval_start = None
        self.current_interval_frames = []
        self.current_interval_states = []

    def reset_session(self) -> None:
        """Reset all state for new session"""
        self.current_interval_start = None
        self.current_interval_frames = []
        self.current_interval_states = []
        self.previous_top_emotions = None
        self.previous_state = None
        self.interval_count = 0
