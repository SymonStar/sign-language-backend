import requests
import json

# Sample skeletal data (mock)
sample_frames = [
    {
        "timestamp": 1234567890,
        "frame_id": 1,
        "pose_landmarks": [[0.5, 0.3, 0.1]] * 33,
        "left_hand": [[0.4, 0.5, 0.2]] * 21,
        "right_hand": [[0.6, 0.5, 0.2]] * 21
    }
] * 30  # 30 frames

def test_health():
    """Test if server is running"""
    try:
        response = requests.get('http://localhost:5000/api/health')
        print("✅ Health check:", response.json())
        return True
    except Exception as e:
        print("❌ Server not running:", e)
        return False

def test_translation():
    """Test translation endpoint"""
    try:
        response = requests.post(
            'http://localhost:5000/api/translate',
            json={'frames': sample_frames}
        )
        result = response.json()
        print("\n✅ Translation test:")
        print(f"   Words recognized: {result.get('words')}")
        print(f"   Translation: {result.get('translation')}")
        print(f"   Confidence: {result.get('confidence')}")
        print(f"   Frames processed: {result.get('frame_count')}")
        return True
    except Exception as e:
        print("❌ Translation failed:", e)
        return False

if __name__ == '__main__':
    print("🧪 Testing Sign Language API...\n")
    
    if test_health():
        test_translation()
    else:
        print("\n⚠️  Make sure the server is running:")
        print("   python app.py")
