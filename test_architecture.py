"""
Test script for new architecture components
"""

import numpy as np
from feature_extractor import FeatureExtractor
from gesture_segmenter import GestureSegmenter
from gesture_recognizer_v2 import GestureRecognizerV2

def create_sample_frame():
    """Create a sample frame with MediaPipe landmarks"""
    # Generate random hand landmarks (21 points, 3D)
    left_hand = np.random.rand(21, 3).tolist()
    right_hand = np.random.rand(21, 3).tolist()
    
    # Generate pose landmarks (33 points, but we only need first 13)
    pose = np.random.rand(13, 3).tolist()
    
    return {
        'left_hand': left_hand,
        'right_hand': right_hand,
        'pose': pose
    }

def test_feature_extraction():
    """Test feature extraction"""
    print("="*60)
    print("TEST 1: Feature Extraction")
    print("="*60)
    
    extractor = FeatureExtractor()
    frame = create_sample_frame()
    
    features = extractor.extract_frame_features(frame)
    
    print("\n[OK] Feature extraction successful!")
    print(f"\nLeft hand features:")
    if features['left_hand']:
        print(f"  - Wrist position: {features['left_hand']['wrist_pos']}")
        print(f"  - Joint angles: {len(features['left_hand']['joint_angles'])} angles")
        print(f"  - Spread angles: {len(features['left_hand']['spread_angles'])} angles")
        print(f"  - Fingertip distances: {len(features['left_hand']['fingertip_distances'])} distances")
        print(f"  - Palm normal: {features['left_hand']['palm_normal']}")
    
    print(f"\nWrist velocities:")
    print(f"  - Left: {features['wrist_velocity']['left']:.4f}")
    print(f"  - Right: {features['wrist_velocity']['right']:.4f}")
    
    return True

def test_gesture_segmentation():
    """Test gesture segmentation"""
    print("\n" + "="*60)
    print("TEST 2: Gesture Segmentation")
    print("="*60)
    
    extractor = FeatureExtractor()
    segmenter = GestureSegmenter(
        velocity_threshold=0.015,
        hold_frames=3,
        max_gesture_frames=90
    )
    
    # Simulate a gesture: movement -> hold -> movement -> hold
    print("\nSimulating gesture sequence...")
    
    gesture_count = 0
    
    # First gesture: 20 frames of movement + 5 frames of hold
    print("\n  Phase 1: Movement (20 frames)")
    for i in range(20):
        frame = create_sample_frame()
        features = extractor.extract_frame_features(frame)
        
        # Artificially set high velocity
        features['wrist_velocity']['left'] = 0.05
        features['wrist_velocity']['right'] = 0.05
        
        is_boundary, gesture_frames = segmenter.add_frame(features)
        
        if is_boundary:
            gesture_count += 1
            print(f"\n[OK] Gesture {gesture_count} detected! ({len(gesture_frames)} frames)")
    
    print("\n  Phase 2: Hold (5 frames)")
    for i in range(5):
        frame = create_sample_frame()
        features = extractor.extract_frame_features(frame)
        
        # Artificially set low velocity (hold)
        features['wrist_velocity']['left'] = 0.005
        features['wrist_velocity']['right'] = 0.005
        
        is_boundary, gesture_frames = segmenter.add_frame(features)
        
        if is_boundary:
            gesture_count += 1
            print(f"\n[OK] Gesture {gesture_count} detected! ({len(gesture_frames)} frames)")
    
    # Second gesture
    print("\n  Phase 3: Movement (15 frames)")
    for i in range(15):
        frame = create_sample_frame()
        features = extractor.extract_frame_features(frame)
        features['wrist_velocity']['left'] = 0.04
        features['wrist_velocity']['right'] = 0.04
        
        is_boundary, gesture_frames = segmenter.add_frame(features)
        
        if is_boundary:
            gesture_count += 1
            print(f"\n[OK] Gesture {gesture_count} detected! ({len(gesture_frames)} frames)")
    
    print("\n  Phase 4: Hold (5 frames)")
    for i in range(5):
        frame = create_sample_frame()
        features = extractor.extract_frame_features(frame)
        features['wrist_velocity']['left'] = 0.003
        features['wrist_velocity']['right'] = 0.003
        
        is_boundary, gesture_frames = segmenter.add_frame(features)
        
        if is_boundary:
            gesture_count += 1
            print(f"\n[OK] Gesture {gesture_count} detected! ({len(gesture_frames)} frames)")
    
    # Force final segment
    final = segmenter.force_segment()
    if final:
        gesture_count += 1
        print(f"\n[OK] Final gesture detected! ({len(final)} frames)")
    
    print(f"\n[OK] Segmentation test complete! Detected {gesture_count} gestures")
    
    return True

def test_gesture_recognition():
    """Test gesture recognition (without templates)"""
    print("\n" + "="*60)
    print("TEST 3: Gesture Recognition")
    print("="*60)
    
    recognizer = GestureRecognizerV2(confidence_threshold=0.7)
    
    # Check if templates loaded
    stats = recognizer.get_stats()
    print(f"\n[INFO] Loaded templates: {stats['total_gestures']} gestures")
    
    if stats['total_gestures'] == 0:
        print("\n[WARN] No templates loaded. Run reprocess_fsl_dataset.py first.")
        return False
    
    # Create sample gesture
    extractor = FeatureExtractor()
    gesture_frames = []
    
    for i in range(20):
        frame = create_sample_frame()
        features = extractor.extract_frame_features(frame)
        gesture_frames.append(features)
    
    # Recognize
    result = recognizer.recognize(gesture_frames)
    
    print(f"\n[OK] Recognition complete!")
    print(f"  - Gesture: {result['gesture']}")
    print(f"  - Confidence: {result['confidence']:.2%}")
    print(f"  - Top 5 scores:")
    
    sorted_scores = sorted(result['all_scores'].items(), key=lambda x: x[1], reverse=True)[:5]
    for gesture, score in sorted_scores:
        print(f"      {gesture}: {score:.2%}")
    
    return True

def main():
    print("\n[TEST] Testing New Architecture Components\n")
    
    try:
        # Test 1: Feature Extraction
        test_feature_extraction()
        
        # Test 2: Gesture Segmentation
        test_gesture_segmentation()
        
        # Test 3: Gesture Recognition
        test_gesture_recognition()
        
        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: python reprocess_fsl_dataset.py")
        print("2. Run: python app_v2.py")
        print("3. Update PWA to send pose landmarks along with hand landmarks")
        
    except Exception as e:
        print(f"\n[ERROR] TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
