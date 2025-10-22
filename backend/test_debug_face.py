#!/usr/bin/env python3
"""
Debug script for face detection issues
Tests with known good images and provides detailed diagnostics
"""

import asyncio
import base64
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from app.hume_client import HumeClient


def encode_image(image_path: str) -> str:
    """Encode image file to base64"""
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
    return base64_data


async def test_image_detailed(image_path: str):
    """Test image with detailed debugging"""
    print(f"\n{'='*70}")
    print(f"DEBUG: Testing {image_path}")
    print(f"{'='*70}")

    # Check file
    path = Path(image_path)
    if not path.exists():
        print(f"❌ File not found: {image_path}")
        return

    file_size = path.stat().st_size
    print(f"✅ File exists: {file_size:,} bytes")

    # Encode
    try:
        print("\n📸 Encoding image...")
        image_data = encode_image(image_path)
        print(f"✅ Encoded: {len(image_data):,} chars of base64")
    except Exception as e:
        print(f"❌ Encoding failed: {e}")
        return

    # Connect
    print("\n🔌 Connecting to Hume AI...")
    client = HumeClient()
    connected = await client.connect()

    if not connected:
        print("❌ Connection failed")
        return

    print("✅ Connected")

    # Analyze
    print("\n🧠 Analyzing (check debug logs above for details)...")
    result = await client.analyze_face(image_data)

    await client.disconnect()

    # Results
    print(f"\n{'='*70}")
    if result:
        print("✅ SUCCESS - Face detected!")
        print(f"{'='*70}")
        print(f"Primary Emotion: {result['primary_emotion']}")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Investor State: {result['investor_state']}")
        print(f"\nTop 5 Emotions:")
        for emotion in result.get('top_emotions', [])[:5]:
            print(f"  - {emotion['name']}: {emotion['score']:.1%}")
    else:
        print("❌ FAILED - No face detected")
        print(f"{'='*70}")
        print("\nPossible reasons:")
        print("  1. No clear face in image")
        print("  2. Face too small or at wrong angle")
        print("  3. Poor lighting")
        print("  4. API configuration issue")
        print("\nCheck DEBUG logs above for details!")

    print(f"{'='*70}\n")


async def main():
    print("\n" + "="*70)
    print("🔍 Hume Face Detection Debug Tool")
    print("="*70)

    if len(sys.argv) < 2:
        print("\nUsage: python test_debug_face.py <image_path>")
        print("\nExample:")
        print("  python test_debug_face.py /tmp/hume_test_capture.jpg")
        print("  python test_debug_face.py ~/Pictures/photo.jpg")
        return

    image_path = sys.argv[1]
    await test_image_detailed(image_path)


if __name__ == "__main__":
    asyncio.run(main())
