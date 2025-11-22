#!/bin/bash
# PyInstaller Build Script for SubWeave

set -e  # Exit on error

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "SubWeave macOS App 빌드"
echo "=========================================="
echo ""

# Conda 환경 확인
ENV_NAME="subweave"

if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Conda가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo -e "${RED}✗ Conda 환경 '${ENV_NAME}'이 존재하지 않습니다.${NC}"
    echo "먼저 install.sh를 실행해주세요."
    exit 1
fi

# Conda 환경 활성화
echo "Conda 환경 활성화: ${ENV_NAME}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# PyInstaller 설치 확인
if ! pip show pyinstaller &> /dev/null; then
    echo "PyInstaller 설치 중..."
    pip install pyinstaller
fi

# 이전 빌드 정리
echo ""
echo "이전 빌드 정리 중..."
rm -rf build dist *.spec

# PyInstaller spec 파일 생성
echo "PyInstaller spec 파일 생성 중..."

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
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'whisper',
        'ctranslate2',
        'sentencepiece',
        'ffmpeg',
        'send2trash',
        'torch',
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
        'CFBundleDisplayName': 'SubWeave - Japanese to Korean Subtitle Generator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSMicrophoneUsageDescription': 'SubWeave needs access to process audio for subtitle generation.',
    },
)
EOF

# PyInstaller로 빌드
echo ""
echo "애플리케이션 빌드 중..."
pyinstaller SubWeave.spec --clean

# 빌드 성공 확인
if [ -d "dist/SubWeave.app" ]; then
    echo ""
    echo "=========================================="
    echo -e "${GREEN}✓ 빌드 완료!${NC}"
    echo "=========================================="
    echo ""
    echo "애플리케이션 위치:"
    echo "  dist/SubWeave.app"
    echo ""
    echo "테스트 실행:"
    echo "  open dist/SubWeave.app"
    echo ""
    echo -e "${YELLOW}참고사항:${NC}"
    echo "  • FFmpeg가 시스템에 설치되어 있어야 합니다: brew install ffmpeg"
    echo "  • 번역 모델은 앱 내에서 별도 다운로드 필요"
    echo ""
    echo "배포용 서명 및 공증:"
    echo "  1. codesign --deep --force --sign 'Developer ID Application' dist/SubWeave.app"
    echo "  2. ditto -c -k --keepParent dist/SubWeave.app SubWeave.zip"
    echo "  3. xcrun notarytool submit SubWeave.zip --apple-id YOUR_EMAIL --password YOUR_APP_PASSWORD --team-id YOUR_TEAM_ID"
    echo "  4. xcrun stapler staple dist/SubWeave.app"
    echo ""
else
    echo ""
    echo -e "${RED}✗ 빌드 실패${NC}"
    exit 1
fi
