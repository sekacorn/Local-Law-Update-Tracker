#!/bin/bash
# dev_run.sh - Start development environment for LLUT
# Starts both the FastAPI backend and Tauri frontend in development mode

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LLUT Development Environment${NC}"
echo "========================================"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# PID file locations
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

# Clean up old PID files
rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"

# Trap to clean up on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    if [ -f "$BACKEND_PID_FILE" ]; then
        BACKEND_PID=$(cat "$BACKEND_PID_FILE")
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
    fi
    if [ -f "$FRONTEND_PID_FILE" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Check if Python is available
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3.11+ is required but not found${NC}"
        exit 1
    fi
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Using Python version: $PYTHON_VERSION"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not found${NC}"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "Using Node.js version: $NODE_VERSION"

# Create app_data directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/app_data"
mkdir -p "$PROJECT_ROOT/app_data/cache"

# Start backend
echo -e "\n${GREEN}Starting FastAPI backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing backend dependencies..."
    pip install -q -r requirements.txt
fi

# Start backend server
echo "Starting FastAPI on http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$BACKEND_PID_FILE"
echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}Backend is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Backend failed to start. Check backend.log for details.${NC}"
        cleanup
    fi
    sleep 1
done

# Start frontend
echo -e "\n${GREEN}Starting Tauri frontend...${NC}"
cd "$PROJECT_ROOT/apps/desktop"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start Tauri dev server
echo "Starting Tauri development server..."
npm run tauri dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Development environment running!${NC}"
echo -e "${GREEN}================================${NC}"
echo "Backend:  http://localhost:8000"
echo "Frontend: Tauri development window"
echo ""
echo "Logs:"
echo "  Backend:  $PROJECT_ROOT/backend.log"
echo "  Frontend: $PROJECT_ROOT/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all processes${NC}"

# Wait for processes
wait
