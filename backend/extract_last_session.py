"""
Extract Session Data from Backend Logs
Recovers lost session data by parsing backend log files
"""

import json
import re
from datetime import datetime
from typing import List, Dict
import argparse


def parse_timestamp(log_line: str) -> float:
    """Extract timestamp from log line"""
    match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+\]', log_line)
    if match:
        dt = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
        return dt.timestamp()
    return 0.0


def extract_client_sessions(log_file: str) -> Dict[str, Dict]:
    """
    Extract all client sessions from log file

    Returns:
        Dict mapping client_id to session data
    """
    sessions = {}

    with open(log_file, 'r') as f:
        lines = f.readlines()

    current_client = None

    for line in lines:
        # Client connection
        match = re.search(r'Client ([a-f0-9\-]+) connected', line)
        if match:
            client_id = match.group(1)
            if client_id not in sessions:
                sessions[client_id] = {
                    "metadata": {
                        "client_id": client_id,
                        "session_start": parse_timestamp(line),
                        "session_id": f"session_{client_id[:8]}"
                    },
                    "emotions": [],
                    "intervals": [],
                    "llm_updates": [],
                    "events": []
                }
            continue

        # Emotion detection
        match = re.search(
            r'Emotion detected for ([a-f0-9\-]+): (\w+) \(([^:]+): ([\d.]+)\)',
            line
        )
        if match:
            client_id = match.group(1)
            investor_state = match.group(2)
            primary_emotion = match.group(3)
            confidence = float(match.group(4))

            if client_id in sessions:
                sessions[client_id]["emotions"].append({
                    "timestamp": parse_timestamp(line),
                    "investor_state": investor_state,
                    "primary_emotion": primary_emotion,
                    "confidence": confidence,
                    "top_emotions": [],  # Not available in logs
                    "face_detected": True
                })
            continue

        # Interval complete
        match = re.search(
            r'Interval complete for ([a-f0-9\-]+): (\w+), (\d+) words',
            line
        )
        if match:
            client_id = match.group(1)
            investor_state = match.group(2)
            word_count = int(match.group(3))

            if client_id in sessions:
                timestamp = parse_timestamp(line)
                interval_num = len(sessions[client_id]["intervals"]) + 1

                sessions[client_id]["intervals"].append({
                    "interval_number": interval_num,
                    "timestamp": timestamp,
                    "interval_start": timestamp - 1.0,  # Approximate
                    "interval_end": timestamp,
                    "investor_state": investor_state,
                    "top_emotions": [],  # Would need to correlate with emotions
                    "words": [],  # Not available in logs
                    "full_text": "",
                    "frames_count": 0,  # Would need to count emotions
                    "flags": {
                        "silence": word_count == 0,
                        "high_confidence": False,
                        "emotion_shift": False,
                        "state_transition": False
                    }
                })
            continue

        # LLM/Coaching advice
        match = re.search(
            r'Coaching advice sent for ([a-f0-9\-]+): (.+)',
            line
        )
        if match:
            client_id = match.group(1)
            coaching_advice = match.group(2).strip()

            if client_id in sessions:
                timestamp = parse_timestamp(line)
                update_num = len(sessions[client_id]["llm_updates"]) + 1

                # Try to infer dominant state from last interval
                last_interval = sessions[client_id]["intervals"][-1] if sessions[client_id]["intervals"] else {}
                dominant_state = last_interval.get("investor_state", "neutral")

                sessions[client_id]["llm_updates"].append({
                    "update_number": update_num,
                    "timestamp": timestamp,
                    "context": {
                        "time_window": {},
                        "summary": {
                            "dominant_state": dominant_state
                        },
                        "patterns": {},
                        "flags": {},
                        "intervals_count": 5
                    },
                    "formatted_prompt": "[Not available from logs]",
                    "coaching_advice": coaching_advice,
                    "dominant_state": dominant_state,
                    "total_words": 0,
                    "engagement_trend": "stable"
                })
            continue

        # Client disconnection
        match = re.search(r'Client ([a-f0-9\-]+) disconnected', line)
        if match:
            client_id = match.group(1)
            if client_id in sessions:
                sessions[client_id]["metadata"]["session_end"] = parse_timestamp(line)
            continue

    return sessions


