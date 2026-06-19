#!/usr/bin/env bash
set -e
[ -f .env ] || cp .env.example .env
echo "Starting FastAPI on :8000 ..."
uvicorn backend.main:app --port 8000 &
BACK=$!
sleep 3
echo "Starting Streamlit ..."
streamlit run streamlit_app.py
kill $BACK 2>/dev/null || true
