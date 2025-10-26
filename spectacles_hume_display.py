#!/usr/bin/env python3
"""
BeneAI Spectacles Display - Hume AI Integration
Adapts existing BeneAI web app for Spectacles MVP with real Hume AI emotion detection
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
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.hume_client import get_hume_client
from app.config import settings

class SpectaclesHumeDisplay:
    def __init__(self):
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise Exception("Could not open camera")
        
        # Set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Spectacles UI state
        self.current_emotion = 'neutral'
        self.current_confidence = 0.5
        self.current_state = 'neutral'
        self.recommendation = "Starting analysis..."
        self.last_analysis = 0
        self.analysis_interval = 2.0  # Analyze every 2 seconds
        
        # Hume AI client
        self.hume_client = None
        self.backend_connected = False
        
        # Spectacles UI colors and states
        self.state_colors = {
            'skeptical': (0, 100, 255),      # Orange
            'evaluative': (255, 255, 0),     # Yellow  
            'receptive': (0, 255, 0),        # Green
            'positive': (0, 255, 255),       # Cyan
            'neutral': (200, 200, 200)       # Gray
        }
        
        self.state_emojis = {
            'skeptical': '🤔',
            'evaluative': '🧠', 
            'receptive': '😊',
            'positive': '🎉',
            'neutral': '😐'
        }
        
        # Coaching recommendations
        self.recommendations = {
            'skeptical': "Address concerns with concrete data and examples",
            'evaluative': "They're analyzing - provide more detailed information",
            'receptive': "Great! They're engaged - keep building momentum",
            'positive': "Excellent! They're enthusiastic - close the deal",
            'neutral': "Create more emotional connection and engagement"
        }
        
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
            # Test backend connection
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
                self.current_emotion = result.get('primary_emotion', 'neutral')
                self.current_confidence = result.get('confidence', 0.5)
                self.current_state = result.get('investor_state', 'neutral')
                
                # Get recommendation
                self.recommendation = self.recommendations.get(self.current_state, "Continue monitoring")
                
                print(f"🎭 Hume Analysis: {self.current_state} ({self.current_emotion}: {self.current_confidence:.2f})")
                return result
            
        except Exception as e:
            print(f"Error analyzing with Hume AI: {e}")
        
        return None
    
    async def get_coaching_advice(self, emotion_data):
        """Get coaching advice from BeneAI backend"""
        if not self.backend_connected:
            return self.recommendation
        
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
                advice = data.get('advice', self.recommendation)
                print(f"💡 Coaching: {advice}")
                return advice
                
        except Exception as e:
            print(f"Error getting coaching advice: {e}")
        
        return self.recommendation
    
    def draw_spectacles_ui(self, frame):
        """Draw Spectacles-style UI overlay"""
        height, width = frame.shape[:2]
        
        # Get current state info
        color = self.state_colors.get(self.current_state, (200, 200, 200))
        emoji = self.state_emojis.get(self.current_state, '😐')
        
        # Create overlay
        overlay = frame.copy()
        
        # Main emotion indicator (top-right corner)
        indicator_x = width - 150
        indicator_y = 50
        
        # Background circle
        cv2.circle(overlay, (indicator_x, indicator_y), 50, (0, 0, 0), -1)
        cv2.circle(overlay, (indicator_x, indicator_y), 50, color, 3)
        
        # State emoji (simulated with text)
        cv2.putText(overlay, emoji, (indicator_x - 15, indicator_y + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        
        # Confidence bar
        bar_x = indicator_x - 40
        bar_y = indicator_y + 35
        bar_width = 80
        bar_height = 6
        
        # Background bar
        cv2.rectangle(overlay, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Confidence fill
        fill_width = int(bar_width * self.current_confidence)
        cv2.rectangle(overlay, (bar_x, bar_y), 
                     (bar_x + fill_width, bar_y + bar_height), color, -1)
        
        # Confidence percentage
        cv2.putText(overlay, f"{int(self.current_confidence * 100)}%", 
                   (bar_x + bar_width + 5, bar_y + bar_height + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # State name
        cv2.putText(overlay, self.current_state.upper(), 
                   (indicator_x - 30, indicator_y - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Recommendation text (bottom of screen)
        rec_y = height - 80
        rec_x = 20
        
        # Background for recommendation
        text_size = cv2.getTextSize(self.recommendation, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.rectangle(overlay, (rec_x - 5, rec_y - 20), 
                     (rec_x + text_size[0] + 5, rec_y + 5), (0, 0, 0), -1)
        cv2.rectangle(overlay, (rec_x - 5, rec_y - 20), 
                     (rec_x + text_size[0] + 5, rec_y + 5), color, 1)
        
        # Recommendation text
        cv2.putText(overlay, self.recommendation, (rec_x, rec_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Blend overlay
        alpha = 0.8
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
    
    async def run(self):
        """Main display loop"""
        print("BeneAI Spectacles - Hume AI Integration")
        print("=" * 50)
        
        # Initialize Hume AI
        if not await self.initialize_hume():
            print("❌ Failed to initialize Hume AI. Exiting.")
            return
        
        # Connect to backend
        await self.connect_to_backend()
        
        print("Starting Spectacles display...")
        print("Press 'q' to quit, 's' to save screenshot")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            current_time = time.time()
            
            # Analyze with Hume AI every analysis_interval seconds
            if current_time - self.last_analysis >= self.analysis_interval:
                emotion_data = await self.analyze_with_hume(frame)
                
                if emotion_data and self.backend_connected:
                    # Get coaching advice from backend
                    self.recommendation = await self.get_coaching_advice(emotion_data)
                
                self.last_analysis = current_time
            
            # Draw Spectacles UI
            frame = self.draw_spectacles_ui(frame)
            
            # Add FPS counter
            frame_count += 1
            if frame_count % 30 == 0:
                fps = frame_count / (time.time() - start_time)
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('BeneAI Spectacles - Hume AI', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"spectacles_hume_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        
        # Disconnect Hume AI
        if self.hume_client:
            await self.hume_client.disconnect()
        
        print("Spectacles display closed")

async def main():
    """Main function"""
    try:
        display = SpectaclesHumeDisplay()
        await display.run()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure:")
        print("1. Camera is connected")
        print("2. BeneAI backend is running on port 8000")
        print("3. Hume AI API key is configured")

if __name__ == "__main__":
    asyncio.run(main())


