"""
Session Data Logger
Logs all emotion, interval, and LLM data to JSON for visualization and analysis
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class SessionLogger:
    """
    Logs session data to JSON file for post-analysis and visualization

    Captures:
    - Raw emotion data per frame
    - Aggregated 1-second intervals
    - LLM context (what gets sent to GPT-4)
    - LLM responses (coaching advice)

    Each client gets their own session file to prevent data loss.
    """

    def __init__(self, client_id: str, output_dir: str = "."):
        """
        Initialize session logger for a specific client

        Args:
            client_id: Unique client identifier
            output_dir: Directory to save session files (default: current directory)
        """
        self.client_id = client_id
        self.output_dir = Path(output_dir)
        # Create timestamp-based filename for easy identification of test runs
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_file = self.output_dir / f"session_{timestamp}.json"
        # Also update the "latest" symlink
        self.latest_file = self.output_dir / "session_data.json"
        self.session_data = {
            "metadata": {
                "session_start": time.time(),
                "session_id": None,
                "client_id": None
            },
            "emotions": [],  # Raw emotion detections per frame
            "intervals": [],  # 1-second aggregated intervals
            "llm_updates": [],  # LLM context and responses
            "events": []  # Other notable events (state transitions, etc.)
        }

    def start_new_session(self, session_id: str = None):
        """
        Start a new session

        Args:
            session_id: Optional session identifier
        """
        self.session_data = {
            "metadata": {
                "session_start": time.time(),
                "session_id": session_id or f"session_{int(time.time())}",
                "client_id": self.client_id
            },
            "emotions": [],
            "intervals": [],
            "llm_updates": [],
            "events": []
        }

        # Save initial session file
        self._save_to_file()
        # Update latest symlink
        self._update_latest_symlink()

    def log_emotion(self, emotion_data: Dict, timestamp: float):
        """
        Log a single emotion detection result

        Args:
            emotion_data: Emotion data from Hume AI
            timestamp: Timestamp of detection
        """
        self.session_data["emotions"].append({
            "timestamp": timestamp,
            "investor_state": emotion_data.get("investor_state"),
            "primary_emotion": emotion_data.get("primary_emotion"),
            "confidence": emotion_data.get("confidence"),
            "top_emotions": emotion_data.get("top_emotions", [])[:5],  # Keep top 5
            "face_detected": emotion_data.get("face_bbox") is not None
        })

    def log_interval(self, interval_data: Dict, interval_number: int):
        """
        Log a completed 1-second interval

        Args:
            interval_data: Interval data from IntervalAggregator
            interval_number: Interval sequence number
        """
        self.session_data["intervals"].append({
            "interval_number": interval_number,
            "timestamp": interval_data.get("timestamp"),
            "interval_start": interval_data.get("interval_start"),
            "interval_end": interval_data.get("interval_end"),
            "investor_state": interval_data.get("investor_state"),
            "top_emotions": interval_data.get("top_emotions", [])[:3],
            "words": interval_data.get("words", []),
            "full_text": interval_data.get("full_text", ""),
            "frames_count": interval_data.get("frames_count", 0),
            "flags": interval_data.get("flags", {})
        })

    def log_llm_update(
        self,
        llm_context: Dict,
        formatted_prompt: str,
        coaching_advice: str,
        timestamp: float,
        update_number: int
    ):
        """
        Log an LLM update (context + response)

        Args:
            llm_context: Full context dictionary sent to LLM
            formatted_prompt: Human-readable formatted prompt text
            coaching_advice: LLM response (coaching advice)
            timestamp: Timestamp of update
            update_number: LLM update sequence number
        """
        self.session_data["llm_updates"].append({
            "update_number": update_number,
            "timestamp": timestamp,
            "context": {
                "time_window": llm_context.get("time_window", {}),
                "summary": llm_context.get("summary", {}),
                "patterns": llm_context.get("patterns", {}),
                "flags": llm_context.get("flags", {}),
                "intervals_count": len(llm_context.get("intervals", []))
            },
            "formatted_prompt": formatted_prompt,
            "coaching_advice": coaching_advice,
            "dominant_state": llm_context.get("summary", {}).get("dominant_state", "neutral"),
            "total_words": llm_context.get("summary", {}).get("total_words", 0),
            "engagement_trend": llm_context.get("patterns", {}).get("engagement_trend", "stable")
        })

    def log_event(self, event_type: str, description: str, data: Dict = None):
        """
        Log a notable event

        Args:
            event_type: Type of event (state_transition, emotion_shift, etc.)
            description: Human-readable description
            data: Optional additional data
        """
        self.session_data["events"].append({
            "timestamp": time.time(),
            "type": event_type,
            "description": description,
            "data": data or {}
        })

    def get_summary(self) -> Dict:
        """
        Get summary statistics for current session

        Returns:
            Dictionary with summary stats
        """
        metadata = self.session_data["metadata"]
        emotions = self.session_data["emotions"]
        intervals = self.session_data["intervals"]
        llm_updates = self.session_data["llm_updates"]

        duration = time.time() - metadata["session_start"] if metadata["session_start"] else 0

        return {
            "session_duration_seconds": round(duration, 1),
            "total_emotions_detected": len(emotions),
            "total_intervals": len(intervals),
            "total_llm_updates": len(llm_updates),
            "total_words_spoken": sum(len(i.get("words", [])) for i in intervals),
            "total_frames_processed": sum(i.get("frames_count", 0) for i in intervals),
            "session_id": metadata.get("session_id"),
            "client_id": metadata.get("client_id")
        }

    def save(self):
        """Save current session data to JSON file"""
        self._save_to_file()

    def _save_to_file(self):
        """Internal method to write data to file"""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            with open(self.output_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            print(f"Error saving session data to {self.output_file}: {e}")

    def _update_latest_symlink(self):
        """Update session_data.json symlink to point to this session"""
        try:
            # Remove old symlink if exists
            if self.latest_file.exists() or self.latest_file.is_symlink():
                self.latest_file.unlink()

            # Create symlink to this session
            # Use relative path for symlink
            relative_target = self.output_file.name
            self.latest_file.symlink_to(relative_target)
        except Exception as e:
            # If symlinks don't work (Windows), just copy the file
            try:
                import shutil
                shutil.copy(self.output_file, self.latest_file)
            except Exception as e2:
                print(f"Error updating latest file: {e}, {e2}")

    def auto_save(self):
        """
        Save data every N operations (call after each log operation)
        Auto-saves after every interval or LLM update to prevent data loss
        """
        # Auto-save on interval or LLM update
        if len(self.session_data["intervals"]) % 1 == 0 or \
           len(self.session_data["llm_updates"]) % 1 == 0:
            self._save_to_file()


# Per-client session loggers
_session_loggers: Dict[str, SessionLogger] = {}


def get_session_logger(client_id: str, output_dir: str = ".") -> SessionLogger:
    """
    Get or create session logger for a specific client

    Args:
        client_id: Unique client identifier
        output_dir: Directory to save session files

    Returns:
        SessionLogger instance for this client
    """
    global _session_loggers

    if client_id not in _session_loggers:
        _session_loggers[client_id] = SessionLogger(client_id, output_dir)

    return _session_loggers[client_id]


def close_session_logger(client_id: str):
    """
    Close and remove session logger for a client

    Args:
        client_id: Client identifier
    """
    global _session_loggers

    if client_id in _session_loggers:
        # Final save
        _session_loggers[client_id].save()
        del _session_loggers[client_id]
