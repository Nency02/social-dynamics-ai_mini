# Data Schema Documentation

## live_data.json Format

The system outputs real-time classroom discussion data in JSON format to `outputs/live_data.json`.

### Root Object

```typescript
{
  "timestamp": number,        // Unix timestamp (seconds since epoch)
  "total_students": number,   // Count of detected students
  "students": Student[],      // Array of student data
  "metrics": Metrics          // Aggregate classroom metrics
}
```

### Student Object

```typescript
{
  "student_id": number,                    // Unique student identifier (0, 1, 2, ...)
  "role": "Active" | "Moderate" | "Passive",  // Classified participation level
  "participation_score": number            // 0.0 to 1.0 (0% to 100%)
}
```

#### Role Classifications

| Role | Score Range | Behavior | Voice in Discussion |
|------|---|---|---|
| **Active** | 0.6-1.0 | Leading, gesturing, central position | Speaking frequently |
| **Moderate** | 0.3-0.6 | Engaged, responding, facing group | Contributing regularly |
| **Passive** | 0.0-0.3 | Quiet, on periphery, minimal gesture | Rarely speaking |

#### Participation Score Calculation

```
participation_score = (engagement_score + dominance_score) / 2.0

where:
  engagement_score = 0.35 * face_direction
                   + 0.25 * distance_from_group
                   + 0.15 * proximity_to_others
                   + 0.15 * gesture_activity
                   + 0.10 * centrality_in_group

  dominance_score  = 0.40 * gesture_activity
                   + 0.20 * arm_spread
                   + 0.20 * centrality_in_group
                   + 0.10 * face_direction
                   + 0.10 * distance_from_group
```

### Metrics Object

```typescript
{
  "most_active_student": number | null,  // Student ID with highest score (null if no students)
  "participation_level": number,          // Average score of all students (0.0-1.0)
  "discussion_balance": number            // Distribution evenness (0.0-1.0)
}
```

#### Metric Definitions

**participation_level**
- Formula: `mean(all student participation_scores)`
- Range: 0.0 (no participation) to 1.0 (max engagement)
- Interpretation:
  - 0.0-0.2: Very low classroom participation
  - 0.2-0.4: Low participation
  - 0.4-0.6: Moderate participation
  - 0.6-0.8: Good participation
  - 0.8-1.0: Excellent engagement

**discussion_balance**
- Formula: `1.0 - min(1.0, variance(scores))`
- Range: 0.0 (highly skewed) to 1.0 (perfectly balanced)
- Interpretation:
  - 0.0-0.3: One or few students dominate
  - 0.3-0.6: Some imbalance in participation
  - 0.6-0.8: Reasonably balanced discussion
  - 0.8-1.0: Highly inclusive participation

**most_active_student**
- The student_id with the highest participation_score
- Identifies: Opinion leaders, engaged participants, or dominant voices
- null when no students detected

## Complete Example

```json
{
  "timestamp": 1710951234.567,
  "total_students": 4,
  "students": [
    {
      "student_id": 0,
      "role": "Active",
      "participation_score": 0.8234
    },
    {
      "student_id": 1,
      "role": "Moderate",
      "participation_score": 0.5621
    },
    {
      "student_id": 2,
      "role": "Moderate",
      "participation_score": 0.5201
    },
    {
      "student_id": 3,
      "role": "Passive",
      "participation_score": 0.1892
    }
  ],
  "metrics": {
    "most_active_student": 0,
    "participation_level": 0.5237,
    "discussion_balance": 0.6842
  }
}
```

### Data Update Rate

- **Frequency**: Every 5 frames (depends on FPS)
- **FPS**: Typically 15-30 frames/second
- **Effective Rate**: ~3-6 updates per second
- **Latency**: <100ms from pose detection to JSON write

## API Response Format

The `/data` endpoint returns the exact same format as stored in `live_data.json`:

```bash
$ curl http://localhost:8000/data

{
  "timestamp": 1710951234.567,
  "total_students": 3,
  "students": [...],
  "metrics": {...}
}
```

## Historical Tracking (Optional)

To track changes over time, implement a logger:

```python
import json
from pathlib import Path
from datetime import datetime

def log_discussion_frame(data):
    """Log each frame to a historical file for analysis."""
    timestamp = datetime.fromtimestamp(data['timestamp'])
    log_file = Path('outputs/history.jsonl')

    with open(log_file, 'a') as f:
        f.write(json.dumps({
            'frame_timestamp': timestamp.isoformat(),
            'data': data
        }) + '\n')
```

This creates a JSONL file (one JSON object per line) for later analysis.

## Key Behaviors to Watch For

### High Discussion Balance (0.8+)
✅ Positive indicators:
- Equal voice for all students
- Inclusive classroom culture
- Diverse perspectives shared

### Low Discussion Balance (<0.3)
⚠️ Potential issues:
- Domination by one or few students
- Others not participating
- Need for facilitator intervention

### High Participation Level (0.6+)
✅ Positive indicators:
- Engaged class
- Active learning environment
- Good attention focus

### Passive Role Dominance
⚠️ Potential issues:
- Need to encourage shy students
- Break into smaller groups
- Change discussion format

## Integration Examples

### Python - Parse the Data
```python
import json

with open('outputs/live_data.json', 'r') as f:
    data = json.load(f)

print(f"Total students: {data['total_students']}")
print(f"Participation: {data['metrics']['participation_level']*100:.1f}%")
print(f"Balance: {data['metrics']['discussion_balance']*100:.1f}%")

for student in data['students']:
    print(f"  Student {student['student_id']}: {student['role']} ({student['participation_score']*100:.1f}%)")
```

### JavaScript - Fetch from API
```javascript
async function getClassroomData() {
  const response = await fetch('http://localhost:8000/data');
  const data = await response.json();

  console.log(`Active: ${data.metrics.most_active_student}`);
  console.log(`Participation: ${(data.metrics.participation_level*100).toFixed(1)}%`);
  console.log(`Balance: ${(data.metrics.discussion_balance*100).toFixed(1)}%`);
}
```

### Bash - Query the API
```bash
# Get all data
curl http://localhost:8000/data | jq '.'

# Get participation level only
curl http://localhost:8000/data | jq '.metrics.participation_level'

# Get all active students
curl http://localhost:8000/data | jq '.students[] | select(.role=="Active")'
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-20 | Initial schema for classroom analyzer |

---

**Last Updated:** 2026-03-20
