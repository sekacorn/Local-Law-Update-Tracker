#!/usr/bin/env python3
"""
Build script to prepare backend sidecar for Tauri bundling
Uses PyInstaller to package the FastAPI backend as a standalone executable
"""
import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TAURI_DIR = PROJECT_ROOT / "apps" / "desktop" / "src-tauri"
BINARIES_DIR = TAURI_DIR / "binaries"

def main():
    """Build the backend sidecar executable"""
    print("=" * 60)
    print("LLUT Backend Sidecar Builder")
    print("=" * 60)

    # Check if we're in a virtual environment
    if not hasattr(sys, 'base_prefix') or sys.base_prefix == sys.prefix:
        print("\nWARNING: Not running in a virtual environment!")
        print("Please activate the backend virtual environment first:")
        print("  cd backend")
        print("  source venv/bin/activate  # Linux/Mac")
        print("  venv\\Scripts\\activate     # Windows")
        sys.exit(1)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("\nPyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Determine platform
    system = platform.system()
    if system == "Windows":
        binary_name = "llut-backend.exe"
    else:
        binary_name = "llut-backend"

    print(f"\nBuilding for: {system}")
    print(f"Binary name: {binary_name}")

    # Create binaries directory if it doesn't exist
    BINARIES_DIR.mkdir(parents=True, exist_ok=True)

    # Create PyInstaller spec file
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{BACKEND_DIR / "app" / "main.py"}'],
    pathex=['{BACKEND_DIR}'],
    binaries=[],
    datas=[
        ('{BACKEND_DIR / "app"}', 'app'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'aiosqlite',
        'httpx',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{binary_name.replace(".exe", "")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    spec_file = BACKEND_DIR / "backend_sidecar.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)

    print(f"\nCreated spec file: {spec_file}")

    # Run PyInstaller
    print("\nRunning PyInstaller...")
    print("This may take a few minutes...\n")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        str(spec_file)
    ]

    subprocess.run(cmd, cwd=BACKEND_DIR, check=True)

    # Copy the built executable to Tauri binaries directory
    source_exe = BACKEND_DIR / "dist" / binary_name
    target_exe = BINARIES_DIR / binary_name

    if source_exe.exists():
        print(f"\nCopying {binary_name} to Tauri binaries directory...")
        shutil.copy2(source_exe, target_exe)
        print(f"[OK] Copied to: {target_exe}")

        # Make executable on Unix systems
        if system != "Windows":
            os.chmod(target_exe, 0o755)
            print("[OK] Made executable")
    else:
        print(f"\n[ERROR] ERROR: Built executable not found at {source_exe}")
        sys.exit(1)

    # Clean up build artifacts
    print("\nCleaning up build artifacts...")
    for dir_name in ["build", "dist"]:
        dir_path = BACKEND_DIR / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"[OK] Removed {dir_name}/")

    if spec_file.exists():
        spec_file.unlink()
        print(f"[OK] Removed {spec_file.name}")

    print("\n" + "=" * 60)
    print("[OK] Backend sidecar built successfully!")
    print("=" * 60)
    print(f"\nBinary location: {target_exe}")
    print(f"Binary size: {target_exe.stat().st_size / 1024 / 1024:.2f} MB")
    print("\nNext steps:")
    print("1. Test the binary: cd apps/desktop/src-tauri")
    print("2. Run: npm run tauri build")
    print("\n")

if __name__ == "__main__":
    main()
