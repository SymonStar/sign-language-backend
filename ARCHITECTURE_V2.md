# SinaLinaw Architecture V2

## Overview
Complete rebuild of gesture recognition system using body-relative coordinates, detailed finger joint angles, and velocity-based segmentation. Expected accuracy: 60-70% (vs 40% in V1).

## Architecture Components

### 1. Feature Extraction (`feature_extractor.py`)
Extracts rich normalized features from MediaPipe landmarks:

**Body-Relative Normalization:**
- Wrist position normalized to face center and shoulder width
- Removes camera distance and signer position variance
- Creates consistent "templated paper" coordinate space

**Per-Hand Features (27 values):**
- **Wrist position** (2): X, Y relative to face/shoulders
- **Joint angles** (15): 3 angles per finger (thumb, index, middle, ring, pinky)
- **Spread angles** (4): Angles between adjacent fingers at base
- **Fingertip distances** (5): Normalized distances from wrist to each fingertip
- **Palm normal** (1): Z-component of palm orientation vector

**Velocity Tracking:**
- Frame-to-frame wrist velocity for segmentation
- Separate tracking for left and right hands

### 2. Gesture Segmentation (`gesture_segmenter.py`)
Segments continuous signing into individual gestures using velocity-based hold detection:

**Hold Detection:**
- Monitors wrist velocity continuously
- Hold = velocity < threshold for N consecutive frames
- Default: < 0.015 for 3 frames (~100ms at 30fps)

**Segmentation Logic:**
- High velocity = movement (in gesture)
- Velocity drops to hold = gesture boundary
- Extracts frames between holds as complete gestures
- Max gesture length: 90 frames (3 seconds)

### 3. Gesture Recognition (`gesture_recognizer_v2.py`)
DTW-based matching using rich feature vectors:

**Template Matching:**
- Each gesture has multiple templates (one per training video)
- Live gesture converted to feature sequence (Nx54 for two hands)
- FastDTW compares against all templates
- Distance converted to similarity score (0-1)

**Confidence Threshold:**
- Default: 0.7 (70% similarity required)
- Rejects low-confidence matches

### 4. Dataset Reprocessing (`reprocess_fsl_dataset.py`)
Converts FSL-105 dataset to new format:

**Process:**
1. Load original skeletal data (2130 videos)
2. Extract new features for each frame
3. Segment each video using velocity detection
4. Create templates from longest segment per video
5. Save to `gesture_templates_v2.json`

**Output:**
- 105 gestures
- ~20 templates per gesture
- Each template: sequence of 27-value feature vectors

### 5. API (`app_v2.py`)
Flask endpoints for PWA integration:

**Endpoints:**
- `POST /api/translate` - Batch translation (stateless)
- `POST /api/translate/continuous` - Continuous translation (stateful)
- `GET /api/stats` - Template statistics
- `GET /api/health` - Health check

## Setup Instructions

### 1. Install Dependencies
```bash
cd C:\SignLanguageBackend
pip install numpy scipy fastdtw flask flask-cors tqdm
```

### 2. Test Architecture
```bash
python test_architecture.py
```

This validates:
- Feature extraction (27 values per hand)
- Gesture segmentation (hold detection)
- Recognition pipeline (without templates)

### 3. Reprocess FSL-105 Dataset
```bash
python reprocess_fsl_dataset.py
```

This will:
- Load `data/fsl_skeletal_data.json` (3.44GB)
- Extract new features for all 2130 videos
- Segment gestures using velocity detection
- Create `data/gesture_templates_v2.json`
- Takes ~10-20 minutes

### 4. Start API Server
```bash
python app_v2.py
```

Server runs on `http://localhost:5000`

### 5. Update PWA
The PWA needs to send **pose landmarks** along with hand landmarks:

**Current format:**
```javascript
{
  frames: [
    {
      left_hand: [[x,y,z], ...],  // 21 points
      right_hand: [[x,y,z], ...]  // 21 points
    }
  ]
}
```

