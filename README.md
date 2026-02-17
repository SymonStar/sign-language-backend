# Sign Language Translation Backend

Cloud API that receives skeletal data, recognizes gestures, and translates to English using AI.

## Setup (2 minutes)

**1. Install dependencies:**
```bash
cd C:\SignLanguageBackend
pip install -r requirements.txt
```

**2. (Optional) Get free Groq API key:**
- Go to: https://console.groq.com
- Sign up (free)
- Create API key
- Edit `.env` file and paste your key

**Without API key:** Works fine, just uses simple translation instead of AI.

## Run Server

```bash
python app.py
```

Server runs on: http://localhost:5000

## Test It

**Open new terminal:**
```bash
python test_api.py
```

Should show:
- ✅ Health check
- ✅ Translation with recognized words

## How It Works

1. **Receives skeletal data** from mobile app (30 frames)
2. **Compares with gesture database** (12 common signs)
3. **Recognizes words** from hand movements
4. **Translates to English** using Groq AI (or simple rules)
5. **Returns translation** to mobile app

## API Endpoints

**Health Check:**
```
GET http://localhost:5000/api/health
```

**Translate:**
```
POST http://localhost:5000/api/translate
Body: {
  "frames": [array of skeletal data],
  "timestamp": 1234567890
}

Response: {
  "translation": "Hello.",
  "words": ["HELLO"],
  "confidence": 0.85,
  "frame_count": 30
}
```

## Gesture Database

Located in `data/gestures.json`

Current signs:
- HELLO, THANK YOU, YES, NO
- PLEASE, SORRY, HELP
- GOOD, BAD, LOVE
- NAME, MY

## Next Steps

1. ✅ Backend API working
2. ⏭️ Connect mobile app to this API
3. ⏭️ Add more gestures to database
4. ⏭️ Improve recognition accuracy with ML model

## Files

- `app.py` - Flask API server
- `gesture_recognizer.py` - Compares skeletal data with database
- `translator.py` - AI translation using Groq
- `data/gestures.json` - Gesture database
- `test_api.py` - Test script
