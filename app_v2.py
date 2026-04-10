from flask import Flask, request, jsonify
from flask_cors import CORS
from feature_extractor import FeatureExtractor
from gesture_segmenter import GestureSegmenter
from gesture_recognizer_v2 import GestureRecognizerV2
from translator import Translator
import os

app = Flask(__name__)
CORS(app)

# Initialize new architecture components
feature_extractor = FeatureExtractor()
gesture_segmenter = GestureSegmenter(
    velocity_threshold=0.015,
    hold_frames=3,
    max_gesture_frames=90
)
gesture_recognizer = GestureRecognizerV2(confidence_threshold=0.7)
translator = Translator()

# Session state for continuous recognition
session_state = {
    'frame_count': 0,
    'recognized_gestures': []
}

@app.route('/api/translate', methods=['POST'])
def translate():
    """Main translation endpoint - processes frame batch"""
    try:
        data = request.json
        frames = data.get('frames', [])
        
        if not frames:
            return jsonify({'error': 'No frames provided'}), 400
        
        recognized_gestures = []
        
        # Process each frame through the pipeline
        for frame in frames:
            # Extract features
            frame_features = feature_extractor.extract_frame_features(frame)
            
            # Add to segmenter
            is_boundary, gesture_frames = gesture_segmenter.add_frame(frame_features)
            
            # If gesture boundary detected, recognize it
            if is_boundary and gesture_frames:
                result = gesture_recognizer.recognize(gesture_frames)
                
                if result['gesture'] and result['confidence'] >= 0.7:
                    recognized_gestures.append({
                        'gesture': result['gesture'],
                        'confidence': result['confidence']
                    })
        
        # Extract gesture names
        gesture_names = [g['gesture'] for g in recognized_gestures]
        
        # Translate to English
        if gesture_names:
            translation = translator.translate_to_english(gesture_names)
        else:
            translation = ""
        
        # Calculate average confidence
        avg_confidence = sum(g['confidence'] for g in recognized_gestures) / len(recognized_gestures) if recognized_gestures else 0
        
        return jsonify({
            'translation': translation,
            'words': gesture_names,
            'confidence': avg_confidence,
            'frame_count': len(frames),
            'gesture_count': len(recognized_gestures)
        })
    
    except Exception as e:
        print(f"[ERROR] Error in /api/translate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate/continuous', methods=['POST'])
def translate_continuous():
    """Continuous translation endpoint - maintains state across requests"""
    try:
        data = request.json
        frames = data.get('frames', [])
        reset = data.get('reset', False)
        
        if reset:
            # Reset session state
            feature_extractor.reset_velocity_tracking()
            gesture_segmenter._reset()
            session_state['frame_count'] = 0
            session_state['recognized_gestures'] = []
            return jsonify({'status': 'reset', 'message': 'Session reset'})
        
        if not frames:
            return jsonify({'error': 'No frames provided'}), 400
        
        # Process frames
        for frame in frames:
            frame_features = feature_extractor.extract_frame_features(frame)
            is_boundary, gesture_frames = gesture_segmenter.add_frame(frame_features)
            
            if is_boundary and gesture_frames:
                result = gesture_recognizer.recognize(gesture_frames)
                
                if result['gesture'] and result['confidence'] >= 0.7:
                    session_state['recognized_gestures'].append({
                        'gesture': result['gesture'],
                        'confidence': result['confidence']
                    })
        
        session_state['frame_count'] += len(frames)
        
        # Get recent gestures
        gesture_names = [g['gesture'] for g in session_state['recognized_gestures']]
        
        # Translate
        translation = translator.translate_to_english(gesture_names) if gesture_names else ""
        
        return jsonify({
            'translation': translation,
            'words': gesture_names,
            'gesture_count': len(gesture_names),
            'frame_count': session_state['frame_count'],
            'buffer_info': gesture_segmenter.get_buffer_info()
        })
    
    except Exception as e:
        print(f"[ERROR] Error in /api/translate/continuous: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get recognizer statistics"""
    try:
        stats = gesture_recognizer.get_stats()
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Sign Language API v2 is running',
        'architecture': 'body-relative + joint angles + velocity segmentation'
    })

if __name__ == '__main__':
    print("[START] Sign Language Translation API v2 starting...")
    print("[ARCH] Architecture: Body-relative coordinates + Joint angles + Velocity segmentation")
    print("[SERVER] Server running on http://localhost:5000")
    print("[TEST] Test with: http://localhost:5000/api/health")
    
    # Print loaded templates
    stats = gesture_recognizer.get_stats()
    print(f"\n[TEMPLATES] Loaded {stats['total_gestures']} gesture templates")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
