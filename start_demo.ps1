# BeneAI Demo Startup Script for Windows
# Starts both backend and frontend servers

Write-Host "Starting BeneAI Demo..." -ForegroundColor Green
Write-Host ""

# Start backend in background
Write-Host "Starting backend server on port 8000..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "main.py" -WorkingDirectory "backend" -WindowStyle Hidden

# Wait for backend to start
Start-Sleep 5

# Check if backend is running
try {
    $response = Invoke-WebRequest http://localhost:8000/ -TimeoutSec 5
    Write-Host "Backend server running" -ForegroundColor Green
} catch {
    Write-Host "Backend failed to start" -ForegroundColor Red
    exit 1
}

# Start frontend server in background
Write-Host "Starting frontend server on port 8080..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "http.server", "8080" -WorkingDirectory "frontend" -WindowStyle Hidden

# Wait for frontend to start
Start-Sleep 3

Write-Host ""
Write-Host "BeneAI Demo Ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open http://localhost:8080 in your browser" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop the demo, close this window or press Ctrl+C" -ForegroundColor Gray
Write-Host ""

# Keep script running
Read-Host "Press Enter to stop the demo"
