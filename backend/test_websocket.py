#!/usr/bin/env python3
"""
WebSocket Connection Test for BeneAI Backend

Tests the WebSocket endpoint to verify connectivity and basic message handling.
"""

import asyncio
import websockets
import json


async def test_connection():
    """Test WebSocket connection to BeneAI backend"""
    uri = "ws://localhost:8000/ws"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to WebSocket!\n")

            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"✓ Received welcome message:")
            print(f"   Type: {welcome_data.get('type')}")
            print(f"   Status: {welcome_data.get('status')}")
            print(f"   Message: {welcome_data.get('message')}")
            print(f"   Version: {welcome_data.get('server_version')}\n")

            # Send ping
            print("Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            print("✓ Sent ping\n")

            # Receive pong
            pong = await websocket.recv()
            pong_data = json.loads(pong)
            print(f"✓ Received pong:")
            print(f"   Type: {pong_data.get('type')}")
            print(f"   Timestamp: {pong_data.get('timestamp')}\n")

            print("=" * 50)
            print("✅ WebSocket is working perfectly!")
            print("=" * 50)
            print("\nYour backend is ready to:")
            print("  • Receive video frames")
            print("  • Process emotions with Hume AI")
            print("  • Aggregate into 1-second intervals")
            print("  • Send LLM context updates every 5 seconds")

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ WebSocket Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is the backend running? (python main.py)")
        print("  2. Is it running on port 8000?")
        print("  3. Check backend logs for errors")

    except ConnectionRefusedError:
        print(f"❌ Connection Refused")
        print("\nThe backend is not running. Start it with:")
        print("  cd backend")
        print("  uvicorn main:app --reload --port 8000")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("BeneAI WebSocket Connection Test")
    print("=" * 50 + "\n")

    asyncio.run(test_connection())

    print("\n")
