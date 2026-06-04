import json
import gzip
import numpy as np
from pathlib import Path
from fastdtw import fastdtw

class GestureRecognizerV3:
    """DTW-based gesture recognition with zero-masking support"""
    
    def __init__(self, confidence_threshold=0.70):
        """
        Args:
            confidence_threshold: Minimum similarity score to accept match (0-1)
        """
        self.templates = self.load_templates()
        self.confidence_threshold = confidence_threshold
    
    def load_templates(self):
        """Load gesture templates from database (supports compressed .gz files)"""
        # Try FIXED optimized compressed V3 templates first
        db_path_v3_fixed_gz = Path(__file__).parent / 'data' / 'gesture_templates_v3_fixed_optimized.json.gz'
        db_path_v3_fixed = Path(__file__).parent / 'data' / 'gesture_templates_v3_fixed_optimized.json'
        # Fallback to old paths
        db_path_v3_opt_gz = Path(__file__).parent / 'data' / 'gesture_templates_v3_optimized.json.gz'
        db_path_v2 = Path(__file__).parent / 'data' / 'gesture_templates_v2_filtered.json'
        
        # Try FIXED compressed
        if db_path_v3_fixed_gz.exists():
            print(f"[INFO] Loading FIXED V3 optimized compressed templates (54 features)")
            try:
                with gzip.open(db_path_v3_fixed_gz, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load compressed templates: {e}")
        
        # Try FIXED uncompressed
        if db_path_v3_fixed.exists():
            print(f"[INFO] Loading FIXED V3 optimized templates (54 features)")
            with open(db_path_v3_fixed, 'r') as f:
                return json.load(f)
        
        # Try old compressed (48 features - WRONG)
        if db_path_v3_opt_gz.exists():
            print(f"[WARN] Loading OLD V3 templates (48 features - WRONG!)")
            try:
                with gzip.open(db_path_v3_opt_gz, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load compressed templates: {e}")
        
        # Fallback to V2 (54 features but only 4 frames)
        if db_path_v2.exists():
            print(f"[WARN] Using V2 templates (4 frames each)")
            with open(db_path_v2, 'r') as f:
                return json.load(f)
        
        print(f"[ERROR] No template database found")
        return {}
    
    def recognize(self, gesture_frames):
        """
        Recognize gesture from feature sequence
        
        Args:
            gesture_frames: List of frame features from FeatureExtractor
        
        Returns:
            dict: {'gesture': name, 'confidence': score, 'all_scores': {...}}
        """
        MIN_FRAMES = 10  # Require minimum frames for reliable matching
        
        if not gesture_frames or len(gesture_frames) < MIN_FRAMES:
            print(f"[DEBUG] Too few frames: {len(gesture_frames) if gesture_frames else 0} < {MIN_FRAMES}")
            return {'gesture': None, 'confidence': 0, 'all_scores': {}}
        
        # Convert frames to feature vectors with masks
        feature_sequence, mask_sequence = self._frames_to_feature_vectors_with_mask(gesture_frames)
        
        if feature_sequence is None or len(feature_sequence) == 0:
            print(f"[DEBUG] No feature vectors extracted")
            return {'gesture': None, 'confidence': 0, 'all_scores': {}}
        
        print(f"[DEBUG] Processing {len(feature_sequence)} frames")
        
        # Compare against all templates
        scores = {}
        
        for gesture_name, template_data in self.templates.items():
            for template_idx, template in enumerate(template_data['templates']):
                template_sequence = np.array(template['feature_sequence'])
                
                # Compute mask on-the-fly from feature_sequence
                template_mask = self._compute_mask_from_features(template_sequence)
                
                # Create wrapped sequences (features + masks bundled)
                wrapped_sequence = [(feature_sequence[i], mask_sequence[i]) for i in range(len(feature_sequence))]
                wrapped_template = [(template_sequence[i], template_mask[i]) for i in range(len(template_sequence))]
                
                # DTW distance with masking
                distance, _ = fastdtw(
                    wrapped_sequence, 
                    wrapped_template, 
                    dist=self._wrapped_distance
                )
                
                # Convert distance to similarity with length penalty
                similarity = self._distance_to_similarity(
                    distance, 
                    len(feature_sequence),
                    len(template_sequence)
                )
                
                # Keep best score for this gesture
                if gesture_name not in scores or similarity > scores[gesture_name]:
                    scores[gesture_name] = similarity
        
        # Find best match
        if not scores:
            return {'gesture': None, 'confidence': 0, 'all_scores': {}}
        
        # Get top 5 for debugging
        top_5 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"[DEBUG] Top 5 matches:")
        for gesture, score in top_5:
            print(f"  {gesture}: {score:.3f}")
        
        best_gesture = max(scores, key=scores.get)
        best_score = scores[best_gesture]
        
        print(f"[DEBUG] Best: {best_gesture} ({best_score:.3f}), Threshold: {self.confidence_threshold}")
        
        # Apply confidence threshold
        if best_score < self.confidence_threshold:
            print(f"[DEBUG] Below threshold, rejecting")
            return {'gesture': None, 'confidence': best_score, 'all_scores': scores}
        
        return {
            'gesture': best_gesture,
            'confidence': best_score,
            'all_scores': scores
        }
    
    def _frames_to_feature_vectors_with_mask(self, gesture_frames):
        """Convert frame features to numerical vectors with masks for DTW"""
        vectors = []
        masks = []
        
        for frame in gesture_frames:
            # Determine which hand(s) to use
            left = frame.get('left_hand')
            right = frame.get('right_hand')
            
            if not left and not right:
                # No hands detected in this frame, skip it
                continue
            
            # Build vector and mask
            if left and right:
                # Two hands: concatenate features
                vector = self._hand_to_vector(left) + self._hand_to_vector(right)
                mask = [True] * 54  # All features valid
            elif left:
                # Left hand only: pad right side with zeros
                vector = self._hand_to_vector(left) + [0] * 27
                mask = [True] * 27 + [False] * 27  # Only left valid
            elif right:
                # Right hand only: pad left side with zeros
                vector = [0] * 27 + self._hand_to_vector(right)
                mask = [False] * 27 + [True] * 27  # Only right valid
            
            vectors.append(vector)
            masks.append(mask)
        
        if not vectors:
            return None, None
        
        return np.array(vectors), np.array(masks, dtype=bool)
    
    def _hand_to_vector(self, hand_features):
        """Convert hand features to flat numerical vector"""
        if hand_features is None:
            return [0] * 27
        
        vector = []
        
        # Wrist position (2 values)
        vector.extend(hand_features['wrist_pos'])
        
        # Joint angles (15 values)
        vector.extend(hand_features['joint_angles'])
        
        # Spread angles (4 values)
        vector.extend(hand_features['spread_angles'])
        
        # Fingertip distances (5 values)
        vector.extend(hand_features['fingertip_distances'])
        
        # Palm normal (1 value - just use Z component for simplicity)
        vector.append(hand_features['palm_normal'][2])
        
        return vector
    
    def _compute_mask_from_features(self, feature_sequence):
        """Compute mask from feature values (True if hand present, False if all zeros)"""
        masks = []
        for frame in feature_sequence:
            frame_arr = np.array(frame)
            # Left hand (features 0-26)
            left_has_data = np.any(frame_arr[:27] != 0)
            # Right hand (features 27-53)
            right_has_data = np.any(frame_arr[27:54] != 0)
            
            mask = [left_has_data] * 27 + [right_has_data] * 27
            masks.append(mask)
        
        return np.array(masks, dtype=bool)
    
    def _wrapped_distance(self, wrapped1, wrapped2):
        """Distance function for wrapped (feature, mask) tuples"""
        vec1, mask1 = wrapped1
        vec2, mask2 = wrapped2
        return self._masked_euclidean_dist(vec1, vec2, mask1, mask2)
    
    def _masked_euclidean_dist(self, vec1, vec2, mask1, mask2):
        """
        Euclidean distance between two feature vectors, only comparing valid features
        
        Args:
            vec1, vec2: Feature vectors (54 elements)
            mask1, mask2: Boolean masks (True = valid, False = zero-padded)
        
        Returns:
            float: Normalized distance
        """
        # Combine masks: only compare where BOTH are True
        valid_mask = mask1 & mask2
        
        num_valid = np.sum(valid_mask)
        
        if num_valid == 0:
            # No common features - return large distance
            return 100.0
        
        # Calculate distance only on valid features
        vec1_arr = np.array(vec1)
        vec2_arr = np.array(vec2)
        
        diff = (vec1_arr - vec2_arr) * valid_mask
        distance = np.linalg.norm(diff)
        
        # Normalize by number of valid features
        # This ensures one-handed vs two-handed comparisons are fair
        normalized_distance = distance / np.sqrt(num_valid)
        
        return normalized_distance
    
    def _euclidean_dist(self, vec1, vec2):
        """Standard Euclidean distance (for V2 templates without masking)"""
        return np.linalg.norm(np.array(vec1) - np.array(vec2))
    
    def _distance_to_similarity(self, distance, sequence_length, template_length):
        """
        Convert DTW distance to similarity score (0-1)
        
        Includes penalty for frame count mismatch to prevent short sequences
        from matching longer ones too easily.
        """
        # Normalize by sequence length
        normalized_distance = distance / (sequence_length + 1e-8)
        
        # Penalty for length mismatch
        length_ratio = abs(sequence_length - template_length) / max(sequence_length, template_length)
        length_penalty = length_ratio * 1.5
        
        # Apply penalty
        adjusted_distance = normalized_distance + length_penalty
        
        # Convert to similarity using exponential decay
        # Scaling factor 8 - sharper penalty for differences
        similarity = np.exp(-adjusted_distance / 8)
        
        return float(similarity)
    
    def get_stats(self):
        """Get statistics about loaded templates"""
        total_templates = sum(len(data['templates']) for data in self.templates.values())
        
        stats = {
            'total_templates': total_templates,
            'unique_signs': len(self.templates),
            'gestures': {}
        }
        
        for gesture_name, data in self.templates.items():
            template_count = len(data['templates'])
            
            # Calculate average frame count
            frame_counts = []
            for template in data['templates']:
                if 'stats' in template:
                    frame_counts.append(template['stats']['frame_count'])
                else:
                    frame_counts.append(len(template['feature_sequence']))
            
            avg_frames = sum(frame_counts) / len(frame_counts) if frame_counts else 0
            
            stats['gestures'][gesture_name] = {
                'template_count': template_count,
                'avg_frames': avg_frames
            }
        
        return stats
