#!/bin/bash
# reset_db.sh - Reset the local LLUT database and cache
# WARNING: This will delete all downloaded legal documents and metadata!

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}LLUT Database Reset${NC}"
echo "==================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Database and cache locations
DB_FILE="$PROJECT_ROOT/app_data/llut.db"
CACHE_DIR="$PROJECT_ROOT/app_data/cache"
SETTINGS_FILE="$PROJECT_ROOT/app_data/settings.json"

echo -e "${YELLOW}This will delete:${NC}"
echo "  - Local database: $DB_FILE"
echo "  - Cached files: $CACHE_DIR"
echo ""
echo -e "${RED}WARNING: All downloaded legal documents, metadata, and search indexes will be lost!${NC}"
echo -e "${YELLOW}Your settings and API keys will be preserved.${NC}"
echo ""

# Check if running in non-interactive mode
if [ "$1" == "--force" ] || [ "$1" == "-f" ]; then
    CONFIRM="y"
else
    read -p "Are you sure you want to continue? (y/N): " CONFIRM
fi

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Reset cancelled${NC}"
    exit 0
fi

echo -e "\n${BLUE}Starting reset...${NC}"

# Calculate sizes before deletion
DB_SIZE=0
CACHE_SIZE=0

if [ -f "$DB_FILE" ]; then
    DB_SIZE=$(du -sb "$DB_FILE" 2>/dev/null | awk '{print $1}' || echo "0")
fi

if [ -d "$CACHE_DIR" ]; then
    CACHE_SIZE=$(du -sb "$CACHE_DIR" 2>/dev/null | awk '{print $1}' || echo "0")
fi

TOTAL_SIZE=$((DB_SIZE + CACHE_SIZE))

# Format bytes to human-readable
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

# Delete database
if [ -f "$DB_FILE" ]; then
    echo -e "${BLUE}Deleting database ($(format_bytes $DB_SIZE))...${NC}"
    rm -f "$DB_FILE"
    echo -e "${GREEN}Database deleted${NC}"
else
    echo -e "${YELLOW}No database file found${NC}"
fi

# Delete database journal/WAL files if they exist
rm -f "$DB_FILE-journal" 2>/dev/null || true
rm -f "$DB_FILE-shm" 2>/dev/null || true
rm -f "$DB_FILE-wal" 2>/dev/null || true

# Delete cache directory
if [ -d "$CACHE_DIR" ]; then
    echo -e "${BLUE}Deleting cache directory ($(format_bytes $CACHE_SIZE))...${NC}"
    rm -rf "$CACHE_DIR"
    echo -e "${GREEN}Cache deleted${NC}"
else
    echo -e "${YELLOW}No cache directory found${NC}"
fi

# Recreate empty app_data structure
echo -e "${BLUE}Recreating app_data structure...${NC}"
mkdir -p "$PROJECT_ROOT/app_data"
mkdir -p "$PROJECT_ROOT/app_data/cache"

# Create empty database (schema will be initialized on next run)
touch "$DB_FILE"

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Reset complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Space freed: $(format_bytes $TOTAL_SIZE)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Start the application: make dev or make start"
echo "  2. Run sync to download new data"
echo ""
if [ -f "$SETTINGS_FILE" ]; then
    echo -e "${GREEN}Your settings have been preserved${NC}"
else
    echo -e "${YELLOW}You may need to reconfigure settings and API keys${NC}"
fi
