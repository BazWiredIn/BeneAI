#!/usr/bin/env python3
"""
BeneAI Spectacles System Test
Quick test to verify all services are running
"""

import requests
import time
import json

def test_backend():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend: Running on port 8000")
            return True
        else:
            print(f"❌ Backend: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend: {e}")
        return False

def test_mobile_app():
    """Test if mobile app is running"""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Mobile App: Running on port 5000")
            print(f"   Status: {data}")
            return True
        else:
            print(f"❌ Mobile App: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Mobile App: {e}")
        return False

def test_adapter():
    """Test if adapter is running"""
    try:
        response = requests.get("http://localhost:9000/", timeout=5)
        if response.status_code == 200:
            print("✅ Adapter: Running on port 9000")
            return True
        else:
            print(f"❌ Adapter: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Adapter: {e}")
        return False

def main():
    print("BeneAI Spectacles System Test")
    print("=" * 40)
    
    backend_ok = test_backend()
    mobile_ok = test_mobile_app()
    adapter_ok = test_adapter()
    
    print("\n" + "=" * 40)
    print("SUMMARY:")
    print(f"Backend:  {'✅ Running' if backend_ok else '❌ Not Running'}")
    print(f"Mobile:   {'✅ Running' if mobile_ok else '❌ Not Running'}")
    print(f"Adapter:  {'✅ Running' if adapter_ok else '❌ Not Running'}")
    
    if backend_ok and mobile_ok and adapter_ok:
        print("\n🎉 ALL SERVICES RUNNING!")
        print("You can now access:")
        print("- Mobile App: http://localhost:5000")
        print("- Backend API: http://localhost:8000")
        print("- Adapter: ws://localhost:9000")
    else:
        print("\n⚠️  Some services are not running.")
        print("Please start the missing services using the commands above.")

if __name__ == "__main__":
    main()


