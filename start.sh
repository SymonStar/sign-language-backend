#!/bin/bash
# V3 optimized compressed templates (4.3MB)
# Auto-loads gesture_templates_v3_optimized.json.gz

echo "[OK] Using V3 optimized compressed templates"

# Start the app
gunicorn app_v3:app
