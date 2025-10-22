"""
Test script for Hume AI integration
Tests facial expression, speech prosody, and emotional language analysis
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
from app.config import settings


async def test_hume_connection():
    """Test basic Hume AI connection"""
    print("\n=== Testing Hume AI Connection ===")

    if not settings.hume_api_key:
        print("❌ ERROR: HUME_API_KEY not set in environment")
        print("   Please set HUME_API_KEY in backend/.env file")
        return False

    client = HumeClient()
    connected = await client.connect()

    if connected:
        print("✅ Successfully connected to Hume AI WebSocket")
        print(f"   - Facial Expression: {'Enabled' if client.enable_face else 'Disabled'}")
        print(f"   - Speech Prosody: {'Enabled' if client.enable_prosody else 'Disabled'}")
        print(f"   - Emotional Language: {'Enabled' if client.enable_language else 'Disabled'}")
        await client.disconnect()
        return True
    else:
        print("❌ Failed to connect to Hume AI")
        return False


async def test_facial_expression():
    """Test facial expression analysis"""
    print("\n=== Testing Facial Expression Analysis ===")

    if not settings.hume_enable_face:
        print("⚠️  Facial expression analysis is disabled in config")
        return

    # Sample test: Create a small test image (1x1 pixel red PNG)
    # This is just for testing the API flow - won't detect actual emotions
    test_image_base64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    )

    client = HumeClient()
    await client.connect()

    print("Analyzing test image...")
    result = await client.analyze_face(test_image_base64)

    if result:
        print("✅ Facial analysis successful")
        print(f"   - Primary emotion: {result['primary_emotion']}")
        print(f"   - Confidence: {result['confidence']:.3f}")
        print(f"   - Investor state: {result['investor_state']}")
        print(f"   - Top 5 emotions:")
        for emotion in result.get('top_emotions', [])[:5]:
            print(f"     • {emotion['name']}: {emotion['score']:.3f}")
    else:
        print("⚠️  No face detected (expected for test image)")

    await client.disconnect()


async def test_emotional_language():
    """Test emotional language analysis"""
    print("\n=== Testing Emotional Language Analysis ===")

    if not settings.hume_enable_language:
        print("⚠️  Language analysis is disabled in config")
        return

    test_texts = [
        "I'm really excited about this opportunity!",
        "This is concerning and makes me worried.",
        "The proposal looks interesting but I have some questions."
    ]

    client = HumeClient()
    await client.connect()

    for text in test_texts:
        print(f"\nAnalyzing: \"{text}\"")
        result = await client.analyze_text(text)

        if result and result.get("predictions"):
            print(f"✅ Language analysis successful ({len(result['predictions'])} words)")
            for pred in result["predictions"][:3]:  # Show first 3 words
                print(f"   - \"{pred['text']}\": {pred['primary_emotion']} ({pred['confidence']:.3f})")
        else:
            print("❌ Language analysis failed")

    await client.disconnect()


async def test_investor_state_mapping():
    """Test investor state mapping logic"""
    print("\n=== Testing Investor State Mapping ===")

    client = HumeClient()

    # Test different emotion scenarios
    test_cases = [
        {
            "name": "Skeptical scenario",
            "emotions": {
                "Doubt": 0.7,
                "Contempt": 0.5,
                "Disapproval": 0.4,
                "Interest": 0.1
            }
        },
        {
            "name": "Positive scenario",
            "emotions": {
                "Admiration": 0.8,
                "Joy": 0.6,
                "Excitement": 0.7,
                "Interest": 0.5
            }
        },
        {
            "name": "Evaluative scenario",
            "emotions": {
                "Concentration": 0.7,
                "Contemplation": 0.6,
                "Interest": 0.4,
                "Confusion": 0.3
            }
        },
        {
            "name": "Receptive scenario",
            "emotions": {
                "Interest": 0.6,
                "Curiosity": 0.5,
                "Aesthetic Appreciation": 0.4,
                "Calmness": 0.3
            }
        }
    ]

    for test_case in test_cases:
        state = client._map_to_investor_state(test_case["emotions"])
        print(f"✅ {test_case['name']}: {state}")


async def main():
    """Run all tests"""
    print("╔════════════════════════════════════════════════╗")
    print("║      Hume AI Integration Test Suite           ║")
    print("╚════════════════════════════════════════════════╝")

    # Test 1: Connection
    connection_ok = await test_hume_connection()

    if not connection_ok:
        print("\n❌ Connection test failed. Stopping tests.")
        print("\nPlease ensure:")
        print("  1. HUME_API_KEY is set in backend/.env")
        print("  2. You have an active internet connection")
        print("  3. Your Hume API key is valid")
        return

    # Test 2: Investor state mapping (offline test)
    await test_investor_state_mapping()

    # Test 3: Emotional language (if enabled)
    if settings.hume_enable_language:
        await test_emotional_language()

    # Test 4: Facial expression (if enabled)
    if settings.hume_enable_face:
        await test_facial_expression()

    print("\n╔════════════════════════════════════════════════╗")
    print("║           Test Suite Complete                  ║")
    print("╚════════════════════════════════════════════════╝")
    print("\nNext steps:")
    print("  1. Update your backend/.env with HUME_API_KEY")
    print("  2. Set HUME_USE_PRIMARY=true to use Hume as primary service")
    print("  3. Restart the backend server: uvicorn main:app --reload")
    print("  4. Test with the Chrome extension")


if __name__ == "__main__":
    asyncio.run(main())
