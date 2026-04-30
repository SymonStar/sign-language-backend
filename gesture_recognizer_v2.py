import json
import numpy as np
from pathlib import Path
from fastdtw import fastdtw

class GestureRecognizerV2:
    """DTW-based gesture recognition using rich normalized features"""
    
    def __init__(self, confidence_threshold=0.75):
        """
        Args:
            confidence_threshold: Minimum similarity score to accept match (0-1)
        """
        self.templates = self.load_templates()
        self.confidence_threshold = confidence_threshold
    
    def load_templates(self):
        """Load gesture templates from database"""
        # Try filtered templates first (15 distinct signs)
        db_path_filtered = Path(__file__).parent / 'data' / 'gesture_templates_v2_filtered.json'
        db_path_full = Path(__file__).parent / 'data' / 'gesture_templates_v2.json'
        
        if db_path_filtered.exists():
            print(f"[INFO] Loading FILTERED templates (distinct signs only)")
            with open(db_path_filtered, 'r') as f:
                return json.load(f)
        elif db_path_full.exists():
            print(f"[WARN] Using FULL templates (105 signs - expect lower accuracy)")
            with open(db_path_full, 'r') as f:
                return json.load(f)
        
        print(f"[WARN] Template database not found")
        return {}
    
    def recognize(self, gesture_frames):
        """
        Recognize gesture from feature sequence
        
        Args:
            gesture_frames: List of frame features from FeatureExtractor
        
        Returns:
            dict: {'gesture': name, 'confidence': score, 'all_scores': {...}}
        """
        if not gesture_frames or len(gesture_frames) < 5:
            print(f"[DEBUG] Too few frames: {len(gesture_frames) if gesture_frames else 0}")
            return {'gesture': None, 'confidence': 0, 'all_scores': {}}
        
        # Convert frames to feature vectors
        feature_sequence = self._frames_to_feature_vectors(gesture_frames)
        
        if feature_sequence is None or len(feature_sequence) == 0:
            print(f"[DEBUG] No feature vectors extracted")
            return {'gesture': None, 'confidence': 0, 'all_scores': {}}
        
        print(f"[DEBUG] Processing {len(feature_sequence)} frames")
        
        # Compare against all templates
        scores = {}
        
        for gesture_name, template_data in self.templates.items():
            for template_idx, template in enumerate(template_data['templates']):
                template_sequence = np.array(template['feature_sequence'])
                
                # DTW distance
                distance, _ = fastdtw(feature_sequence, template_sequence, dist=self._euclidean_dist)
                
                # Convert distance to similarity score (0-1, higher is better)
                similarity = self._distance_to_similarity(distance, len(feature_sequence))
                
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
    
    def _frames_to_feature_vectors(self, gesture_frames):
        """Convert frame features to numerical vectors for DTW"""
        vectors = []
        
        for frame in gesture_frames:
            # Determine which hand(s) to use
            left = frame.get('left_hand')
            right = frame.get('right_hand')
            
            if left and right:
                # Two hands: concatenate features
                vector = self._hand_to_vector(left) + self._hand_to_vector(right)
            elif left:
                # Left hand only: pad right side with zeros
                vector = self._hand_to_vector(left) + [0] * 27
            elif right:
                # Right hand only: pad left side with zeros
                vector = [0] * 27 + self._hand_to_vector(right)
            else:
                # No hands detected in this frame
                continue
            
            vectors.append(vector)
        
        return np.array(vectors) if vectors else None
    
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
    
    def _euclidean_dist(self, vec1, vec2):
        """Euclidean distance between two feature vectors"""
        return np.linalg.norm(np.array(vec1) - np.array(vec2))
    
    def _distance_to_similarity(self, distance, sequence_length):
        """
        Convert DTW distance to similarity score (0-1)
        
        Normalized by sequence length and scaled to 0-1 range
        Scaling factor changed from 15 to 8 based on deep analysis:
        - /15 was too lenient (38% of signs passed threshold)
        - /8 provides better discrimination (only correct match passes)
        """
        # Normalize by sequence length
        normalized_distance = distance / (sequence_length + 1e-8)
        
        # Convert to similarity using exponential decay
        # Scaling factor 8 (was 15) - sharper penalty for differences
        similarity = np.exp(-normalized_distance / 8)
        
        return float(similarity)
    
    def add_template(self, gesture_name, gesture_frames):
        """Add a new template to the database"""
        feature_sequence = self._frames_to_feature_vectors(gesture_frames)
        
        if feature_sequence is None:
            return False
        
        if gesture_name not in self.templates:
            self.templates[gesture_name] = {'templates': []}
        
        self.templates[gesture_name]['templates'].append({
            'feature_sequence': feature_sequence.tolist()
        })
        
        return True
    
    def save_templates(self):
        """Save templates to disk"""
        db_path = Path(__file__).parent / 'data' / 'gesture_templates_v2.json'
        
        with open(db_path, 'w') as f:
            json.dump(self.templates, f, indent=2)
        
        print(f"[OK] Saved {len(self.templates)} gesture templates to {db_path}")
    
    def get_stats(self):
        """Get statistics about loaded templates"""
        stats = {
            'total_gestures': len(self.templates),
            'gestures': {}
        }
        
        for gesture_name, data in self.templates.items():
            stats['gestures'][gesture_name] = {
                'template_count': len(data['templates'])
            }
        
        return stats
