import numpy as np
from scipy.spatial.distance import euclidean

class FeatureExtractor:
    """Extracts rich normalized features from MediaPipe landmarks"""
    
    def __init__(self):
        self.prev_wrist_pos = {'left': None, 'right': None}
    
    def extract_frame_features(self, frame_data):
        """
        Extract per-frame feature vector from MediaPipe landmarks
        
        Args:
            frame_data: dict with 'left_hand', 'right_hand', 'pose' landmarks
        
        Returns:
            dict with normalized features for this frame
        """
        features = {
            'left_hand': None,
            'right_hand': None,
            'wrist_velocity': {'left': 0, 'right': 0}
        }
        
        # Get body anchors for normalization
        body_anchors = self._get_body_anchors(frame_data.get('pose'))
        
        if frame_data.get('left_hand'):
            features['left_hand'] = self._extract_hand_features(
                frame_data['left_hand'], 
                body_anchors, 
                'left'
            )
            features['wrist_velocity']['left'] = self._calculate_wrist_velocity(
                frame_data['left_hand'][0], 
                'left'
            )
        
        if frame_data.get('right_hand'):
            features['right_hand'] = self._extract_hand_features(
                frame_data['right_hand'], 
                body_anchors, 
                'right'
            )
            features['wrist_velocity']['right'] = self._calculate_wrist_velocity(
                frame_data['right_hand'][0], 
                'right'
            )
        
        return features
    
    def _get_body_anchors(self, pose_landmarks):
        """Extract face and shoulder anchors for coordinate normalization"""
        if not pose_landmarks or len(pose_landmarks) < 12:
            # Default anchors if pose not detected
            return {
                'face_center': np.array([0.5, 0.3, 0]),
                'shoulder_width': 0.3,
                'shoulder_center': np.array([0.5, 0.5, 0])
            }
        
        # MediaPipe Pose landmark indices
        # 0: nose, 7: left ear, 8: right ear
        # 11: left shoulder, 12: right shoulder
        nose = np.array(pose_landmarks[0])
        left_shoulder = np.array(pose_landmarks[11])
        right_shoulder = np.array(pose_landmarks[12])
        
        face_center = nose
        shoulder_center = (left_shoulder + right_shoulder) / 2
        shoulder_width = euclidean(left_shoulder[:2], right_shoulder[:2])
        
        return {
            'face_center': face_center,
            'shoulder_width': max(shoulder_width, 0.1),  # Prevent division by zero
            'shoulder_center': shoulder_center
        }
    
    def _extract_hand_features(self, hand_landmarks, body_anchors, hand_side):
        """Extract all features for one hand"""
        if not hand_landmarks or len(hand_landmarks) < 21:
            return None
        
        landmarks = np.array(hand_landmarks)
        
        # 1. Body-relative wrist position
        wrist = landmarks[0]
        normalized_wrist = self._normalize_position(wrist, body_anchors)
        
        # 2. Finger joint angles (15 angles: 3 per finger)
        joint_angles = self._calculate_joint_angles(landmarks)
        
        # 3. Finger spread angles (4 angles between adjacent fingers)
        spread_angles = self._calculate_spread_angles(landmarks)
        
        # 4. Fingertip-to-wrist distances (5 distances, normalized to hand size)
        fingertip_distances = self._calculate_fingertip_distances(landmarks)
        
        # 5. Palm normal vector (orientation)
        palm_normal = self._calculate_palm_normal(landmarks)
        
        return {
            'wrist_pos': normalized_wrist.tolist(),
            'joint_angles': joint_angles,
            'spread_angles': spread_angles,
            'fingertip_distances': fingertip_distances,
            'palm_normal': palm_normal.tolist()
        }
    
    def _normalize_position(self, position, body_anchors):
        """Normalize position to body-relative coordinate space"""
        pos = np.array(position)
        face = body_anchors['face_center']
        shoulder_width = body_anchors['shoulder_width']
        
        # Position relative to face, scaled by shoulder width
        normalized = (pos - face) / shoulder_width
        
        return normalized[:2]  # Return only X, Y (Z is unreliable)
    
    def _calculate_joint_angles(self, landmarks):
        """
        Calculate 15 finger joint angles (3 per finger)
        Uses dot product of adjacent bone vectors
        """
        # Finger landmark indices: [base, pip, dip, tip]
        fingers = {
            'thumb': [1, 2, 3, 4],
            'index': [5, 6, 7, 8],
            'middle': [9, 10, 11, 12],
            'ring': [13, 14, 15, 16],
            'pinky': [17, 18, 19, 20]
        }
        
        angles = []
        
        for finger_name, indices in fingers.items():
            # Calculate 3 joint angles per finger
            for i in range(len(indices) - 2):
                p1 = landmarks[indices[i]]
                p2 = landmarks[indices[i + 1]]
                p3 = landmarks[indices[i + 2]]
                
                angle = self._angle_between_points(p1, p2, p3)
                angles.append(angle)
        
        return angles
    
    def _angle_between_points(self, p1, p2, p3):
        """Calculate angle at p2 formed by p1-p2-p3"""
        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)
        
        # Normalize vectors
        v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
        v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
        
        # Dot product gives cosine of angle
        cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return float(angle)
    
    def _calculate_spread_angles(self, landmarks):
        """Calculate 4 angles between adjacent fingers at base"""
        # Base knuckle indices
        bases = [5, 9, 13, 17]  # index, middle, ring, pinky
        wrist = landmarks[0]
        
        angles = []
        
        for i in range(len(bases) - 1):
            p1 = landmarks[bases[i]]
            p2 = landmarks[bases[i + 1]]
            
            # Vectors from wrist to each base
            v1 = np.array(p1) - np.array(wrist)
            v2 = np.array(p2) - np.array(wrist)
            
            # Angle between vectors
            v1_norm = v1 / (np.linalg.norm(v1) + 1e-8)
            v2_norm = v2 / (np.linalg.norm(v2) + 1e-8)
            
            cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
            angle = np.arccos(cos_angle)
            
            angles.append(float(angle))
        
        return angles
    
    def _calculate_fingertip_distances(self, landmarks):
        """Calculate normalized distances from fingertips to wrist"""
        wrist = landmarks[0]
        fingertips = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky
        
        # Hand size reference: distance from wrist to middle finger base
        middle_base = landmarks[9]
        hand_size = euclidean(wrist, middle_base)
        
        distances = []
        for tip_idx in fingertips:
            tip = landmarks[tip_idx]
            dist = euclidean(wrist, tip)
            normalized_dist = dist / (hand_size + 1e-8)
            distances.append(float(normalized_dist))
        
        return distances
    
    def _calculate_palm_normal(self, landmarks):
        """
        Calculate palm normal vector (direction palm is facing)
        Uses cross product of two palm vectors
        """
        wrist = np.array(landmarks[0])
        index_base = np.array(landmarks[5])
        pinky_base = np.array(landmarks[17])
        
        # Two vectors across the palm
        v1 = index_base - wrist
        v2 = pinky_base - wrist
        
        # Cross product gives normal vector
        normal = np.cross(v1, v2)
        
        # Normalize
        normal_normalized = normal / (np.linalg.norm(normal) + 1e-8)
        
        return normal_normalized
    
    def _calculate_wrist_velocity(self, current_wrist, hand_side):
        """Calculate wrist velocity magnitude for segmentation"""
        if self.prev_wrist_pos[hand_side] is None:
            self.prev_wrist_pos[hand_side] = current_wrist
            return 0.0
        
        prev = np.array(self.prev_wrist_pos[hand_side])
        curr = np.array(current_wrist)
        
        velocity = euclidean(prev[:2], curr[:2])  # Use only X, Y
        
        self.prev_wrist_pos[hand_side] = current_wrist
        
        return float(velocity)
    
    def reset_velocity_tracking(self):
        """Reset velocity tracking between gestures"""
        self.prev_wrist_pos = {'left': None, 'right': None}
