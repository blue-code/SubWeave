#!/bin/bash
# PyInstaller Build Script for SubWeave

set -e  # Exit on error

echo "=================================="
echo "SubWeave Build Script"
echo "=================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Error: Virtual environment is not activated."
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

# Install PyInstaller if not already installed
if ! pip show pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.spec

# Create PyInstaller spec
echo "Creating PyInstaller spec..."

cat > SubWeave.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'faster_whisper',
        'ctranslate2',
        'sentencepiece',
        'mpv',
        'send2trash',
    ],
    hookspath=[],
    hooksconfig={},
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
    [],
    exclude_binaries=True,
    name='SubWeave',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SubWeave',
)

app = BUNDLE(
    coll,
    name='SubWeave.app',
    icon=None,
    bundle_identifier='com.subweave.app',
    info_plist={
        'CFBundleName': 'SubWeave',
        'CFBundleDisplayName': 'SubWeave',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
    },
)
EOF

# Build with PyInstaller
echo ""
echo "Building application with PyInstaller..."
pyinstaller SubWeave.spec --clean

# Check if build was successful
if [ -d "dist/SubWeave.app" ]; then
    echo ""
    echo "=================================="
    echo "Build completed successfully!"
    echo "=================================="
    echo ""
    echo "Application bundle created at:"
    echo "  dist/SubWeave.app"
    echo ""
    echo "To test the app:"
    echo "  open dist/SubWeave.app"
    echo ""
    echo "Note: You may need to install libmpv system-wide:"
    echo "  brew install mpv"
    echo ""
    echo "To sign and notarize for distribution:"
    echo "  1. codesign --deep --force --sign 'Developer ID' dist/SubWeave.app"
    echo "  2. zip -r SubWeave.zip dist/SubWeave.app"
    echo "  3. xcrun notarytool submit SubWeave.zip --apple-id YOUR_EMAIL --password YOUR_APP_PASSWORD"
    echo "  4. xcrun stapler staple dist/SubWeave.app"
    echo ""
else
    echo ""
    echo "Build failed!"
    exit 1
fi
