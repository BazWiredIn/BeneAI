#!/usr/bin/env python3
"""
BeneAI Spectacles Backend Adapter
Adapts the existing BeneAI backend for Spectacles integration
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol

class SpectaclesAdapter:
    """Adapter for integrating Spectacles with existing BeneAI backend"""
    
    def __init__(self, backend_url: str = "ws://localhost:8000/ws"):
        self.backend_url = backend_url
        self.spectacles_clients = {}  # Store Spectacles connections
        self.mobile_clients = {}      # Store mobile app connections
        self.backend_connection = None
        self.is_running = False
    
    async def start_server(self, host: str = "localhost", port: int = 9000):
        """Start the Spectacles adapter server"""
        print(f"Starting Spectacles Adapter on {host}:{port}")
        
        async def handle_client(websocket: WebSocketServerProtocol, path: str):
            """Handle incoming client connections"""
            client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
            print(f"New client connected: {client_id}")
            
            try:
                # Determine client type based on path
                if path == "/spectacles":
                    await self.handle_spectacles_client(websocket, client_id)
                elif path == "/mobile":
                    await self.handle_mobile_client(websocket, client_id)
                else:
                    await websocket.close(code=1000, reason="Invalid path")
                    
            except websockets.exceptions.ConnectionClosed:
                print(f"Client disconnected: {client_id}")
            except Exception as e:
                print(f"Error handling client {client_id}: {e}")
            finally:
                # Clean up client connections
                if client_id in self.spectacles_clients:
                    del self.spectacles_clients[client_id]
                if client_id in self.mobile_clients:
                    del self.mobile_clients[client_id]
        
        # Start WebSocket server
        self.is_running = True
        async with websockets.serve(handle_client, host, port):
            print(f"Spectacles Adapter running on ws://{host}:{port}")
            print("Available endpoints:")
            print("  - ws://localhost:9000/spectacles (for Spectacles devices)")
            print("  - ws://localhost:9000/mobile (for mobile apps)")
            
            # Keep server running
            await asyncio.Future()
    
    async def handle_spectacles_client(self, websocket: WebSocketServerProtocol, client_id: str):
        """Handle Spectacles device connections"""
        self.spectacles_clients[client_id] = websocket
        print(f"Spectacles device connected: {client_id}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "client_type": "spectacles",
            "message": "Connected to BeneAI Spectacles Adapter"
        }))
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_spectacles_message(data, client_id)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"Spectacles device disconnected: {client_id}")
        except Exception as e:
            print(f"Error processing Spectacles message: {e}")
    
    async def handle_mobile_client(self, websocket: WebSocketServerProtocol, client_id: str):
        """Handle mobile app connections"""
        self.mobile_clients[client_id] = websocket
        print(f"Mobile app connected: {client_id}")
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connection_established",
            "client_type": "mobile",
            "message": "Connected to BeneAI Spectacles Adapter"
        }))
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.process_mobile_message(data, client_id)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"Mobile app disconnected: {client_id}")
        except Exception as e:
            print(f"Error processing mobile message: {e}")
    
    async def process_spectacles_message(self, data: Dict[str, Any], client_id: str):
        """Process messages from Spectacles devices"""
        message_type = data.get("type")
        
        if message_type == "emotion_data":
            # Forward emotion data to mobile apps
            await self.broadcast_to_mobile_clients({
                "type": "emotion_update",
                "emotionData": data.get("emotionData"),
                "source": "spectacles",
                "timestamp": time.time()
            })
            
        elif message_type == "gesture_input":
            # Handle gesture input from Spectacles
            await self.handle_gesture_input(data.get("gesture"), client_id)
            
        elif message_type == "status_update":
            # Handle status updates from Spectacles
            print(f"Spectacles status update: {data.get('status')}")
            
        else:
            print(f"Unknown Spectacles message type: {message_type}")
    
    async def process_mobile_message(self, data: Dict[str, Any], client_id: str):
        """Process messages from mobile apps"""
        message_type = data.get("type")
        
        if message_type == "emotion_data":
            # Process emotion data and generate coaching advice
            emotion_data = data.get("data")
            coaching_advice = await self.generate_coaching_advice(emotion_data)
            
            # Send advice back to mobile app
            await self.send_to_mobile_client(client_id, {
                "type": "coaching_advice",
                "advice": coaching_advice,
                "timestamp": time.time()
            })
            
            # Forward to Spectacles devices
            await self.broadcast_to_spectacles_clients({
                "type": "coaching_advice",
                "advice": coaching_advice,
                "timestamp": time.time()
            })
            
        elif message_type == "request_coaching":
            # Handle explicit coaching requests
            emotion_data = data.get("emotionData")
            coaching_advice = await self.generate_coaching_advice(emotion_data)
            
            await self.send_to_mobile_client(client_id, {
                "type": "coaching_advice",
                "advice": coaching_advice,
                "timestamp": time.time()
            })
            
        else:
            print(f"Unknown mobile message type: {message_type}")
    
    async def generate_coaching_advice(self, emotion_data: Dict[str, Any]) -> str:
        """Generate coaching advice based on emotion data"""
        if not emotion_data:
            return "Continue monitoring the conversation dynamics."
        
        dominant_state = emotion_data.get("dominantState", "neutral")
        confidence = emotion_data.get("confidence", 0.5)
        
        # Coaching advice based on emotion state
        advice_map = {
            "interested": "Excellent! The audience is engaged. Keep building on this positive energy with specific examples and interactive elements.",
            "skeptical": "They seem skeptical. Try addressing their concerns directly with concrete data and case studies. Ask clarifying questions.",
            "concerned": "They appear concerned. Show empathy and provide reassurance with specific solutions and next steps.",
            "confused": "They seem confused. Simplify your explanation and use visual aids or analogies to clarify your points.",
            "bored": "They appear disengaged. Increase your energy level, ask questions, and make the content more interactive.",
            "neutral": "The audience seems neutral. Try to create more emotional connection and excitement in your delivery."
        }
        
        base_advice = advice_map.get(dominant_state, "Continue monitoring the conversation dynamics.")
        
        # Add confidence-based modifiers
        if confidence > 0.8:
            base_advice += " (High confidence in this assessment.)"
        elif confidence < 0.4:
            base_advice += " (Low confidence - continue monitoring for clearer signals.)"
        
        return base_advice
    
    async def handle_gesture_input(self, gesture: str, client_id: str):
        """Handle gesture input from Spectacles"""
        print(f"Gesture received from {client_id}: {gesture}")
        
        # Process gesture and send appropriate response
        gesture_responses = {
            "tap": "Toggled display visibility",
            "swipe_left": "Previous emotion state",
            "swipe_right": "Next emotion state",
            "swipe_up": "Increased display size",
            "swipe_down": "Decreased display size",
            "pinch": "Toggled coaching advice display"
        }
        
        response = gesture_responses.get(gesture, "Unknown gesture")
        
        # Send response back to Spectacles
        await self.send_to_spectacles_client(client_id, {
            "type": "gesture_response",
            "gesture": gesture,
            "response": response,
            "timestamp": time.time()
        })
    
    async def broadcast_to_spectacles_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected Spectacles devices"""
        if not self.spectacles_clients:
            return
        
        disconnected_clients = []
        for client_id, websocket in self.spectacles_clients.items():
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                print(f"Error sending to Spectacles {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del self.spectacles_clients[client_id]
    
    async def broadcast_to_mobile_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected mobile apps"""
        if not self.mobile_clients:
            return
        
        disconnected_clients = []
        for client_id, websocket in self.mobile_clients.items():
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client_id)
            except Exception as e:
                print(f"Error sending to mobile {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            del self.mobile_clients[client_id]
    
    async def send_to_spectacles_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific Spectacles client"""
        if client_id in self.spectacles_clients:
            try:
                await self.spectacles_clients[client_id].send(json.dumps(message))
            except Exception as e:
                print(f"Error sending to Spectacles {client_id}: {e}")
    
    async def send_to_mobile_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific mobile client"""
        if client_id in self.mobile_clients:
            try:
                await self.mobile_clients[client_id].send(json.dumps(message))
            except Exception as e:
                print(f"Error sending to mobile {client_id}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current adapter status"""
        return {
            "is_running": self.is_running,
            "spectacles_clients": len(self.spectacles_clients),
            "mobile_clients": len(self.mobile_clients),
            "total_clients": len(self.spectacles_clients) + len(self.mobile_clients)
        }

async def main():
    """Main function to start the Spectacles adapter"""
    adapter = SpectaclesAdapter()
    
    try:
        await adapter.start_server()
    except KeyboardInterrupt:
        print("\nShutting down Spectacles Adapter...")
    except Exception as e:
        print(f"Error starting adapter: {e}")

if __name__ == "__main__":
    print("BeneAI Spectacles Backend Adapter")
    print("=" * 40)
    asyncio.run(main())


