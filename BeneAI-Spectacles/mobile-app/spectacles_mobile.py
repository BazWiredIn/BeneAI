#!/usr/bin/env python3
"""
BeneAI Spectacles Mobile Companion App
Handles video processing and communicates with Spectacles via BLE
"""

import cv2
import asyncio
import base64
import json
import time
import websockets
import requests
from datetime import datetime
import sys
import os

# Add backend path to import BeneAI modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.hume_client import get_hume_client
from app.config import settings

class SpectaclesMobileApp:
    def __init__(self):
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Could not open camera")
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Hume AI client
        self.hume_client = None
        self.backend_connected = False
        
        # Spectacles BLE connection (simulated)
        self.spectacles_connected = False
        self.spectacles_device_id = None
        
        # Processing state
        self.is_processing = False
        self.last_analysis = 0
        self.analysis_interval = 3.0  # Analyze every 3 seconds
        
        # Current emotion data
        self.current_emotion_data = None
        
    async def initialize_hume(self):
        """Initialize Hume AI client"""
        try:
            print("Initializing Hume AI client...")
            self.hume_client = await get_hume_client()
            if self.hume_client:
                print("✅ Hume AI client initialized")
                return True
            else:
                print("❌ Hume AI client failed to initialize")
                return False
        except Exception as e:
            print(f"❌ Error initializing Hume AI: {e}")
            return False
    
    async def connect_to_backend(self):
        """Connect to BeneAI backend for coaching advice"""
        try:
            print("Connecting to BeneAI backend...")
            response = requests.get("http://localhost:8000/", timeout=5)
            if response.status_code == 200:
                self.backend_connected = True
                print("✅ Connected to BeneAI backend")
                return True
            else:
                print(f"❌ Backend connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend connection error: {e}")
            return False
    
    def connect_to_spectacles(self):
        """Simulate BLE connection to Spectacles"""
        print("Connecting to Spectacles via BLE...")
        time.sleep(2)  # Simulate connection time
        self.spectacles_connected = True
        self.spectacles_device_id = "spectacles-001"
        print(f"✅ Connected to Spectacles: {self.spectacles_device_id}")
        return True
    
    def frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 for Hume AI"""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    
    async def analyze_with_hume(self, frame):
        """Analyze frame with Hume AI"""
        if not self.hume_client:
            return None
        
        try:
            # Convert frame to base64
            image_data = self.frame_to_base64(frame)
            
            # Analyze with Hume AI
            result = await self.hume_client.analyze_face(image_data)
            
            if result:
                emotion_data = {
                    'dominantState': result.get('investor_state', 'neutral'),
                    'confidence': result.get('confidence', 0.5),
                    'primaryEmotion': result.get('primary_emotion', 'neutral'),
                    'timestamp': time.time()
                }
                
                print(f"🎭 Hume Analysis: {emotion_data['dominantState']} ({emotion_data['primaryEmotion']}: {emotion_data['confidence']:.2f})")
                return emotion_data
            
        except Exception as e:
            print(f"Error analyzing with Hume AI: {e}")
        
        return None
    
    async def get_coaching_advice(self, emotion_data):
        """Get coaching advice from BeneAI backend"""
        if not self.backend_connected:
            return self.get_default_advice(emotion_data['dominantState'])
        
        try:
            # Send emotion data to backend for GPT-4 coaching
            payload = {
                "emotion_data": emotion_data,
                "timestamp": time.time()
            }
            
            response = requests.post(
                "http://localhost:8000/api/coaching", 
                json=payload, 
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                advice = data.get('advice', self.get_default_advice(emotion_data['dominantState']))
                print(f"💡 Coaching: {advice}")
                return advice
                
        except Exception as e:
            print(f"Error getting coaching advice: {e}")
        
        return self.get_default_advice(emotion_data['dominantState'])
    
    def get_default_advice(self, state):
        """Get default coaching advice based on state"""
        advice_map = {
            'skeptical': "Address concerns with concrete data and examples",
            'evaluative': "They're analyzing - provide more detailed information",
            'receptive': "Great! They're engaged - keep building momentum",
            'positive': "Excellent! They're enthusiastic - close the deal",
            'neutral': "Create more emotional connection and engagement"
        }
        return advice_map.get(state, "Continue monitoring the conversation")
    
    def send_to_spectacles(self, data):
        """Send data to Spectacles via BLE (simulated)"""
        if self.spectacles_connected:
            print(f"📡 Sending to Spectacles: {data['type']}")
            # In real implementation, this would send via BLE
            return True
        return False
    
    async def process_video_loop(self):
        """Main video processing loop"""
        print("Starting video processing...")
        self.is_processing = True
        
        while self.is_processing:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            current_time = time.time()
            
            # Analyze with Hume AI every analysis_interval seconds
            if current_time - self.last_analysis >= self.analysis_interval:
                emotion_data = await self.analyze_with_hume(frame)
                
                if emotion_data:
                    self.current_emotion_data = emotion_data
                    
                    # Get coaching advice
                    advice = await self.get_coaching_advice(emotion_data)
                    
                    # Send to Spectacles
                    self.send_to_spectacles({
                        'type': 'emotion_update',
                        'emotionData': emotion_data,
                        'advice': advice,
                        'timestamp': current_time
                    })
                
                self.last_analysis = current_time
            
            # Control frame rate
            await asyncio.sleep(0.1)
        
        print("Video processing stopped")
    
    async def run(self):
        """Main application loop"""
        print("BeneAI Spectacles Mobile App")
        print("=" * 40)
        
        # Initialize Hume AI
        if not await self.initialize_hume():
            print("Failed to initialize Hume AI. Exiting.")
            return
        
        # Connect to backend
        await self.connect_to_backend()
        
        # Connect to Spectacles
        self.connect_to_spectacles()
        
        # Start video processing
        print("Starting video processing...")
        await self.process_video_loop()
    
    def stop(self):
        """Stop the application"""
        self.is_processing = False
        self.cap.release()
        print("Mobile app stopped")

async def main():
    """Main function"""
    try:
        app = SpectaclesMobileApp()
        await app.run()
    except KeyboardInterrupt:
        print("\nStopping mobile app...")
        app.stop()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())


