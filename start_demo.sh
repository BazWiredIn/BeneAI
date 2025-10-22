#!/bin/bash

# BeneAI Demo Startup Script
# Starts both backend and frontend servers

echo "🚀 Starting BeneAI Demo..."
echo ""

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ] && [ ! -f "backend/.env" ]; then
    echo "⚠️  First time setup detected"
    echo "📦 Installing backend dependencies..."
    cd backend
    pip install -r requirements.txt
    cd ..
fi

# Start backend in background
echo "🔧 Starting backend server on port 8000..."
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Backend server running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start"
    exit 1
fi

# Start frontend server
echo "🌐 Starting frontend server on port 8080..."
cd frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 2

echo ""
echo "✅ BeneAI Demo Ready!"
echo ""
echo "📍 Frontend: http://localhost:8080"
echo "📍 Backend:  http://localhost:8000"
echo ""
echo "👉 Open http://localhost:8080 in your browser"
echo ""
echo "To stop the demo:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  Or press Ctrl+C and run: killall python python3"
echo ""

# Keep script running
wait