**New format:**
```javascript
{
  frames: [
    {
      left_hand: [[x,y,z], ...],   // 21 points
      right_hand: [[x,y,z], ...],  // 21 points
      pose: [[x,y,z], ...]         // 13 points (0-12: nose, shoulders, etc.)
    }
  ]
}
```

## Key Improvements Over V1

| Feature | V1 | V2 |
|---------|----|----|
| Coordinate space | Raw XYZ | Body-relative normalized |
| Hand features | Generic shapes (open/fist) | 15 joint angles + 4 spread angles |
| Orientation | Simple angle | Palm normal vector |
| Segmentation | Fixed windows | Velocity-based holds |
| Expected accuracy | 40% | 60-70% |

## Feature Vector Dimensions

**Single hand:** 27 values
- Wrist XY: 2
- Joint angles: 15
- Spread angles: 4
- Fingertip distances: 5
- Palm normal Z: 1

**Two hands:** 54 values (concatenated)

**One hand missing:** 54 values (missing hand padded with zeros)

## Tunable Parameters

### Feature Extraction
- None (fully deterministic)

### Segmentation
- `velocity_threshold`: 0.015 (lower = more sensitive)
- `hold_frames`: 3 (higher = longer hold required)
- `max_gesture_frames`: 90 (max 3 seconds)

### Recognition
- `confidence_threshold`: 0.7 (higher = stricter matching)

## Expected Performance

**Accuracy:** 60-70% on movement-distinct signs
- V1 achieved 40% with raw coordinates
- Body-relative normalization: +10-15%
- Rich joint angles: +10-15%

**Speed:**
- Feature extraction: <1ms per frame
- Segmentation: <0.1ms per frame
- Recognition: ~50ms per gesture (DTW on 20 templates)

**Latency:**
- Hold detection: 100ms (3 frames at 30fps)
- Total: ~150ms from gesture end to result

## Next Steps

1. ✅ Build core architecture
2. ⏳ Test with sample data
3. ⏳ Reprocess FSL-105 dataset
4. ⏳ Update PWA to send pose landmarks
5. ⏳ Test end-to-end with real signing
6. ⏳ Tune parameters for optimal accuracy
7. ⏳ Select 30-50 movement-distinct signs for Phase 1

## File Structure

```
SignLanguageBackend/
├── feature_extractor.py          # NEW: Body-relative feature extraction
├── gesture_segmenter.py          # NEW: Velocity-based segmentation
├── gesture_recognizer_v2.py      # NEW: DTW with rich features
├── app_v2.py                     # NEW: API with new pipeline
├── reprocess_fsl_dataset.py      # NEW: Dataset conversion
├── test_architecture.py          # NEW: Validation tests
├── data/
│   ├── fsl_skeletal_data.json    # Original dataset (3.44GB)
│   └── gesture_templates_v2.json # NEW: Reprocessed templates
├── gesture_recognizer.py         # OLD: V1 recognizer
└── app.py                        # OLD: V1 API
```

## Migration Path

**Phase 1: Parallel Testing**
- Keep V1 running on port 5000
- Run V2 on port 5001
- Compare accuracy side-by-side

**Phase 2: Gradual Rollout**
- Switch PWA to V2 endpoint
- Monitor accuracy metrics
- Keep V1 as fallback

**Phase 3: Full Migration**
- Deprecate V1 files
- V2 becomes primary system
- Archive old code

## Troubleshooting

**No templates loaded:**
- Run `reprocess_fsl_dataset.py` first
- Check `data/gesture_templates_v2.json` exists

**Low accuracy:**
- Tune `velocity_threshold` (try 0.010 - 0.020)
- Adjust `confidence_threshold` (try 0.6 - 0.8)
- Check pose landmarks are being sent from PWA

**Segmentation issues:**
- Increase `hold_frames` for longer holds
- Decrease `velocity_threshold` for more sensitive detection
- Check wrist velocity values in debug output

## Contact

Built by Symon for SinaLinaw FSL Translation System
Architecture designed for 60-70% accuracy on movement-distinct signs
