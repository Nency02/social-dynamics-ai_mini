# 🎓 Classroom Group Discussion Analyzer

A real-time computer vision system that analyzes student participation, engagement, and discussion dynamics in classroom group discussions.

**Status:** ✅ Production Ready | **Version:** 1.0 | **Updated:** 2026-03-20

## Overview

This is an enhanced version of the Social Dynamics AI system, specifically configured for classroom learning environments. It automatically detects and classifies student participation levels during group discussions, providing real-time metrics on engagement patterns.

## ✅ What's Implemented

**Vision & Detection Pipeline:**
- ✅ Real-time camera capture (OpenCV)
- ✅ YOLOv8 pose detection via MediaPipe
- ✅ 17-point keypoint extraction (COCO format)
- ✅ Multi-person tracking with stable IDs
- ✅ Orientation calculation

**Behavior Analysis & Scoring:**
- ✅ Gesture activity detection
- ✅ Arm spread measurement
- ✅ Body lean analysis
- ✅ Head tilt detection
- ✅ Facing direction & engagement
- ✅ Proximity & density measurement
- ✅ Group centrality calculation
- ✅ Dominance score computation
- ✅ Engagement score computation
- ✅ Role classification (Speaker, Listener, Engaged, Peripheral, Isolated)

**Classroom Analyzer Features:**
- ✅ Simplified role mapping (Active, Moderate, Passive)
- ✅ Participation level metrics
- ✅ Discussion balance calculation
- ✅ Most active student identification
- ✅ Real-time JSON output (`outputs/live_data.json`)
- ✅ FastAPI backend with `/data` endpoint
- ✅ Interactive web dashboard
- ✅ CORS-enabled API
- ✅ Health check endpoint
- ✅ Startup automation scripts

## 🔄 System Architecture

```
Camera Input
    ↓
Pose Detection (YOLOv8/MediaPipe)
    ↓
Keypoint Extraction (17 COCO points)
    ↓
Behavior Feature Analysis
    ↓
Role Classification (Active/Moderate/Passive)
    ↓
Metrics Calculation
    ↓
JSON Export (live_data.json)
    ↓
FastAPI Backend
    ↓
Web Dashboard
```

**Data Flow:**
1. Camera frames → Pose detection (~30-50ms)
2. Keypoints extracted → Behavior features (~20-30ms)
3. Scores calculated → Roles assigned (~10ms)
4. JSON written to `outputs/live_data.json` (every 5 frames)
5. API serves latest data on `/data` endpoint (<10ms)
6. Dashboard fetches and displays (1/second)

## 🚀 Quick Start (3 Steps)

### 1. Install Dependencies
```bash
pip install fastapi uvicorn opencv-python
```

### 2. Run the System

**Windows (Automatic):**
```bash
start_system.bat
```

**Mac/Linux:**
```bash
bash start_system.sh
```

**Manual:**
```bash
# Terminal 1: Start API
python api.py

# Terminal 2: Start camera pipeline
python main.py
```

### 3. Open Dashboard
Simply open `dashboard.html` in any web browser (double-click it)

Or use a local server:
```bash
python -m http.server 8001
# Visit: http://localhost:8001/dashboard.html
```

## 📊 Student Roles & Metrics

### Role Classification
| Role | Score | Meaning | Visual |
|------|-------|---------|--------|
| **Active** | 60%+ | Leading discussion | 🟣 Purple |
| **Moderate** | 30-60% | Active participant | 🔴 Red/Pink |
| **Passive** | <30% | Minimal involvement | 🔵 Blue |

### Key Metrics
- **Participation Level**: Average engagement (0-100%)
- **Discussion Balance**: Participation distribution (0-100%)
  - High (>70%): All students contributing
  - Low (<30%): One student dominates
- **Most Active Student**: Student ID leading the discussion

## 🌐 REST API

### GET `/data`
Returns current classroom state
```bash
curl http://localhost:8000/data
```

