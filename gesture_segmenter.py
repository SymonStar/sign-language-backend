import numpy as np
from collections import deque

class GestureSegmenter:
    """Segments continuous signing stream into individual gestures using velocity-based hold detection"""
    
    def __init__(self, velocity_threshold=0.015, hold_frames=3, max_gesture_frames=90):
        """
        Args:
            velocity_threshold: Wrist velocity below this = hold (default 0.015)
            hold_frames: Number of consecutive low-velocity frames to trigger segmentation (default 3 = ~100ms at 30fps)
            max_gesture_frames: Maximum frames per gesture (default 90 = 3 seconds at 30fps)
        """
        self.velocity_threshold = velocity_threshold
        self.hold_frames = hold_frames
        self.max_gesture_frames = max_gesture_frames
        
        self.frame_buffer = []
        self.velocity_buffer = deque(maxlen=hold_frames)
        self.in_gesture = False
    
    def add_frame(self, frame_features):
        """
        Add a frame and check if gesture boundary detected
        
        Args:
            frame_features: Output from FeatureExtractor.extract_frame_features()
        
        Returns:
            tuple: (is_boundary, gesture_frames)
                - is_boundary: True if gesture completed
                - gesture_frames: List of frames if boundary detected, else None
        """
        # Get maximum wrist velocity from both hands
        left_vel = frame_features['wrist_velocity']['left']
        right_vel = frame_features['wrist_velocity']['right']
        max_velocity = max(left_vel, right_vel)
        
        # Add to buffers
        self.velocity_buffer.append(max_velocity)
        self.frame_buffer.append(frame_features)
        
        # Check if we're in a hold (low velocity)
        is_hold = self._is_holding()
        
        # Gesture boundary detection logic
        if is_hold and self.in_gesture and len(self.frame_buffer) >= 10:
            # Hold detected after movement = gesture complete
            gesture_frames = self.frame_buffer[:-self.hold_frames]  # Exclude hold frames
            self._reset()
            return True, gesture_frames
        
        elif max_velocity > self.velocity_threshold:
            # Movement detected = in gesture
            self.in_gesture = True
        
        # Force segmentation if gesture too long
        if len(self.frame_buffer) >= self.max_gesture_frames:
            gesture_frames = self.frame_buffer.copy()
            self._reset()
            return True, gesture_frames
        
        return False, None
    
    def _is_holding(self):
        """Check if currently in a hold (low velocity for hold_frames consecutive frames)"""
        if len(self.velocity_buffer) < self.hold_frames:
            return False
        
        # All recent frames below threshold = hold
        return all(v < self.velocity_threshold for v in self.velocity_buffer)
    
    def _reset(self):
        """Reset buffers for next gesture"""
        self.frame_buffer = []
        self.velocity_buffer.clear()
        self.in_gesture = False
    
    def force_segment(self):
        """Force segmentation (e.g., at end of video)"""
        if len(self.frame_buffer) >= 10:
            gesture_frames = self.frame_buffer.copy()
            self._reset()
            return gesture_frames
        
        self._reset()
        return None
    
    def get_buffer_info(self):
        """Get current buffer state for debugging"""
        return {
            'frame_count': len(self.frame_buffer),
            'in_gesture': self.in_gesture,
            'recent_velocities': list(self.velocity_buffer),
            'is_holding': self._is_holding()
        }
