from flask import Flask, request, jsonify
from flask_cors import CORS
from gesture_recognizer import GestureRecognizer
from translator import Translator
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for PWA access

# Initialize services
gesture_recognizer = GestureRecognizer()
translator = Translator()

@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        frames = data.get('frames', [])
        
        if not frames:
            return jsonify({'error': 'No frames provided'}), 400
        
        # Recognize gestures from skeletal data
        recognized_words = gesture_recognizer.recognize_sequence(frames)
        
        # Translate to proper English using AI
        translation = translator.translate_to_english(recognized_words)
        
        return jsonify({
            'translation': translation,
            'words': recognized_words,
            'confidence': 0.85,
            'frame_count': len(frames)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'Sign Language API is running'})

if __name__ == '__main__':
    print("🚀 Sign Language Translation API starting...")
    print("📡 Server running on http://localhost:5000")
    print("🔍 Test with: http://localhost:5000/api/health")
    app.run(host='0.0.0.0', port=5000, debug=True)