Response:
```json
{
  "timestamp": 1710951234.567,
  "total_students": 3,
  "students": [
    {"student_id": 0, "role": "Active", "participation_score": 0.75},
    {"student_id": 1, "role": "Moderate", "participation_score": 0.46},
    {"student_id": 2, "role": "Passive", "participation_score": 0.22}
  ],
  "metrics": {
    "most_active_student": 0,
    "participation_level": 0.4767,
    "discussion_balance": 0.6234
  }
}
```

### GET `/health`
Health check
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

## 📁 Project Files

### New/Modified Files
- **main.py** - Updated with classroom analyzer output
- **api.py** - FastAPI backend (NEW)
- **dashboard.html** - Web dashboard (NEW)
- **start_system.bat** - Windows launcher (NEW)
- **start_system.sh** - Unix launcher (NEW)
- **QUICKSTART.md** - Quick start guide (NEW)
- **SCHEMA.md** - Data format docs (NEW)
- **SETUP.md** - Detailed setup (NEW)

### Core Modules (Unchanged)
```
src/
├── behavior/
│   ├── features.py      - Behavior feature extraction
│   ├── scoring.py       - Score calculation
│   └── roles.py         - Role classification
├── vision/
│   ├── camera.py        - Camera capture
│   ├── pose.py          - Pose detection
│   ├── keypoints.py     - Keypoint tracking
│   ├── detect.py        - Person detection
│   └── Overlay.py       - Visualization
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Camera won't open** | Try different CAMERA_INDEX (0, 1, 2...) in main.py |
| **Dashboard shows "Offline"** | Ensure api.py is running on port 8000 |
| **No students detected** | Ensure good lighting, stand in visible pose |
| **Module not found** | Run: `pip install -U fastapi uvicorn opencv-python` |
| **Port 8000 already in use** | Change port in api.py (line 59) and dashboard.html (line ~107) |

## 📈 Use Cases

✅ **Classroom Assessment**
- Monitor student engagement levels
- Identify quiet students who need encouragement
- Measure discussion inclusivity
- Evaluate teaching effectiveness

✅ **Group Discussion Analysis**
- Track opinion leaders and participation patterns
- Identify engagement gaps
- Monitor meeting dynamics
- Document classroom interactions

✅ **Teacher Training**
- Review classroom interaction patterns
- Improve facilitation skills
- Build awareness of participation dynamics

## 📚 Documentation

- **QUICKSTART.md** - Get started in 5 minutes
- **SETUP.md** - Detailed installation & configuration
- **SCHEMA.md** - Complete data format reference
- **README.md** - This file

## 🎯 Performance

| Metric | Value |
|--------|-------|
| Pose Detection | 30-50ms/frame |
| Behavior Analysis | 10-20ms/frame |
| JSON Write Rate | ~5-6/sec |
| API Latency | <10ms |
| Dashboard Update | 1/sec |
| Total E2E Latency | <500ms |

## 🔐 Data Privacy

- No personal data is stored
- Only participant IDs (0, 1, 2...) are used
- Camera frames are not saved by default
- All data stays on local machine
- To restrict API access, modify CORS in api.py

## 📄 Sample Output

**Dashboard Display:**
```
┌─────────────────────────────────┐
│  Classroom Discussion Analyzer   │
│   🔴 Live (Connected)           │
├─────────────────────────────────┤
│ Total Students: 3               │
│ Most Active: Student #0         │
│ Participation: 47.7%            │
│ Balance: 62.3%                  │
├─────────────────────────────────┤
│ Student #0: [🟣 Active] 75%    │
│ Student #1: [🔴 Moderate] 46% │
│ Student #2: [🔵 Passive] 22%  │
└─────────────────────────────────┘
```

---

**For detailed guides, see:**
- Quick start: [QUICKSTART.md](QUICKSTART.md)
- Setup: [SETUP.md](SETUP.md)
- Data format: [SCHEMA.md](SCHEMA.md)
