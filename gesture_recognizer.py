import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

class GestureRecognizer:
    def __init__(self):
        self.database = self.load_database()
        self.previous_gesture = None
        self.gesture_cooldown = 0
    
    def load_database(self):
        db_path = Path(__file__).parent / 'data' / 'gestures.json'
        if db_path.exists():
            with open(db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def recognize_sequence(self, frames):
        recognized_words = []
        
        # Use sliding window with overlap
        window_size = 15
        step_size = 10
        
        for i in range(0, len(frames) - window_size + 1, step_size):
            window = frames[i:i+window_size]
            
            word = self.recognize_gesture(window)
            
            # Avoid duplicate consecutive words
            if word and (not recognized_words or word != recognized_words[-1]):
                recognized_words.append(word)
        
        if not recognized_words:
            recognized_words = ['HELLO']
        
        return recognized_words
    
    def recognize_gesture(self, frames):
        features = self.extract_advanced_features(frames)
        
        if not features:
            return None
        
        best_match = None
        best_score = 0
        
        for sign_name, sign_data in self.database.items():
            score = self.advanced_compare(features, sign_data['features'])
            
            if score > best_score and score > 0.6:
                best_score = score
                best_match = sign_name
        
        return best_match
    
    def extract_advanced_features(self, frames):
        if not frames or len(frames) < 3:
            return None
        
        features = {
            'hand_trajectory': {'left': [], 'right': []},
            'hand_velocity': {'left': 0, 'right': 0},
            'hand_acceleration': {'left': 0, 'right': 0},
            'hand_shape_sequence': [],
            'hand_orientation': {'left': [], 'right': []},
            'hand_height_avg': 0,
            'hand_distance_avg': 0,
            'two_hands': False,
            'dominant_hand': None,
            'movement_direction': None,
            'movement_smoothness': 0,
            'finger_extension': []
        }
        
        left_positions = []
        right_positions = []
        
        for frame in frames:
            # Track hand trajectories
            if frame.get('left_hand'):
                left_center = self.get_hand_center(frame['left_hand'])
                left_positions.append(left_center)
                features['hand_trajectory']['left'].append(left_center)
                
                # Hand orientation
                orientation = self.calculate_hand_orientation(frame['left_hand'])
                features['hand_orientation']['left'].append(orientation)
                
                # Hand shape
                shape = self.detect_hand_shape_detailed(frame['left_hand'])
                features['hand_shape_sequence'].append(('left', shape))
                
                # Finger extension
                extension = self.calculate_finger_extension(frame['left_hand'])
                features['finger_extension'].append(extension)
            
            if frame.get('right_hand'):
                right_center = self.get_hand_center(frame['right_hand'])
                right_positions.append(right_center)
                features['hand_trajectory']['right'].append(right_center)
                
                orientation = self.calculate_hand_orientation(frame['right_hand'])
                features['hand_orientation']['right'].append(orientation)
                
                shape = self.detect_hand_shape_detailed(frame['right_hand'])
                features['hand_shape_sequence'].append(('right', shape))
                
                extension = self.calculate_finger_extension(frame['right_hand'])
                features['finger_extension'].append(extension)
        
        # Calculate velocities and accelerations
        if len(left_positions) > 1:
            features['hand_velocity']['left'] = self.calculate_velocity(left_positions)
            features['hand_acceleration']['left'] = self.calculate_acceleration(left_positions)
        
        if len(right_positions) > 1:
            features['hand_velocity']['right'] = self.calculate_velocity(right_positions)
            features['hand_acceleration']['right'] = self.calculate_acceleration(right_positions)
        
        # Two hands detection
        features['two_hands'] = len(left_positions) > 0 and len(right_positions) > 0
        
        # Dominant hand
        if len(left_positions) > len(right_positions):
            features['dominant_hand'] = 'left'
        elif len(right_positions) > len(left_positions):
            features['dominant_hand'] = 'right'
        else:
            features['dominant_hand'] = 'both'
        
        # Average hand height
        all_positions = left_positions + right_positions
        if all_positions:
            features['hand_height_avg'] = np.mean([p[1] for p in all_positions])
        
        # Hand distance (if two hands)
        if left_positions and right_positions:
            features['hand_distance_avg'] = self.calculate_avg_hand_distance(left_positions, right_positions)
        
        # Movement direction
        if len(all_positions) > 2:
            features['movement_direction'] = self.calculate_movement_direction(all_positions)
        
        # Movement smoothness
        if len(all_positions) > 3:
            features['movement_smoothness'] = self.calculate_smoothness(all_positions)
        
        return features
    
    def get_hand_center(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 21:
            return [0, 0, 0]
        # Use wrist (0) and middle finger base (9) for center
        wrist = hand_landmarks[0]
        middle_base = hand_landmarks[9]
        return [
            (wrist[0] + middle_base[0]) / 2,
            (wrist[1] + middle_base[1]) / 2,
            (wrist[2] + middle_base[2]) / 2
        ]
    
    def calculate_hand_orientation(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 21:
            return 0
        
        # Vector from wrist to middle finger tip
        wrist = np.array(hand_landmarks[0])
        middle_tip = np.array(hand_landmarks[12])
        
        vector = middle_tip - wrist
        # Angle in radians
        angle = np.arctan2(vector[1], vector[0])
        return angle
    
    def detect_hand_shape_detailed(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 21:
            return 'unknown'
        
        # Fingertips and bases
        fingers = {
            'thumb': (4, 2),
            'index': (8, 5),
            'middle': (12, 9),
            'ring': (16, 13),
            'pinky': (20, 17)
        }
        
        extended = []
        palm_base = hand_landmarks[0]
        
        for finger_name, (tip_idx, base_idx) in fingers.items():
            tip = hand_landmarks[tip_idx]
            base = hand_landmarks[base_idx]
            
            # Check if tip is further from palm than base
            tip_dist = euclidean(tip[:2], palm_base[:2])
            base_dist = euclidean(base[:2], palm_base[:2])
            
            if tip_dist > base_dist * 1.2:
                extended.append(finger_name)
        
        # Classify based on extended fingers
        num_extended = len(extended)
        
        if num_extended == 0:
            return 'fist'
        elif num_extended == 5:
            return 'open'
        elif num_extended == 1:
            if 'index' in extended:
                return 'point'
            elif 'thumb' in extended:
                return 'thumbs_up'
        elif num_extended == 2:
            if 'index' in extended and 'middle' in extended:
                return 'peace'
            elif 'index' in extended and 'thumb' in extended:
                return 'L_shape'
        elif num_extended == 3:
            return 'three'
        
        return 'partial'
    
    def calculate_finger_extension(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 21:
            return 0
        
        fingertips = [4, 8, 12, 16, 20]
        palm_base = hand_landmarks[0]
        
        total_extension = 0
        for tip_idx in fingertips:
            tip = hand_landmarks[tip_idx]
            dist = euclidean(tip[:2], palm_base[:2])
            total_extension += dist
        
        return total_extension / 5
    
    def calculate_velocity(self, positions):
        if len(positions) < 2:
            return 0
        
        velocities = []
        for i in range(1, len(positions)):
            dist = euclidean(positions[i], positions[i-1])
            velocities.append(dist)
        
        return np.mean(velocities)
    
    def calculate_acceleration(self, positions):
        if len(positions) < 3:
            return 0
        
        velocities = []
        for i in range(1, len(positions)):
            dist = euclidean(positions[i], positions[i-1])
            velocities.append(dist)
        
        accelerations = []
        for i in range(1, len(velocities)):
            accel = abs(velocities[i] - velocities[i-1])
            accelerations.append(accel)
        
        return np.mean(accelerations)
    
    def calculate_avg_hand_distance(self, left_positions, right_positions):
        min_len = min(len(left_positions), len(right_positions))
        distances = []
        
        for i in range(min_len):
            dist = euclidean(left_positions[i], right_positions[i])
            distances.append(dist)
        
        return np.mean(distances) if distances else 0
    
    def calculate_movement_direction(self, positions):
        if len(positions) < 2:
            return None
        
        start = np.array(positions[0])
        end = np.array(positions[-1])
        
        vector = end - start
        
        # Classify direction
        if abs(vector[0]) > abs(vector[1]):
            return 'horizontal' if vector[0] > 0 else 'horizontal_left'
        else:
            return 'vertical_up' if vector[1] < 0 else 'vertical_down'
    
    def calculate_smoothness(self, positions):
        if len(positions) < 4:
            return 0
        
        # Calculate jerk (rate of change of acceleration)
        velocities = []
        for i in range(1, len(positions)):
            dist = euclidean(positions[i], positions[i-1])
            velocities.append(dist)
        
        accelerations = []
        for i in range(1, len(velocities)):
            accel = velocities[i] - velocities[i-1]
            accelerations.append(accel)
        
        jerks = []
        for i in range(1, len(accelerations)):
            jerk = abs(accelerations[i] - accelerations[i-1])
            jerks.append(jerk)
        
        # Lower jerk = smoother movement
        return 1 / (1 + np.mean(jerks)) if jerks else 0
    
    def advanced_compare(self, features1, features2):
        score = 0.0
        weights = {
            'hand_shape': 0.25,
            'velocity': 0.15,
            'height': 0.10,
            'two_hands': 0.10,
            'hand_distance': 0.10,
            'direction': 0.15,
            'smoothness': 0.05,
            'orientation': 0.10
        }
        
        # Hand shape comparison
        if 'hand_shape' in features2:
            shape_match = sum(1 for hand, shape in features1['hand_shape_sequence'] 
                            if shape == features2['hand_shape'])
            shape_score = shape_match / len(features1['hand_shape_sequence']) if features1['hand_shape_sequence'] else 0
            score += shape_score * weights['hand_shape']
        
        # Velocity comparison
        if 'hand_velocity' in features2:
            avg_velocity = np.mean([features1['hand_velocity']['left'], features1['hand_velocity']['right']])
            velocity_diff = abs(avg_velocity - features2.get('hand_movement', 0))
            velocity_score = max(0, 1 - velocity_diff / 0.5)
            score += velocity_score * weights['velocity']
        
        # Height comparison
        if 'hand_height' in features2:
            height_diff = abs(features1['hand_height_avg'] - features2['hand_height'])
            height_score = max(0, 1 - height_diff / 0.3)
            score += height_score * weights['height']
        
        # Two hands check
        if 'two_hands' in features2:
            if features1['two_hands'] == features2['two_hands']:
                score += weights['two_hands']
        
        # Hand distance
        if 'hand_distance' in features2 and features1['two_hands']:
            dist_diff = abs(features1['hand_distance_avg'] - features2['hand_distance'])
            dist_score = max(0, 1 - dist_diff / 0.5)
            score += dist_score * weights['hand_distance']
        
        # Movement direction
        if 'movement_direction' in features2:
            if features1['movement_direction'] == features2.get('movement_direction'):
                score += weights['direction']
        
        # Smoothness (higher is better for most signs)
        if features1['movement_smoothness'] > 0.5:
            score += weights['smoothness']
        
        return score
