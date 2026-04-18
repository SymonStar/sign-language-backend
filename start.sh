#!/bin/bash
# Filtered templates are now in the repo (small enough for GitHub)
# No need to download from Google Drive

echo "[OK] Using filtered templates from repo"

# Start the app
gunicorn app_v2:app
