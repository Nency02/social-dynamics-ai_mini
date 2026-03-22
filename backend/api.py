"""
FastAPI backend for Classroom Group Discussion Analyzer
Serves real-time data from live_data.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import threading

app = FastAPI(title="Classroom Discussion Analyzer API")

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adjusted path for new project structure
LIVE_DATA_PATH = Path(__file__).parent / "outputs" / "live_data.json"

# Global state for pipeline process management
_pipeline_process = None
_pipeline_lock = threading.Lock()


@app.get("/data")
async def get_live_data():
    """
    Returns the current classroom discussion data.

    Response format:
    {
        "timestamp": float,
        "total_students": int,
        "students": [
            {
                "student_id": int,
                "role": "Active" | "Moderate" | "Passive",
                "participation_score": float
            }
        ],
        "metrics": {
            "most_active_student": int | null,
            "participation_level": float,
            "discussion_balance": float
        }
    }
    """
    if not LIVE_DATA_PATH.exists():
        return JSONResponse(
            status_code=200,
            content={
                "timestamp": 0,
                "total_students": 0,
                "students": [],
                "metrics": {
                    "most_active_student": None,
                    "participation_level": 0.0,
                    "discussion_balance": 0.0,
                },
            },
        )

    try:
        with open(LIVE_DATA_PATH, "r") as f:
            data = json.load(f)
        return JSONResponse(status_code=200, content=data)
    except (json.JSONDecodeError, IOError) as e:
        return JSONResponse(
            status_code=200,
            content={
                "error": str(e),
                "timestamp": 0,
                "total_students": 0,
                "students": [],
                "metrics": {
                    "most_active_student": None,
                    "participation_level": 0.0,
                    "discussion_balance": 0.0,
                },
            },
        )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/pipeline/status")
async def pipeline_status():
    """Check if the camera pipeline is running."""
    with _pipeline_lock:
        is_running = _pipeline_process is not None and _pipeline_process.poll() is None
        return {"running": is_running}


@app.post("/pipeline/start")
async def pipeline_start():
    """Start the camera and vision pipeline."""
    global _pipeline_process
    with _pipeline_lock:
        if _pipeline_process is not None and _pipeline_process.poll() is None:
            return {"status": "already_running", "message": "Pipeline is already running"}
        
        try:
            backend_dir = Path(__file__).parent
            _pipeline_process = subprocess.Popen(
                [sys.executable, str(backend_dir / "main.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(backend_dir),
            )
            return {"status": "started", "pid": _pipeline_process.pid}
        except Exception as e:
            return {"status": "error", "message": str(e)}


@app.post("/pipeline/stop")
async def pipeline_stop():
    """Stop the camera and vision pipeline."""
    global _pipeline_process
    with _pipeline_lock:
        if _pipeline_process is None or _pipeline_process.poll() is not None:
            return {"status": "not_running", "message": "Pipeline is not running"}
        
        try:
            _pipeline_process.terminate()
            _pipeline_process.wait(timeout=5)
            _pipeline_process = None
            return {"status": "stopped"}
        except subprocess.TimeoutExpired:
            _pipeline_process.kill()
            _pipeline_process = None
            return {"status": "stopped", "message": "Process force-killed after timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    def is_port_available(host: str, port: int) -> bool:
        """Check whether a TCP port can be bound on the current machine."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
                return True
            except OSError:
                return False

    preferred_port = int(os.getenv("API_PORT", "8000"))
    candidate_ports = [preferred_port, 8001, 8002, 8080]

    selected_port = None
    for port in candidate_ports:
        if is_port_available("0.0.0.0", port):
            selected_port = port
            break

    if selected_port is None:
        raise RuntimeError(
            f"No available API port found in candidates: {candidate_ports}"
        )

    print(f"Starting API on port {selected_port}")
    uvicorn.run(app, host="0.0.0.0", port=selected_port)
