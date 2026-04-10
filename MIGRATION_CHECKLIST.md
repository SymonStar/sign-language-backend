# Migration Checklist: V1 → V2

## ✅ Completed

- [x] Create `feature_extractor.py` - Body-relative coordinates + joint angles
- [x] Create `gesture_segmenter.py` - Velocity-based hold detection
- [x] Create `gesture_recognizer_v2.py` - DTW with rich features
- [x] Create `app_v2.py` - New API endpoints
- [x] Create `reprocess_fsl_dataset.py` - Dataset conversion script
- [x] Create `test_architecture.py` - Validation tests
- [x] Create `ARCHITECTURE_V2.md` - Documentation

## 🔄 Backend Tasks

### 1. Test Architecture Components
```bash
cd C:\SignLanguageBackend
python test_architecture.py
```

**Expected output:**
- ✅ Feature extraction: 27 values per hand
- ✅ Segmentation: Detects 2-3 gestures from simulated sequence
- ⚠️  Recognition: No templates (expected until step 2)

### 2. Reprocess FSL-105 Dataset
```bash
python reprocess_fsl_dataset.py
```

**Expected output:**
- Processes 2130 videos
- Creates 105 gesture templates
- ~20 templates per gesture
- Saves to `data/gesture_templates_v2.json`
- Takes 10-20 minutes

**Verify:**
```bash
# Check file exists and size
dir data\gesture_templates_v2.json
```

### 3. Start V2 API Server
```bash
python app_v2.py
```

**Expected output:**
```
🚀 Sign Language Translation API v2 starting...
📐 Architecture: Body-relative coordinates + Joint angles + Velocity segmentation
📡 Server running on http://localhost:5000
📊 Loaded 105 gesture templates
```

**Test health endpoint:**
```bash
curl http://localhost:5000/api/health
```

### 4. Test with Sample Request
```bash
curl -X POST http://localhost:5000/api/stats
```

Should return template statistics.

## 🔄 Frontend Tasks (PWA)

### 1. Update MediaPipe Initialization
**File:** `C:\SignLanguagePWA\js\mediapipe-setup.js`

Add MediaPipe Pose alongside Hands:

```javascript
// Add pose detection
const pose = new Pose({
    locateFile: (file) => {
        return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
    }
});

pose.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});
```

### 2. Update Frame Capture
**File:** `C:\SignLanguagePWA\js\app.js`

Modify frame capture to include pose landmarks:

```javascript
// Current format
const frame = {
    left_hand: leftHandLandmarks,
    right_hand: rightHandLandmarks
};

// New format
const frame = {
    left_hand: leftHandLandmarks,
    right_hand: rightHandLandmarks,
    pose: poseLandmarks  // ADD THIS
};
```

### 3. Update API Endpoint (Optional)
**File:** `C:\SignLanguagePWA\js\config.js`

For parallel testing, add V2 endpoint:

```javascript
const API_ENDPOINT_V1 = 'http://localhost:5000/api/translate';
const API_ENDPOINT_V2 = 'http://localhost:5000/api/translate';  // Same port after migration

// Or for parallel testing:
const API_ENDPOINT_V2 = 'http://localhost:5001/api/translate';
```

### 4. Test End-to-End
1. Open PWA in browser
2. Allow camera access
3. Sign a gesture
4. Verify translation appears
5. Check browser console for errors

## 🔄 Testing & Validation

### 1. Accuracy Comparison
Create test script to compare V1 vs V2:

**Test cases:**
- 10 videos per gesture (randomly selected)
- Measure accuracy for both systems
- Expected: V2 > V1 by 20-30%

### 2. Performance Benchmarks
- Feature extraction time: <1ms per frame
- Segmentation time: <0.1ms per frame
- Recognition time: <50ms per gesture
- End-to-end latency: <200ms

### 3. Edge Cases
- [ ] One hand only
- [ ] Hands entering/leaving frame
- [ ] Fast movements
- [ ] Slow movements
- [ ] Similar gestures (confusion matrix)

## 🔄 Parameter Tuning

### Segmentation Parameters
Test different values:

```python
# In gesture_segmenter.py or app_v2.py
GestureSegmenter(
    velocity_threshold=0.015,  # Try: 0.010, 0.015, 0.020
    hold_frames=3,             # Try: 2, 3, 4
    max_gesture_frames=90      # Try: 60, 90, 120
)
```

### Recognition Parameters
```python
# In gesture_recognizer_v2.py or app_v2.py
GestureRecognizerV2(
    confidence_threshold=0.7   # Try: 0.6, 0.7, 0.8
)
```

**Tuning strategy:**
1. Start with defaults
2. Measure accuracy on test set
3. Adjust one parameter at a time
4. Re-measure and compare
5. Keep best configuration

## 🔄 Deployment

### 1. Update Requirements
**File:** `C:\SignLanguageBackend\requirements.txt`

Verify includes:
```
numpy
scipy
fastdtw
flask
flask-cors
tqdm
```

### 2. Update Render Config
**File:** `C:\SignLanguageBackend\render.yaml`

Change start command:
```yaml
services:
  - type: web
    name: signlanguage-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python app_v2.py"  # Changed from app.py
```

### 3. Deploy to Render
```bash
git add .
git commit -m "Migrate to V2 architecture: body-relative coords + joint angles"
git push origin main
```

### 4. Update PWA API URL
**File:** `C:\SignLanguagePWA\js\config.js`

```javascript
const API_ENDPOINT = 'https://your-render-url.onrender.com/api/translate';
```

## 🔄 Monitoring

### Metrics to Track
- [ ] Recognition accuracy (%)
- [ ] Average confidence score
- [ ] Gestures per minute
- [ ] False positive rate
- [ ] API response time
- [ ] User feedback ratings

### Logging
Add to `app_v2.py`:
```python
import logging

logging.basicConfig(
    filename='recognition_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Log each recognition
logging.info(f"Recognized: {gesture_name}, Confidence: {confidence:.2f}")
```

## 🔄 Rollback Plan

If V2 has issues:

1. **Quick rollback:**
   ```bash
   # Change Render start command back to:
   startCommand: "python app.py"
   ```

2. **PWA rollback:**
   ```javascript
   // Revert API endpoint
   const API_ENDPOINT = 'https://old-url.onrender.com/api/translate';
   ```

3. **Keep V1 files:**
   - Don't delete `gesture_recognizer.py`
   - Don't delete `app.py`
   - Don't delete `data/gestures.json`

## 📊 Success Criteria

V2 is ready for production when:

- [x] All architecture components built
- [ ] Test script passes all tests
- [ ] FSL-105 dataset reprocessed
- [ ] Accuracy > 60% on test set (vs 40% in V1)
- [ ] End-to-end latency < 200ms
- [ ] PWA successfully sends pose landmarks
- [ ] No crashes or errors in 1-hour test session
- [ ] User testing shows improved experience

## 🎯 Timeline Estimate

- **Backend setup:** 30 minutes (tests + reprocessing)
- **PWA updates:** 1-2 hours (MediaPipe Pose integration)
- **Testing:** 2-3 hours (accuracy validation)
- **Parameter tuning:** 1-2 hours
- **Deployment:** 30 minutes

**Total:** 5-8 hours for complete migration

## 📝 Notes

- Keep V1 running during testing phase
- Document any issues encountered
- Save accuracy metrics for comparison
- Get user feedback before full rollout
- Consider A/B testing if possible

---

**Current Status:** ✅ Architecture built, ready for testing
**Next Step:** Run `python test_architecture.py`
