#!/usr/bin/env python3
"""
BeneAI Spectacles Display - Simple UI
Minimal overlay display for Spectacles recommendations
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import random
from datetime import datetime

class SpectaclesDisplay:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Emotion states
        self.emotion_states = {
            'interested': {'emoji': '😊', 'color': (0, 255, 0), 'name': 'Interested'},
            'skeptical': {'emoji': '🤔', 'color': (0, 165, 255), 'name': 'Skeptical'},
            'concerned': {'emoji': '😟', 'color': (0, 0, 255), 'name': 'Concerned'},
            'confused': {'emoji': '😕', 'color': (0, 255, 255), 'name': 'Confused'},
            'bored': {'emoji': '😴', 'color': (128, 128, 128), 'name': 'Bored'},
            'neutral': {'emoji': '😐', 'color': (200, 200, 200), 'name': 'Neutral'}
        }
        
        # Coaching recommendations
        self.recommendations = {
            'interested': "Great! Keep building momentum with specific examples",
            'skeptical': "Address concerns directly with concrete data",
            'concerned': "Show empathy and provide reassurance",
            'confused': "Simplify explanation and use visual aids",
            'bored': "Increase energy and ask engaging questions",
            'neutral': "Create more emotional connection"
        }
        
        # Current state
        self.current_emotion = 'neutral'
        self.current_confidence = 0.5
        self.last_update = time.time()
        self.recommendation_text = "Starting analysis..."
        
    def detect_emotion(self, frame):
        """Simulate emotion detection"""
        # In real implementation, this would use Hume AI
        # For now, we'll simulate realistic emotion changes
        current_time = time.time()
        
        # Change emotion every 3-5 seconds
        if current_time - self.last_update > random.uniform(3, 5):
            self.current_emotion = random.choice(list(self.emotion_states.keys()))
            self.current_confidence = random.uniform(0.6, 0.95)
            self.recommendation_text = self.recommendations[self.current_emotion]
            self.last_update = current_time
        
        return {
            'emotion': self.current_emotion,
            'confidence': self.current_confidence,
            'recommendation': self.recommendation_text
        }
    
    def draw_spectacles_overlay(self, frame, emotion_data):
        """Draw Spectacles-style overlay on frame"""
        height, width = frame.shape[:2]
        
        # Get emotion info
        emotion = emotion_data['emotion']
        confidence = emotion_data['confidence']
        recommendation = emotion_data['recommendation']
        
        state_info = self.emotion_states[emotion]
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        
        # Draw main emotion indicator (top-right corner)
        emotion_x = width - 200
        emotion_y = 50
        
        # Background circle for emotion
        cv2.circle(overlay, (emotion_x, emotion_y), 60, (0, 0, 0), -1)
        cv2.circle(overlay, (emotion_x, emotion_y), 60, state_info['color'], 3)
        
        # Emotion emoji (simulated with text)
        cv2.putText(overlay, state_info['emoji'], 
                   (emotion_x - 20, emotion_y + 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, state_info['color'], 2)
        
        # Confidence bar
        bar_x = emotion_x - 50
        bar_y = emotion_y + 40
        bar_width = 100
        bar_height = 8
        
        # Background bar
        cv2.rectangle(overlay, (bar_x, bar_y), 
                     (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Confidence fill
        fill_width = int(bar_width * confidence)
        cv2.rectangle(overlay, (bar_x, bar_y), 
                     (bar_x + fill_width, bar_y + bar_height), state_info['color'], -1)
        
        # Confidence percentage
        cv2.putText(overlay, f"{int(confidence * 100)}%", 
                   (bar_x + bar_width + 10, bar_y + bar_height + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, state_info['color'], 1)
        
        # Recommendation text (bottom of screen)
        rec_y = height - 100
        rec_x = 20
        
        # Background for text
        text_size = cv2.getTextSize(recommendation, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(overlay, (rec_x - 10, rec_y - 25), 
                     (rec_x + text_size[0] + 10, rec_y + 10), (0, 0, 0), -1)
        cv2.rectangle(overlay, (rec_x - 10, rec_y - 25), 
                     (rec_x + text_size[0] + 10, rec_y + 10), state_info['color'], 2)
        
        # Recommendation text
        cv2.putText(overlay, recommendation, (rec_x, rec_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Blend overlay with original frame
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
    
    def run(self):
        """Main display loop"""
        print("BeneAI Spectacles Display")
        print("=" * 30)
        print("Starting camera...")
        print("Press 'q' to quit, 's' to save screenshot")
        
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        # Set camera resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            
            # Detect emotion
            emotion_data = self.detect_emotion(frame)
            
            # Draw Spectacles overlay
            frame = self.draw_spectacles_overlay(frame, emotion_data)
            
            # Add FPS counter
            frame_count += 1
            if frame_count % 30 == 0:
                fps = frame_count / (time.time() - start_time)
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('BeneAI Spectacles Display', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"spectacles_screenshot_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Screenshot saved: {filename}")
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("Display closed")

def main():
    """Main function"""
    display = SpectaclesDisplay()
    display.run()

if __name__ == "__main__":
    main()


