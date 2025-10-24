"""
Emotion Time-Series Visualization Tool

Visualizes emotion data from recorded sessions.
Generates graphs showing:
- Top 3 emotions over time
- Investor state transitions
- Emotion scores over time
- Speech alignment
"""

import json
import argparse
from typing import List, Dict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime


def load_session_data(filepath: str) -> Dict:
    """
    Load recorded session data from JSON file

    Args:
        filepath: Path to JSON file with session data

    Returns:
        Dictionary with session data (metadata, intervals, llm_updates, etc.)
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    # Support old format (just intervals list) and new format (full session dict)
    if isinstance(data, list):
        # Old format: just intervals
        return {
            "metadata": {},
            "intervals": data,
            "llm_updates": [],
            "emotions": [],
            "events": []
        }
    elif isinstance(data, dict):
        # New format: full session data
        return data
    else:
        raise ValueError("Invalid data format. Expected list or dict")


def plot_emotions_over_time(intervals: List[Dict], llm_updates: List[Dict] = None, output_file: str = None, session_start: float = None):
    """
    Plot top 3 emotions over time with LLM updates

    Args:
        intervals: List of interval data
        llm_updates: List of LLM update data (optional)
        output_file: Optional filename to save plot
        session_start: Session start timestamp for proper x-axis scaling
    """
    if not intervals:
        print("No intervals to plot")
        return

    llm_updates = llm_updates or []

    # Extract data
    timestamps = [interval["timestamp"] for interval in intervals]

    # Calculate session start (earliest timestamp) if not provided
    if session_start is None:
        session_start = intervals[0].get("interval_start", timestamps[0])

    # Calculate session end (latest timestamp)
    session_end = intervals[-1].get("interval_end", timestamps[-1])

    # Get all emotion names that appear in top 3
    all_emotion_names = set()
    for interval in intervals:
        for emotion in interval.get("top_emotions", [])[:3]:
            all_emotion_names.add(emotion["name"])

    # Create figure with multiple subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle("Emotion Analysis Over Time", fontsize=16, fontweight='bold')

    # Plot 1: Average scores for top emotions
    emotion_data = {name: [] for name in all_emotion_names}

    for interval in intervals:
        # Initialize all emotions with 0 for this timestamp
        current_emotions = {name: 0 for name in all_emotion_names}

        # Fill in actual values from top emotions
        for emotion in interval.get("top_emotions", [])[:3]:
            name = emotion["name"]
            current_emotions[name] = emotion.get("avg_score", 0)

        # Append to data
        for name in all_emotion_names:
            emotion_data[name].append(current_emotions[name])

    # Plot emotion lines
    colors = plt.cm.tab10.colors
    for i, emotion_name in enumerate(sorted(all_emotion_names)):
        color = colors[i % len(colors)]
        ax1.plot(
            timestamps,
            emotion_data[emotion_name],
            label=emotion_name,
            linewidth=2,
            color=color,
            alpha=0.8
        )

    # Add LLM update markers (no clipping - show all updates)
    for llm_update in llm_updates:
        update_time = llm_update.get("timestamp", 0)
        ax1.axvline(x=update_time, color='purple', linestyle='--', linewidth=2, alpha=0.6)
        ax1.text(
            update_time, 0.95, f"LLM #{llm_update.get('update_number', '?')}",
            rotation=90, verticalalignment='top', fontsize=8,
            color='purple', fontweight='bold'
        )

    ax1.set_xlabel("Time (seconds)", fontsize=12)
    ax1.set_ylabel("Emotion Score", fontsize=12)
    ax1.set_title("Top 3 Emotions (Per-Interval Average) with LLM Updates", fontsize=14)
    ax1.legend(loc='upper right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 1)
    # Set x-axis to show full session from start to end (no clipping)
    ax1.set_xlim(session_start - 0.5, session_end + 0.5)

    # Plot 2: Investor state timeline
    state_colors = {
        "positive": "#2ecc71",
        "receptive": "#3498db",
        "evaluative": "#f39c12",
        "skeptical": "#e74c3c",
        "neutral": "#95a5a6"
    }

    # Create colored bars for each interval
    for i, interval in enumerate(intervals):
        state = interval.get("investor_state", "neutral")
        color = state_colors.get(state, "#95a5a6")

        # Interval duration
        start = interval.get("interval_start", timestamps[i])
        end = interval.get("interval_end", timestamps[i] + 1)

        ax2.barh(
            0,
            width=end - start,
            left=start,
            height=0.5,
            color=color,
            alpha=0.7,
            edgecolor='black',
            linewidth=0.5
        )

        # Add text labels if interval has speech
        text = interval.get("full_text", "")
        if text and len(text) > 0:
            mid = (start + end) / 2
            ax2.text(
                mid,
                -0.3,
                text[:20] + "..." if len(text) > 20 else text,
                ha='center',
                va='top',
                fontsize=8,
                rotation=45
            )

    # Set x-axis to show full session from start to end (no clipping)
    ax2.set_xlim(session_start - 0.5, session_end + 0.5)
    ax2.set_ylim(-1, 1)
    ax2.set_xlabel("Time (seconds)", fontsize=12)
    ax2.set_title("Investor State Timeline with Speech", fontsize=14)
    ax2.set_yticks([])

    # Create legend for states
    legend_patches = [
        mpatches.Patch(color=color, label=state.capitalize(), alpha=0.7)
        for state, color in state_colors.items()
    ]
    ax2.legend(handles=legend_patches, loc='upper right', fontsize=10)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()


def plot_emotion_trends(intervals: List[Dict], output_file: str = None):
    """
    Plot emotion trends (increasing/decreasing/stable)

    Args:
        intervals: List of interval data
        output_file: Optional filename to save plot
    """
    if not intervals:
        print("No intervals to plot")
        return

    timestamps = [interval["timestamp"] for interval in intervals]

    # Count trends
    trend_counts = {
        "increasing": [],
        "decreasing": [],
        "stable": []
    }

    for interval in intervals:
        counts = {"increasing": 0, "decreasing": 0, "stable": 0}

        for emotion in interval.get("top_emotions", [])[:3]:
            trend = emotion.get("trend", "stable")
            if trend in counts:
                counts[trend] += 1

        for trend in trend_counts:
            trend_counts[trend].append(counts[trend])

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("Emotion Trends Over Time", fontsize=16, fontweight='bold')

    # Stacked area plot
    ax.fill_between(timestamps, trend_counts["increasing"], label="Increasing", alpha=0.7, color='#2ecc71')
    ax.fill_between(
        timestamps,
        trend_counts["increasing"],
        [i + d for i, d in zip(trend_counts["increasing"], trend_counts["decreasing"])],
        label="Decreasing",
        alpha=0.7,
        color='#e74c3c'
    )
    ax.fill_between(
        timestamps,
        [i + d for i, d in zip(trend_counts["increasing"], trend_counts["decreasing"])],
        [i + d + s for i, d, s in zip(trend_counts["increasing"], trend_counts["decreasing"], trend_counts["stable"])],
        label="Stable",
        alpha=0.7,
        color='#95a5a6'
    )

    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Number of Emotions", fontsize=12)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_file}")
    else:
        plt.show()


def plot_llm_updates(llm_updates: List[Dict], intervals: List[Dict], output_file: str = None):
    """
    Plot LLM updates timeline with coaching advice

    Args:
        llm_updates: List of LLM update data
        intervals: List of interval data (for context)
        output_file: Optional filename to save plot
    """
    if not llm_updates:
        print("No LLM updates to plot")
        return

    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
    fig.suptitle("LLM Coaching Updates Timeline", fontsize=16, fontweight='bold')

    # Plot 1: Dominant state at each LLM update
    state_colors = {
        "positive": "#2ecc71",
        "receptive": "#3498db",
        "evaluative": "#f39c12",
        "skeptical": "#e74c3c",
        "neutral": "#95a5a6"
    }

    update_times = [u["timestamp"] for u in llm_updates]
    update_numbers = [u["update_number"] for u in llm_updates]
    dominant_states = [u["dominant_state"] for u in llm_updates]

    # Color bars by dominant state
    colors = [state_colors.get(state, "#95a5a6") for state in dominant_states]

    ax1.bar(update_numbers, [1]*len(update_numbers), color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel("LLM Update", fontsize=12)
    ax1.set_xlabel("Update Number", fontsize=12)
    ax1.set_title("Dominant Investor State at Each LLM Update", fontsize=14)
    ax1.set_ylim(0, 1.5)
    ax1.set_yticks([])

    # Add state labels on bars
    for i, (num, state) in enumerate(zip(update_numbers, dominant_states)):
        ax1.text(num, 0.5, state.upper(), ha='center', va='center',
                fontsize=10, fontweight='bold', color='white')

    # Create legend
    legend_patches = [
        mpatches.Patch(color=color, label=state.capitalize(), alpha=0.7)
        for state, color in state_colors.items()
    ]
    ax1.legend(handles=legend_patches, loc='upper right', fontsize=9)

    # Plot 2: Words spoken per update window
    words_counts = [u.get("total_words", 0) for u in llm_updates]
    ax2.bar(update_numbers, words_counts, color='#3498db', alpha=0.7, edgecolor='black')
    ax2.set_xlabel("Update Number", fontsize=12)
    ax2.set_ylabel("Words Spoken (in 5-sec window)", fontsize=12)
    ax2.set_title("Speech Activity at Each LLM Update", fontsize=14)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"LLM updates plot saved to {output_file}")
    else:
        plt.show()


def print_llm_prompts(llm_updates: List[Dict]):
    """
    Print all LLM prompts and responses

    Args:
        llm_updates: List of LLM update data
    """
    if not llm_updates:
        print("No LLM updates to display")
        return

    print("\n" + "=" * 80)
    print("LLM PROMPTS & COACHING ADVICE")
    print("=" * 80)

    for update in llm_updates:
        print(f"\n--- UPDATE #{update['update_number']} @ {update['timestamp']:.1f}s ---")
        print(f"Dominant State: {update['dominant_state'].upper()}")
        print(f"Words Spoken: {update.get('total_words', 0)}")
        print(f"Engagement Trend: {update.get('engagement_trend', 'N/A')}")
        print(f"\nCoaching Advice: \"{update['coaching_advice']}\"")
        print(f"\nFull Context Sent to LLM:")
        print("-" * 80)
        print(update.get('formatted_prompt', 'N/A'))
        print("-" * 80)

    print("\n" + "=" * 80 + "\n")


def print_summary_stats(session_data: Dict):
    """
    Print summary statistics for the session

    Args:
        session_data: Full session data dictionary
    """
    intervals = session_data.get("intervals", [])
    llm_updates = session_data.get("llm_updates", [])
    metadata = session_data.get("metadata", {})

    if not intervals:
        print("No intervals to analyze")
        return

    print("\n" + "=" * 60)
    print("SESSION SUMMARY STATISTICS")
    print("=" * 60)

    # Metadata
    print(f"\nSession ID: {metadata.get('session_id', 'N/A')}")
    print(f"Client ID: {metadata.get('client_id', 'N/A')}")

    # Basic stats
    if intervals:
        total_duration = intervals[-1]["interval_end"] - intervals[0]["interval_start"]
        total_words = sum(len(interval.get("words", [])) for interval in intervals)
        total_frames = sum(interval.get("frames_count", 0) for interval in intervals)

        print(f"\nDuration: {total_duration:.1f} seconds ({len(intervals)} intervals)")
        print(f"Total Words: {total_words}")
        print(f"Total Frames: {total_frames}")
        print(f"Average Frames per Interval: {total_frames / len(intervals):.1f}")
        print(f"LLM Updates: {len(llm_updates)}")

    # State distribution
    state_counts = {}
    for interval in intervals:
        state = interval.get("investor_state", "neutral")
        state_counts[state] = state_counts.get(state, 0) + 1

    print("\nInvestor State Distribution:")
    for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(intervals)) * 100
        print(f"  {state.capitalize()}: {count} intervals ({percentage:.1f}%)")

    # State transitions
    transitions = 0
    for i in range(1, len(intervals)):
        if intervals[i]["investor_state"] != intervals[i-1]["investor_state"]:
            transitions += 1

    print(f"\nState Transitions: {transitions}")

    # Silence analysis
    silence_count = sum(
        1 for interval in intervals
        if interval.get("flags", {}).get("silence", False)
    )
    print(f"Silence Intervals: {silence_count} ({(silence_count / len(intervals)) * 100:.1f}%)")

    # Top emotions
    emotion_appearances = {}
    for interval in intervals:
        for emotion in interval.get("top_emotions", [])[:3]:
            name = emotion["name"]
            emotion_appearances[name] = emotion_appearances.get(name, 0) + 1

    print("\nMost Common Emotions in Top 3:")
    for emotion, count in sorted(emotion_appearances.items(), key=lambda x: x[1], reverse=True)[:5]:
        percentage = (count / len(intervals)) * 100
        print(f"  {emotion}: {count} times ({percentage:.1f}%)")

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Visualize emotion time-series data from BeneAI sessions"
    )
    parser.add_argument(
        "session_file",
        nargs="?",
        default="session_data.json",
        help="Path to JSON file containing session data (default: session_data.json)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for plots (default: show plots)",
        default=None
    )
    parser.add_argument(
        "--trends",
        action="store_true",
        help="Also plot emotion trends"
    )
    parser.add_argument(
        "--prompts",
        action="store_true",
        help="Print all LLM prompts and coaching advice"
    )

    args = parser.parse_args()

    try:
        # Load data
        print(f"Loading session data from {args.session_file}...")
        session_data = load_session_data(args.session_file)

        intervals = session_data.get("intervals", [])
        llm_updates = session_data.get("llm_updates", [])

        print(f"Loaded {len(intervals)} intervals and {len(llm_updates)} LLM updates")

        # Print summary
        print_summary_stats(session_data)

        # Print LLM prompts if requested
        if args.prompts and llm_updates:
            print_llm_prompts(llm_updates)

        # Generate plots
        output_file_main = None
        output_file_trends = None
        output_file_llm = None

        if args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_main = f"{args.output}/emotions_{timestamp}.png"
            output_file_trends = f"{args.output}/trends_{timestamp}.png"
            output_file_llm = f"{args.output}/llm_updates_{timestamp}.png"

        if intervals:
            print("\nGenerating emotion time-series plot...")
            # Get session start time from metadata for proper timeline scaling
            session_start_time = session_data.get("metadata", {}).get("session_start", None)
            plot_emotions_over_time(intervals, llm_updates, output_file_main, session_start_time)

            if args.trends:
                print("Generating emotion trends plot...")
                plot_emotion_trends(intervals, output_file_trends)

        if llm_updates:
            print("\nGenerating LLM updates plot...")
            plot_llm_updates(llm_updates, intervals, output_file_llm)

        print("\nVisualization complete!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
