# 🎓 Classroom Group Discussion Analyzer - Quick Start Guide

## What You'll Get

A complete real-time system that:
- 📹 Captures classroom video
- 🧠 Detects student poses and behavior
- 📊 Classifies students as **Active**, **Moderate**, or **Passive**
- 📈 Calculates participation metrics
- 🌐 Serves data via REST API
- 📱 Displays analytics on an interactive web dashboard

## System Pipeline

```
Camera Feed
    ↓
Pose Detection (MediaPipe)
    ↓
Behavior Analysis (Gesture, Engagement, Dominance)
    ↓
Role Classification (Active/Moderate/Passive)
    ↓
JSON Export (live_data.json)
    ↓
FastAPI Backend
    ↓
Web Dashboard
```

## Quick Start (3 Steps)

### Step 1: Install Python Dependencies
```bash
pip install fastapi uvicorn opencv-python
```

### Step 2: Start the System

**Option A: Windows (Automatic)**
```bash
start_system.bat
```
This opens 2 windows:
- Terminal 1: FastAPI server
- Terminal 2: Camera pipeline

**Option B: Mac/Linux**
```bash
bash start_system.sh
```

**Option C: Manual Start**

Terminal 1 - Start API server:
```bash
python api.py
```

Terminal 2 - Start camera pipeline:
```bash
python main.py
```

### Step 3: Open Dashboard
Simply open `dashboard.html` in your browser (double-click it)

OR use a local web server:
```bash
python -m http.server 8001
# Then visit: http://localhost:8001/dashboard.html
```

## What You'll See

### Dashboard Display:
```
┌─────────────────────────────────────────────────┐
│    Classroom Group Discussion Analyzer          │
│   Real-time Student Participation Analytics     │
│                 🔴 Live (Connected)             │
├─────────────────────────────────────────────────┤
│                                                 │
│  Total Students     Most Active      Particip.  │
│       3         Student #1            67%       │
│                                                 │
│  Discussion Balance                            │
│       82% (Very Balanced)                      │
│                                                 │
├─────────────────────────────────────────────────┤
│          Student Participation Details          │
│                                                 │
│  ┌──────────┬──────────┬──────────┐            │
│  │Student #0│Student #1│Student #2│            │
│  │  ACTIVE  │ MODERATE │ PASSIVE  │            │
│  │  75%     │   45%    │   20%    │            │
│  └──────────┴──────────┴──────────┘            │
└─────────────────────────────────────────────────┘
```

## Student Roles & Meanings

| 🟣 **Active** | 🔴 **Moderate** | 🔵 **Passive** |
|---|---|---|
| Leading discussion | Participating well | Minimal involvement |
| High gestures | Engaged listener | Isolated or quiet |
| Central position | Facing group | On periphery |
| Dominance: >0.42 | Engagement: >0.36 | Others |

## Key Metrics Explained

### 📊 Participation Level
- **What:** Average engagement score across all students
- **Range:** 0% (no participation) → 100% (max engagement)
- **Good:** 50%+ (healthy classroom engagement)

### ⚖️ Discussion Balance
- **What:** How evenly participation is distributed
- **Range:** 0% (one student dominates) → 100% (perfectly balanced)
- **Goal:** >70% (inclusive discussion)

### 🏆 Most Active Student
- **What:** Student ID with highest participation
- **Use:** Identify opinion leaders or dominating voices

## API Endpoints

### GET `/data`
Returns current classroom discussion state:
```json
{
  "timestamp": 1710951234.5,
  "total_students": 3,
  "students": [
    {
      "student_id": 0,
      "role": "Active",
      "participation_score": 0.75
    }
  ],
  "metrics": {
    "most_active_student": 0,
    "participation_level": 0.4667,
    "discussion_balance": 0.7234
  }
}
```

Test it:
```bash
curl http://localhost:8000/data
```

### GET `/health`
API health check:
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### ❌ "Cannot open camera"
- Another app is using the camera
- Camera is not connected/enabled
- Try different CAMERA_INDEX in main.py (0, 1, 2...)

**Test:**
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### ❌ Dashboard shows "Offline (Disconnected)"
- API server (api.py) is not running
- API server is running on different port
- Firewall blocking localhost:8000
- Check: `curl http://localhost:8000/health`

### ❌ No students detected
- Wait a few seconds (first detection takes time)
- Ensure good lighting
- Stand in front of camera in visible pose
- Multiple students recommended for better analysis

### ❌ Module not found errors
```bash
pip install --upgrade pip
pip install fastapi uvicorn opencv-python
```

## Customization

### Change API Port
In `api.py`, line 57:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change 8000 to desired port
```

Then update dashboard.html:
```javascript
const API_BASE = "http://localhost:8000";  // Change 8000
```

### Adjust FPS Recording
In `main.py`, line 17:
```python
JSON_EVERY_N     = 5       # Write every 5 frames (increase = less frequent)
```

### Change Camera Index
In `main.py`, line 25:
```python
CAMERA_INDEX     = 0       # Try 0, 1, 2, etc.
```

## Files & Directory Structure

```
social-dynamics-ai/
├── main.py                  # 👉 Start camera pipeline
├── api.py                   # 👉 Start API server
├── dashboard.html           # 👉 Open in browser
├── start_system.bat         # Windows quick-start
├── start_system.sh          # Mac/Linux quick-start
├── SETUP.md                 # Detailed setup guide
├── QUICKSTART.md            # This file
├── outputs/
│   ├── live_data.json       # Current classroom state (auto-updated)
│   └── keypoints.json       # Detailed pose keypoints
└── src/
    ├── behavior/            # Role/scoring analysis
    ├── vision/              # Pose detection
    └── ...
```

## Performance Tips

✅ **Optimal Setup:**
- 2-5 students visible
- Good lighting
- 1080p+ camera
- Modern CPU (Intel i5+ / AMD Ryzen 5+)

⚠️ **Performance:**
- FPS: 15-30 (depends on hardware)
- API latency: <10ms
- Dashboard updates: 1/sec
- JSON writes: Every 5 frames (~5/sec at 25fps)

## Next Steps

1. ✅ Run the system (`start_system.bat` or `start_system.sh`)
2. ✅ Open dashboard (double-click `dashboard.html`)
3. ✅ Stand in front of camera
4. ✅ Watch roles and metrics update in real-time
5. 🔍 Experiment with group dynamics
6. 📊 Use data for classroom analysis

## Questions?

Check individual file headers for detailed documentation:
- `main.py` - Real-time pipeline
- `api.py` - API implementation
- `dashboard.html` - Frontend code
- `src/behavior/` - Role classification logic
- `src/vision/` - Pose detection

---

**Version:** 1.0
**Last Updated:** 2026-03-20
**Status:** Production Ready ✅
