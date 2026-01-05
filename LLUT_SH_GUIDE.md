# llut.sh - All-in-One Runner Script

## Overview

`llut.sh` is a comprehensive shell script that manages your entire LLUT application from a single command. It replaces the need to manually run multiple scripts or remember different commands.

## Why Use llut.sh?

- **Single Command** - Start everything with one command
- **Auto-Detection** - Checks for dependencies automatically
- **Smart Setup** - Creates venv, installs packages, starts services
- **Status Monitoring** - See what's running at a glance
- **Log Management** - View logs without opening files
- **Cache Control** - Clear cache files easily
- **Graceful Shutdown** - Stops processes cleanly
- **Error Recovery** - Handles stray processes and cleanup

## Key Features

### 1. Automatic Dependency Management

- Checks for Python 3.11+ and Node.js
- Creates Python virtual environment if needed
- Installs backend and frontend dependencies
- No manual setup required!

### 2. Process Management

- Tracks backend and frontend PIDs
- Graceful shutdown (SIGTERM)
- Force kill if needed (SIGKILL)
- Cleans up stray processes
- Removes PID files

### 3. Health Monitoring

- Waits for backend to be ready (up to 30s)
- Shows real-time status
- Displays database and cache sizes
- Shows running process PIDs

### 4. Cache Management

- Clears app cache directory
- Removes log files
- Cleans Python cache
- Shows space freed
- Preserves database and settings

### 5. Color-Coded Output

- 🟢 Green = Success/Running
- 🟡 Yellow = Warning/Stopped
- 🔴 Red = Error
- 🔵 Blue = Info
- 🔷 Cyan = Headers

## Quick Reference Card

```
╔══════════════════════════════════════════════════════╗
║              LLUT.SH QUICK REFERENCE                 ║
╠══════════════════════════════════════════════════════╣
║ START        ./llut.sh                               ║
║ STOP         ./llut.sh --stop                        ║
║ RESTART      ./llut.sh --restart                     ║
║ CLEAN        ./llut.sh --clean                       ║
║ STATUS       ./llut.sh --status                      ║
║ LOGS         ./llut.sh --logs                        ║
║ HELP         ./llut.sh --help                        ║
╠══════════════════════════════════════════════════════╣
║ STOP + CLEAN ./llut.sh -s -c                         ║
║ RESTART + CLEAN ./llut.sh -r -c                      ║
╚══════════════════════════════════════════════════════╝
```

## Usage Examples

### Starting the App

```bash
$ ./llut.sh

Starting LLUT Application
=========================

Starting backend...
Creating virtual environment...
Installing backend dependencies...
Starting FastAPI on http://localhost:8000
Backend started (PID: 12345)
Waiting for backend...
Backend is ready!

Starting frontend...
Installing frontend dependencies...
Starting Tauri...
Frontend started (PID: 12346)

================================
LLUT is running!
================================

Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
Frontend: Tauri window

Logs:
  Backend:  /path/to/project/backend.log
  Frontend: /path/to/project/frontend.log

To stop: ./llut.sh --stop
Status:  ./llut.sh --status
```

### Checking Status

```bash
$ ./llut.sh --status

Application Status
==================
Backend:  Running (PID: 12345)
Frontend: Running (PID: 12346)

Database: 2.5MB
Cache:    45MB (127 files)
```

### Stopping the App

```bash
$ ./llut.sh --stop

Stopping LLUT...
Stopping backend (PID: 12345)...
Backend stopped
Stopping frontend (PID: 12346)...
Frontend stopped

Cleaning up stray processes...

Application stopped successfully
```

### Clearing Cache

```bash
$ ./llut.sh --clean

Clearing cache files...
Clearing app_data/cache...
Clearing backend.log...
Clearing frontend.log...
Clearing Python cache...

Cache cleared: 47MB freed
```

### Combined Operations

```bash
# Stop and clean
$ ./llut.sh --stop --clean

# Restart with clean cache
$ ./llut.sh --restart --clean

# Using short flags
$ ./llut.sh -s -c
$ ./llut.sh -r -c
```

### Viewing Logs

```bash
$ ./llut.sh --logs

Recent Logs
===========

Backend (last 20 lines):
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
...

Frontend (last 20 lines):
[Tauri] Starting development server...
[Vite] ready in 823ms
...
```

## What Gets Cleared with --clean?

### Cleared:

- `app_data/cache/` - Downloaded documents cache
- `backend.log` - Backend log file
- `frontend.log` - Frontend log file
- `__pycache__/` - Python bytecode cache
- `*.pyc` - Compiled Python files
- `.backend.pid` - Backend PID file
- `.frontend.pid` - Frontend PID file

### NOT Cleared:

- `app_data/llut.db` - Database (use `make reset` for this)
- `app_data/settings.json` - User settings
- `backend/venv/` - Virtual environment
- `apps/desktop/node_modules/` - Node modules
- Build artifacts (use `make clean` for deeper cleaning)

## Error Recovery

### Backend Won't Start

**Symptom**: Backend fails to start or health check times out

