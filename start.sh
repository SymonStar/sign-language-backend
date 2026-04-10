#!/bin/bash
# Download gesture templates from Google Drive if not present

TEMPLATES_FILE="data/gesture_templates_v2.json"

if [ ! -f "$TEMPLATES_FILE" ]; then
    echo "[DOWNLOAD] Gesture templates not found, downloading from Google Drive..."
    
    # Replace FILE_ID with your Google Drive file ID
    FILE_ID="1xYkh3c5PaYv9rwO4aEELTItyOkrtPdz5"
    
    # Download using gdown or curl
    pip install gdown
    gdown "https://drive.google.com/uc?id=${FILE_ID}" -O "$TEMPLATES_FILE"
    
    if [ -f "$TEMPLATES_FILE" ]; then
        echo "[OK] Templates downloaded successfully"
    else
        echo "[ERROR] Failed to download templates"
        exit 1
    fi
else
    echo "[OK] Templates already present"
fi

# Start the app
gunicorn app_v2:app
