# Debug Tools Guide

## Why Accuracy Is Still Low

You've fixed the template format (54 features instead of 2), but accuracy is still around 50-65%. Here's why:

### Root Causes:
1. **Too many similar signs** - FSL-105 has 105 signs, many are visually similar
2. **Insufficient training data** - Only ~20 samples per sign (need 50-100)
3. **Features may not be discriminative enough** - All signs scoring 0.6-0.8 similarity
4. **Threshold too low** - 0.6 lets too many false positives through
5. **Scaling factor too lenient** - `/15` in similarity calculation makes everything look similar

## Debug Tools Created

### 1. Deep_Debug_Recognition.ipynb (Google Colab)
**Purpose**: Analyze templates offline to understand why signs look similar

**What it shows**:
- Raw feature vectors for each sign
- Feature statistics (mean, std, range)
- DTW distance breakdown by feature type
- Similarity score distribution
- Feature correlation analysis
- Pairwise sign comparison with visualizations

**How to use**:
```python
# 1. Upload to Google Colab
# 2. Mount Google Drive
# 3. Set path to FIXED templates
TEMPLATES_PATH = '/content/drive/MyDrive/fsl_processed/gesture_templates_v2_FIXED.json'
# 4. Run all cells
# 5. Analyze output
```

**What to look for**:
- Top 5 similarity range < 0.1 = signs too similar
- Above threshold > 20% = threshold too low
- Feature variance < 0.1 = features not discriminative
- Correlation analysis shows which features help distinguish signs

---

### 2. app_debug.py (Local Backend)
**Purpose**: Real-time debug endpoint for live captures

**What it shows**:
- Feature extraction details (first 3 frames)
- Feature vector statistics (shape, mean, std, range)
- DTW distances for ALL signs
- Feature-by-feature breakdown (wrist, angles, spread, fingertip)
- Top 10 matches with detailed scores
- Warnings if top 5 too close or too many above threshold

**How to use**:
```bash
# Terminal 1: Start debug server
cd C:\SignLanguageBackend
python app_debug.py
# Runs on http://localhost:5001

# Terminal 2: Keep main server running
python app_v2.py
# Runs on http://localhost:5000
```

**API Endpoint**:
```
POST http://localhost:5001/api/debug-recognize
Body: { "frames": [...] }
```

---

### 3. debug.html (Frontend)
**Purpose**: Visual interface for debug endpoint

**What it shows**:
- Live camera feed with MediaPipe overlay
- 2-second capture window
- Statistics cards:
  - Input frames
  - Feature frames
  - Features per frame
  - Feature mean/std
  - Top 5 range
  - Signs above threshold
- Best match with confidence
- Top 10 matches with:
  - Similarity score
  - Total distance
  - Normalized distance
  - Template frame count
  - Feature breakdown (8 feature types)
- Visual warnings if issues detected

**How to use**:
```bash
# 1. Start debug server (app_debug.py)
# 2. Open debug.html in browser
# 3. Click "Start Camera"
# 4. Sign a gesture
# 5. Click "Capture & Analyze"
# 6. Wait 2 seconds
# 7. View detailed results
```

---

## Interpreting Results

### Good Signs ✓
- Top 5 range > 0.15 (clear winner)
- Above threshold < 20% of total signs
- Feature std > 0.5 (good variance)
- Best match confidence > 0.75
- Feature breakdown shows clear differences

### Bad Signs ⚠️
- Top 5 range < 0.1 (all look similar)
- Above threshold > 30% of total signs
- Feature std < 0.3 (low variance)
- Best match confidence 0.6-0.7 (barely passing)
- Feature breakdown all similar values

---

## What Each Feature Type Means

### Left/Right Wrist (2 values each)
- X, Y position relative to face
- **High distance** = different hand position
- **Low distance** = same hand position

### Left/Right Angles (15 values each)
- Joint angles for 5 fingers (3 joints per finger)
- **High distance** = different hand shape
- **Low distance** = similar hand shape
- Most important for distinguishing signs!

### Left/Right Spread (4 values each)
- Angle between adjacent fingers
- **High distance** = different finger spacing
- **Low distance** = similar finger spacing

### Left/Right Fingertip (5 values each)
- Distance from each fingertip to wrist
- **High distance** = different finger extension
- **Low distance** = similar finger extension

---

## Troubleshooting Workflow

### Step 1: Run Deep_Debug_Recognition.ipynb
**Goal**: Understand template quality

**Questions to answer**:
1. Do templates have 54 features? (Check Part 1)
2. Are features different between signs? (Check Part 2)
3. What's the top 5 similarity range? (Check Part 3)
4. How many signs above threshold? (Check Part 4)
5. Which features correlate with similarity? (Check Part 5)

**Actions**:
- If top 5 range < 0.1 → Reduce vocabulary or change scaling
- If above threshold > 30% → Raise threshold
- If feature variance low → Add more features or collect better data