def enrich_session_data(session: Dict) -> Dict:
    """
    Enrich session data with computed fields
    """
    # Calculate frames per interval
    if session["intervals"]:
        emotions_by_time = {}
        for emotion in session["emotions"]:
            t = emotion["timestamp"]
            emotions_by_time[t] = emotion

        for interval in session["intervals"]:
            # Count emotions within this interval
            interval_start = interval["interval_start"]
            interval_end = interval["interval_end"]

            frames_in_interval = [
                e for e in session["emotions"]
                if interval_start <= e["timestamp"] < interval_end
            ]

            interval["frames_count"] = len(frames_in_interval)

            # Get top emotions for this interval
            if frames_in_interval:
                # Use last 3 emotions
                interval["top_emotions"] = [
                    {
                        "name": e["primary_emotion"],
                        "avg_score": e["confidence"],
                        "trend": "stable"
                    }
                    for e in frames_in_interval[-3:]
                ]

    return session


def main():
    parser = argparse.ArgumentParser(
        description="Extract session data from backend logs"
    )
    parser.add_argument(
        "--log-file",
        "-l",
        default="/tmp/beneai-backend.log",
        help="Path to backend log file (default: /tmp/beneai-backend.log)"
    )
    parser.add_argument(
        "--client-id",
        "-c",
        help="Extract specific client ID (optional, extracts all if not specified)"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for session files (default: current directory)"
    )
    parser.add_argument(
        "--list-clients",
        action="store_true",
        help="List all client IDs found in logs and exit"
    )

    args = parser.parse_args()

    # Extract sessions
    print(f"Parsing log file: {args.log_file}")
    sessions = extract_client_sessions(args.log_file)

    if not sessions:
        print("❌ No sessions found in log file")
        return 1

    print(f"\n✅ Found {len(sessions)} client sessions:")
    for client_id, session in sessions.items():
        metadata = session["metadata"]
        emotion_count = len(session["emotions"])
        interval_count = len(session["intervals"])
        llm_count = len(session["llm_updates"])

        print(f"\nClient: {client_id}")
        print(f"  Emotions: {emotion_count}")
        print(f"  Intervals: {interval_count}")
        print(f"  LLM Updates: {llm_count}")

        if "session_start" in metadata:
            start_time = datetime.fromtimestamp(metadata["session_start"])
            print(f"  Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if "session_end" in metadata:
            end_time = datetime.fromtimestamp(metadata["session_end"])
            duration = metadata["session_end"] - metadata.get("session_start", 0)
            print(f"  Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Duration: {duration:.1f} seconds")

    if args.list_clients:
        return 0

    # Extract specific client or all clients
    clients_to_extract = [args.client_id] if args.client_id else sessions.keys()

    for client_id in clients_to_extract:
        if client_id not in sessions:
            print(f"\n❌ Client {client_id} not found in logs")
            continue

        # Enrich session data
        session = enrich_session_data(sessions[client_id])

        # Save to file
        output_file = f"{args.output_dir}/session_{client_id[:8]}_recovered.json"
        with open(output_file, 'w') as f:
            json.dump(session, f, indent=2)

        print(f"\n✅ Saved session to: {output_file}")
        print(f"   Emotions: {len(session['emotions'])}")
        print(f"   Intervals: {len(session['intervals'])}")
        print(f"   LLM Updates: {len(session['llm_updates'])}")
        print(f"\n💡 Visualize with:")
        print(f"   python visualize_emotions.py {output_file} --prompts")

    return 0


if __name__ == "__main__":
    exit(main())
