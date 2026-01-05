#!/bin/bash
# stop_all.sh - Stop all LLUT processes (backend and frontend)

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping LLUT processes${NC}"
echo "======================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# PID file locations
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

STOPPED=0

# Stop backend
if [ -f "$BACKEND_PID_FILE" ]; then
    BACKEND_PID=$(cat "$BACKEND_PID_FILE")
    echo -e "Stopping backend process (PID: $BACKEND_PID)..."

    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID 2>/dev/null || true

        # Wait for process to stop (max 10 seconds)
        for i in {1..10}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo -e "${GREEN}Backend stopped successfully${NC}"
                STOPPED=$((STOPPED + 1))
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${YELLOW}Force killing backend...${NC}"
            kill -9 $BACKEND_PID 2>/dev/null || true
            STOPPED=$((STOPPED + 1))
        fi
    else
        echo -e "${YELLOW}Backend process not running${NC}"
    fi

    rm -f "$BACKEND_PID_FILE"
else
    echo "No backend PID file found"
fi

# Stop frontend
if [ -f "$FRONTEND_PID_FILE" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_PID_FILE")
    echo -e "Stopping frontend process (PID: $FRONTEND_PID)..."

    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID 2>/dev/null || true

        # Wait for process to stop (max 10 seconds)
        for i in {1..10}; do
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                echo -e "${GREEN}Frontend stopped successfully${NC}"
                STOPPED=$((STOPPED + 1))
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "${YELLOW}Force killing frontend...${NC}"
            kill -9 $FRONTEND_PID 2>/dev/null || true
            STOPPED=$((STOPPED + 1))
        fi
    else
        echo -e "${YELLOW}Frontend process not running${NC}"
    fi

    rm -f "$FRONTEND_PID_FILE"
else
    echo "No frontend PID file found"
fi

# Additional cleanup: kill any stray processes
echo -e "\n${YELLOW}Checking for stray processes...${NC}"

# Kill any uvicorn processes (backend)
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "Killing stray uvicorn processes..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    STOPPED=$((STOPPED + 1))
fi

# Kill any Tauri dev processes
if pgrep -f "tauri dev" > /dev/null; then
    echo "Killing stray Tauri processes..."
    pkill -f "tauri dev" 2>/dev/null || true
    STOPPED=$((STOPPED + 1))
fi

# Kill any Node.js dev server processes related to the project
if pgrep -f "node.*desktop" > /dev/null; then
    echo "Killing stray Node.js processes..."
    pkill -f "node.*desktop" 2>/dev/null || true
    STOPPED=$((STOPPED + 1))
fi

echo ""
if [ $STOPPED -gt 0 ]; then
    echo -e "${GREEN}All LLUT processes stopped${NC}"
else
    echo -e "${YELLOW}No running processes found${NC}"
fi
