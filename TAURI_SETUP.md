# Tauri Desktop Application Setup

## Overview

LLUT is packaged as a desktop application using Tauri. The Tauri app bundles:
- React frontend (Vite + TypeScript)
- FastAPI backend as a sidecar process
- All necessary dependencies

## Prerequisites

### Required Software

1. **Node.js** (>= 18.0.0) - For frontend development
   - Current: v24.9.0 [OK]
   - npm >= 9.0.0 (Current: 11.6.0 [OK])

2. **Python** (>= 3.8) - For backend server
   - Must be available in PATH
   - pip for package management

3. **Rust** - Required by Tauri
   - Install from: https://rustup.rs/
   - Required for building the desktop application

4. **Platform-specific build tools**:
   - **Windows**: Visual Studio Build Tools or Visual Studio Community
   - **macOS**: Xcode Command Line Tools
   - **Linux**: See Tauri docs for distribution-specific requirements

## Project Structure

```
LLUT/
├── apps/
│   └── desktop/              # Tauri desktop app
│       ├── src/              # React frontend source
│       ├── src-tauri/        # Tauri configuration
│       │   ├── binaries/     # Sidecar scripts
│       │   │   ├── llut-backend-x86_64-pc-windows-msvc.bat
│       │   │   ├── llut-backend-x86_64-apple-darwin
│       │   │   └── llut-backend-x86_64-unknown-linux-gnu
│       │   └── tauri.conf.json
│       └── package.json
├── backend/                  # FastAPI backend
│   ├── app/                  # Application code
│   ├── requirements.txt      # Python dependencies
│   └── venv/                 # Virtual environment (dev only)
└── scripts/
    ├── run_backend.bat       # Windows backend startup
    ├── run_backend.sh        # Linux/macOS backend startup
    └── build_sidecar.py      # Optional: PyInstaller builder
```

## Development Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Access API at: http://localhost:8000
# Health check: http://localhost:8000/health
```

### 2. Frontend Setup

```bash
# Navigate to desktop app
cd apps/desktop

# Install dependencies (already done)
npm install

# Run development server
npm run dev

# Frontend runs at: http://localhost:1420
```

### 3. Tauri Development Mode

To run the full desktop application with backend sidecar:

```bash
cd apps/desktop

# Run Tauri in development mode
npm run tauri:dev
```

**Important**: In development mode, Tauri will execute the sidecar scripts in `src-tauri/binaries/`. These scripts require:
- Python to be available in PATH
- Backend dependencies installed (uvicorn, fastapi, etc.)

## Building for Production

### Prerequisites for Building

1. **Install Rust** (if not already installed):
   ```bash
   # Windows/macOS/Linux:
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Ensure Python dependencies are available**:
   The bundled app needs Python runtime on the target system. For a truly standalone build, consider using PyInstaller (see `scripts/build_sidecar.py`).

### Build Command

```bash
cd apps/desktop

# Build for current platform
npm run tauri:build
```

The built application will be in:
- **Windows**: `src-tauri/target/release/bundle/msi/` or `.exe`
- **macOS**: `src-tauri/target/release/bundle/dmg/` or `.app`
- **Linux**: `src-tauri/target/release/bundle/appimage/` or `.deb`

## Backend Sidecar Configuration

### How It Works

1. **Tauri Configuration** (`tauri.conf.json`):
   - `externalBin`: Lists platform-specific sidecar binaries
   - `bundle.resources`: Includes backend Python code
   - `shell.scope`: Allows launching the backend sidecar

2. **Sidecar Scripts**:
   - Platform-specific wrapper scripts in `src-tauri/binaries/`
   - Scripts start the FastAPI backend server on localhost:8000
   - Named with target triple for automatic platform selection

3. **Frontend Connection**:
   - React app connects to `http://localhost:8000`
   - Uses axios/fetch for API calls
   - TanStack Query for data fetching/caching

### Platform-Specific Sidecar Names

- **Windows**: `llut-backend-x86_64-pc-windows-msvc.bat`
- **macOS (Intel)**: `llut-backend-x86_64-apple-darwin`
- **macOS (ARM)**: `llut-backend-aarch64-apple-darwin` (needs creation)
- **Linux**: `llut-backend-x86_64-unknown-linux-gnu`

## Tauri Configuration Details

### Security Allowlist

```json
{
  "shell": {
    "sidecar": true,
    "scope": [{"name": "llut-backend", "sidecar": true}]
  },
  "http": {
    "all": true,
    "scope": ["http://localhost:8000/**"]
  },
  "fs": {
    "readFile": true,
    "writeFile": true,
    "scope": ["$APPDATA/*", "$APPDATA/**"]
  }
}
```

- **shell.sidecar**: Allows launching backend process
- **http.scope**: Restricts HTTP requests to localhost:8000
- **fs.scope**: Limits file access to app data directory

## Alternative: PyInstaller Build (Optional)

For a fully standalone application without requiring Python on target systems:

```bash
# Activate backend virtual environment first
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run PyInstaller build script
cd ..
python scripts/build_sidecar.py
```

This creates a standalone executable in `apps/desktop/src-tauri/binaries/`.

**Note**: PyInstaller builds can be large (50-100MB+) as they bundle the entire Python runtime.

## Testing the Build

### 1. Test Backend Standalone

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visit http://localhost:8000/health - should return JSON with status

### 2. Test Frontend Standalone

```bash
cd apps/desktop
npm run dev
```

Visit http://localhost:1420 - should show React app

### 3. Test Sidecar Script

```bash
# Windows
cd apps/desktop/src-tauri/binaries
llut-backend-x86_64-pc-windows-msvc.bat

# Linux/macOS
cd apps/desktop/src-tauri/binaries
./llut-backend-x86_64-apple-darwin  # or linux-gnu
```

Backend should start on http://localhost:8000

### 4. Test Full Tauri App

```bash
cd apps/desktop
npm run tauri:dev
```

Desktop window should open with frontend + backend running

## Troubleshooting

### Backend doesn't start in Tauri

**Issue**: Sidecar process fails to start

**Solutions**:
- Check Python is in PATH: `python --version`
- Verify backend dependencies: `cd backend && pip list`
- Check sidecar script permissions (Unix): `chmod +x binaries/llut-backend-*`
- Review Tauri logs in console

### Port 8000 already in use

**Issue**: Backend can't bind to port 8000

**Solutions**:
- Kill existing process:
  - Windows: `taskkill /F /IM python.exe`
  - Unix: `pkill -f uvicorn`
- Change port in both backend and frontend config

### Build fails with Rust errors

**Issue**: Tauri build fails during Rust compilation

**Solutions**:
- Update Rust: `rustup update`
- Clear target directory: `rm -rf src-tauri/target`
- Check platform requirements: https://tauri.app/v1/guides/building/

### Missing dependencies in built app

**Issue**: Built application crashes due to missing Python/libs

**Solutions**:
- Use PyInstaller to bundle Python runtime
- Include requirements.txt in bundle resources
- Test on clean system without Python installed

## Next Steps

1. [OK] Tauri configuration complete
2. [OK] Sidecar scripts created for all platforms
3. [OK] Backend bundled as resources
4. [PENDING] Test Tauri dev mode
5. [PENDING] Test production build
6. [PENDING] Create installers for distribution

## Resources

- Tauri Docs: https://tauri.app/
- Tauri Sidecar Guide: https://tauri.app/v1/guides/building/sidecar
- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
