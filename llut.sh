#!/bin/bash
# llut.sh - LLUT Application Runner
# All-in-one script to run, stop, and manage the LLUT application

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# PID file locations
BACKEND_PID_FILE="$PROJECT_ROOT/.backend.pid"
FRONTEND_PID_FILE="$PROJECT_ROOT/.frontend.pid"

# Function to show usage
show_usage() {
    echo -e "${GREEN}LLUT - Local Law Update Tracker${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Usage: ./llut.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  (no args)           Start the application"
    echo "  -s, --stop          Stop the application"
    echo "  -c, --clean         Clear all cache files"
    echo "  -r, --restart       Restart the application"
    echo "  --status            Show application status"
    echo "  --logs              Show recent logs"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Combined options:"
    echo "  --stop --clean      Stop app and clear cache"
    echo "  -r -c               Restart and clear cache"
    echo ""
    echo "Examples:"
    echo "  ./llut.sh           # Start the app"
    echo "  ./llut.sh --stop    # Stop the app"
    echo "  ./llut.sh -s -c     # Stop and clean cache"
    echo "  ./llut.sh -r        # Restart the app"
    echo ""
}

# Function to check if process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to get process status
get_status() {
    echo -e "${CYAN}Application Status${NC}"
    echo -e "${CYAN}==================${NC}"

    # Check backend
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "Backend:  ${GREEN}Running${NC} (PID: $backend_pid)"
    else
        echo -e "Backend:  ${RED}Stopped${NC}"
    fi

    # Check frontend
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "Frontend: ${GREEN}Running${NC} (PID: $frontend_pid)"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi

    echo ""

    # Show database and cache size
    if [ -f "$PROJECT_ROOT/app_data/llut.db" ]; then
        local db_size=$(du -sh "$PROJECT_ROOT/app_data/llut.db" 2>/dev/null | awk '{print $1}')
        echo -e "Database: ${BLUE}$db_size${NC}"
    else
        echo -e "Database: ${YELLOW}Not initialized${NC}"
    fi

    if [ -d "$PROJECT_ROOT/app_data/cache" ]; then
        local cache_size=$(du -sh "$PROJECT_ROOT/app_data/cache" 2>/dev/null | awk '{print $1}')
        local cache_files=$(find "$PROJECT_ROOT/app_data/cache" -type f 2>/dev/null | wc -l)
        echo -e "Cache:    ${BLUE}$cache_size${NC} ($cache_files files)"
    else
        echo -e "Cache:    ${YELLOW}Empty${NC}"
    fi

    if [ -d "$PROJECT_ROOT/app_data/uploads" ]; then
        local uploads_size=$(du -sh "$PROJECT_ROOT/app_data/uploads" 2>/dev/null | awk '{print $1}')
        local uploads_count=$(find "$PROJECT_ROOT/app_data/uploads" -maxdepth 1 -type d 2>/dev/null | grep -v "^$PROJECT_ROOT/app_data/uploads$" | wc -l)
        echo -e "Uploads:  ${BLUE}$uploads_size${NC} ($uploads_count documents)"
    else
        echo -e "Uploads:  ${YELLOW}No uploads yet${NC}"
    fi

    echo ""
}

# Function to show logs
show_logs() {
    echo -e "${CYAN}Recent Logs${NC}"
    echo -e "${CYAN}===========${NC}"

    if [ -f "$PROJECT_ROOT/backend.log" ]; then
        echo -e "\n${YELLOW}Backend (last 20 lines):${NC}"
        tail -n 20 "$PROJECT_ROOT/backend.log"
    fi

    if [ -f "$PROJECT_ROOT/frontend.log" ]; then
        echo -e "\n${YELLOW}Frontend (last 20 lines):${NC}"
        tail -n 20 "$PROJECT_ROOT/frontend.log"
    fi
}

