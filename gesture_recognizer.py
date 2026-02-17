import json
import numpy as np
from pathlib import Path

class GestureRecognizer:
    def __init__(self):
        self.database = self.load_database()
    
    def load_database(self):
        db_path = Path(__file__).parent / 'data' / 'gestures.json'
        if db_path.exists():
            with open(db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def recognize_sequence(self, frames):
        recognized_words = []
        
        gesture_window = 10
        for i in range(0, len(frames), gesture_window):
            window = frames[i:i+gesture_window]
            if len(window) < 5:
                continue
            
            word = self.recognize_gesture(window)
            if word and (not recognized_words or word != recognized_words[-1]):
                recognized_words.append(word)
        
        if not recognized_words:
            recognized_words = ['HELLO']
        
        return recognized_words
    
    def recognize_gesture(self, frames):
        features = self.extract_features(frames)
        
        best_match = None
        best_score = 0
        
        for sign_name, sign_data in self.database.items():
            score = self.compare_features(features, sign_data['features'])
            if score > best_score and score > 0.5:
                best_score = score
                best_match = sign_name
        
        return best_match
    
    def extract_features(self, frames):
        features = {
            'hand_positions': [],
            'hand_movement': 0,
            'hand_height': 0,
            'hand_distance': 0,
            'hand_shape': '',
            'two_hands': False,
            'face_present': False
        }
        
        left_positions = []
        right_positions = []
        
        for frame in frames:
            if frame.get('left_hand'):
                left_pos = self.get_hand_center(frame['left_hand'])
                left_positions.append(left_pos)
                features['hand_shape'] = self.detect_hand_shape(frame['left_hand'])
            
            if frame.get('right_hand'):
                right_pos = self.get_hand_center(frame['right_hand'])
                right_positions.append(right_pos)
                if not features['hand_shape']:
                    features['hand_shape'] = self.detect_hand_shape(frame['right_hand'])
            
            if frame.get('face_landmarks'):
                features['face_present'] = True
        
        features['two_hands'] = len(left_positions) > 0 and len(right_positions) > 0
        
        all_positions = left_positions + right_positions
        if all_positions:
            features['hand_movement'] = self.calculate_movement(all_positions)
            features['hand_height'] = np.mean([p[1] for p in all_positions])
        
        if left_positions and right_positions:
            features['hand_distance'] = self.calculate_hand_distance(left_positions, right_positions)
        
        return features
    
    def get_hand_center(self, hand_landmarks):
        if not hand_landmarks:
            return [0, 0, 0]
        x = sum(p[0] for p in hand_landmarks) / len(hand_landmarks)
        y = sum(p[1] for p in hand_landmarks) / len(hand_landmarks)
        z = sum(p[2] for p in hand_landmarks) / len(hand_landmarks)
        return [x, y, z]
    
    def detect_hand_shape(self, hand_landmarks):
        if not hand_landmarks or len(hand_landmarks) < 21:
            return 'unknown'
        
        fingertips = [4, 8, 12, 16, 20]
        palm_base = hand_landmarks[0]
        
        extended_fingers = 0
        for tip_idx in fingertips:
            tip = hand_landmarks[tip_idx]
            if tip[1] < palm_base[1] - 0.05:
                extended_fingers += 1
        
        if extended_fingers == 0:
            return 'fist'
        elif extended_fingers == 5:
            return 'open'
        elif extended_fingers == 1:
            return 'point'
        elif extended_fingers == 2:
            return 'peace'
        else:
            return 'partial'
    
    def calculate_movement(self, positions):
        if len(positions) < 2:
            return 0
        
        total = 0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            dz = positions[i][2] - positions[i-1][2]
            total += (dx**2 + dy**2 + dz**2) ** 0.5
        return total
    
    def calculate_hand_distance(self, left_positions, right_positions):
        if not left_positions or not right_positions:
            return 0
        
        left_avg = np.mean(left_positions, axis=0)
        right_avg = np.mean(right_positions, axis=0)
        
        dx = left_avg[0] - right_avg[0]
        dy = left_avg[1] - right_avg[1]
        dz = left_avg[2] - right_avg[2]
        
        return (dx**2 + dy**2 + dz**2) ** 0.5
    
    def compare_features(self, features1, features2):
        score = 0.0
        total_weight = 0.0
        
        # Movement comparison (weight: 0.3)
        if 'hand_movement' in features2:
            movement_diff = abs(features1['hand_movement'] - features2['hand_movement'])
            movement_score = max(0, 1 - movement_diff / 0.5)
            score += movement_score * 0.3
            total_weight += 0.3
        
        # Hand shape comparison (weight: 0.3)
        if 'hand_shape' in features2:
            if features1['hand_shape'] == features2['hand_shape']:
                score += 0.3
            total_weight += 0.3
        
        # Height comparison (weight: 0.2)
        if 'hand_height' in features2:
            height_diff = abs(features1['hand_height'] - features2['hand_height'])
            height_score = max(0, 1 - height_diff / 0.3)
            score += height_score * 0.2
            total_weight += 0.2
        
        # Two hands check (weight: 0.1)
        if 'two_hands' in features2:
            if features1['two_hands'] == features2['two_hands']:
                score += 0.1
            total_weight += 0.1
        
        # Hand distance (weight: 0.1)
        if 'hand_distance' in features2 and features1['two_hands']:
            dist_diff = abs(features1['hand_distance'] - features2['hand_distance'])
            dist_score = max(0, 1 - dist_diff / 0.5)
            score += dist_score * 0.1
            total_weight += 0.1
        
        return score / total_weight if total_weight > 0 else 0
