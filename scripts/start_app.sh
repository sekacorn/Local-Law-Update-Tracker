#!/bin/bash
# start_app.sh - Start the built LLUT application

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting LLUT Application${NC}"
echo "========================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Determine the executable path based on OS
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    EXECUTABLE="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/llut.exe"
    BUNDLE_EXE=$(find "$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle" -name "*.exe" -type f 2>/dev/null | head -n 1)

    if [ -f "$BUNDLE_EXE" ]; then
        EXECUTABLE="$BUNDLE_EXE"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    APP_BUNDLE=$(find "$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle/macos" -name "*.app" -type d 2>/dev/null | head -n 1)

    if [ -d "$APP_BUNDLE" ]; then
        echo -e "${GREEN}Launching $APP_BUNDLE${NC}"
        open "$APP_BUNDLE"
        exit 0
    else
        EXECUTABLE="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/llut"
    fi
else
    # Linux
    EXECUTABLE="$PROJECT_ROOT/apps/desktop/src-tauri/target/release/llut"
    APPIMAGE=$(find "$PROJECT_ROOT/apps/desktop/src-tauri/target/release/bundle/appimage" -name "*.AppImage" -type f 2>/dev/null | head -n 1)

    if [ -f "$APPIMAGE" ]; then
        EXECUTABLE="$APPIMAGE"
        chmod +x "$EXECUTABLE"
    fi
fi

# Check if executable exists
if [ ! -f "$EXECUTABLE" ]; then
    echo -e "${RED}Error: Application executable not found${NC}"
    echo "Expected location: $EXECUTABLE"
    echo ""
    echo -e "${YELLOW}You need to build the application first:${NC}"
    echo "  make build"
    exit 1
fi

echo -e "${GREEN}Starting application...${NC}"
echo "Executable: $EXECUTABLE"

# Start the application
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: start in background
    cmd //c start "" "$EXECUTABLE"
else
    # Unix-like: start in background
    "$EXECUTABLE" &
    APP_PID=$!
    echo -e "${GREEN}Application started (PID: $APP_PID)${NC}"
fi

echo -e "${GREEN}LLUT is running${NC}"
