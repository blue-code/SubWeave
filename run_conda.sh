#!/bin/bash
# SubWeave 실행 스크립트 (Miniconda)

set -e  # Exit on error

# Conda 환경 이름
ENV_NAME="subweave"

echo "=========================================="
echo "SubWeave 실행"
echo "=========================================="
echo ""

# Miniconda 설치 확인
if ! command -v conda &> /dev/null; then
    echo "Error: Miniconda/Anaconda가 설치되어 있지 않습니다."
    echo "먼저 install_conda.sh를 실행하여 설치해주세요."
    exit 1
fi

# Conda 환경 존재 확인
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "Error: Conda 환경 '${ENV_NAME}'이 존재하지 않습니다."
    echo "먼저 install_conda.sh를 실행하여 환경을 설치해주세요:"
    echo "  ./install_conda.sh"
    exit 1
fi

# Conda 초기화 및 환경 활성화
echo "Conda 환경 활성화 중: ${ENV_NAME}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate ${ENV_NAME}

# Python 버전 확인
echo "Python 버전: $(python --version)"
echo ""

# Locale 설정 (UTF-8)
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# 애플리케이션 실행
echo "SubWeave 시작..."
echo ""

# 스크립트가 위치한 디렉토리 (subweave 내부)에서 main.py 직접 실행
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python main.py "$@"