---

### Step 2: Test Live with debug.html
**Goal**: See what happens with YOUR signing

**Questions to answer**:
1. Are hands detected? (Check statistics)
2. How many feature frames captured? (Should be ~60)
3. What's the feature mean/std? (Compare to templates)
4. What's the top 5 range? (Should be > 0.1)
5. Which feature types have highest distances?

**Actions**:
- If hands not detected → Better lighting, clearer background
- If feature mean very different → Sign closer/farther from camera
- If top 5 range low → Your signing looks like multiple signs
- If specific feature type always low → That feature not helping

---

### Step 3: Compare Template vs Live
**Goal**: Find mismatch between training and testing

**Process**:
1. Run Deep_Debug on templates → Note feature statistics
2. Capture live gesture → Note feature statistics
3. Compare:
   - Feature mean (should be similar)
   - Feature std (should be similar)
   - Feature range (should overlap)

**Common issues**:
- Live mean much higher/lower → Camera distance different
- Live std much higher → Shaky hands, inconsistent signing
- Live range outside template range → Signing style different from dataset

---

## Recommended Fixes Based on Debug Results

### If Top 5 Range < 0.1
**Problem**: Can't distinguish between signs

**Fix 1**: Change scaling factor
```python
# In gesture_recognizer_v2.py, line ~120
# Change from:
similarity = np.exp(-normalized_distance / 15)
# To:
similarity = np.exp(-normalized_distance / 10)
```
Effect: Makes differences more pronounced

**Fix 2**: Reduce vocabulary
```python
# Use only filtered 13 signs
# Already done if gesture_templates_v2_filtered.json exists
```

---

### If Above Threshold > 30%
**Problem**: Threshold too low, accepting too many matches

**Fix**: Raise confidence threshold
```python
# In app_v2.py, line 16
# Change from:
gesture_recognizer = GestureRecognizerV2(confidence_threshold=0.6)
# To:
gesture_recognizer = GestureRecognizerV2(confidence_threshold=0.75)
```

---

### If Feature Variance Low
**Problem**: Features not discriminative

**Fix 1**: Add more features
- Hand orientation (roll, pitch, yaw)
- Movement trajectory
- Acceleration patterns
- Hand-to-face distance

**Fix 2**: Collect better data
- More samples per sign (50-100)
- More consistent signing
- Better hand detection

---

### If Specific Feature Type Always Low Distance
**Problem**: That feature type not helping

**Example**: If "left_wrist" always low distance for all signs
→ All signs have similar left hand position
→ That feature not useful for discrimination

**Fix**: Weight features differently or remove unhelpful features

---

## Expected Results After Fixes

### With Current Data (20 samples/sign):
- **Best case**: 60-70% accuracy
- **Realistic**: 50-60% accuracy
- **With 13 filtered signs**: 65-75% accuracy

### With More Data (50-100 samples/sign):
- **Best case**: 80-90% accuracy
- **Realistic**: 70-80% accuracy

### With Deep Learning (100+ samples/sign):
- **Best case**: 90-95% accuracy
- **Realistic**: 85-90% accuracy

---

## Quick Reference

### Start Debug Session
```bash
# Terminal 1
cd C:\SignLanguageBackend
python app_debug.py

# Terminal 2
cd C:\SignLanguagePWA
# Open debug.html in browser
```

### Check Template Quality
```python
# Upload Deep_Debug_Recognition.ipynb to Colab
# Run all cells
# Look for warnings
```

### Test Live Capture
```
1. Open debug.html
2. Start camera
3. Sign gesture
4. Capture & analyze
5. Check top 5 range
6. Check feature breakdown
```

### Adjust Parameters
```python
# Threshold: app_v2.py line 16
confidence_threshold=0.75

# Scaling: gesture_recognizer_v2.py line ~120
similarity = np.exp(-normalized_distance / 10)

# Vocabulary: Use gesture_templates_v2_filtered.json
```

---

## Files Created

```
C:\SignLanguageBackend\
├── Deep_Debug_Recognition.ipynb  ← Colab notebook for template analysis
├── app_debug.py                  ← Debug server with detailed logging
└── FIXES_APPLIED.md              ← Previous fixes documentation

C:\SignLanguagePWA\
├── debug.html                    ← Visual debug interface
└── css\style.css                 ← Camera size reverted to 70vh
```

---

## Next Steps

1. **Run Deep_Debug_Recognition.ipynb** in Colab
   - Analyze template quality
   - Identify problem areas
   - Get specific recommendations

2. **Test with debug.html**
   - Capture your signing
   - Compare to templates
   - See real-time feature breakdown

3. **Apply fixes based on results**
   - Adjust threshold if needed
   - Change scaling factor if needed
   - Reduce vocabulary if needed

4. **Iterate**
   - Test again
   - Measure improvement
   - Repeat until acceptable accuracy

The debug tools will show you EXACTLY why signs are getting confused!
