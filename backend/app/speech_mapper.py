"""
Speech Mapper
Maps transcribed words to emotion intervals for synchronized analysis
"""

import time
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SpeechMapper:
    """
    Maps speech transcription to 1-second emotion intervals

    Handles:
    - Word-level timestamp alignment
    - Silence detection
    - Text aggregation per interval
    - Pause tracking
    """

    def __init__(self, silence_threshold: float = 0.5):
        """
        Initialize speech mapper

        Args:
            silence_threshold: Seconds of no speech to mark as silence (default 0.5)
        """
        self.silence_threshold = silence_threshold

        # Current state
        self.pending_words = []  # Words waiting to be mapped
        self.last_word_time = None

        # Session statistics
        self.total_words_mapped = 0
        self.total_silence_detected = 0

    def add_word(
        self,
        word: str,
        timestamp: float,
        confidence: float = 1.0
    ) -> None:
        """
        Add a transcribed word with its timestamp

        Args:
            word: Transcribed word text
            timestamp: Unix timestamp when word was spoken
            confidence: Speech recognition confidence (0.0-1.0)
        """
        self.pending_words.append({
            "word": word,
            "timestamp": timestamp,
            "confidence": confidence
        })

        self.last_word_time = timestamp

        logger.debug(f"📝 [SpeechMapper.add_word] \"{word}\" @ {timestamp:.2f}s (pending: {len(self.pending_words)})")

    def add_transcript_segment(
        self,
        text: str,
        start_time: float,
        end_time: float,
        confidence: float = 1.0
    ) -> None:
        """
        Add a full transcript segment (alternative to word-by-word)

        This is useful when the speech API returns phrases instead of individual words.
        We'll estimate word timestamps by distributing them evenly across the segment.

        Args:
            text: Full transcript text
            start_time: Segment start timestamp
            end_time: Segment end timestamp
            confidence: Recognition confidence
        """
        words = text.strip().split()
        if not words:
            return

        # Distribute timestamps evenly across words
        duration = end_time - start_time
        time_per_word = duration / len(words)

        for i, word in enumerate(words):
            word_timestamp = start_time + (i * time_per_word)
            self.add_word(word, word_timestamp, confidence)

    def map_to_interval(
        self,
        interval_start: float,
        interval_end: float
    ) -> Tuple[List[Dict], str, bool]:
        """
        Map pending words to a specific interval

        Args:
            interval_start: Start timestamp of interval
            interval_end: End timestamp of interval

        Returns:
            Tuple of (words_list, full_text, is_silence)
            - words_list: List of word dictionaries in this interval
            - full_text: Concatenated text for interval
            - is_silence: True if interval contains silence
        """
        # BUFFER: Allow words up to 5 seconds before interval start
        # This accounts for transcription delay (Google API takes ~600ms)
        LOOKBACK_BUFFER = 5.0  # seconds

        # Find words that fall within this interval (or just before it)
        interval_words = []

        # Filter words for this interval
        remaining_words = []
        for word_data in self.pending_words:
            word_timestamp = word_data["timestamp"]

            # Check if word falls within interval (with lookback buffer)
            if (interval_start - LOOKBACK_BUFFER) <= word_timestamp < interval_end:
                # Word is within the lookback window, include it
                interval_words.append(word_data)
                self.total_words_mapped += 1

                time_diff = interval_start - word_timestamp
                logger.info(f"   ✅ Word \"{word_data['word']}\" matched to interval (offset: {time_diff:.2f}s)")
                logger.debug(f"      Word @ {word_timestamp:.2f}s vs interval [{interval_start:.2f}s - {interval_end:.2f}s]")

            elif word_timestamp >= interval_end:
                # Keep for future intervals
                remaining_words.append(word_data)
                logger.debug(f"   ⏭️  Word \"{word_data['word']}\" @ {word_timestamp:.2f}s is after interval end, keeping for future")

            else:
                # Word is too old (before lookback buffer), discard it
                logger.warning(f"   🗑️  Word \"{word_data['word']}\" @ {word_timestamp:.2f}s is too old, discarding (before {interval_start - LOOKBACK_BUFFER:.2f}s)")

        # Update pending words
        self.pending_words = remaining_words

        # Build full text
        full_text = " ".join(w["word"] for w in interval_words)

        # Detect silence
        is_silence = self._is_silence_interval(
            interval_start,
            interval_end,
            interval_words
        )

        if is_silence:
            self.total_silence_detected += 1

        return interval_words, full_text, is_silence

    def _is_silence_interval(
        self,
        interval_start: float,
        interval_end: float,
        interval_words: List[Dict]
    ) -> bool:
        """
        Check if interval should be marked as silence

        Args:
            interval_start: Interval start time
            interval_end: Interval end time
            interval_words: Words found in interval

        Returns:
            True if interval is silent
        """
        # If no words in interval, it's silence
        if not interval_words:
            return True

        # Check if there's a long gap within the interval
        if len(interval_words) > 1:
            # Sort by timestamp
            sorted_words = sorted(interval_words, key=lambda x: x["timestamp"])

            # Check gaps between consecutive words
            for i in range(len(sorted_words) - 1):
                gap = sorted_words[i + 1]["timestamp"] - sorted_words[i]["timestamp"]
                if gap >= self.silence_threshold:
                    return True

        return False

    def update_interval_with_speech(self, interval_data: Dict) -> Dict:
        """
        Update an interval dictionary with speech data

        Args:
            interval_data: Interval data from IntervalAggregator

        Returns:
            Updated interval data with speech fields populated
        """
        interval_start = interval_data["interval_start"]
        interval_end = interval_data["interval_end"]

        logger.info(f"🔗 [SpeechMapper.update_interval] Mapping words to interval [{interval_start:.2f}s - {interval_end:.2f}s]")
        logger.info(f"   Pending words before mapping: {len(self.pending_words)}")

        # Map words to this interval
        words, full_text, is_silence = self.map_to_interval(
            interval_start,
            interval_end
        )

        logger.info(f"   ✅ Mapped {len(words)} words to interval")
        logger.info(f"   Text: \"{full_text}\"")
        logger.info(f"   Silence: {is_silence}")
        logger.info(f"   Remaining pending words: {len(self.pending_words)}")

        # Update interval data
        interval_data["words"] = words
        interval_data["full_text"] = full_text
        interval_data["flags"]["silence"] = is_silence

        # Add speech statistics
        interval_data["speech_stats"] = {
            "word_count": len(words),
            "avg_confidence": (
                sum(w["confidence"] for w in words) / len(words)
                if words else 0.0
            ),
            "is_silence": is_silence
        }

        return interval_data

    def get_pending_word_count(self) -> int:
        """
        Get number of words waiting to be mapped

        Returns:
            Count of pending words
        """
        return len(self.pending_words)

    def get_stats(self) -> Dict:
        """
        Get speech mapping statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "total_words_mapped": self.total_words_mapped,
            "total_silence_detected": self.total_silence_detected,
            "pending_words": len(self.pending_words),
            "last_word_time": self.last_word_time
        }

    def flush_old_words(self, current_time: float, max_age: float = 10.0):
        """
        Remove words that are too old and haven't been mapped

        This prevents memory buildup if intervals are not being processed.

        Args:
            current_time: Current timestamp
            max_age: Maximum age in seconds for pending words
        """
        cutoff_time = current_time - max_age

        self.pending_words = [
            w for w in self.pending_words
            if w["timestamp"] >= cutoff_time
        ]

    def reset_session(self):
        """Reset all state for new session"""
        self.pending_words = []
        self.last_word_time = None
        self.total_words_mapped = 0
        self.total_silence_detected = 0
