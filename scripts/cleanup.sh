#!/bin/bash
# cleanup.sh - Clean temporary files, build artifacts, and cached data

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Cleaning LLUT temporary files${NC}"
echo "=============================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Track what was cleaned
CLEANED_ITEMS=0
FREED_SPACE=0

# Function to calculate directory size
get_dir_size() {
    if [ -d "$1" ]; then
        du -sb "$1" 2>/dev/null | awk '{print $1}' || echo "0"
    else
        echo "0"
    fi
}

# Function to format bytes to human-readable
format_bytes() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$(( bytes / 1024 ))KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$(( bytes / 1048576 ))MB"
    else
        echo "$(( bytes / 1073741824 ))GB"
    fi
}

# Function to remove directory or file
remove_item() {
    local path=$1
    local description=$2

    if [ -e "$path" ]; then
        local size=$(get_dir_size "$path")
        echo -e "${BLUE}Removing $description...${NC}"
        rm -rf "$path"
        CLEANED_ITEMS=$((CLEANED_ITEMS + 1))
        FREED_SPACE=$((FREED_SPACE + size))
        echo -e "  ${GREEN}Removed $(format_bytes $size)${NC}"
    fi
}

echo -e "\n${YELLOW}Cleaning backend artifacts...${NC}"

# Python cache files
remove_item "$PROJECT_ROOT/backend/__pycache__" "Python cache (__pycache__)"
find "$PROJECT_ROOT/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT/backend" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT/backend" -type f -name "*.pyo" -delete 2>/dev/null || true

# PyInstaller build artifacts
remove_item "$PROJECT_ROOT/backend/build" "PyInstaller build directory"
remove_item "$PROJECT_ROOT/backend/dist" "PyInstaller dist directory"
find "$PROJECT_ROOT/backend" -type f -name "*.spec" -delete 2>/dev/null || true

# pytest cache
remove_item "$PROJECT_ROOT/backend/.pytest_cache" "pytest cache"
remove_item "$PROJECT_ROOT/backend/tests/__pycache__" "test cache"

# Coverage reports
remove_item "$PROJECT_ROOT/backend/.coverage" "coverage data"
remove_item "$PROJECT_ROOT/backend/htmlcov" "coverage HTML reports"

echo -e "\n${YELLOW}Cleaning frontend artifacts...${NC}"

# Node modules (optional - can be large)
# Uncomment the next line if you want to remove node_modules
# remove_item "$PROJECT_ROOT/apps/desktop/node_modules" "Node modules"

# Build artifacts
remove_item "$PROJECT_ROOT/apps/desktop/dist" "frontend dist"
remove_item "$PROJECT_ROOT/apps/desktop/build" "frontend build"

# Tauri build artifacts
remove_item "$PROJECT_ROOT/apps/desktop/src-tauri/target" "Tauri target directory"
remove_item "$PROJECT_ROOT/apps/desktop/src-tauri/resources" "Tauri resources"

# Vite cache
remove_item "$PROJECT_ROOT/apps/desktop/.vite" "Vite cache"
remove_item "$PROJECT_ROOT/apps/desktop/node_modules/.vite" "Vite node cache"

echo -e "\n${YELLOW}Cleaning application data...${NC}"

# Runtime cache (NOT the database - see reset_db.sh for that)
remove_item "$PROJECT_ROOT/app_data/cache" "application cache directory"
mkdir -p "$PROJECT_ROOT/app_data/cache"  # Recreate empty cache dir

# Log files
remove_item "$PROJECT_ROOT/backend.log" "backend log"
remove_item "$PROJECT_ROOT/frontend.log" "frontend log"

# PID files
remove_item "$PROJECT_ROOT/.backend.pid" "backend PID file"
remove_item "$PROJECT_ROOT/.frontend.pid" "frontend PID file"

echo -e "\n${YELLOW}Cleaning system temp files...${NC}"

# OS-specific temp files
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    find "$PROJECT_ROOT" -type f -name ".DS_Store" -delete 2>/dev/null || true
    echo -e "${BLUE}Removed .DS_Store files${NC}"
fi

# Editor temp files
find "$PROJECT_ROOT" -type f -name "*~" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swp" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.swo" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name ".*.swp" -delete 2>/dev/null || true

# Git ignored files (optional - be careful!)
# Uncomment to clean all git-ignored files
# cd "$PROJECT_ROOT" && git clean -fdX

echo -e "\n${YELLOW}Cleaning Rust build artifacts...${NC}"

# Cargo cache (if exists)
if [ -d "$PROJECT_ROOT/apps/desktop/src-tauri" ]; then
    cd "$PROJECT_ROOT/apps/desktop/src-tauri"
    if command -v cargo &> /dev/null; then
        echo -e "${BLUE}Running cargo clean...${NC}"
        cargo clean 2>/dev/null || true
    fi
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Items cleaned: $CLEANED_ITEMS"
echo -e "Space freed: $(format_bytes $FREED_SPACE)"
echo ""
echo -e "${YELLOW}Note: Database and pinned files were NOT deleted.${NC}"
echo -e "${YELLOW}Use 'make reset' or run scripts/reset_db.sh to reset the database.${NC}"
