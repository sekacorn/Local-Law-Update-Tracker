#!/bin/bash
# Start LLUT Frontend (React + Vite)

echo "============================================================"
echo "Starting LLUT Frontend"
echo "============================================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    echo ""
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "[ERROR] npm is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    echo ""
    exit 1
fi

echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"
echo ""

# Navigate to frontend directory
cd apps/desktop || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "[WARN] node_modules not found. Installing dependencies..."
    echo ""
    npm install
    echo ""
fi

echo "Starting Vite dev server..."
echo "Frontend will be available at: http://localhost:1420/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the dev server
npm run dev

# This line will only execute if npm run dev exits
echo ""
echo "Frontend server stopped."
