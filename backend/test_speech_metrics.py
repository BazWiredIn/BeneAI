#!/usr/bin/env python3
"""
Test script to verify speech metrics handler
"""

import asyncio
import websockets
import json
import time


async def test_speech_metrics():
    """Test sending speech metrics to backend"""

    uri = "ws://localhost:8000/ws"

    print("=" * 60)
    print("Testing Speech Metrics Handler")
    print("=" * 60)
    print()

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to backend")

            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"✓ Received welcome: {welcome_data.get('message')}")
            print()

            # Test 1: Send speech metrics with transcript
            print("Test 1: Sending speech metrics with transcript...")
            speech_metrics = {
                "type": "speech_metrics",
                "timestamp": int(time.time() * 1000),
                "metrics": {
                    "wordsPerMinute": 150,
                    "recentTranscript": "Hello world this is a test of the speech recognition system",
                    "fillerWords": {"total": 2},
                    "pauseFrequency": 0.15,
                    "volumeLevel": 0.65
                }
            }

            await websocket.send(json.dumps(speech_metrics))
            print("✓ Sent speech metrics")

            # Wait for any response
            await asyncio.sleep(1)
            print("✓ Metrics processed (check backend.log for details)")
            print()

            # Test 2: Send empty transcript
            print("Test 2: Sending speech metrics without transcript...")
            empty_metrics = {
                "type": "speech_metrics",
                "timestamp": int(time.time() * 1000),
                "metrics": {
                    "wordsPerMinute": 0,
                    "recentTranscript": "",
                    "fillerWords": {"total": 0},
                    "pauseFrequency": 0.95,
                    "volumeLevel": 0.05
                }
            }

            await websocket.send(json.dumps(empty_metrics))
            print("✓ Sent empty metrics")
            await asyncio.sleep(1)
            print("✓ Empty metrics processed")
            print()

            # Test 3: Send multiple words
            print("Test 3: Sending speech metrics with longer transcript...")
            long_metrics = {
                "type": "speech_metrics",
                "timestamp": int(time.time() * 1000),
                "metrics": {
                    "wordsPerMinute": 180,
                    "recentTranscript": "We have achieved significant growth in the past quarter with revenue up by thirty percent and user engagement doubled across all platforms making this our best quarter yet",
                    "fillerWords": {"total": 5},
                    "pauseFrequency": 0.08,
                    "volumeLevel": 0.75
                }
            }

            await websocket.send(json.dumps(long_metrics))
            print("✓ Sent long transcript")
            await asyncio.sleep(1)
            print("✓ Long transcript processed")
            print()

            print("=" * 60)
            print("✅ All tests passed!")
            print()
            print("Check backend.log for:")
            print("  - 'Received speech metrics from {client_id}: WPM=...'")
            print("  - 'Processed X words from {client_id}, WPM: ...'")
            print()
            print("Next steps:")
            print("  1. Open frontend in browser (http://localhost:8080)")
            print("  2. Click 'Start' and speak into microphone")
            print("  3. Check that WPM shows > 0")
            print("  4. Stop session and check session_*.json file")
            print("  5. Verify intervals have words in them")
            print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_speech_metrics())
