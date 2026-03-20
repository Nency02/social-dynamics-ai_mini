#!/bin/bash

# Classroom Group Discussion Analyzer - Unix Startup Script

echo ""
echo "============================================================"
echo "  Classroom Group Discussion Analyzer"
echo "============================================================"
echo ""
echo "Starting the end-to-end pipeline..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found. Please install Python 3."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn, cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Warning: Some dependencies may be missing."
    echo "Run: pip install fastapi uvicorn opencv-python"
fi

# Start API in background
echo "[1/2] Starting FastAPI Backend on port 8000..."
python3 api.py > /tmp/api.log 2>&1 &
API_PID=$!
sleep 2

# Start main pipeline
echo "[2/2] Starting Camera Pipeline..."
python3 main.py &
MAIN_PID=$!

echo ""
echo "============================================================"
echo "  System Started!"
echo "============================================================"
echo ""
echo "API Backend:     http://localhost:8000"
echo "Health Check:    http://localhost:8000/health"
echo "Data Endpoint:   http://localhost:8000/data"
echo ""
echo "Dashboard:       Open dashboard.html in your browser"
echo ""
echo "To verify live data:"
echo "  curl http://localhost:8000/data"
echo ""
echo "Process IDs:"
echo "  API: $API_PID"
echo "  Camera: $MAIN_PID"
echo ""
echo "To stop:"
echo "  press ESC in camera window, then Ctrl+C"
echo "  or run: kill $API_PID $MAIN_PID"
echo ""

# Wait for both processes
wait
