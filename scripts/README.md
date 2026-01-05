# LLUT Build & Management Scripts

This directory contains scripts for building, running, and managing the Local Law Update Tracker (LLUT) application.

## Quick Start

All scripts can be run via the Makefile from the project root:

```bash
# Show all available commands
make help

# Install dependencies
make install

# Start development environment
make dev

# Build production application
make build

# Stop all processes
make stop

# Clean temporary files
make clean

# Reset database
make reset
```

## Scripts Overview

### 1. `dev_run.sh` - Development Environment

Starts both the FastAPI backend and Tauri frontend in development mode.

**Usage:**
```bash
bash scripts/dev_run.sh
# or
make dev
```

**What it does:**
- Creates Python virtual environment if needed
- Installs backend dependencies
- Starts FastAPI server on http://localhost:8000
- Starts Tauri development window
- Creates log files: `backend.log` and `frontend.log`
- Saves PIDs to `.backend.pid` and `.frontend.pid`

**Stopping:**
- Press `Ctrl+C` to stop both processes
- Or run `make stop`

### 2. `build_desktop.sh` - Production Build

Builds the distributable desktop application with embedded backend.

**Usage:**
```bash
bash scripts/build_desktop.sh
# or
make build
```

**What it does:**
- Installs all dependencies
- Creates standalone backend executable with PyInstaller
- Builds Tauri application with embedded backend
- Generates platform-specific installers:
  - **Windows:** `.exe` installer (NSIS) and/or `.msi`
  - **macOS:** `.dmg` and `.app` bundle
  - **Linux:** `.deb`, `.AppImage`, etc.

**Output locations:**
- Installers: `apps/desktop/src-tauri/target/release/bundle/`
- Executable: `apps/desktop/src-tauri/target/release/llut` (or `.exe`)
- Backend: `backend/dist/llut-backend` (or `.exe`)

**Requirements:**
- Python 3.11+
- Node.js
- Rust/Cargo (for Tauri)

### 3. `start_app.sh` - Start Built Application

Launches the production-built application.

**Usage:**
```bash
bash scripts/start_app.sh
# or
make start
```

**What it does:**
- Finds the built executable
- Launches the application in the background
- Works with installers or standalone executables

**Note:** You must run `make build` first!

### 4. `stop_all.sh` - Stop All Processes

Stops all running LLUT development processes.

**Usage:**
```bash
bash scripts/stop_all.sh
# or
make stop
```

**What it does:**
- Reads PID files and kills processes gracefully
- Force kills if processes don't stop within 10 seconds
- Cleans up stray processes:
  - uvicorn (backend)
  - Tauri dev server
  - Node.js dev servers
- Removes PID files

### 5. `cleanup.sh` - Clean Temporary Files

Removes build artifacts, caches, and temporary files to reclaim disk space.

**Usage:**
```bash
bash scripts/cleanup.sh
# or
make clean
```

**What it cleans:**

**Backend:**
- Python cache (`__pycache__`, `*.pyc`, `*.pyo`)
- PyInstaller artifacts (`build/`, `dist/`, `*.spec`)
- pytest cache
- Coverage reports

**Frontend:**
- Tauri build artifacts (`target/`)
- Vite cache
- Build directories (`dist/`, `build/`)

**Application:**
- Runtime cache (`app_data/cache/`)
- Log files (`backend.log`, `frontend.log`)
- PID files

**System:**
- Editor temp files (`*~`, `*.swp`)
- OS temp files (`.DS_Store` on macOS)

**What it preserves:**
- Database (`app_data/llut.db`)
- Settings (`app_data/settings.json`)
- Pinned documents
- `node_modules/` (optional - uncomment in script to remove)

**Output:**
- Shows number of items cleaned
- Reports space freed

### 6. `reset_db.sh` - Reset Database

Deletes the local database and cache, resetting the application to a fresh state.

**Usage:**
```bash
bash scripts/reset_db.sh
# or
make reset
```

**Interactive mode (default):**
```bash
make reset
# Prompts: "Are you sure you want to continue? (y/N):"
```

**Force mode (no prompt):**
```bash
bash scripts/reset_db.sh --force
```

**What it deletes:**
- `app_data/llut.db` (database)
- `app_data/cache/` (all cached files)
- Database journal/WAL files

**What it preserves:**
- `app_data/settings.json` (API keys and preferences)

**After reset:**
- Empty database and cache directories are recreated
- Run sync to download data again

## Platform Compatibility

All scripts are written for Bash and are compatible with:
- **Windows:** Git Bash, MSYS2, WSL
- **macOS:** Built-in Bash/Zsh
- **Linux:** Bash

## Requirements

### Development
- Python 3.11 or higher
- Node.js (latest LTS recommended)
- Rust and Cargo (for Tauri)
- Git Bash (Windows only)

### Build Tools
- PyInstaller (installed automatically)
- Tauri CLI (installed via npm)

## Troubleshooting

### Backend won't start
```bash
# Check backend.log for errors
cat backend.log

# Verify Python version
python --version  # Should be 3.11+

# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

### Frontend won't start
```bash
# Check frontend.log
cat frontend.log

# Reinstall Node modules
cd apps/desktop
rm -rf node_modules
npm install
```

### Build fails
```bash
# Clean everything first
make clean

# Verify Rust is installed
cargo --version

# Try building again
make build
```

### Processes won't stop
```bash
# Force stop
bash scripts/stop_all.sh

# Manual cleanup
pkill -f uvicorn
pkill -f "tauri dev"

# Remove PID files
rm -f .backend.pid .frontend.pid
```

### Out of disk space
```bash
# Clean all artifacts
make clean

# Check app data size
du -sh app_data/

# Reset database if too large
make reset
```

## Development Workflow

### First-time setup
```bash
make install
make dev
```

### Daily development
```bash
make dev                 # Start dev environment
# ... make changes ...
make stop                # Stop when done
```

### Testing changes
```bash
make dev
# In another terminal:
cd backend && pytest tests/
```

### Preparing release
```bash
make clean               # Clean old artifacts
make build               # Build production app
make start               # Test the build
```

### Maintenance
```bash
make clean               # Regular cleanup
make reset               # Reset database if corrupted
```

## Environment Variables

Scripts support these optional environment variables:

```bash
# Use specific Python command
export PYTHON_CMD=python3.11
make dev

# Specify port for backend
export BACKEND_PORT=8080
bash scripts/dev_run.sh

# Skip confirmations
export LLUT_NO_CONFIRM=1
make reset
```

## Logging

Development logs are written to:
- `backend.log` - FastAPI server output
- `frontend.log` - Tauri/Vite output

**View logs in real-time:**
```bash
# Backend
tail -f backend.log

# Frontend
tail -f frontend.log
```

## Notes

1. **Always stop processes before cleaning:** Run `make stop` before `make clean`
2. **Database resets are permanent:** Use `make reset` carefully
3. **Build artifacts are large:** The `target/` directory can be several GB
4. **PID files are temporary:** Don't commit `.backend.pid` or `.frontend.pid`
5. **Settings are preserved:** API keys survive resets but not full cleans

## Script Customization

All scripts use color-coded output:
- 🟢 **Green:** Success messages
- 🟡 **Yellow:** Warnings
- 🔵 **Blue:** Info messages
- 🔴 **Red:** Errors

To disable colors, set:
```bash
export NO_COLOR=1
```

## Getting Help

For issues with:
- **Scripts:** Check this README or script comments
- **Application:** See main project README
- **Tauri:** https://tauri.app/
- **FastAPI:** https://fastapi.tiangolo.com/

---

**Last updated:** 2025-12-24