**Solutions**:

```bash
# Check logs
./llut.sh --logs

# Full restart with cache clear
./llut.sh -r -c

# Manual check
cat backend.log

# Check Python
python --version  # Should be 3.11+

# Reinstall deps
cd backend
pip install -r requirements.txt
```

### Frontend Won't Start

**Symptom**: Frontend window doesn't appear

**Solutions**:

```bash
# Check logs
./llut.sh --logs

# Check frontend log
cat frontend.log

# Check Node
node --version

# Reinstall deps
cd apps/desktop
npm install
```

### Port Already in Use

**Symptom**: "Address already in use" error

**Solutions**:

```bash
# Stop everything
./llut.sh --stop

# Find what's using port 8000
lsof -i :8000

# Kill it manually
kill -9 <PID>

# Restart
./llut.sh
```

### Can't Stop Processes

**Symptom**: Processes won't stop with --stop

**Solutions**:

```bash
# Try stop again
./llut.sh --stop

# Manual kill
pkill -9 -f "uvicorn app.main:app"
pkill -9 -f "tauri dev"

# Remove PID files
rm -f .backend.pid .frontend.pid

# Restart
./llut.sh
```

## Advanced Usage

### Running in Background

```bash
# Start and detach
nohup ./llut.sh > /dev/null 2>&1 &

# Check status later
./llut.sh --status

# Stop when done
./llut.sh --stop
```

### Monitoring Status Continuously

```bash
# Update every 5 seconds
watch -n 5 './llut.sh --status'
```

### Tailing Logs in Real-Time

```bash
# Backend
tail -f backend.log

# Frontend
tail -f frontend.log

# Both (requires multitail)
multitail backend.log frontend.log
```

### Scheduled Restarts

```bash
# Cron job to restart daily at 3am
0 3 * * * cd /path/to/llut && ./llut.sh -r -c
```

## Integration with Other Tools

### With Make

```bash
# Install deps with make
make install

# Run with llut.sh
./llut.sh

# Build with make
make build
```

### With Git

```bash
# Pull updates
git pull

# Restart app
./llut.sh -r
```

### With systemd (Linux)

Create `/etc/systemd/system/llut.service`:

```ini
[Unit]
Description=LLUT Application
After=network.target

[Service]
Type=forking
User=youruser
WorkingDirectory=/path/to/llut
ExecStart=/path/to/llut/llut.sh
ExecStop=/path/to/llut/llut.sh --stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Performance Tips

### Faster Startups

- Keep venv and node_modules (don't delete them)
- Use `./llut.sh --restart` instead of `--stop` then start

### Reduce Resource Usage

- Use `./llut.sh --clean` regularly to clear cache
- Monitor with `./llut.sh --status`

### Debugging

- Always check `./llut.sh --logs` first
- Use `./llut.sh --status` to verify what's running
- Check individual log files for full details

## Comparison with Other Methods

| Feature           | llut.sh | make dev | Scripts manually |
| ----------------- | ------- | -------- | ---------------- |
| Single command    | Yes     | Yes      | No               |
| Auto-install deps | Yes     | No       | No               |
| Status check      | Yes     | No       | No               |
| Log viewer        | Yes     | No       | No               |
| Cache management  | Yes     | Yes      | No               |
| Restart command   | Yes     | No       | No               |
| PID tracking      | Yes     | Yes      | No               |
| Health check      | Yes     | Yes      | No               |

## Best Practices

1. **Always use llut.sh for daily development**

   ```bash
   ./llut.sh          # Start
   # ... work ...
   ./llut.sh --stop   # End of day
   ```

2. **Check status when in doubt**

   ```bash
   ./llut.sh --status
   ```

3. **Clean cache weekly**

   ```bash
   ./llut.sh --clean
   ```

4. **Restart after pulling changes**

   ```bash
   git pull
   ./llut.sh -r
   ```

5. **Use --logs for troubleshooting**
   ```bash
   ./llut.sh --logs
   ```

## Troubleshooting Checklist

- [ ] Check status: `./llut.sh --status`
- [ ] View logs: `./llut.sh --logs`
- [ ] Try restart: `./llut.sh -r`
- [ ] Clear cache: `./llut.sh -c`
- [ ] Full restart with clean: `./llut.sh -r -c`
- [ ] Check backend log: `cat backend.log`
- [ ] Check frontend log: `cat frontend.log`
- [ ] Verify dependencies: `python --version`, `node --version`
- [ ] Manual stop: `pkill -f uvicorn; pkill -f tauri`
- [ ] Remove PIDs: `rm -f .backend.pid .frontend.pid`

## Summary

`llut.sh` is your one-stop command for managing LLUT:

- **Start**: `./llut.sh`
- **Stop**: `./llut.sh -s`
- **Restart**: `./llut.sh -r`
- **Clean**: `./llut.sh -c`
- **Status**: `./llut.sh --status`
- **Logs**: `./llut.sh --logs`

**It's that simple!**

---

For more details, see [QUICKSTART.md](QUICKSTART.md) or run `./llut.sh --help`.
