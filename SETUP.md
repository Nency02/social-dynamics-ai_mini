# Classroom Group Discussion Analyzer - Setup & Run Guide

## System Architecture
```
Camera → Pose Detection → Behavior Analysis → live_data.json → FastAPI → Dashboard
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install fastapi uvicorn opencv-python
```

### 2. Project Structure
```
social-dynamics-ai/
├── main.py                 # Camera pipeline (outputs to live_data.json)
├── api.py                  # FastAPI backend (serves /data endpoint)
├── dashboard.html          # Web dashboard
├── outputs/
│   ├── keypoints.json     # Detailed pose data
│   └── live_data.json     # Classroom discussion data (updated in real-time)
├── src/
│   ├── behavior/          # Behavior analysis modules
│   ├── vision/            # Pose detection modules
│   └── ...
```

## Running the System (End-to-End)

### Terminal 1: Start the FastAPI Backend
```bash
python api.py
```
The API will start at `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Data endpoint: `http://localhost:8000/data`

### Terminal 2: Start the Camera Pipeline
```bash
python main.py
```
This will:
- Open your camera
- Detect poses in real-time
- Analyze student behavior
- Update `outputs/live_data.json` every 5 frames

### Terminal 3 (or Browser): Open the Dashboard
```bash
# Option A: Open in default browser
open dashboard.html

# Option B: Use a simple HTTP server
python -m http.server 8001
# Then visit http://localhost:8001/dashboard.html
```

## Output Format

### live_data.json Structure
```json
{
  "timestamp": 1710951234.5,
  "total_students": 3,
  "students": [
    {
      "student_id": 0,
      "role": "Active",
      "participation_score": 0.75
    },
    {
      "student_id": 1,
      "role": "Moderate",
      "participation_score": 0.45
    },
    {
      "student_id": 2,
      "role": "Passive",
      "participation_score": 0.20
    }
  ],
  "metrics": {
    "most_active_student": 0,
    "participation_level": 0.4667,
    "discussion_balance": 0.7234
  }
}
```

## Student Roles

| Role | Description | Criteria |
|------|-------------|----------|
| **Active** | Leading the discussion | Speaker role (high dominance/gesture) |
| **Moderate** | Actively participating | Listener or Engaged roles (good engagement) |
| **Passive** | Minimal participation | Peripheral or Isolated roles |

## Metrics Explained

- **Participation Level**: Average engagement score across all students (0-1, shown as 0-100%)
- **Discussion Balance**: How evenly participation is distributed (high = balanced, low = dominated by few)
- **Most Active Student**: Student ID with highest participation score

## Dashboard Features

✅ Real-time data updates (every 1 second)
✅ Total student count
✅ Most active student identification
✅ Participation level visualization
✅ Discussion balance indicator
✅ Individual student role badges
✅ Participation scores per student
✅ Connection status indicator
✅ Responsive design for all devices

## Troubleshooting

**API Connection Error?**
- Ensure api.py is running on port 8000
- Check firewall settings
- Verify dashboard.html points to correct API URL

**No data in dashboard?**
- Camera pipeline (main.py) must be running
- Check camera permission/availability
- Wait a few seconds for first data update

**Camera not opening?**
- Try different CAMERA_INDEX (0, 1, 2, etc.)
- Check camera is not in use by another app
- Test camera with: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`

## Performance Notes

- JSON writes throttled to every 5 frames to reduce I/O
- Dashboard fetches every 1 second
- Optimal performance with 2-5 students visible in frame
