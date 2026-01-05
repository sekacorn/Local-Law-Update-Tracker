# LLUT Scripts Guide

Quick reference for starting and stopping the LLUT frontend with proper memory cleanup.

## Available Scripts

### Windows Scripts (.bat)
- `start-frontend.bat` - Start the React frontend
- `stop-frontend.bat` - Stop frontend and clean up memory

### Linux/Mac Scripts (.sh)
- `start-frontend.sh` - Start the React frontend
- `stop-frontend.sh` - Stop frontend and clean up memory

---

## Start Frontend

### Windows:
**Option 1: Double-click**
- Just double-click `start-frontend.bat` in File Explorer

**Option 2: Command Prompt**
```cmd
start-frontend.bat
```

**Option 3: PowerShell**
```powershell
.\start-frontend.bat
```

### Linux/Mac:
```bash
./start-frontend.sh
```

### What It Does:
- Checks if Node.js and npm are installed
- Installs dependencies if `node_modules` is missing
- Starts Vite dev server on http://localhost:1420/
- Shows version information
- Displays helpful messages

### Expected Output:
```
============================================================
Starting LLUT Frontend
============================================================

Node.js version: v24.9.0
npm version: 11.6.0

Starting Vite dev server...
Frontend will be available at: http://localhost:1420/

Press Ctrl+C to stop the server

  VITE v5.4.21  ready in 479 ms

  ➜  Local:   http://localhost:1420/
```

---

## Stop Frontend

### Windows:
**Option 1: Double-click**
- Just double-click `stop-frontend.bat` in File Explorer

**Option 2: Command Prompt**
```cmd
stop-frontend.bat
```

**Option 3: PowerShell**
```powershell
.\stop-frontend.bat
```

### Linux/Mac:
```bash
./stop-frontend.sh
```

### What It Does:
- Finds and kills all Node processes on port 1420
- Stops all Vite processes
- Removes Vite cache (`node_modules/.vite`)
- Removes build artifacts (`dist` folder)
- Cleans up temporary files
- Frees up memory

### Expected Output:
```
============================================================
Stopping LLUT Frontend
============================================================

Searching for Node processes on port 1420...
Found process with PID: 12345
[OK] Stopped process 12345

Stopping Vite processes...

Cleaning up cache and temporary files...
Removing Vite cache...
[OK] Vite cache cleared
Removing dist folder...
[OK] Dist folder cleared

============================================================
Frontend stopped and cleaned up!
============================================================

Memory cleanup completed:
  - Killed Node processes on port 1420
  - Removed Vite cache
  - Removed build artifacts
```

---

## Troubleshooting

### "Node.js is not installed"
**Solution**: Install Node.js from https://nodejs.org/
Make sure to check "Add to PATH" during installation

### "Port 1420 is already in use"
**Solution**: Run the stop script to kill existing processes:
```cmd
stop-frontend.bat
```
Then start again:
```cmd
start-frontend.bat
```

### "npm install fails"
**Solution**: Try cleaning npm cache:
```cmd
cd apps\desktop
npm cache clean --force
npm install
```

### Script doesn't run on Linux/Mac
**Solution**: Make sure scripts are executable:
```bash
chmod +x start-frontend.sh stop-frontend.sh
```

### Process won't stop
**Solution**: Use more aggressive cleanup:

**Windows:**
```cmd
taskkill /F /IM node.exe
```

**Linux/Mac:**
```bash
pkill -9 node
```

---

## Memory Usage

### Before Cleanup:
- Vite cache: ~50-100 MB
- Node processes: ~100-200 MB
- Dist folder: ~5-10 MB

### After Cleanup:
- All cleared = **~150-300 MB freed**

---

## Quick Commands

### Full Workflow (Windows):
```cmd
REM Start frontend
start-frontend.bat

REM ... do your work ...

REM Stop and clean up
stop-frontend.bat
```

### Full Workflow (Linux/Mac):
```bash
# Start frontend
./start-frontend.sh

# ... do your work ...

# Stop and clean up
./stop-frontend.sh
```

---

## Advanced Usage

### Start Frontend in Background (Linux/Mac):
```bash
nohup ./start-frontend.sh > frontend.log 2>&1 &
```

### Monitor Frontend Logs (Linux/Mac):
```bash
tail -f frontend.log
```

### Check What's Running on Port 1420:

**Windows:**
```cmd
netstat -ano | findstr :1420
```

**Linux/Mac:**
```bash
lsof -i :1420
```

---

## Alternative: Manual Commands

If you prefer to run commands manually:

### Start:
```bash
cd apps/desktop
npm install    # Only needed first time
npm run dev
```

### Stop:
- Press `Ctrl+C` in the terminal where it's running

### Clean Up Cache:
```bash
cd apps/desktop
rm -rf node_modules/.vite
rm -rf dist
```

---

## Script Locations

All scripts are in the project root directory:

```
LLUT/
├── start-frontend.bat     (Windows)
├── stop-frontend.bat      (Windows)
├── start-frontend.sh      (Linux/Mac)
├── stop-frontend.sh       (Linux/Mac)
└── apps/
    └── desktop/
        ├── node_modules/
        ├── dist/
        └── package.json
```

---

## Best Practices

1. **Always use stop script** - Don't just close the terminal
   - Ensures proper cleanup
   - Frees memory properly
   - Removes cache files

2. **Check if backend is running** - Frontend needs backend API
   - Backend should be on http://localhost:8000/
   - Start backend first if not running

3. **Restart after errors** - If frontend acts weird:
   ```cmd
   stop-frontend.bat
   start-frontend.bat
   ```

4. **Clear browser cache** - If UI doesn't update:
   - Press `Ctrl+Shift+R` (hard refresh)
   - Or clear browser cache

---

## Emergency Stop

If scripts don't work and you need to force-stop everything:

### Windows (Nuclear Option):
```cmd
taskkill /F /IM node.exe
```

### Linux/Mac (Nuclear Option):
```bash
pkill -9 node
```

**WARNING**: This kills ALL Node processes on your system!

---

## Related Scripts

You can create similar scripts for the backend:

**start-backend.bat:**
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

**stop-backend.bat:**
```cmd
taskkill /F /FI "WINDOWTITLE eq *uvicorn*"
```

---

## Tips

- **Keep terminals open** - See logs and errors
- **Use separate terminals** - One for backend, one for frontend
- **Check logs** - Look for error messages
- **Clean regularly** - Run stop script to free memory
- **Update dependencies** - Run `npm install` occasionally

---

**Happy developing!**

For more help, see:
- `README.md` - Full project documentation
- `QUICKSTART.md` - Quick start guide
- `FRONTEND_ENHANCEMENTS.md` - Frontend features
