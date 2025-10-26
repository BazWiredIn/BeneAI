#!/usr/bin/env python3
"""
Quick test for BeneAI Spectacles system
"""

import requests
import time

def test_mobile_app():
    """Test if mobile app is running"""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Mobile App: Running")
            return True
        else:
            print(f"❌ Mobile App: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Mobile App: {e}")
        return False

def test_backend():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend: Running")
            return True
        else:
            print(f"❌ Backend: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend: {e}")
        return False

def main():
    print("BeneAI Spectacles Quick Test")
    print("=" * 30)
    
    mobile_ok = test_mobile_app()
    backend_ok = test_backend()
    
    print("\nResults:")
    if mobile_ok and backend_ok:
        print("🎉 System is running! You can now:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Click 'Connect Spectacles' and 'Connect Backend'")
        print("3. Click 'Start Processing' to begin emotion detection")
        print("4. Watch the real-time emotion display and coaching advice")
    else:
        print("⚠️  Some services are not running. Please check the logs above.")

if __name__ == "__main__":
    main()