# Function to stop the application
stop_app() {
    echo -e "${YELLOW}Stopping LLUT...${NC}"

    local stopped=0

    # Stop backend
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        echo -e "Stopping backend (PID: $backend_pid)..."

        kill "$backend_pid" 2>/dev/null || true

        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$backend_pid" 2>/dev/null; then
                echo -e "${GREEN}Backend stopped${NC}"
                stopped=$((stopped + 1))
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 "$backend_pid" 2>/dev/null; then
            echo -e "${YELLOW}Force killing backend...${NC}"
            kill -9 "$backend_pid" 2>/dev/null || true
            stopped=$((stopped + 1))
        fi

        rm -f "$BACKEND_PID_FILE"
    else
        echo -e "${YELLOW}Backend not running${NC}"
    fi

    # Stop frontend
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        echo -e "Stopping frontend (PID: $frontend_pid)..."

        kill "$frontend_pid" 2>/dev/null || true

        # Wait for process to stop
        for i in {1..10}; do
            if ! kill -0 "$frontend_pid" 2>/dev/null; then
                echo -e "${GREEN}Frontend stopped${NC}"
                stopped=$((stopped + 1))
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if kill -0 "$frontend_pid" 2>/dev/null; then
            echo -e "${YELLOW}Force killing frontend...${NC}"
            kill -9 "$frontend_pid" 2>/dev/null || true
            stopped=$((stopped + 1))
        fi

        rm -f "$FRONTEND_PID_FILE"
    else
        echo -e "${YELLOW}Frontend not running${NC}"
    fi

    # Kill any stray processes
    echo -e "\n${YELLOW}Cleaning up stray processes...${NC}"
    pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Killed stray uvicorn processes" || true
    pkill -f "tauri dev" 2>/dev/null && echo "Killed stray Tauri processes" || true

    if [ $stopped -gt 0 ]; then
        echo -e "\n${GREEN}Application stopped successfully${NC}"
    else
        echo -e "\n${YELLOW}No running processes found${NC}"
    fi
}

# Function to clear cache
clear_cache() {
    echo -e "${YELLOW}Clearing cache files...${NC}"

    local cleared_size=0

    # Clear application cache
    if [ -d "$PROJECT_ROOT/app_data/cache" ]; then
        local cache_size=$(du -sb "$PROJECT_ROOT/app_data/cache" 2>/dev/null | awk '{print $1}' || echo "0")
        cleared_size=$((cleared_size + cache_size))

        echo -e "Clearing app_data/cache..."
        rm -rf "$PROJECT_ROOT/app_data/cache"
        mkdir -p "$PROJECT_ROOT/app_data/cache"
    fi

    # Clear log files
    if [ -f "$PROJECT_ROOT/backend.log" ]; then
        local log_size=$(du -sb "$PROJECT_ROOT/backend.log" 2>/dev/null | awk '{print $1}' || echo "0")
        cleared_size=$((cleared_size + log_size))
        echo -e "Clearing backend.log..."
        rm -f "$PROJECT_ROOT/backend.log"
    fi

    if [ -f "$PROJECT_ROOT/frontend.log" ]; then
        local log_size=$(du -sb "$PROJECT_ROOT/frontend.log" 2>/dev/null | awk '{print $1}' || echo "0")
        cleared_size=$((cleared_size + log_size))
        echo -e "Clearing frontend.log..."
        rm -f "$PROJECT_ROOT/frontend.log"
    fi

    # Clear Python cache
    echo -e "Clearing Python cache..."
    find "$PROJECT_ROOT/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT/backend" -type f -name "*.pyc" -delete 2>/dev/null || true

    # Clear temporary build files
    rm -f "$PROJECT_ROOT/.backend.pid" 2>/dev/null || true
    rm -f "$PROJECT_ROOT/.frontend.pid" 2>/dev/null || true

    # Format bytes
    if [ $cleared_size -lt 1024 ]; then
        cleared_readable="${cleared_size}B"
    elif [ $cleared_size -lt 1048576 ]; then
        cleared_readable="$(( cleared_size / 1024 ))KB"
    elif [ $cleared_size -lt 1073741824 ]; then
        cleared_readable="$(( cleared_size / 1048576 ))MB"
    else
        cleared_readable="$(( cleared_size / 1073741824 ))GB"
    fi

    echo -e "${GREEN}Cache cleared: $cleared_readable freed${NC}"
}

