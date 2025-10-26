#!/usr/bin/env python3
"""
BeneAI Spectacles System Test Script
Tests the complete Spectacles integration system
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime

class SpectaclesSystemTester:
    """Test the complete BeneAI Spectacles system"""
    
    def __init__(self):
        self.mobile_app_url = "http://localhost:5000"
        self.backend_url = "ws://localhost:8000/ws"
        self.adapter_url = "ws://localhost:9000"
        self.test_results = {}
    
    async def test_mobile_app(self):
        """Test mobile app connectivity"""
        print("Testing Mobile App...")
        try:
            response = requests.get(f"{self.mobile_app_url}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Mobile App: {data}")
                self.test_results['mobile_app'] = True
                return True
            else:
                print(f"❌ Mobile App: HTTP {response.status_code}")
                self.test_results['mobile_app'] = False
                return False
        except Exception as e:
            print(f"❌ Mobile App: {e}")
            self.test_results['mobile_app'] = False
            return False
    
    async def test_backend_websocket(self):
        """Test backend WebSocket connection"""
        print("Testing Backend WebSocket...")
        try:
            async with websockets.connect(self.backend_url) as websocket:
                # Send test message
                test_message = {
                    "type": "test",
                    "message": "Testing backend connection",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"✅ Backend WebSocket: {data}")
                self.test_results['backend_websocket'] = True
                return True
        except Exception as e:
            print(f"❌ Backend WebSocket: {e}")
            self.test_results['backend_websocket'] = False
            return False
    
    async def test_adapter_websocket(self):
        """Test adapter WebSocket connection"""
        print("Testing Adapter WebSocket...")
        try:
            # Test mobile endpoint
            async with websockets.connect(f"{self.adapter_url}/mobile") as websocket:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"✅ Adapter Mobile: {data}")
                
                # Test spectacles endpoint
                async with websockets.connect(f"{self.adapter_url}/spectacles") as websocket2:
                    response2 = await asyncio.wait_for(websocket2.recv(), timeout=5)
                    data2 = json.loads(response2)
                    print(f"✅ Adapter Spectacles: {data2}")
                
                self.test_results['adapter_websocket'] = True
                return True
        except Exception as e:
            print(f"❌ Adapter WebSocket: {e}")
            self.test_results['adapter_websocket'] = False
            return False
    
    async def test_emotion_processing(self):
        """Test emotion processing pipeline"""
        print("Testing Emotion Processing...")
        try:
            # Start processing
            response = requests.post(f"{self.mobile_app_url}/api/start_processing", timeout=5)
            if response.status_code == 200:
                print("✅ Emotion Processing: Started")
                
                # Wait a bit for processing
                await asyncio.sleep(3)
                
                # Check status
                status_response = requests.get(f"{self.mobile_app_url}/api/status", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('processing'):
                        print("✅ Emotion Processing: Running")
                        self.test_results['emotion_processing'] = True
                        return True
                    else:
                        print("❌ Emotion Processing: Not running")
                        self.test_results['emotion_processing'] = False
                        return False
                else:
                    print("❌ Emotion Processing: Status check failed")
                    self.test_results['emotion_processing'] = False
                    return False
            else:
                print(f"❌ Emotion Processing: Start failed - {response.status_code}")
                self.test_results['emotion_processing'] = False
                return False
        except Exception as e:
            print(f"❌ Emotion Processing: {e}")
            self.test_results['emotion_processing'] = False
            return False
    
    async def test_spectacles_simulation(self):
        """Test Spectacles simulation"""
        print("Testing Spectacles Simulation...")
        try:
            # Connect to adapter as Spectacles
            async with websockets.connect(f"{self.adapter_url}/spectacles") as websocket:
                # Send emotion data
                emotion_data = {
                    "type": "emotion_data",
                    "emotionData": {
                        "dominantState": "interested",
                        "confidence": 0.85,
                        "timestamp": time.time()
                    }
                }
                await websocket.send(json.dumps(emotion_data))
                
                # Send gesture input
                gesture_data = {
                    "type": "gesture_input",
                    "gesture": "tap",
                    "timestamp": time.time()
                }
                await websocket.send(json.dumps(gesture_data))
                
                print("✅ Spectacles Simulation: Data sent")
                self.test_results['spectacles_simulation'] = True
                return True
        except Exception as e:
            print(f"❌ Spectacles Simulation: {e}")
            self.test_results['spectacles_simulation'] = False
            return False
    
    async def test_mobile_simulation(self):
        """Test mobile app simulation"""
        print("Testing Mobile App Simulation...")
        try:
            # Connect to adapter as mobile app
            async with websockets.connect(f"{self.adapter_url}/mobile") as websocket:
                # Send emotion data
                emotion_data = {
                    "type": "emotion_data",
                    "data": {
                        "dominantState": "skeptical",
                        "confidence": 0.72,
                        "timestamp": time.time()
                    }
                }
                await websocket.send(json.dumps(emotion_data))
                
                # Wait for coaching advice
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("type") == "coaching_advice":
                    print(f"✅ Mobile Simulation: Received advice - {data.get('advice')}")
                    self.test_results['mobile_simulation'] = True
                    return True
                else:
                    print(f"❌ Mobile Simulation: Unexpected response - {data}")
                    self.test_results['mobile_simulation'] = False
                    return False
        except Exception as e:
            print(f"❌ Mobile Simulation: {e}")
            self.test_results['mobile_simulation'] = False
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        print("BeneAI Spectacles System Test")
        print("=" * 50)
        print(f"Test started at: {datetime.now()}")
        print()
        
        # Test individual components
        await self.test_mobile_app()
        await self.test_backend_websocket()
        await self.test_adapter_websocket()
        await self.test_emotion_processing()
        await self.test_spectacles_simulation()
        await self.test_mobile_simulation()
        
        # Print results
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:25} {status}")
        
        print("-" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is ready for Spectacles deployment.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please check the issues above.")
        
        return passed_tests == total_tests

async def main():
    """Main test function"""
    tester = SpectaclesSystemTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    print("Starting BeneAI Spectacles System Test...")
    success = asyncio.run(main())
    exit(0 if success else 1)


