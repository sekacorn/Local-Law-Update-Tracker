#!/bin/bash
# build_desktop.sh - Build production desktop application for LLUT
# Creates distributable packages with embedded FastAPI backend

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building LLUT Desktop Application${NC}"
echo "=================================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Build timestamp
BUILD_TIME=$(date +"%Y-%m-%d %H:%M:%S")
echo -e "${BLUE}Build started at: $BUILD_TIME${NC}"

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

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is required but not found${NC}"
    exit 1
fi

# Check if Rust is available (required for Tauri)
if ! command -v cargo &> /dev/null; then
    echo -e "${RED}Error: Rust/Cargo is required for Tauri but not found${NC}"
    echo "Install from: https://rustup.rs/"
    exit 1
fi

echo -e "\n${GREEN}Step 1: Preparing backend bundle${NC}"
cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
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

# Install/update dependencies
echo "Installing backend dependencies..."
pip install -q -r requirements.txt

# Install PyInstaller if not already installed
pip install -q pyinstaller

# Create standalone backend executable
echo "Building backend executable with PyInstaller..."
pyinstaller --onefile \
    --name llut-backend \
    --hidden-import uvicorn.logging \
    --hidden-import uvicorn.loops \
    --hidden-import uvicorn.loops.auto \
    --hidden-import uvicorn.protocols \
    --hidden-import uvicorn.protocols.http \
    --hidden-import uvicorn.protocols.http.auto \
    --hidden-import uvicorn.protocols.websockets \
    --hidden-import uvicorn.protocols.websockets.auto \
    --hidden-import uvicorn.lifespan \
    --hidden-import uvicorn.lifespan.on \
    --add-data "app:app" \
    app/main.py

echo -e "${GREEN}Backend executable created at: backend/dist/llut-backend${NC}"

echo -e "\n${GREEN}Step 2: Building frontend${NC}"
cd "$PROJECT_ROOT/apps/desktop"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Copy backend executable to Tauri resources
echo "Copying backend to Tauri resources..."
mkdir -p src-tauri/resources
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    cp "$PROJECT_ROOT/backend/dist/llut-backend.exe" src-tauri/resources/
else
    cp "$PROJECT_ROOT/backend/dist/llut-backend" src-tauri/resources/
fi

# Build Tauri application
echo "Building Tauri application (this may take several minutes)..."
npm run tauri build

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"

# Find and display build artifacts
echo -e "\n${BLUE}Build artifacts:${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    BUNDLE_DIR="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle"
    if [ -d "$BUNDLE_DIR/nsis" ]; then
        echo "  Windows Installer: $(ls "$BUNDLE_DIR/nsis"/*.exe 2>/dev/null || echo 'Not found')"
    fi
    if [ -d "$BUNDLE_DIR/msi" ]; then
        echo "  MSI Installer: $(ls "$BUNDLE_DIR/msi"/*.msi 2>/dev/null || echo 'Not found')"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    BUNDLE_DIR="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle"
    if [ -d "$BUNDLE_DIR/dmg" ]; then
        echo "  DMG: $(ls "$BUNDLE_DIR/dmg"/*.dmg 2>/dev/null || echo 'Not found')"
    fi
    if [ -d "$BUNDLE_DIR/macos" ]; then
        echo "  App Bundle: $(ls -d "$BUNDLE_DIR/macos"/*.app 2>/dev/null || echo 'Not found')"
    fi
else
    BUNDLE_DIR="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle"
    if [ -d "$BUNDLE_DIR/deb" ]; then
        echo "  DEB: $(ls "$BUNDLE_DIR/deb"/*.deb 2>/dev/null || echo 'Not found')"
    fi
    if [ -d "$BUNDLE_DIR/appimage" ]; then
        echo "  AppImage: $(ls "$BUNDLE_DIR/appimage"/*.AppImage 2>/dev/null || echo 'Not found')"
    fi
fi

# Display binary location
RELEASE_BIN="$PROJECT_ROOT/apps/desktop/src-tauri/target/release"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "  Executable: $RELEASE_BIN/llut.exe"
else
    echo "  Executable: $RELEASE_BIN/llut"
fi

BUILD_END=$(date +"%Y-%m-%d %H:%M:%S")
echo -e "\n${BLUE}Build finished at: $BUILD_END${NC}"