# Function to start the application
start_app() {
    echo -e "${GREEN}Starting LLUT Application${NC}"
    echo -e "${GREEN}=========================${NC}"

    # Check if already running
    if is_running "$BACKEND_PID_FILE" || is_running "$FRONTEND_PID_FILE"; then
        echo -e "${YELLOW}Warning: Application may already be running${NC}"
        get_status
        echo ""
        read -p "Do you want to restart? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Cancelled${NC}"
            exit 0
        fi
        stop_app
        echo ""
        sleep 2
    fi

    # Check Python
    if ! command -v python &> /dev/null; then
        if ! command -v python3 &> /dev/null; then
            echo -e "${RED}Error: Python 3.11+ is required but not found${NC}"
            exit 1
        fi
        PYTHON_CMD=python3
    else
        PYTHON_CMD=python
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is required but not found${NC}"
        exit 1
    fi

    # Create app_data directory
    mkdir -p "$PROJECT_ROOT/app_data"
    mkdir -p "$PROJECT_ROOT/app_data/cache"

    # Start backend
    echo -e "\n${GREEN}Starting backend...${NC}"
    cd "$PROJECT_ROOT/backend"

    # Create/activate virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi

    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi

    # Upgrade pip first to avoid issues with old pip versions (use python -m pip to avoid Windows lock issues)
    echo "Upgrading pip..."
    python -m pip install --upgrade pip setuptools wheel 2>/dev/null || echo "Pip upgrade skipped (using existing version)"

    # Install dependencies if needed
    if [ -f "requirements.txt" ]; then
        echo "Installing backend dependencies..."
        python -m pip install -r requirements.txt
    fi

    # Start backend server
    echo "Starting FastAPI on http://localhost:8000"
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_PID_FILE"
    echo -e "${GREEN}Backend started (PID: $BACKEND_PID)${NC}"

    # Wait for backend to be ready
    echo "Waiting for backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}Backend is ready!${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}Backend failed to start. Check backend.log${NC}"
            cat "$PROJECT_ROOT/backend.log"
            stop_app
            exit 1
        fi
        sleep 1
    done

    # Start frontend
    echo -e "\n${GREEN}Starting frontend...${NC}"
    cd "$PROJECT_ROOT/apps/desktop"

    # Install npm dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi

    # Start Tauri dev server
    echo "Starting Tauri..."
    npm run tauri dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_PID_FILE"
    echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID)${NC}"

    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}LLUT is running!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "Backend:  ${BLUE}http://localhost:8000${NC}"
    echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
    echo -e "Frontend: ${BLUE}Tauri window${NC}"
    echo ""
    echo -e "Logs:"
    echo -e "  Backend:  ${CYAN}$PROJECT_ROOT/backend.log${NC}"
    echo -e "  Frontend: ${CYAN}$PROJECT_ROOT/frontend.log${NC}"
    echo ""
    echo -e "${YELLOW}To stop: ./llut.sh --stop${NC}"
    echo -e "${YELLOW}Status:  ./llut.sh --status${NC}"
    echo ""
}

# Parse command line arguments
STOP_FLAG=false
CLEAN_FLAG=false
RESTART_FLAG=false
STATUS_FLAG=false
LOGS_FLAG=false

if [ $# -eq 0 ]; then
    # No arguments, start the app
    start_app
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--stop)
            STOP_FLAG=true
            shift
            ;;
        -c|--clean)
            CLEAN_FLAG=true
            shift
            ;;
        -r|--restart)
            RESTART_FLAG=true
            shift
            ;;
        --status)
            STATUS_FLAG=true
            shift
            ;;
        --logs)
            LOGS_FLAG=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Execute based on flags
if [ "$STATUS_FLAG" = true ]; then
    get_status
    exit 0
fi

if [ "$LOGS_FLAG" = true ]; then
    show_logs
    exit 0
fi

if [ "$RESTART_FLAG" = true ]; then
    stop_app
    if [ "$CLEAN_FLAG" = true ]; then
        echo ""
        clear_cache
    fi
    echo ""
    sleep 2
    start_app
    exit 0
fi

if [ "$STOP_FLAG" = true ]; then
    stop_app
fi

if [ "$CLEAN_FLAG" = true ]; then
    if [ "$STOP_FLAG" = true ]; then
        echo ""
    fi
    clear_cache
fi

if [ "$STOP_FLAG" = false ] && [ "$CLEAN_FLAG" = false ]; then
    # No recognized flags, show help
    show_usage
fi
