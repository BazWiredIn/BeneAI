#!/usr/bin/env python3
"""
BeneAI Spectacles Mobile App
Main Flask application for processing video and communicating with Spectacles
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import asyncio
import websockets
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Global variables
is_processing = False
current_emotion = None
websocket_connection = None
spectacles_connected = False

class EmotionProcessor:
    """Processes video frames and detects emotions"""
    
    def __init__(self):
        self.emotion_states = {
            'interested': {'emoji': '😊', 'color': [0, 1, 0], 'name': 'Interested'},
            'skeptical': {'emoji': '🤔', 'color': [1, 0.5, 0], 'name': 'Skeptical'},
            'concerned': {'emoji': '😟', 'color': [1, 0, 0], 'name': 'Concerned'},
            'confused': {'emoji': '😕', 'color': [1, 1, 0], 'name': 'Confused'},
            'bored': {'emoji': '😴', 'color': [0.5, 0.5, 0.5], 'name': 'Bored'},
            'neutral': {'emoji': '😐', 'color': [0.8, 0.8, 0.8], 'name': 'Neutral'}
        }
    
    def process_frame(self, frame):
        """Process a single video frame for emotion detection"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = face_mesh.process(rgb_frame)
            
            if results.multi_face_landmarks:
                # Simulate emotion detection (in real implementation, use Hume AI)
                emotion_data = self.simulate_emotion_detection()
                return emotion_data
            
            return None
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return None
    
    def simulate_emotion_detection(self):
        """Simulate emotion detection for demo purposes"""
        import random
        
        states = list(self.emotion_states.keys())
        dominant_state = random.choice(states)
        confidence = 0.5 + random.random() * 0.5
        
        return {
            'dominantState': dominant_state,
            'confidence': confidence,
            'timestamp': time.time(),
            'state': self.emotion_states[dominant_state]
        }

class SpectaclesBLE:
    """Handles BLE communication with Spectacles"""
    
    def __init__(self):
        self.connected = False
        self.device_id = None
    
    def connect(self):
        """Simulate BLE connection to Spectacles"""
        print("Connecting to Spectacles via BLE...")
        time.sleep(2)  # Simulate connection time
        self.connected = True
        self.device_id = "spectacles-001"
        print(f"Connected to Spectacles: {self.device_id}")
        return True
    
    def send_emotion_data(self, emotion_data):
        """Send emotion data to Spectacles"""
        if self.connected:
            print(f"Sending emotion data to Spectacles: {emotion_data['dominantState']}")
            # In real implementation, send via BLE
            return True
        return False
    
    def send_coaching_advice(self, advice):
        """Send coaching advice to Spectacles"""
        if self.connected:
            print(f"Sending coaching advice to Spectacles: {advice}")
            # In real implementation, send via BLE
            return True
        return False

class WebSocketClient:
    """Handles WebSocket communication with backend"""
    
    def __init__(self, url="ws://localhost:8000/ws"):
        self.url = url
        self.connected = False
        self.websocket = None
    
    async def connect(self):
        """Connect to backend WebSocket"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            print(f"Connected to backend WebSocket: {self.url}")
            return True
        except Exception as e:
            print(f"Failed to connect to backend: {e}")
            return False
    
    async def send_emotion_data(self, emotion_data):
        """Send emotion data to backend"""
        if self.connected and self.websocket:
            try:
                message = {
                    "type": "emotion_data",
                    "data": emotion_data,
                    "timestamp": time.time()
                }
                await self.websocket.send(json.dumps(message))
                print(f"Sent emotion data to backend: {emotion_data['dominantState']}")
            except Exception as e:
                print(f"Error sending emotion data: {e}")
    
    async def receive_coaching_advice(self):
        """Receive coaching advice from backend"""
        if self.connected and self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                if data.get("type") == "coaching_advice":
                    return data.get("advice", "No advice available")
            except Exception as e:
                print(f"Error receiving coaching advice: {e}")
        return None

# Initialize components
emotion_processor = EmotionProcessor()
spectacles_ble = SpectaclesBLE()
websocket_client = WebSocketClient()

def video_processing_loop():
    """Main video processing loop"""
    global is_processing, current_emotion
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    print("Starting video processing...")
    is_processing = True
    
    while is_processing:
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Process frame for emotions
        emotion_data = emotion_processor.process_frame(frame)
        
        if emotion_data:
            current_emotion = emotion_data
            
            # Send to Spectacles
            spectacles_ble.send_emotion_data(emotion_data)
            
            # Send to backend
            asyncio.run(websocket_client.send_emotion_data(emotion_data))
            
            print(f"Processed emotion: {emotion_data['dominantState']} "
                  f"(confidence: {emotion_data['confidence']:.2f})")
        
        # Control frame rate
        time.sleep(0.1)  # ~10 FPS
    
    cap.release()
    print("Video processing stopped")

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    return jsonify({
        'processing': is_processing,
        'current_emotion': current_emotion,
        'spectacles_connected': spectacles_ble.connected,
        'backend_connected': websocket_client.connected
    })

@app.route('/api/start_processing', methods=['POST'])
def start_processing():
    """Start video processing"""
    global is_processing
    
    if not is_processing:
        # Connect to Spectacles
        spectacles_ble.connect()
        
        # Start video processing in separate thread
        thread = threading.Thread(target=video_processing_loop)
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'message': 'Video processing started'})
    else:
        return jsonify({'status': 'already_running', 'message': 'Processing already running'})

@app.route('/api/stop_processing', methods=['POST'])
def stop_processing():
    """Stop video processing"""
    global is_processing
    
    is_processing = False
    return jsonify({'status': 'stopped', 'message': 'Video processing stopped'})

@app.route('/api/connect_spectacles', methods=['POST'])
def connect_spectacles():
    """Connect to Spectacles"""
    success = spectacles_ble.connect()
    return jsonify({
        'status': 'connected' if success else 'failed',
        'message': 'Spectacles connected' if success else 'Failed to connect to Spectacles'
    })

@app.route('/api/connect_backend', methods=['POST'])
def connect_backend():
    """Connect to backend"""
    success = asyncio.run(websocket_client.connect())
    return jsonify({
        'status': 'connected' if success else 'failed',
        'message': 'Backend connected' if success else 'Failed to connect to backend'
    })

if __name__ == '__main__':
    print("BeneAI Spectacles Mobile App")
    print("=" * 40)
    print("Starting Flask server...")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)


