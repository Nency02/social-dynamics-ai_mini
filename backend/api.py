"""
FastAPI backend for Classroom Group Discussion Analyzer
Serves real-time data from live_data.json
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from pathlib import Path

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
