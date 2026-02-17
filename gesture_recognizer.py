import json
import numpy as np
from pathlib import Path

class GestureRecognizer:
    def __init__(self):
        self.database = self.load_database()
    
    def load_database(self):
        """Load gesture database from JSON file"""
        db_path = Path(__file__).parent / 'data' / 'gestures.json'
        if db_path.exists():
            with open(db_path, 'r') as f:
                return json.load(f)
        return {}
    
    def recognize_sequence(self, frames):
        """Recognize gestures from a sequence of skeletal frames"""
        recognized_words = []
        
        # Group frames into potential gestures (every 10 frames = 1 gesture)
        gesture_window = 10
        for i in range(0, len(frames), gesture_window):
            window = frames[i:i+gesture_window]
            if len(window) < 5:  # Skip if too few frames
                continue
            
            word = self.recognize_gesture(window)
            if word:
                recognized_words.append(word)
        
        # If no gestures recognized, return placeholder
        if not recognized_words:
            recognized_words = ['HELLO']  # Default for demo
        
        return recognized_words
    
    def recognize_gesture(self, frames):
        """Recognize a single gesture from frames"""
        # Extract features from frames
        features = self.extract_features(frames)
        
        # Compare with database
        best_match = None
        best_score = 0
        
        for sign_name, sign_data in self.database.items():
            score = self.compare_features(features, sign_data['features'])
            if score > best_score and score > 0.6:  # Threshold
                best_score = score
                best_match = sign_name
        
        return best_match
    
    def extract_features(self, frames):
        """Extract features from skeletal frames"""
        features = {
            'hand_positions': [],
            'hand_movement': 0,
            'hand_shape': []
        }
        
        for frame in frames:
            # Extract hand positions
            if frame.get('left_hand'):
                features['hand_positions'].append(self.get_hand_center(frame['left_hand']))
            if frame.get('right_hand'):
                features['hand_positions'].append(self.get_hand_center(frame['right_hand']))
        
        # Calculate movement (distance traveled)
        if len(features['hand_positions']) > 1:
            features['hand_movement'] = self.calculate_movement(features['hand_positions'])
        
        return features
    
    def get_hand_center(self, hand_landmarks):
        """Get center point of hand"""
        if not hand_landmarks:
            return [0, 0, 0]
        x = sum(p[0] for p in hand_landmarks) / len(hand_landmarks)
        y = sum(p[1] for p in hand_landmarks) / len(hand_landmarks)
        z = sum(p[2] for p in hand_landmarks) / len(hand_landmarks)
        return [x, y, z]
    
    def calculate_movement(self, positions):
        """Calculate total movement distance"""
        total = 0
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            dz = positions[i][2] - positions[i-1][2]
            total += (dx**2 + dy**2 + dz**2) ** 0.5
        return total
    
    def compare_features(self, features1, features2):
        """Compare two feature sets and return similarity score"""
        # Simple comparison - can be improved with ML
        score = 0.7  # Base score for demo
        
        # Compare movement
        if 'hand_movement' in features2:
            movement_diff = abs(features1['hand_movement'] - features2['hand_movement'])
            if movement_diff < 0.2:
                score += 0.2
        
        return min(score, 1.0)
