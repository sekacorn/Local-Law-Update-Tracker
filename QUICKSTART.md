# LLUT Quick Start Guide

## The Easiest Way to Run LLUT

Use the all-in-one `llut.sh` script in the project root. It handles everything automatically!

## Basic Usage

### Start the Application

```bash
./llut.sh
```

This will:

- [OK] Check for Python and Node.js
- [OK] Create virtual environment if needed
- [OK] Install dependencies automatically
- [OK] Start the backend on http://localhost:8000
- [OK] Start the frontend Tauri window
- [OK] Show you the status and log locations

### Stop the Application

```bash
./llut.sh --stop
```

or

```bash
./llut.sh -s
```

This will:

- [OK] Gracefully stop backend and frontend
- [OK] Kill any stray processes
- [OK] Clean up PID files

### Clear Cache Files

```bash
./llut.sh --clean
```

or

```bash
./llut.sh -c
```

This will clear:

- [OK] Application cache (`app_data/cache/`)
- [OK] Log files (`backend.log`, `frontend.log`)
- [OK] Python cache (`__pycache__/`, `*.pyc`)
- [OK] PID files

### Stop AND Clear Cache (Combined)

```bash
./llut.sh --stop --clean
```

or

```bash
./llut.sh -s -c
```

### Restart the Application

```bash
./llut.sh --restart
```

or

```bash
./llut.sh -r
```

### Restart and Clear Cache

```bash
./llut.sh --restart --clean
```

or

```bash
./llut.sh -r -c
```

### Check Status

```bash
./llut.sh --status
```

Shows:

- Backend status (running/stopped)
- Frontend status (running/stopped)
- Database size
- Cache size and file count

### View Recent Logs

```bash
./llut.sh --logs
```

Shows the last 20 lines from both backend and frontend logs.

### Help

```bash
./llut.sh --help
```

or

```bash
./llut.sh -h
```

## Complete Command Reference

| Command     | Short | Description             |
| ----------- | ----- | ----------------------- |
| `./llut.sh` | -     | Start the application   |
| `--stop`    | `-s`  | Stop the application    |
| `--clean`   | `-c`  | Clear cache files       |
| `--restart` | `-r`  | Restart the application |
| `--status`  | -     | Show application status |
| `--logs`    | -     | Show recent logs        |
| `--help`    | `-h`  | Show help message       |

## Common Workflows

### First Time Setup

```bash
# Install dependencies
make install

# Start the app
./llut.sh
```

### Daily Development

```bash
# Morning: Start the app
./llut.sh

# ... work on code ...

# Evening: Stop the app
./llut.sh --stop
```

### Troubleshooting

```bash
# Check what's running
./llut.sh --status

# View logs
./llut.sh --logs

# Full restart with cache clear
./llut.sh -r -c
```

### Cleanup

```bash
# Stop and clear everything
./llut.sh --stop --clean

# Or use make for deeper clean
make clean
```

## What Happens When You Start?

1. **Dependency Check**: Verifies Python 3.11+ and Node.js are installed
2. **Virtual Environment**: Creates/activates Python venv if needed
3. **Backend Setup**: Installs Python packages from requirements.txt
4. **Backend Start**: Launches FastAPI on port 8000
5. **Health Check**: Waits for backend to be ready (up to 30 seconds)
6. **Frontend Setup**: Installs npm packages if needed
7. **Frontend Start**: Launches Tauri development window
8. **PID Files**: Saves process IDs for later management
9. **Ready**: Shows URLs and log locations

## Where Are Things?

- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: Tauri desktop window
- **Database**: `app_data/llut.db`
- **Cache**: `app_data/cache/`
- **Logs**: `backend.log` and `frontend.log` in project root
- **PID Files**: `.backend.pid` and `.frontend.pid` in project root

## Process Management

The script tracks processes using PID files:

- `.backend.pid` - Backend process ID
- `.frontend.pid` - Frontend process ID

