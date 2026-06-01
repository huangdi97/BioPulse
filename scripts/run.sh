#!/bin/bash
cd "$(dirname "$0")/.."
echo "Starting Cloud API..."
exec python3 -m uvicorn cloud.app.main:app --host 0.0.0.0 --port 8000 --reload
