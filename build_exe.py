#!/usr/bin/env python
"""
TIC Nexus - Automated Build Script for PyInstaller

This script creates a standalone Windows executable using PyInstaller.

Usage:
    python build_exe.py [--clean] [--version VERSION]

Options:
    --clean     Clean build artifacts before building
    --version   Set version number for the distribution folder (default: 1.0.0)
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.resolve()
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
SPEC_FILE = PROJECT_ROOT / "tic_nexus.spec"


def clean_build():
    """Remove build artifacts."""
    print("Cleaning build artifacts...")
    
    dirs_to_remove = [BUILD_DIR, DIST_DIR]
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")
    
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
        print(f"  Removed: {SPEC_FILE}")
    
    print("Clean complete.\n")


def check_requirements():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("Install it with: pip install pyinstaller pyinstaller-hooks-contrib")
        sys.exit(1)


def create_spec_file():
    """Create the PyInstaller spec file if it doesn't exist."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for TIC Nexus."""

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config.ini', '.'),
    ],
    hiddenimports=[
        'bcrypt',
        'passlib.handlers.bcrypt',
        'passlib.handlers',
        'jose',
        'jose.jwt',
        'jose.jws',
        'jose.constants',
        'jose.exceptions',
        'jose.utils',
        'jose.backends',
        'jose.backends.base',
        'jose.backends.cryptography_backend',
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.default_backend',
        'sqlalchemy.dialects.sqlite',
        'multipart',
        'multipart.multipart',
        'starlette',
        'starlette.requests',
        'starlette.responses',
        'starlette.routing',
        'starlette.middleware',
        'starlette.staticfiles',
        'starlette.templating',
        'uvicorn',
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
        'click',
        'click.core',
        'h11',
        'anyio',
        'anyio.abc',
        'anyio._backends',
        'anyio._backends._asyncio',
        'httpcore',
        'httpcore._async',
        'httpcore._backends',
        'httpcore._backends.auto',
        'httptools',
        'httptools.parser',
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'websockets.legacy.client',
        'watchfiles',
        'watchfiles.main',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'pytest',
        'sphinx',
    ],
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
    name='tic_nexus',
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
    icon=None,
)
'''
    
    if not SPEC_FILE.exists():
        print(f"Creating spec file: {SPEC_FILE}")
        with open(SPEC_FILE, 'w') as f:
            f.write(spec_content)
        print("Spec file created.\n")


def build_executable():
    """Build the executable using PyInstaller."""
    print("\nBuilding executable with PyInstaller...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    
    if result.returncode != 0:
        print(f"\nERROR: Build failed with code {result.returncode}")
        sys.exit(result.returncode)
    
    print("\nBuild completed successfully!")


def create_distribution(version: str):
    """Create distribution folder with all required files."""
    print(f"\nCreating distribution package v{version}...")
    
    dist_name = f"TIC_Nexus_v{version}"
    dist_path = DIST_DIR / dist_name
    
    if dist_path.exists():
        shutil.rmtree(dist_path)
    
    dist_path.mkdir(parents=True, exist_ok=True)
    
    exe_src = DIST_DIR / "tic_nexus.exe"
    exe_dst = dist_path / "tic_nexus.exe"
    if exe_src.exists():
        shutil.copy2(exe_src, exe_dst)
        print(f"  Copied: tic_nexus.exe")
    else:
        print(f"ERROR: Executable not found at {exe_src}")
        sys.exit(1)
    
    config_src = PROJECT_ROOT / "config.ini"
    config_dst = dist_path / "config.ini"
    if config_src.exists():
        shutil.copy2(config_src, config_dst)
        print(f"  Copied: config.ini")
    else:
        print(f"  WARNING: config.ini not found, creating default...")
        create_default_config(config_dst)
    
    (dist_path / "data").mkdir(exist_ok=True)
    print(f"  Created: data/")
    
    library_vault = dist_path / "library_vault" / "digital_books"
    library_vault.mkdir(parents=True, exist_ok=True)
    print(f"  Created: library_vault/digital_books/")
    
    uploads = dist_path / "static" / "uploads" / "magazines"
    uploads.mkdir(parents=True, exist_ok=True)
    print(f"  Created: static/uploads/magazines/")
    
    readme_path = dist_path / "README.txt"
    create_readme(readme_path, version)
    print(f"  Created: README.txt")
    
    print(f"\nDistribution created at: {dist_path}")
    
    total_size = sum(f.stat().st_size for f in dist_path.rglob("*") if f.is_file())
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    
    return dist_path


def create_default_config(config_path: Path):
    """Create a default config.ini file."""
    config_content = """[server]
# Server configuration
host = 0.0.0.0
port = 8000

[security]
# IMPORTANT: Change this secret key before first use!
# Generate a secure random string (at least 32 characters)
secret_key = CHANGE-THIS-SECRET-KEY-BEFORE-FIRST-USE

# Example for generating a secure key in Python:
# import secrets; print(secrets.token_urlsafe(32))
"""
    with open(config_path, "w") as f:
        f.write(config_content)


def create_readme(readme_path: Path, version: str):
    """Create README.txt for the distribution."""
    readme_content = f"""TIC Nexus v{version}
====================
Technical Information Center
Bharat Electronics Limited

SETUP INSTRUCTIONS
------------------

1. CONFIGURATION
   - Open config.ini in a text editor
   - IMPORTANT: Change the secret_key to a secure random string
     (at least 32 characters)
   - Optionally change the port if 8000 is already in use

2. FIRST RUN
   - Double-click tic_nexus.exe to start the server
   - A command window will open showing server status
   - Your browser should automatically open to http://localhost:8000
   - If not, manually open http://localhost:8000 in your browser

3. DEFAULT LOGIN
   - Username: admin
   - Password: admin123
   - IMPORTANT: Change the default password immediately after first login!

4. DATA STORAGE
   - Database: data/tic_nexus.db
   - Digital books: library_vault/digital_books/
   - Magazine uploads: static/uploads/magazines/

5. BACKUP
   - To backup, simply copy the following folders:
     * data/
     * library_vault/
     * static/uploads/
   - Keep config.ini safe (contains your secret key)

6. TROUBLESHOOTING
   - If the port is in use, change it in config.ini
   - If browser doesn't open, manually navigate to http://localhost:PORT
   - Check the command window for error messages

SYSTEM REQUIREMENTS
-------------------
- Windows 10 or later
- No Python installation required
- Network access for port 8000 (or configured port)

SUPPORT
-------
For issues or questions, contact your IT administrator.

Version: {version}
Build Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    with open(readme_path, "w") as f:
        f.write(readme_content)


def main():
    parser = argparse.ArgumentParser(
        description="Build TIC Nexus as a standalone executable"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version number for distribution folder (default: 1.0.0)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("  TIC Nexus Build Script")
    print("=" * 50)
    
    if args.clean:
        clean_build()
    
    check_requirements()
    
    create_spec_file()
    
    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        print("Run this script from the project root directory.")
        sys.exit(1)
    
    build_executable()
    
    create_distribution(args.version)
    
    print("\n" + "=" * 50)
    print("  BUILD COMPLETE!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Navigate to the dist/ folder")
    print("2. Copy the TIC_Nexus_v{version} folder to target machines")
    print("3. Edit config.ini and change the secret_key")
    print("4. Run tic_nexus.exe")


if __name__ == "__main__":
    main()
