#!/bin/bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start FastAPI app
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
