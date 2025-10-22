#!/usr/bin/env python3
"""
Simple Test Script for Hume AI with Real Photos

Usage:
    python test_with_photo.py path/to/photo.jpg           # Test with image file
    python test_with_photo.py --webcam                    # Capture from webcam
    python test_with_photo.py --text "Your text here"     # Test language analysis
"""

import asyncio
import base64
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.hume_client import HumeClient


def encode_image(image_path: str) -> str:
    """Encode image file to base64"""
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
    return base64_data


async def test_facial_emotion(image_path: str):
    """Test facial emotion detection with an image file"""
    print(f"\n{'='*60}")
    print(f"Testing Facial Emotion Analysis")
    print(f"{'='*60}")
    print(f"Image: {image_path}")

    # Check if file exists
    if not Path(image_path).exists():
        print(f"❌ Error: File not found: {image_path}")
        return

    # Encode image
    print("📸 Encoding image...")
    try:
        image_data = encode_image(image_path)
        print(f"✅ Image encoded ({len(image_data)} bytes)")
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return

    # Connect to Hume AI
    print("\n🔌 Connecting to Hume AI...")
    client = HumeClient()
    connected = await client.connect()

    if not connected:
        print("❌ Failed to connect to Hume AI")
        return

    print("✅ Connected successfully")

    # Analyze facial emotions
    print("\n🧠 Analyzing facial emotions...")
    result = await client.analyze_face(image_data)

    await client.disconnect()

    # Display results
    if not result:
        print("❌ No face detected in image")
        print("\nTips:")
        print("  - Make sure the image has a clear, visible face")
        print("  - Try a well-lit photo")
        print("  - Face should be facing forward")
        return

    print(f"\n{'='*60}")
    print("✅ RESULTS")
    print(f"{'='*60}")

    print(f"\n🎯 Primary Emotion: {result['primary_emotion']}")
    print(f"📊 Confidence: {result['confidence']:.1%}")
    print(f"💼 Investor State: {result['investor_state'].upper()}")

    if result.get('num_faces', 1) > 1:
        print(f"👥 Faces Detected: {result['num_faces']} (showing first face)")

    print(f"\n🔝 Top 10 Emotions:")
    print(f"{'─'*60}")
    for i, emotion in enumerate(result.get('top_emotions', [])[:10], 1):
        bar_length = int(emotion['score'] * 40)
        bar = '█' * bar_length + '░' * (40 - bar_length)
        print(f"{i:2d}. {emotion['name']:25s} {bar} {emotion['score']:.1%}")

    print(f"\n{'='*60}")
    print("📝 Interpretation:")
    print(f"{'='*60}")

    state = result['investor_state']
    if state == "positive":
        print("🎉 Great! The person appears engaged and positive.")
        print("   Coaching: Continue with your current approach, move toward close.")
    elif state == "receptive":
        print("👂 Good! The person is open and interested.")
        print("   Coaching: Share more details, build on this momentum.")
    elif state == "evaluative":
        print("🤔 The person is thinking and analyzing.")
        print("   Coaching: Give them time, ask if they have questions.")
    elif state == "skeptical":
        print("⚠️  The person seems doubtful or concerned.")
        print("   Coaching: Address concerns directly, provide evidence.")
    else:
        print("😐 Neutral expression detected.")

    print(f"\n{'='*60}\n")


async def test_language_emotion(text: str):
    """Test emotional language analysis"""
    print(f"\n{'='*60}")
    print(f"Testing Language Emotion Analysis")
    print(f"{'='*60}")
    print(f"Text: \"{text}\"")

    # Connect to Hume AI
    print("\n🔌 Connecting to Hume AI...")
    client = HumeClient()

    # Language analysis doesn't need connect() - it creates its own connection
    print("✅ Ready")

    # Analyze text
    print("\n🧠 Analyzing emotional language...")
    result = await client.analyze_text(text)

    # Display results
    if not result or not result.get('predictions'):
        print("❌ No language analysis results")
        return

    print(f"\n{'='*60}")
    print("✅ RESULTS")
    print(f"{'='*60}")

    predictions = result['predictions']
    print(f"\n📊 Analyzed {len(predictions)} word(s)/phrase(s):\n")

    for pred in predictions:
        print(f"  \"{pred['text']}\"")
        print(f"    → {pred['primary_emotion']} ({pred['confidence']:.1%})")

        # Show top 3 emotions for this word
        top_3 = sorted(pred['emotions'].items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"    Top emotions: {', '.join([f'{e[0]} ({e[1]:.1%})' for e in top_3])}")
        print()

    print(f"{'='*60}\n")


async def capture_from_webcam():
    """Capture a frame from webcam and analyze it"""
    print(f"\n{'='*60}")
    print(f"Webcam Capture Test")
    print(f"{'='*60}")

    try:
        import cv2
    except ImportError:
        print("❌ Error: opencv-python not installed")
        print("\nInstall it with: pip install opencv-python")
        return

    print("📸 Opening webcam...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return

    print("✅ Webcam opened")
    print("\n👀 Press SPACE to capture, ESC to cancel")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error reading frame")
            break

        # Display frame
        cv2.imshow('Webcam - Press SPACE to capture, ESC to cancel', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            print("❌ Cancelled")
            break
        elif key == 32:  # SPACE
            print("\n📸 Captured!")

            # Save temporary image
            temp_path = "/tmp/hume_test_capture.jpg"
            cv2.imwrite(temp_path, frame)

            cap.release()
            cv2.destroyAllWindows()

            # Analyze the captured image
            await test_facial_emotion(temp_path)
            return

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Test Hume AI with photos, webcam, or text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_with_photo.py selfie.jpg              # Test with image
  python test_with_photo.py --webcam                # Capture from webcam
  python test_with_photo.py --text "I'm excited!"   # Test language
        """
    )

    parser.add_argument('image', nargs='?', help='Path to image file')
    parser.add_argument('--webcam', action='store_true', help='Capture from webcam')
    parser.add_argument('--text', type=str, help='Text to analyze for emotions')

    args = parser.parse_args()

    # Show banner
    print("\n" + "="*60)
    print("🤖 Hume AI Test Script - BeneAI")
    print("="*60)

    # Determine what to test
    if args.text:
        asyncio.run(test_language_emotion(args.text))
    elif args.webcam:
        asyncio.run(capture_from_webcam())
    elif args.image:
        asyncio.run(test_facial_emotion(args.image))
    else:
        parser.print_help()
        print("\n💡 Tip: Run with an image file path to get started!")
        print("Example: python test_with_photo.py photo.jpg\n")


if __name__ == "__main__":
    main()
