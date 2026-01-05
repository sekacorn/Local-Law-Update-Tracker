#!/bin/bash
# Stop LLUT Frontend and Clean Up Memory

echo "============================================================"
echo "Stopping LLUT Frontend"
echo "============================================================"
echo ""

# Find and kill processes on port 1420
echo "Searching for processes on port 1420..."
if command -v lsof &> /dev/null; then
    # Use lsof (macOS/Linux)
    PID=$(lsof -ti:1420)
    if [ -n "$PID" ]; then
        echo "Found process with PID: $PID"
        kill -9 $PID 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "[OK] Stopped process $PID"
        fi
    fi
elif command -v fuser &> /dev/null; then
    # Use fuser (Linux alternative)
    fuser -k 1420/tcp 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "[OK] Stopped process on port 1420"
    fi
fi

# Kill any Vite/Node processes related to the project
echo ""
echo "Stopping Vite processes..."
pkill -f "vite.*1420" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null

# More aggressive: kill all node processes in this directory (use with caution)
# Uncomment if needed:
# pkill -f "node.*apps/desktop" 2>/dev/null

echo ""
echo "Cleaning up cache and temporary files..."

# Clean Vite cache
if [ -d "apps/desktop/node_modules/.vite" ]; then
    echo "Removing Vite cache..."
    rm -rf apps/desktop/node_modules/.vite
    echo "[OK] Vite cache cleared"
fi

# Clean dist folder
if [ -d "apps/desktop/dist" ]; then
    echo "Removing dist folder..."
    rm -rf apps/desktop/dist
    echo "[OK] Dist folder cleared"
fi

# Clean npm cache (optional - uncomment if needed)
# echo "Cleaning npm cache..."
# npm cache clean --force

# Delete .frontend.pid file if it exists
if [ -f ".frontend.pid" ]; then
    echo "Removing .frontend.pid..."
    rm -f .frontend.pid
fi

echo ""
echo "============================================================"
echo "Frontend stopped and cleaned up!"
echo "============================================================"
echo ""
echo "Memory cleanup completed:"
echo "  - Killed processes on port 1420"
echo "  - Removed Vite cache"
echo "  - Removed build artifacts"
echo ""
