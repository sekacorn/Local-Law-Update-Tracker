#!/bin/bash
# Backend startup script for LLUT (Linux/macOS)
# Starts the FastAPI backend server

echo "Starting LLUT Backend..."

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/../backend"

# Change to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the backend
echo "Backend starting on http://localhost:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