When you stop, it:

1. Reads PID files
2. Sends SIGTERM (graceful shutdown)
3. Waits up to 10 seconds
4. Sends SIGKILL if still running (force kill)
5. Removes PID files
6. Kills any stray processes

## Cache Management

Cache includes:

- **App Cache**: `app_data/cache/` - Downloaded documents
- **Log Files**: `backend.log`, `frontend.log`
- **Python Cache**: `__pycache__/`, `*.pyc` files
- **PID Files**: `.backend.pid`, `.frontend.pid`

Note: `--clean` does NOT delete:

- Database (`app_data/llut.db`)
- Settings (`app_data/settings.json`)
- Node modules (`apps/desktop/node_modules/`)
- Virtual environment (`backend/venv/`)

For those, use `make clean` or `make reset`.

## Error Handling

### Backend Won't Start

```bash
# Check the logs
./llut.sh --logs

# Or view the full backend log
cat backend.log

# Common fixes:
# - Check Python version: python --version (need 3.11+)
# - Reinstall deps: cd backend && pip install -r requirements.txt
# - Check port 8000 is free: lsof -i :8000
```

### Frontend Won't Start

```bash
# Check the logs
./llut.sh --logs

# Or view the full frontend log
cat frontend.log

# Common fixes:
# - Check Node version: node --version
# - Reinstall deps: cd apps/desktop && npm install
# - Check Rust/Cargo: cargo --version
```

### Can't Stop

```bash
# Force stop everything
./llut.sh --stop

# If that fails, manual cleanup:
pkill -f "uvicorn app.main:app"
pkill -f "tauri dev"
rm -f .backend.pid .frontend.pid
```

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or restart the app (will kill old processes)
./llut.sh --restart
```

## Tips & Tricks

### Background Mode

The app runs in the background, so you can close the terminal after starting.

```bash
./llut.sh
# Terminal can be closed, app keeps running
```

### Status Monitoring

Check status without opening logs:

```bash
watch -n 5 './llut.sh --status'
```

### Auto-restart on Changes

The backend and frontend already auto-reload on file changes when started with `./llut.sh`!

### Clean Restart

When things are acting weird:

```bash
./llut.sh -r -c  # Restart and clear cache
```

### Full Reset

Nuclear option (deletes database too):

```bash
./llut.sh --stop
make reset  # Confirm when prompted
./llut.sh
```

## Windows Users

### Git Bash

```bash
# Works in Git Bash
bash llut.sh
bash llut.sh --stop --clean
```

### Command Prompt

```cmd
REM Use the batch wrapper
llut.bat dev    REM Start
llut.bat stop   REM Stop
```

### PowerShell

```powershell
# Use bash from Git for Windows
& "C:\Program Files\Git\bin\bash.exe" llut.sh
```

## Comparison with Make Commands

| llut.sh              | Makefile                | Notes                        |
| -------------------- | ----------------------- | ---------------------------- |
| `./llut.sh`          | `make dev`              | llut.sh shows more info      |
| `./llut.sh -s`       | `make stop`             | Same functionality           |
| `./llut.sh -c`       | `make clean`            | llut.sh lighter, make deeper |
| `./llut.sh -r`       | `make stop && make dev` | llut.sh is one command       |
| `./llut.sh --status` | -                       | llut.sh only                 |
| `./llut.sh --logs`   | -                       | llut.sh only                 |
| -                    | `make build`            | Use make for builds          |
| -                    | `make reset`            | Use make for DB reset        |

**Recommendation**: Use `./llut.sh` for daily development, `make` for builds and resets.

## Need More Help?

- Full documentation: See `README.md`
- Script details: See `scripts/README.md`
- Build status: See `BUILD_STATUS.md`
- Design spec: See `LLUT_ClaudeCode_DesignDoc.txt`

---

**TL;DR**: Just run `./llut.sh` to start everything!
