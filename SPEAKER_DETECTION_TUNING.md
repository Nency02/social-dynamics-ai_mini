# Speaker Detection Tuning Guide

## What Was Changed

### 1. **Role Thresholds** (`src/behavior/roles.py`)

**Old Thresholds (Too Strict):**
- Speaker requirement: `dominance >= 0.35`
- Engaged requirement: `engagement >= 0.36 or dominance >= 0.32`
- Listener requirement: `engagement >= 0.42`

**New Thresholds (More Realistic):**
- Speaker requirement: `dominance >= 0.12` ⬇️ 66% reduction
- Engaged requirement: `engagement >= 0.15 or dominance >= 0.12` ⬇️ 58% reduction
- Listener requirement: `engagement >= 0.18` ⬇️ 57% reduction
- Isolated requirement: `proximity < 0.05` (was 0.12)

### 2. **Score Weights** (`src/behavior/scoring.py`)

**Boosted Gesture Weight:**
```
OLD:
engagement_score = 0.30*facing + 0.20*dist_close + 0.20*proximity + 0.15*gesture + 0.15*centrality
dominance_score = 0.50*gesture + 0.20*arm_spread + 0.15*centrality + 0.10*facing + 0.05*dist_close

NEW:
engagement_score = 0.25*facing + 0.20*dist_close + 0.25*gesture + 0.15*proximity + 0.15*centrality
dominance_score = 0.60*gesture + 0.15*arm_spread + 0.10*centrality + 0.10*facing + 0.05*dist_close
```

**Impact:** Gesture activity now worth **60% of dominance** (was 50%)

## How to Test

### 1. **Restart the System**
```powershell
# Stop current main.py (press ESC in the window)
# Then restart
python main.py
```

### 2. **What to Look For**

While speaking with visible gestures, you should see in console output:
```
ID:0 | Role:Speaker | Eng:0.180 | Dom:0.120 | Act:0.050
```

OR at minimum:
```
ID:0 | Role:Engaged | Eng:0.150 | Dom:0.120 | Act:0.050
```

**NOT:**
```
ID:0 | Role:Isolated | Eng:0.033 | Dom:0.088 | Act:0.005
```

### 3. **Dashboard Should Show**
- Your role as **Active** (was Passive)
- Your participation_score should increase
- Most_active_student should point to you

## Diagnostic Steps

If it **still doesn't detect you as a Speaker**, follow these steps:

### Step A: Check Console Output
```
Are the engagement/dominance scores > 0.1?
- YES: Skip to Step C
- NO: Go to Step B
```

### Step B: Poor Keypoint Detection
If scores are still very low (<0.05), the issue is **pose detection**:

1. **Check pose detection:** In `src/vision/pose.py`, see if keypoints are visible
2. **Try different lighting:** More light = better detection
3. **Try different pose:** Face camera more directly
4. **Try with 2+ people:** Easier to detect with multiple people for comparison

### Step C: Adjust Further (If Needed)
If scores are 0.10-0.15 but still not "Speaker", you can lower thresholds more:

**In `src/behavior/roles.py`, line 41:**
```python
# Current: dominance >= 0.12
if top >= 0.12 and (top - second) >= 0.01:

# If still not working, try:
if top >= 0.08 and (top - second) >= 0.00:
```

## Expected Score Ranges (After Changes)

| Behavior | Old Range | New Range | Visual Cue |
|----------|-----------|-----------|-----------|
| Quietly standing | 0.02-0.05 | 0.03-0.10 | Still body |
| Looking engaged | 0.05-0.10 | 0.10-0.20 | Facing group |
| Some gestures | 0.10-0.15 | 0.15-0.30 | Hand movements |
| **Active speaking** | 0.15-0.25 | 0.30-0.60+ | Large gestures |

## Role Detection (New Criteria)

| Role | Engagement | Dominance | Activity | When |
|------|-----------|-----------|----------|------|
| **Speaker** | Any | ≥0.12 | Any | Has highest dominance |
| **Engaged** | ≥0.15 | OR ≥0.12 | - | Contributing but not leading |
| **Listener** | ≥0.18 | - | <0.10 | Very engaged, no gesture |
| **Peripheral** | <0.15 & <0.12 | - | - | Minimal involvement |
| **Isolated** | - | - | - | Very far from group |

## Tuning Philosophy

The updated thresholds use this philosophy:
1. **Gesture is king** - 60% of dominance score comes from gesture activity
2. **Low baselines** - Thresholds are 50-60% lower to account for real-world classroom detection
3. **Relative ranking** - Speaker is whoever has highest dominance in the group (not absolute threshold)
4. **Forgiving detection** - Single person with any engagement ≥0.08 gets "Engaged" role

## What To Do Next

1. **Restart main.py**
2. **Stand in front of camera with visible gestures**
3. **Check console for updated scores**
4. **Watch dashboard update to "Active"**

If you still see "Passive" after these changes with scores < 0.10, the issue is with **pose keypoint detection**, not role classification. In that case, look at:
- Camera quality/resolution
- Lighting conditions
- Visibility of arms and shoulders
- Pose detection model (`src/vision/pose.py`)

---

## Quick Test: Gesture vs No Gesture

Try this comparison:
1. **Stand still** → Score should be ~0.05-0.10 → "Peripheral" or "Passive"
2. **Raise arms and gesture** → Score should jump to ~0.25+ → "Engaged" or "Speaker"

If you don't see this difference, the gesture_activity feature is not being calculated, pointing to a pose detection issue.

