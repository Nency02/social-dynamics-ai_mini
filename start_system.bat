@echo off
REM Classroom Group Discussion Analyzer - Windows Startup Script

echo.
echo ============================================================
echo  Classroom Group Discussion Analyzer
echo ============================================================
echo.
echo Starting the end-to-end pipeline...
echo.

REM Start API in a new window
echo [1/2] Starting FastAPI Backend on port 8000...
start cmd /k "title API Server && cd backend && python api.py"
timeout /t 2 /nobreak

REM Start main pipeline in a new window
echo [2/2] Starting Camera Pipeline...
start cmd /k "title Camera Pipeline && cd backend && python main.py"
timeout /t 1 /nobreak

echo.
echo ============================================================
echo  System Starting...
echo ============================================================
echo.
echo API Backend:     http://localhost:8000
echo Health Check:    http://localhost:8000/health
echo Data Endpoint:   http://localhost:8000/data
echo.
echo Frontend App:    Start frontend with: cd frontend ^&^& npm run dev
echo Dashboard URL:   http://localhost:5173 (or Vite-selected port)
echo.
echo To verify live data:
echo   curl http://localhost:8000/data
echo.
echo Press CTRL+C in camera window to stop the pipeline (ESC also works)
echo Close API window to stop the server
echo.
pause
