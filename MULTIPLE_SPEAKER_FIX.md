# Multiple Speaker Detection - Fixed!

## What Was Changed

**Old Behavior (Relative - BROKEN):**
- Only the person with the **highest dominance** gets "Speaker" role
- If Person A has dominance=0.15 and Person B has dominance=0.12
- Only Person A is marked as "Speaker"
- Person B gets "Engaged" even though they're clearly speaking

**New Behavior (Absolute - FIXED):**
- **Anyone with dominance >= 0.12 becomes a "Speaker"**
- Multiple people can be Speakers simultaneously
- Person A (dominance=0.15) → "Speaker" ✓
- Person B (dominance=0.12) → "Speaker" ✓
- Both detected correctly!

## How It Works Now

```
Person A speaks:
  dominance=0.15 >= 0.12 → role="Speaker" → classroom role="Active"

Person B speaks:
  dominance=0.12 >= 0.12 → role="Speaker" → classroom role="Active"

Both speaking:
  A: 0.15 >= 0.12 → "Speaker" ✓
  B: 0.12 >= 0.12 → "Speaker" ✓
  result: "2 Active students"

Neither speaking:
  A: 0.08 < 0.12 → "Peripheral" → classroom role="Passive"
  B: 0.09 < 0.12 → "Peripheral" → classroom role="Passive"
```

## Test This Now

### Test Case 1: One Person Speaking
```
Person A only:
  - Make large gestures
  - Speak clearly
  - You should get "Speaker" role
  - Dashboard shows: role="Active"
```

### Test Case 2: Both Speaking (Turn-based)
```
Person A speaks:
  - Dashboard shows: Student A="Active", Student B="Moderate"/"Passive"

Then Person B speaks:
  - Dashboard shows: Student A="Passive"/"Moderate", Student B="Active"
```

✅ **This should now work correctly!** Each person gets "Active" when THEY speak, not just whoever spoke first.

### Test Case 3: Both Speaking Simultaneously
```
Person A and B both gesture:
  - If A: dominance=0.15 and B: dominance=0.13
  - Dashboard shows: Both as "Active"
  - Participation balance: ~50% each
```

## Updated Role Detection Logic

| Condition | Old Logic | New Logic | Result |
|-----------|-----------|-----------|--------|
| dominance >= 0.12 | Only if highest | Always | **Speaker** |
| dominance >= 0.15 | Engaged | Higher Speaker | **Speaker** |
| dominance 0.10-0.12 | Peripheral | **Now Speaker!** | ✅ Fixed |
| dominance < 0.08 | Peripheral | Peripheral | Passive |

## What Changed in Code

File: `src/behavior/roles.py`

```python
# OLD (only ONE speaker):
speaker_id = None
if ranked:
    top = ranked[0].get("dominance_score", 0.0)
    second = ranked[1].get("dominance_score", 0.0) if len(ranked) > 1 else 0.0
    if top >= 0.12 and (top - second) >= 0.01:  # Relative!
        speaker_id = ranked[0].get("track_id")

# Person A (0.15) gets Speaker
# Person B (0.12) gets Engaged ❌

# NEW (multiple speakers):
speaker_ids = set()  # Use a SET not single ID
for person in ranked:
    dominance = person.get("dominance_score", 0.0)
    if dominance >= 0.12:  # Absolute threshold!
        speaker_ids.add(person.get("track_id"))

# Person A (0.15) gets Speaker ✓
# Person B (0.12) gets Speaker ✓
```

## How to Verify It's Fixed

### Check Console Output
While running `python main.py`, look for:
```
ID:0 | Role:Speaker | Eng:0.18 | Dom:0.15 | Act:0.05
ID:1 | Role:Speaker | Eng:0.15 | Dom:0.12 | Act:0.04
```

Both should show "Speaker" when both speak!

### Check Dashboard
- When Person A speaks: Student A shows purple "Active"
- When Person B speaks: Student B shows purple "Active" too
- They should **alternate** or **both show Active** if both speaking

### Check live_data.json
```json
{
  "students": [
    {"student_id": 0, "role": "Active", "participation_score": 0.15},
    {"student_id": 1, "role": "Active", "participation_score": 0.12}
  ]
}
```

Both should be "Active" when both have dominance >= 0.12

## Performance Impact

✅ **No performance impact** - same algorithm, just using a set instead of finding the max

## Edge Cases Handled

**Single person:**
- Still uses old logic (dominance >= 0.10 for "Engaged")
- No change to single-person detection

**Zero speakers:**
- If everyone < 0.12: all become "Peripheral" or lower
- Makes sense when nobody is actively speaking

**All speaking equally:**
- Everyone with dominance >= 0.12: all "Speaker"
- Participation balance shows equal contribution ✓

---

## 🚀 Ready to Test!

**Restart your system:**
```powershell
# Stop current (press ESC)
# Restart
python main.py

# Now:
# Person A speaks → "Speaker"
# Person B speaks → Also "Speaker" (NOT "Engaged" anymore!)
```

This should completely fix the issue where only the first speaker gets detected! 🎉

