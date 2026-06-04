from flask import Flask, request, jsonify
from flask_cors import CORS
from gesture_recognizer_v3 import GestureRecognizer
from translator import Translator

app = Flask(__name__)
CORS(app)

gesture_recognizer = GestureRecognizer()
translator = Translator()

@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        frames = data.get('frames', [])
        
        if not frames:
            return jsonify({'error': 'No frames provided'}), 400
        
        result = gesture_recognizer.recognize(frames)
        
        if result['gesture']:
            words = [result['gesture']]
            translation = translator.translate_to_english(words)
        else:
            words = []
            translation = ""
        
        return jsonify({
            'translation': translation,
            'words': words,
            'confidence': result['confidence'],
            'frame_count': len(frames)
        })
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate-sentence', methods=['POST'])
def translate_sentence():
    try:
        data = request.json
        words = data.get('words', [])
        
        if not words:
            return jsonify({'error': 'No words provided'}), 400
        
        translation = translator.translate_to_english(words)
        
        return jsonify({
            'translation': translation,
            'words': words,
            'word_count': len(words)
        })
    
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    stats = gesture_recognizer.get_stats()
    return jsonify({
        'status': 'ok',
        'message': 'Sign Language API v3 (Optimized)',
        'templates_loaded': stats['total_templates'],
        'signs': stats['unique_signs']
    })

if __name__ == '__main__':
    print("🚀 Sign Language API v3 (Optimized Templates)")
    print("📦 Loading compressed templates...")
    stats = gesture_recognizer.get_stats()
    print(f"✅ Loaded {stats['total_templates']} templates for {stats['unique_signs']} signs")
    print("📡 Server: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
